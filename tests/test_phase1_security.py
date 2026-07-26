import os
import pytest
from fastapi.testclient import TestClient
from backend.api.routes import app
from backend.api.auth import hash_password, verify_password, create_access_token


def test_server_refuses_to_start_if_jwt_secret_unset(monkeypatch):
    """Assert server/auth raises RuntimeError if JWT_SECRET_KEY is missing or empty."""
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CRITICAL SECURITY ERROR: 'JWT_SECRET_KEY' environment variable is not set"):
        # Re-importing or accessing auth module without JWT_SECRET_KEY must fail
        import importlib
        import backend.api.auth
        importlib.reload(backend.api.auth)


def test_password_hashing_per_user_salt():
    """Assert two different calls with the same password produce different hashes due to per-user bcrypt salt."""
    pw = "SecretPassword123!"
    hash1 = hash_password(pw)
    hash2 = hash_password(pw)

    assert hash1 != hash2, "Bcrypt hashes for identical passwords must differ due to unique salts."
    assert verify_password(pw, hash1) is True
    assert verify_password(pw, hash2) is True
    assert verify_password("WrongPassword", hash1) is False


def test_export_endpoints_unauthenticated_returns_401():
    """Assert calling export endpoints without token returns 401 Unauthorized."""
    client = TestClient(app)

    res_json = client.get("/api/doctor/export/json/test-session-id")
    assert res_json.status_code == 401

    res_pdf = client.get("/api/doctor/export/pdf/test-session-id")
    assert res_pdf.status_code == 401

    res_pdf_alias = client.get("/api/doctor/sessions/export/pdf/test-session-id")
    assert res_pdf_alias.status_code == 401

    res_user_sessions = client.get("/api/patient/sessions/user/patient_john")
    assert res_user_sessions.status_code == 401


def test_export_endpoints_non_doctor_forbidden_returns_403():
    """Assert calling doctor export endpoints with patient token returns 403 Forbidden."""
    client = TestClient(app)
    patient_token = create_access_token({"sub": "pat-123", "username": "patient_test", "role": "patient"})
    headers = {"Authorization": f"Bearer {patient_token}"}

    res_json = client.get("/api/doctor/export/json/test-session-id", headers=headers)
    assert res_json.status_code == 403

    res_pdf = client.get("/api/doctor/export/pdf/test-session-id", headers=headers)
    assert res_pdf.status_code == 403

    res_user_sessions = client.get("/api/patient/sessions/user/other_patient_id", headers=headers)
    assert res_user_sessions.status_code == 403
