import os
import uuid
import logging
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, model_validator
from typing import Optional, Dict, Any

from backend.database.connection import engine, Base, get_db, SessionLocal
from backend.database.mysql_store import MySQLStore
from backend.orchestrator.coordinator import Coordinator
from backend.api.auth import (
    create_access_token, create_refresh_token, revoke_token,
    hash_password, verify_password, is_legacy_hash,
    get_current_user, get_optional_current_user, SECRET_KEY, ALGORITHM
)
from backend.api.doctor_routes import router as doctor_router
from backend.api.patient_routes import router as patient_router
from backend.core.middleware import SecurityHeadersMiddleware, RequestIDMiddleware, RateLimitMiddleware
from backend.core.exceptions import (
    ClinicalSystemError, ConcurrentUpdateError,
    clinical_error_handler, unhandled_error_handler
)
from backend.services.audit_service import log_action, ACTION_LOGIN_SUCCESS, ACTION_LOGIN_FAILED, ACTION_REGISTER, ACTION_LOGOUT
import jwt as _jwt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application-wide coordinator singleton — stateless, holds loaded AI models
# Instantiated ONCE at startup; DB session is NEVER stored inside it.
# ---------------------------------------------------------------------------
_shared_coordinator: Optional[Coordinator] = None


def get_coordinator() -> Coordinator:
    """FastAPI dependency — returns the stateless application-wide coordinator."""
    if _shared_coordinator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is initialising, please retry in a moment."
        )
    return _shared_coordinator


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _shared_coordinator
    # ── Step 1: Database tables ───────────────────────────────────────────────
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("[Startup] Database tables verified/created.")
    except Exception as e:
        logger.error(f"[Startup] Table creation warning: {e}")

    # ── Step 2: Seed demo accounts ────────────────────────────────────────────
    try:
        db_seed = SessionLocal()
        mysql_store = MySQLStore(db_seed)

        if not mysql_store.get_user_by_username("dr_jenkins"):
            mysql_store.create_user(
                username="dr_jenkins",
                email="doctor@hospital.org",
                hashed_password=hash_password("password123"),
                role="doctor",
                full_name="Dr. Sarah Jenkins (Cardiologist)"
            )
            logger.info("[Startup] Seeded demo doctor account.")

        if not mysql_store.get_user_by_username("patient_john"):
            mysql_store.create_user(
                username="patient_john",
                email="john.doe@patient.org",
                hashed_password=hash_password("password123"),
                role="patient",
                full_name="John Doe (PAT-88421)"
            )
            logger.info("[Startup] Seeded demo patient account.")

        db_seed.close()
    except Exception as e:
        logger.error(f"[Startup] Demo account seeding failed (non-fatal): {e}")

    # ── Step 3: Seed demo ReviewQueue ─────────────────────────────────────────
    try:
        db_seed2 = SessionLocal()
        from backend.database.models import ReviewQueue
        if db_seed2.query(ReviewQueue).count() == 0:
            ms2 = MySQLStore(db_seed2)
            pat = ms2.get_user_by_username("patient_john")
            pat_id = pat.id if pat else None
            doc1_id = str(uuid.uuid4())
            sess1_id = str(uuid.uuid4())
            sample_note = (
                "Patient: John Doe, 58-year-old male presenting with acute chest pain, "
                "shortness of breath, and dizziness. BP 160/95, HR 102 bpm, RR 20/min. "
                "Labs: Troponin-I 0.12 ng/mL, BNP 320 pg/mL. ECG: ST elevation in "
                "anterolateral leads. History of Type 2 Diabetes Mellitus and Essential "
                "Hypertension. Medications: Metformin 500mg PO BID, Lisinopril 10mg PO OD. "
                "Impression: Acute STEMI in patient with poorly controlled T2DM and HTN."
            )
            ms2.create_document(doc1_id, sample_note, {"patient_id": "PAT-88421"}, user_id=pat_id)
            ms2.create_session(sess1_id, doc1_id)
            ms2.update_session(sess1_id, "COMPLETED", "FINISHED")
            ms2.save_patient_history(
                user_id=pat_id or "anonymous_patient",
                session_id=sess1_id,
                summary_json=[
                    {
                        "disease": "Acute STEMI",
                        "symptoms": ["chest pain", "shortness of breath", "dizziness"],
                        "medication": {
                            "name": "Metformin", "dosage": "500mg",
                            "frequency": "PO BID", "duration": "Ongoing"
                        }
                    },
                    {
                        "disease": "Type 2 Diabetes Mellitus",
                        "symptoms": ["elevated HbA1c"],
                        "medication": {
                            "name": "Lisinopril", "dosage": "10mg",
                            "frequency": "PO OD", "duration": "Ongoing"
                        }
                    }
                ]
            )
            ms2.save_session_review_entry(session_id=sess1_id, user_id=pat_id)
            logger.info("[Startup] Seeded demo ReviewQueue session for patient_john.")
        db_seed2.close()
    except Exception as e:
        logger.error(f"[Startup] ReviewQueue seeding failed (non-fatal): {e}")

    # ── Step 4: Build the stateless coordinator (heavy AI model load) ─────────
    try:
        _shared_coordinator = Coordinator()
        logger.info("[Startup] Coordinator singleton initialised — all agents ready.")
    except Exception as e:
        logger.critical(f"[Startup] CRITICAL — Coordinator failed to initialise: {e}")
        # Do NOT re-raise; server still starts — requests return 503 via get_coordinator()

    yield  # ── Server is now live ─────────────────────────────────────────────

    # ── Cleanup ───────────────────────────────────────────────────────────────
    _shared_coordinator = None
    logger.info("[Shutdown] Coordinator released.")


# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Clinical Multi-Agent Information Extraction & Decision Support API",
    description="Full-Stack Production Clinical NLP & Decision Support System",
    version="2.1.0",
    lifespan=lifespan
)

# ── CORS ──────────────────────────────────────────────────────────────────────
cors_origins_raw = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
)
allowed_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        *allowed_origins,
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ── Security middleware stack ──────────────────────────────────────────────────
# Order matters: outer middleware wraps inner middleware.
# RequestID must be first so all subsequent layers can read request.state.request_id.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

# ── Global exception handlers ─────────────────────────────────────────────────
app.add_exception_handler(ClinicalSystemError, clinical_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
# Include once with /api/v1 prefix; keep bare aliases only for critical endpoints
app.include_router(doctor_router, prefix="/api/v1")
app.include_router(patient_router, prefix="/api/v1")


# ── Request / Response models ─────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "patient"  # 'doctor' or 'patient'
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ExtractNoteRequest(BaseModel):
    content: Optional[str] = None
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def check_content_or_text(cls, values):
        if isinstance(values, dict):
            c = values.get("content") or values.get("text")
            if not c:
                raise ValueError("Either 'content' or 'text' must be provided.")
            values["content"] = c
            values["text"] = c
        return values


from backend.core.phi_filter import apply_phi_filter_to_root
from backend.core.metrics import metrics_collector
from backend.core.cache import pipeline_cache
from backend.core.pool_monitor import ConnectionPoolMonitor

apply_phi_filter_to_root()

# ── Health & Metrics endpoints ────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Clinical Multi-Agent NLP System",
        "version": "2.1.0"
    }


@app.get("/api/health")
def api_health_check(db: Session = Depends(get_db)):
    import time as _t
    import platform as _p
    import sys as _s
    from backend.database.connection import engine

    # Probe DB pool & query latency
    t0 = _t.time()
    db_ok = False
    try:
        db.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    db_latency_ms = round((_t.time() - t0) * 1000, 2)

    pool_info = ConnectionPoolMonitor.inspect_pool(engine)

    overall_status = "HEALTHY" if (db_ok and _shared_coordinator is not None) else "DEGRADED"

    return {
        "status": overall_status,
        "service": "Clinical Multi-Agent NLP System",
        "version": "2.1.0",
        "timestamp": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
        "python_version": _s.version.split()[0],
        "platform": _p.system(),
        "subsystems": {
            "database": {"status": "OPERATIONAL" if db_ok else "UNAVAILABLE", "latency_ms": db_latency_ms},
            "db_connection_pool": pool_info,
            "coordinator_ai_agents": "OPERATIONAL" if _shared_coordinator is not None else "INITIALIZING",
        }
    }


