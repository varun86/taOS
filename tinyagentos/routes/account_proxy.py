"""Proxy for the taOSgo account service (taos.my) -- taOSgo Phase 1.

The taOS client (Settings > Account, the off-network screen) calls same-origin
/api/account/* so the taos.my base URL stays server-side and there is no CORS.
We forward to {TAOS_ACCOUNT_BASE_URL}/api/auth/* with cookie pass-through both
ways, so the taos.my session cookie round-trips through this host origin.

If TAOS_ACCOUNT_BASE_URL is unset the proxy returns 503 and the Account pane
renders its 'service unavailable' state, so the client ships ahead of taos.my.
"""
from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter()

# Only these account actions are proxied. The upstream base is operator config
# (env), never user input, so there is no open-proxy / SSRF surface.
_ACTIONS: dict[str, tuple[str, str]] = {
    "me": ("GET", "/api/auth/me"),
    "login": ("POST", "/api/auth/login"),
    "register": ("POST", "/api/auth/register"),
    "logout": ("POST", "/api/auth/logout"),
}

_TIMEOUT = httpx.Timeout(15.0)


def _base_url() -> str | None:
    base = os.environ.get("TAOS_ACCOUNT_BASE_URL", "").strip()
    return base.rstrip("/") or None


def _rewrite_set_cookie(value: str, secure_ok: bool) -> str:
    """Rescope an upstream Set-Cookie to this proxy origin so the browser
    accepts it: drop the Domain attribute (the cookie was issued for taos.my but
    the browser is talking to this host), and drop Secure when the proxy
    connection is not HTTPS, since a Secure cookie is rejected over plain HTTP."""
    kept: list[str] = []
    for part in value.split(";"):
        p = part.strip()
        low = p.lower()
        if low.startswith("domain="):
            continue
        if low == "secure" and not secure_ok:
            continue
        kept.append(p)
    return "; ".join(kept)


async def _forward(request: Request, action: str) -> Response:
    base = _base_url()
    if base is None:
        return JSONResponse(
            {"error": "account service not configured"}, status_code=503
        )
    method, path = _ACTIONS[action]
    headers: dict[str, str] = {}
    cookie = request.headers.get("cookie")
    if cookie:
        headers["Cookie"] = cookie
    body: bytes | None = None
    if method == "POST":
        body = await request.body()
        ctype = request.headers.get("content-type")
        if ctype:
            headers["Content-Type"] = ctype
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            upstream = await http.request(
                method, base + path, content=body, headers=headers
            )
    except httpx.HTTPError:
        return JSONResponse(
            {"error": "account service unreachable"}, status_code=503
        )
    # Relay the upstream body + content-type verbatim (do not assume JSON), so
    # error pages, redirects, and non-JSON bodies pass through unmangled.
    resp = Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
    )
    # Honor X-Forwarded-Proto so the cookie Secure attr survives a TLS-terminating
    # proxy (the taOSgo relay terminates HTTPS and forwards to us over http).
    fwd = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    secure_ok = request.url.scheme == "https" or fwd == "https"
    # Relay the session cookie (rescoped to this origin) plus a small allowlist of
    # response headers so redirects (Location) and auth challenges survive.
    _RELAY = {"location", "cache-control", "www-authenticate"}
    for name, value in upstream.headers.multi_items():
        low = name.lower()
        if low == "set-cookie":
            resp.raw_headers.append(
                (b"set-cookie", _rewrite_set_cookie(value, secure_ok).encode("latin-1"))
            )
        elif low in _RELAY:
            resp.raw_headers.append((low.encode("latin-1"), value.encode("latin-1")))
    return resp


@router.get("/api/account/me")
async def account_me(request: Request):
    return await _forward(request, "me")


@router.post("/api/account/login")
async def account_login(request: Request):
    return await _forward(request, "login")


@router.post("/api/account/register")
async def account_register(request: Request):
    return await _forward(request, "register")


@router.post("/api/account/logout")
async def account_logout(request: Request):
    return await _forward(request, "logout")
