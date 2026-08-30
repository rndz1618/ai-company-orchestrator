"""Minimal API-key auth for Phase 2.1.

If settings.ORCHESTRATOR_API_KEY is set, every /api/* request must send:
    X-API-Key: <key>
or
    Authorization: Bearer <key>

Health and root remain open.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    OPEN_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        expected = settings.ORCHESTRATOR_API_KEY
        if not expected:
            # Auth disabled (local dev)
            return await call_next(request)

        path = request.url.path
        if path in self.OPEN_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        provided = request.headers.get("X-API-Key")
        if not provided:
            auth = request.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                provided = auth[7:].strip()

        if not provided or provided != expected:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key", "error": "unauthorized"},
            )
        return await call_next(request)