@app.get("/metrics")
@app.get("/api/metrics")
@app.get("/api/v1/metrics")
def get_system_metrics(response_format: Optional[str] = None):
    """
    Exposes operational metrics. Returns JSON or OpenMetrics (Prometheus) format.
    """
    if response_format == "prometheus":
        return Response(content=metrics_collector.export_openmetrics(), media_type="text/plain; version=0.0.4")
    return metrics_collector.get_metrics_summary()


# ── Auth endpoints ────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def register_user(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user account."""
    mysql_store = MySQLStore(db)

    if mysql_store.get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if mysql_store.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pw = hash_password(req.password)
    user = mysql_store.create_user(
        username=req.username,
        email=req.email,
        hashed_password=hashed_pw,
        role=req.role.lower(),
        full_name=req.full_name
    )
    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    refresh = create_refresh_token(user.id, user.username, user.role)

    log_action(
        db=db, action=ACTION_REGISTER,
        actor_user_id=user.id, resource_type="User", resource_id=user.id,
        new_value=f"username={user.username} role={user.role}",
        ip_address=request.client.host if request.client else None,
    )
    return {
        "access_token":  token,
        "refresh_token": refresh,
        "token_type":    "bearer",
        "user": {
            "id":        user.id,
            "username":  user.username,
            "email":     user.email,
            "role":      user.role,
            "full_name": user.full_name
        }
    }


