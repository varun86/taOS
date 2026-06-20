import pytest
from unittest.mock import AsyncMock


def _make_browser_sessions_mock():
    mock = AsyncMock()
    mock.list_visible_sessions = AsyncMock(return_value=[])
    mock.get_session = AsyncMock(return_value=None)
    mock.get_or_create_mine = AsyncMock(
        return_value={
            "id": "test-session-id",
            "owner_type": "user",
            "owner_id": "admin",
            "status": "pending",
            "profile_name": "default",
            "url": "http://example.com",
            "node": None,
            "container_id": None,
            "neko_url": None,
            "cdp_url": None,
            "is_mobile": False,
        }
    )
    return mock


def _make_running_mine_mock():
    mock = AsyncMock()
    mock.get_or_create_mine = AsyncMock(
        return_value={
            "id": "test-session-id",
            "owner_type": "user",
            "owner_id": "admin",
            "status": "running",
            "profile_name": "default",
            "url": "http://example.com",
            "node": "host",
            "container_id": "abc123",
            "neko_url": None,
            "cdp_url": None,
            "is_mobile": False,
        }
    )
    return mock


class TestBrowserSessionsReadRoutes:
    @pytest.mark.asyncio
    async def test_get_nodes_returns_200(self, client):
        resp = await client.get("/api/browser/nodes")
        assert resp.status_code == 200
        body = resp.json()
        assert "nodes" in body
        assert isinstance(body["nodes"], list)

    @pytest.mark.asyncio
    async def test_list_sessions_returns_200_with_collection(self, client, monkeypatch):
        mock_mgr = _make_browser_sessions_mock()
        app = client._transport.app  # noqa: SLF001
        app.state._state["browser_sessions"] = mock_mgr  # noqa: SLF001
        resp = await client.get("/api/browser/sessions")
        assert resp.status_code == 200
        body = resp.json()
        assert "sessions" in body
        assert isinstance(body["sessions"], list)

    @pytest.mark.asyncio
    async def test_get_mine_returns_200(self, client, monkeypatch):
        mock_mgr = _make_running_mine_mock()
        app = client._transport.app  # noqa: SLF001
        app.state._state["browser_sessions"] = mock_mgr  # noqa: SLF001
        resp = await client.get("/api/browser/sessions/mine")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client, monkeypatch):
        mock_mgr = _make_browser_sessions_mock()
        app = client._transport.app  # noqa: SLF001
        app.state._state["browser_sessions"] = mock_mgr  # noqa: SLF001
        resp = await client.get("/api/browser/sessions/unknown-id-12345")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "not_found"
