"""Adds security headers (CSP, X-Frame-Options, X-Content-Type-Options) to every response."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# connect-src includes ws:/wss: so WebSocket upgrades are permitted.
# style-src includes 'unsafe-inline' because the server-rendered auth pages
# embed styles inline (no build step there).
_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https: blob:; "
    # data: lets the canvas (tldraw) load its bundled translation URIs
    # (data:application/json), which are inline data, not a network fetch.
    "connect-src 'self' ws: wss: data:"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", _CSP)
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response
