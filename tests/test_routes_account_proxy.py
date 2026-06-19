import httpx
import pytest

_UPSTREAM = "https://taos.my"


def _patch_upstream(monkeypatch, handler):
    """Patch httpx.AsyncClient.request so ONLY the proxy's upstream call (an
    absolute taos.my URL) is intercepted; the test client's own ASGI calls
    (relative URLs) pass through to the real request."""
    orig = httpx.AsyncClient.request

    async def routed(self, method, url, **kw):
        if str(url).startswith(_UPSTREAM):
            return await handler(method, str(url), **kw)
        return await orig(self, method, url, **kw)

    monkeypatch.setattr("httpx.AsyncClient.request", routed)


@pytest.mark.asyncio
async def test_account_me_503_when_unconfigured(client, monkeypatch):
    """No upstream configured -> the proxy reports unavailable so the Account
    pane shows its 'service unavailable' state."""
    monkeypatch.delenv("TAOS_ACCOUNT_BASE_URL", raising=False)
    r = await client.get("/api/account/me")
    assert r.status_code == 503
    assert "not configured" in r.json().get("error", "")


@pytest.mark.asyncio
async def test_account_me_forwards_and_relays_cookie(client, monkeypatch):
    """When configured, /api/account/me forwards to {base}/api/auth/me and the
    upstream Set-Cookie (the taos.my session) is relayed back to the browser."""
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my/")
    captured: dict[str, str] = {}

    class FakeResp:
        status_code = 200
        headers = httpx.Headers({"set-cookie": "taosgo_session=abc; Path=/"})

        def json(self):
            return {"user_id": "u1", "email": "a@b.c", "taosgo": {"status": "none"}}

    async def handler(method, url, **kw):
        captured["method"] = method
        captured["url"] = url
        return FakeResp()

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me")
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.c"
    # Trailing slash on the base is stripped; the auth path is appended once.
    assert captured["url"] == "https://taos.my/api/auth/me"
    assert captured["method"] == "GET"
    assert "taosgo_session=abc" in r.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_account_me_503_when_upstream_unreachable(client, monkeypatch):
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my")

    async def handler(method, url, **kw):
        raise httpx.ConnectError("down")

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me")
    assert r.status_code == 503
    assert "unreachable" in r.json().get("error", "")
