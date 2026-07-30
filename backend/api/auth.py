import os
import uuid
import datetime
import hashlib
import logging
from typing import Optional, Dict, Any, Set
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import bcrypt
import jwt
from src.monitoring.logger import logger

# ── JWT Configuration ─────────────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: 'JWT_SECRET_KEY' environment variable is not set. "
        "The server cannot start without a secure JWT secret key."
    )
SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))   # 24h
REFRESH_TOKEN_EXPIRE_DAYS  = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

TOKEN_ISSUER = "clinical-multiagent-system"

# ── In-memory JWT blacklist (jti set) ─────────────────────────────────────────
# For production: replace with Redis or a DB table for persistence across restarts.
_revoked_jtis: Set[str] = set()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

_log = logging.getLogger(__name__)


# ── Password utilities ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with per-user salt."""
    pwd_bytes = password.encode("utf-8")[:72]  # bcrypt 72-byte limit
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against stored hash.
    Supports legacy SHA-256 scheme for smooth migration.
    """
    if not hashed_password:
        return False
    # Legacy SHA-256 detection (64 hex chars, no bcrypt prefix)
    if len(hashed_password) == 64 and not hashed_password.startswith("$2"):
        legacy_salt = "clinical_system_salt_2026"
        legacy_hash = hashlib.sha256((plain_password + legacy_salt).encode("utf-8")).hexdigest()
        return legacy_hash == hashed_password
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except (ValueError, TypeError) as e:
        logger.warning(f"[Auth] Password verification error: {e}")
        return False


def is_legacy_hash(hashed_password: str) -> bool:
    """Return True if the hash uses the deprecated SHA-256 scheme."""
    return bool(
        hashed_password
        and len(hashed_password) == 64
        and not hashed_password.startswith("$2")
    )


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Claims included:
      sub      — user ID
      username — display name
      role     — user role
      iat      — issued-at timestamp
      exp      — expiry timestamp
      jti      — unique token ID (for blacklisting)
      iss      — issuer identifier
    """
    to_encode = data.copy()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    expire = now_utc + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode.update({
        "iat": now_utc,
        "exp": expire,
        "jti": str(uuid.uuid4()),   # Unique token ID — enables per-token revocation
        "iss": TOKEN_ISSUER,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, username: str, role: str) -> str:
    """
    Create a long-lived refresh token (7 days).
    Refresh tokens carry a 'type': 'refresh' claim to distinguish them
    from access tokens and prevent misuse.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    expire = now_utc + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub":      user_id,
        "username": username,
        "role":     role,
        "type":     "refresh",
        "iat":      now_utc,
        "exp":      expire,
        "jti":      str(uuid.uuid4()),
        "iss":      TOKEN_ISSUER,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def revoke_token(jti: str) -> None:
    """Add a token's JTI to the revocation blacklist."""
    _revoked_jtis.add(jti)
    _log.info(f"[Auth] Token revoked | jti={jti}")


def is_token_revoked(jti: str) -> bool:
    """Return True if the token has been explicitly revoked (logged out)."""
    return jti in _revoked_jtis


# ── Token decoding ────────────────────────────────────────────────────────────

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.
    Raises HTTP 401 for any invalid/expired/revoked token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        logger.warning(f"[Auth] JWT decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check blacklist
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reject refresh tokens used as access tokens
    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cannot be used as an access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# ── FastAPI dependency functions ──────────────────────────────────────────────

def get_current_user(header_token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Require a valid access token. Raises 401 if missing or invalid."""
    if not header_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(header_token)
    user_id: str = payload.get("sub")
    username: str = payload.get("username")
    role: str = payload.get("role", "patient")

    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials in token",
        )
    return {
        "user_id":  user_id,
        "username": username,
        "role":     role,
        "jti":      payload.get("jti"),
    }


def get_current_user_with_query_fallback(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """Accept token from Authorization header OR ?token= query param (PDF downloads)."""
    token = header_token or request.query_params.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    username: str = payload.get("username")
    role: str = payload.get("role", "patient")

    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials in token",
        )
    return {
        "user_id":  user_id,
        "username": username,
        "role":     role,
        "jti":      payload.get("jti"),
    }


def get_optional_current_user(header_token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Return authenticated user if token present; otherwise return anonymous guest."""
    if not header_token:
        return {"user_id": "guest", "username": "guest", "role": "patient", "jti": None}

    try:
        payload = jwt.decode(header_token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            return {"user_id": "guest", "username": "guest", "role": "patient", "jti": None}
        return {
            "user_id":  payload.get("sub", "guest"),
            "username": payload.get("username", "guest"),
            "role":     payload.get("role", "patient"),
            "jti":      jti,
        }
    except Exception:
        return {"user_id": "guest", "username": "guest", "role": "patient", "jti": None}


def require_doctor(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency that enforces Doctor role. Raises 403 for non-doctors."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Doctor role required",
        )
    return current_user
