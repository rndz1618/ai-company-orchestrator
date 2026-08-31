"""Simple in-memory sliding-window rate limiter.

Not distributed — fine for single-instance MVP. Replace with Redis for multi-instance.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class _Window:
    def __init__(self):
        self.hits: deque[float] = deque()
        self.lock = Lock()


class RateLimitMiddleware(BaseHTTPMiddleware):
    OPEN_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app):
        super().__init__(app)
        self._windows: dict[str, _Window] = defaultdict(_Window)

    def _client_key(self, request: Request) -> str:
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            auth = request.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                api_key = auth[7:].strip()
        if api_key:
            return f"key:{api_key[:32]}"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        client = request.client.host if request.client else "unknown"
        return f"ip:{client}"

    def _allow(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        w = self._windows[key]
        now = time.time()
        with w.lock:
            while w.hits and w.hits[0] <= now - window:
                w.hits.popleft()
            if len(w.hits) >= limit:
                retry_after = int(window - (now - w.hits[0])) + 1
                return False, max(1, retry_after)
            w.hits.append(now)
            return True, 0

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if path in self.OPEN_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        key = self._client_key(request)

        if path.startswith("/api/execution"):
            limit = settings.RATE_LIMIT_EXECUTION_REQUESTS
            window = settings.RATE_LIMIT_EXECUTION_WINDOW_SECONDS
            bucket = f"exec:{key}"
        else:
            limit = settings.RATE_LIMIT_REQUESTS
            window = settings.RATE_LIMIT_WINDOW_SECONDS
            bucket = f"api:{key}"

        ok, retry_after = self._allow(bucket, limit, window)
        if not ok:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Retry after {retry_after}s.",
                    "error": "rate_limited",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
