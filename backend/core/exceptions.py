"""
backend/core/exceptions.py

Typed exception hierarchy for the Clinical Multi-Agent System.

Instead of bare `except Exception: raise HTTPException(500, str(e))` everywhere,
raise domain-specific exceptions. A global exception handler registered in routes.py
converts them to structured JSON responses with machine-readable error codes.

Error code format:  <DOMAIN>-<HTTP_STATUS>
  DB   — database errors
  PLN  — pipeline errors
  NER  — NER / extraction errors
  AUTH — authentication / authorisation errors
  VAL  — validation errors
  CLN  — clinical / business rule errors
"""

import datetime
import logging
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Base exception ─────────────────────────────────────────────────────────────

class ClinicalSystemError(Exception):
    """
    Base class for all application-level exceptions.

    Attributes
    ----------
    error_code  : Machine-readable code (e.g. "DB-500")
    status_code : HTTP status to return
    message     : Human-readable description
    """
    error_code:  str = "SYS-500"
    status_code: int = 500

    def __init__(self, message: str, *, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.detail  = detail or message


# ── Domain exceptions ──────────────────────────────────────────────────────────

class DatabaseError(ClinicalSystemError):
    """Raised when a database operation fails (connection, integrity, timeout)."""
    error_code  = "DB-500"
    status_code = 500


class PipelineError(ClinicalSystemError):
    """Raised when the NLP pipeline encounters a non-recoverable failure."""
    error_code  = "PLN-500"
    status_code = 500


class PipelineTimeoutError(ClinicalSystemError):
    """Raised when a pipeline stage exceeds its configured timeout."""
    error_code  = "PLN-504"
    status_code = 504


class NERError(ClinicalSystemError):
    """Raised when an NER agent fails to extract entities."""
    error_code  = "NER-500"
    status_code = 500


class AuthError(ClinicalSystemError):
    """Raised for authentication and authorisation failures."""
    error_code  = "AUTH-401"
    status_code = 401


class ForbiddenError(ClinicalSystemError):
    """Raised when a user attempts an action they are not authorised for."""
    error_code  = "AUTH-403"
    status_code = 403


class ValidationError(ClinicalSystemError):
    """Raised when request input fails clinical or schema validation."""
    error_code  = "VAL-422"
    status_code = 422


class ClinicalRuleError(ClinicalSystemError):
    """Raised when input violates an impossible clinical combination (e.g. male + pregnant)."""
    error_code  = "CLN-422"
    status_code = 422


class ConcurrentUpdateError(ClinicalSystemError):
    """Raised when optimistic locking detects a concurrent modification."""
    error_code  = "DB-409"
    status_code = 409


class ServiceUnavailableError(ClinicalSystemError):
    """Raised when a required service (LLM, ChromaDB, coordinator) is not ready."""
    error_code  = "SVC-503"
    status_code = 503


# ── Global exception handler ───────────────────────────────────────────────────

async def clinical_error_handler(request: Request, exc: ClinicalSystemError) -> JSONResponse:
    """
    Convert ClinicalSystemError subclasses into consistent JSON error responses.

    Response shape:
    {
        "error_code": "DB-500",
        "message":    "Human-readable description",
        "request_id": "uuid",
        "timestamp":  "2026-07-30T07:00:00Z"
    }
    """
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"[{exc.error_code}] {exc.message} | path={request.url.path} "
        f"| request_id={request_id}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message":    exc.message,
            "request_id": request_id,
            "timestamp":  datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    Logs the full traceback but returns a safe generic message to the client
    (never leaks internal details or patient data in error responses).
    """
    import traceback
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"[SYS-500] Unhandled exception | path={request.url.path} "
        f"| request_id={request_id}\n{traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "SYS-500",
            "message":    "An unexpected internal error occurred. Please try again or contact support.",
            "request_id": request_id,
            "timestamp":  datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    )
