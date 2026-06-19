"""Tests for the ShibaClaw adapter: health endpoint, message proxying,
retry behaviour, and error handling."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import tinyagentos.adapters.shibaclaw_adapter as sc_mod
from tinyagentos.adapters.shibaclaw_adapter import app


# ---------------------------------------------------------------------------
# health endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_returns_ok():
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["framework"] == "shibaclaw"


# ---------------------------------------------------------------------------
# handle_message — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_message_returns_content_on_200(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"content": "hello from shibaclaw"}

    async def _mock_post(url, json):
        return mock_resp

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    result = await sc_mod.handle_message({"text": "hi"})
    assert result["content"] == "hello from shibaclaw"


@pytest.mark.asyncio
async def test_handle_message_sends_text_to_correct_url(monkeypatch):
    sent = {}

    async def _mock_post(url, json):
        sent["url"] = url
        sent["json"] = json
        return MagicMock(status_code=200, json=MagicMock(return_value={"content": "ok"}))

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    monkeypatch.setenv("SHIBACLAW_URL", "http://shibaclaw:19999")
    await sc_mod.handle_message({"text": "ping"})
    assert sent["url"] == "http://shibaclaw:19999/api/message"
    assert sent["json"] == {"text": "ping"}


# ---------------------------------------------------------------------------
# handle_message — non-200 status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_message_returns_status_text_on_non_200(monkeypatch):
    async def _mock_post(url, json):
        return MagicMock(status_code=503)

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    result = await sc_mod.handle_message({"text": "hi"})
    assert "503" in result["content"]


# ---------------------------------------------------------------------------
# handle_message — exception handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_message_returns_error_on_exception(monkeypatch):
    async def _mock_post(url, json):
        raise ConnectionError("refused")

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    result = await sc_mod.handle_message({"text": "hi"})
    assert "ShibaClaw not available" in result["content"]
    assert "refused" in result["content"]


@pytest.mark.asyncio
async def test_handle_message_includes_agent_name_in_error(monkeypatch):
    async def _mock_post(url, json):
        raise ConnectionError("down")

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    monkeypatch.setenv("TAOS_AGENT_NAME", "my-agent")
    result = await sc_mod.handle_message({"text": "hi"})
    assert "[my-agent]" in result["content"]


# ---------------------------------------------------------------------------
# handle_message — edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_message_empty_text(monkeypatch):
    sent = {}

    async def _mock_post(url, json):
        sent["json"] = json
        return MagicMock(status_code=200, json=MagicMock(return_value={"content": "ack"}))

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    result = await sc_mod.handle_message({})
    assert sent["json"]["text"] == ""
    assert result["content"] == "ack"


@pytest.mark.asyncio
async def test_handle_message_uses_default_url_when_env_not_set(monkeypatch):
    sent = {}

    async def _mock_post(url, json):
        sent["url"] = url
        return MagicMock(status_code=200, json=MagicMock(return_value={"content": "ok"}))

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    monkeypatch.delenv("SHIBACLAW_URL", raising=False)
    await sc_mod.handle_message({"text": "x"})
    assert sent["url"] == "http://localhost:19999/api/message"


@pytest.mark.asyncio
async def test_handle_message_falls_back_to_resp_text_when_no_content_key(monkeypatch):
    async def _mock_post(url, json):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {}
        resp.text = "raw text response"
        return resp

    monkeypatch.setattr(sc_mod, "_controller_post", _mock_post)
    result = await sc_mod.handle_message({"text": "hi"})
    assert result["content"] == "raw text response"
