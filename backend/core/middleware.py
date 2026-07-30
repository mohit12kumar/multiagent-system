"""
backend/core/middleware.py

Enterprise-grade FastAPI middleware stack:
  1. SecurityHeadersMiddleware — adds HTTP security headers to every response
  2. RequestIDMiddleware       — attaches a unique X-Request-ID to every request/response
  3. RateLimitMiddleware       — simple in-memory per-IP rate limiter (100 req/min)
"""

import uuid
import time
import logging
from collections import defaultdict, deque
from typing import Callable, Deque

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Attach HTTP security headers to every response.
    These protect against XSS, clickjacking, MIME sniffing, and info leakage.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]   = "nosniff"
        response.headers["X-Frame-Options"]          = "DENY"
        response.headers["X-XSS-Protection"]         = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        # NOTE: HSTS is intentionally omitted here — enable at the reverse proxy
        # (nginx/Caddy) level in production to avoid issues during development.
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Generate a unique UUID for every incoming request and attach it to:
      - request.state.request_id  (available to all route handlers)
      - X-Request-ID response header (visible to API consumers and log correlators)

    Use request.state.request_id in error responses for traceability.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding-window rate limiter.

    Default: 100 requests per 60-second window per client IP.

    Limitations (acceptable for clinical intranet deployment):
      - State is in-memory — resets on server restart.
      - Does not work across multiple server processes/pods.
      - For multi-process production: replace with Redis-backed rate limiting
        (e.g., slowapi + redis).

    Excluded paths:
      /api/health, / — always allowed (used by load balancer health checks).
    """

    EXCLUDED_PATHS = {"/", "/api/health", "/docs", "/openapi.json", "/redoc"}
    MAX_REQUESTS   = 100   # requests
    WINDOW_SECONDS = 60    # per window

    def __init__(self, app, max_requests: int = MAX_REQUESTS, window_seconds: int = WINDOW_SECONDS):
        super().__init__(app)
        self.max_requests    = max_requests
        self.window_seconds  = window_seconds
        # {ip: deque of timestamps}
        self._request_log: dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self.window_seconds

        timestamps = self._request_log[client_ip]

        # Evict timestamps outside the current window
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            logger.warning(
                f"[RateLimit] IP {client_ip} exceeded {self.max_requests} req/{self.window_seconds}s"
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE-429",
                    "message": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds.",
                    "retry_after_seconds": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        timestamps.append(now)
        return await call_next(request)