@app.post("/api/auth/login")
def login_user(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access + refresh tokens."""
    mysql_store = MySQLStore(db)
    user = mysql_store.get_user_by_username(req.username)
    client_ip = request.client.host if request.client else None

    if not user or not verify_password(req.password, user.hashed_password):
        log_action(db=db, action=ACTION_LOGIN_FAILED, resource_type="User",
                   new_value=req.username, ip_address=client_ip)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Seamless hash migration: upgrade legacy SHA-256 → bcrypt on first login
    if is_legacy_hash(user.hashed_password):
        user.hashed_password = hash_password(req.password)
        db.commit()
        logger.info(f"[Auth] Migrated legacy password hash for user '{req.username}'")

    token   = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    refresh = create_refresh_token(user.id, user.username, user.role)

    log_action(db=db, action=ACTION_LOGIN_SUCCESS, actor_user_id=user.id,
               resource_type="User", resource_id=user.id, ip_address=client_ip)
    logger.info(f"[Auth] Successful login for user '{req.username}' (role={user.role})")
    return {
        "access_token":  token,
        "refresh_token": refresh,
        "token_type":    "bearer",
        "user": {
            "id":        user.id,
            "username":  user.username,
            "email":     user.email,
            "role":      user.role,
            "full_name": user.full_name
        }
    }


@app.post("/api/auth/token", include_in_schema=False)
def token_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 form-data login — used by Swagger UI Authorize button only."""
    mysql_store = MySQLStore(db)
    user = mysql_store.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if is_legacy_hash(user.hashed_password):
        user.hashed_password = hash_password(form_data.password)
        db.commit()

    access_token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/refresh")
def refresh_access_token(request: Request, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    Refresh token must be sent in the Authorization: Bearer <token> header.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Refresh token required.")
    refresh_token = auth_header[7:]

    try:
        payload = _jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except _jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {e}")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Provided token is not a refresh token.")

    user_id  = payload.get("sub")
    username = payload.get("username")
    role     = payload.get("role", "patient")

    new_access = create_access_token({"sub": user_id, "username": username, "role": role})
    logger.info(f"[Auth] Access token refreshed for user '{username}'")
    return {"access_token": new_access, "token_type": "bearer"}


@app.post("/api/auth/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Revoke the current access token.
    The token's JTI is added to the in-memory blacklist — subsequent requests
    with this token will receive HTTP 401.
    """
    jti = current_user.get("jti")
    if jti:
        revoke_token(jti)

    log_action(
        db=db, action=ACTION_LOGOUT,
        actor_user_id=current_user.get("user_id"),
        resource_type="User", resource_id=current_user.get("user_id"),
        ip_address=request.client.host if request.client else None,
    )
    logger.info(f"[Auth] User '{current_user.get('username')}' logged out | jti={jti}")
    return {"status": "success", "message": "Logged out successfully."}


@app.get("/api/auth/me")
def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return the currently authenticated user's profile."""
    mysql_store = MySQLStore(db)
    user = mysql_store.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name
    }


# ── Clinical NLP pipeline endpoint ───────────────────────────────────────────

@app.post("/api/v1/extract")
@app.post("/api/extract")
def extract_clinical_note(
    req: ExtractNoteRequest,
    db: Session = Depends(get_db),
    coordinator: Coordinator = Depends(get_coordinator)
):
    """
    Run the full clinical NLP pipeline with caching and duplicate request protection.
    """
    note_text = req.content

    # Check cache
    cached_result = pipeline_cache.get(note_text)
    if cached_result:
        logger.info("[Extract] Serving cached pipeline output.")
        return cached_result

    # Check duplicate pending execution
    if pipeline_cache.is_processing(note_text):
        raise HTTPException(
            status_code=429,
            detail="A request with identical clinical note content is currently being processed. Please wait a moment."
        )

    pipeline_cache.mark_processing(note_text)
    try:
        result = coordinator.run_pipeline(
            document_content=note_text,
            db=db,
            doc_metadata=req.metadata
        )
        pipeline_cache.put(note_text, result)
        return result
    except Exception as e:
        pipeline_cache.clear_processing(note_text)
        import traceback
        logger.error(f"[Extract] Pipeline error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Session summary & PDF endpoints ──────────────────────────────────────────

@app.get("/api/v1/summary/{session_id}")
@app.get("/api/summary/{session_id}")
def get_session_summary(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_optional_current_user)
):
    """Return structured summary for a completed pipeline session."""
    from backend.database.models import PipelineSession, MedicationRelation, DiseaseRelation

    session = db.query(PipelineSession).filter(PipelineSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    med_rels = db.query(MedicationRelation).filter(MedicationRelation.session_id == session_id).all()
    dis_rels = db.query(DiseaseRelation).filter(DiseaseRelation.session_id == session_id).all()

    structured = []
    for mr in med_rels:
        syms = [r.symptom_name for r in dis_rels if r.disease_name == mr.disease_name]
        structured.append({
            "disease": mr.disease_name,
            "symptoms": syms,
            "medication": {
                "name": mr.medication_name,
                "dosage": mr.dosage,
                "frequency": mr.frequency,
                "duration": mr.duration,
                "route": mr.route or "Oral",
                "validation_status": "Verified" if mr.correct else "Needs Review",
            }
        })

    return {
        "session_id": session_id,
        "status": session.status,
        "created_at": session.created_at.isoformat() + "Z" if session.created_at else None,
        "structured_summary": structured,
    }


@app.get("/api/v1/report/{session_id}")
@app.get("/api/v1/pdf/{session_id}")
@app.get("/api/report/{session_id}")
def export_direct_session_pdf(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_optional_current_user)
):
    """Directly stream PDF report for browser tab navigation."""
    from backend.utils.pdf_generator import generate_clinical_report_pdf
    from backend.database.models import PipelineSession, MedicationRelation, DiseaseRelation

    session = db.query(PipelineSession).filter(PipelineSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    med_rels = db.query(MedicationRelation).filter(MedicationRelation.session_id == session_id).all()
    dis_rels = db.query(DiseaseRelation).filter(DiseaseRelation.session_id == session_id).all()

    patient_summary = []
    for mr in med_rels:
        syms = [r.symptom_name for r in dis_rels if r.disease_name == mr.disease_name]
        patient_summary.append({
            "disease": mr.disease_name,
            "symptoms": syms or ["General symptoms"],
            "medication": {
                "name": mr.medication_name,
                "dosage": mr.dosage,
                "frequency": mr.frequency,
                "duration": mr.duration,
                "route": mr.route or "PO (Oral)",
                "validation_status": "Verified",
            }
        })

    json_data = {
        "session_id": session_id,
        "status": session.status,
        "patient_summary": {"structured_summary": patient_summary},
        "doctor_report": "Clinical Intelligence Summary Report",
    }
    pdf_bytes = generate_clinical_report_pdf(json_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="clinical_report_{session_id[:8]}.pdf"',
            "Content-Type": "application/pdf",
        }
    )
