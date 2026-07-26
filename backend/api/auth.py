import os
import datetime
import hashlib
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import bcrypt
import jwt
from src.monitoring.logger import logger

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: 'JWT_SECRET_KEY' environment variable is not set. "
        "The server cannot start without a secure JWT secret key."
    )
SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def hash_password(password: str) -> str:
    """Hashes password using bcrypt with per-user salt."""
    pwd_bytes = password.encode("utf-8")[:72]  # Truncate to bcrypt 72 byte limit
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed password, supporting legacy SHA-256 scheme for smooth migration."""
    if not hashed_password:
        return False
    # Legacy SHA-256 format check (64 hex characters)
    if len(hashed_password) == 64 and not hashed_password.startswith("$2"):
        legacy_salt = "clinical_system_salt_2026"
        legacy_hash = hashlib.sha256((plain_password + legacy_salt).encode("utf-8")).hexdigest()
        return legacy_hash == hashed_password
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except (ValueError, TypeError) as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def is_legacy_hash(hashed_password: str) -> bool:
    """Returns True if the hashed password uses the deprecated SHA-256 scheme."""
    return bool(hashed_password and len(hashed_password) == 64 and not hashed_password.startswith("$2"))


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"JWT token decoding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(header_token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Retrieve authenticated current user strictly from Authorization header."""
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

    if user_id is None or username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials in token"
        )
    return {"user_id": user_id, "username": username, "role": role}


def get_current_user_with_query_fallback(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """Retrieve user from Header or Query Param (restricted for PDF download routes)."""
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

    if user_id is None or username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials in token"
        )
    return {"user_id": user_id, "username": username, "role": role}


def get_optional_current_user(header_token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Retrieve user if token present in header; otherwise return anonymous guest dict."""
    if not header_token:
        return {"user_id": "guest", "username": "guest", "role": "patient"}

    try:
        payload = jwt.decode(header_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub", "guest")
        username: str = payload.get("username", "guest")
        role: str = payload.get("role", "patient")
        return {"user_id": user_id, "username": username, "role": role}
    except Exception:
        return {"user_id": "guest", "username": "guest", "role": "patient"}


def require_doctor(current_user: Dict[str, Any] = Depends(get_current_user)):
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Doctor role required"
        )
    return current_user
