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
from fastapi import APIRouter, Request
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


async def _forward(request: Request, action: str) -> JSONResponse:
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
    try:
        payload = upstream.json()
    except ValueError:
        payload = {}
    resp = JSONResponse(payload, status_code=upstream.status_code)
    # Pass the upstream session cookie back to the browser (scoped to this host).
    for name, value in upstream.headers.multi_items():
        if name.lower() == "set-cookie":
            resp.raw_headers.append((b"set-cookie", value.encode("latin-1")))
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
