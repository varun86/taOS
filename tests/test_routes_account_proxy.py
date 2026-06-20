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


class _FakeResp:
    def __init__(self, content=b"{}", status=200, headers=None):
        self.content = content
        self.status_code = status
        self.headers = httpx.Headers(headers or {})


@pytest.mark.asyncio
async def test_account_me_503_when_unconfigured(client, monkeypatch):
    monkeypatch.delenv("TAOS_ACCOUNT_BASE_URL", raising=False)
    r = await client.get("/api/account/me")
    assert r.status_code == 503
    assert "not configured" in r.json().get("error", "")


@pytest.mark.asyncio
async def test_account_me_forwards_body_and_relays_cookie(client, monkeypatch):
    """/api/account/me forwards to {base}/api/auth/me; the upstream body and
    content-type pass through verbatim and the session cookie is relayed."""
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my/")
    captured: dict[str, str] = {}

    async def handler(method, url, **kw):
        captured["method"] = method
        captured["url"] = url
        return _FakeResp(
            content=b'{"user_id":"u1","email":"a@b.c","taosgo":{"status":"none"}}',
            headers={
                "content-type": "application/json",
                "set-cookie": "taosgo_session=abc; Path=/",
            },
        )

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me")
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.c"
    assert captured["url"] == "https://taos.my/api/auth/me"
    assert captured["method"] == "GET"
    assert "taosgo_session=abc" in r.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_set_cookie_rescoped_to_proxy_origin(client, monkeypatch):
    """A taos.my cookie carrying Domain + Secure must be rescoped to this
    origin, or the browser rejects it: Domain is stripped, and Secure is
    dropped because the test client speaks http. Other attrs are preserved."""
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my")

    async def handler(method, url, **kw):
        return _FakeResp(
            content=b"{}",
            headers={
                "content-type": "application/json",
                "set-cookie": "taosgo_session=abc; Path=/; Domain=taos.my; Secure; HttpOnly",
            },
        )

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me")
    sc = r.headers.get("set-cookie", "")
    assert "taosgo_session=abc" in sc
    assert "domain=" not in sc.lower()
    assert "secure" not in sc.lower()
    assert "HttpOnly" in sc


@pytest.mark.asyncio
async def test_account_me_503_when_upstream_unreachable(client, monkeypatch):
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my")

    async def handler(method, url, **kw):
        raise httpx.ConnectError("down")

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me")
    assert r.status_code == 503
    assert "unreachable" in r.json().get("error", "")


@pytest.mark.asyncio
async def test_secure_kept_when_x_forwarded_proto_https_and_trusted(client, monkeypatch):
    """Behind a TLS-terminating proxy the request scheme is http but the browser
    leg is https (X-Forwarded-Proto). When the deployment trusts that header
    (TAOS_TRUST_FORWARDED_PROTO), the cookie Secure attr must be kept."""
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my")
    monkeypatch.setenv("TAOS_TRUST_FORWARDED_PROTO", "1")

    async def handler(method, url, **kw):
        return _FakeResp(
            headers={"content-type": "application/json", "set-cookie": "s=1; Path=/; Secure"}
        )

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me", headers={"x-forwarded-proto": "https"})
    assert "secure" in r.headers.get("set-cookie", "").lower()


@pytest.mark.asyncio
async def test_x_forwarded_proto_ignored_when_untrusted(client, monkeypatch):
    """Without the trust opt-in, X-Forwarded-Proto is client-spoofable, so it is
    ignored and Secure is dropped over the plain-http test connection."""
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my")
    monkeypatch.delenv("TAOS_TRUST_FORWARDED_PROTO", raising=False)

    async def handler(method, url, **kw):
        return _FakeResp(
            headers={"content-type": "application/json", "set-cookie": "s=1; Path=/; Secure"}
        )

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me", headers={"x-forwarded-proto": "https"})
    assert "secure" not in r.headers.get("set-cookie", "").lower()


@pytest.mark.asyncio
async def test_redirect_location_is_relayed(client, monkeypatch):
    monkeypatch.setenv("TAOS_ACCOUNT_BASE_URL", "https://taos.my")

    async def handler(method, url, **kw):
        return _FakeResp(content=b"", status=302, headers={"location": "https://taos.my/login"})

    _patch_upstream(monkeypatch, handler)
    r = await client.get("/api/account/me", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("location") == "https://taos.my/login"
