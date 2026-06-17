"""Route tests for games endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient, Request as HttpxRequest, Response

LEGAL_MOVES = ["e2e4", "d2d4", "g1f3"]
CHESS_BODY = {
    "agent_name": "chess-bot",
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "legal_moves": LEGAL_MOVES,
    "history": ["e2e4", "e7e5"],
}


def _mock_httpx_response(content: str):
    mock_request = HttpxRequest("POST", "http://localhost:9999/message")
    return Response(
        status_code=200,
        json={"content": content},
        request=mock_request,
    )


def _set_hub_router_port(app, port: int = 9999):
    hub_router = MagicMock()
    hub_router.get_adapter_port.return_value = port
    app.state.channel_hub_router = hub_router
    return hub_router


@pytest.mark.asyncio
class TestChessMove:
    async def test_missing_agent_name_returns_400(self, client):
        resp = await client.post(
            "/api/games/chess/move",
            json={"legal_moves": LEGAL_MOVES},
        )
        assert resp.status_code == 400
        assert "agent_name" in resp.json()["error"].lower()

    async def test_missing_legal_moves_returns_400(self, client):
        resp = await client.post(
            "/api/games/chess/move",
            json={"agent_name": "chess-bot"},
        )
        assert resp.status_code == 400
        assert "legal_moves" in resp.json()["error"].lower()

    async def test_empty_legal_moves_returns_400(self, client):
        resp = await client.post(
            "/api/games/chess/move",
            json={"agent_name": "chess-bot", "legal_moves": []},
        )
        assert resp.status_code == 400

    async def test_unreachable_agent_returns_random_legal_move(self, client):
        app = client._transport.app
        app.state.channel_hub_router = None
        app.state.channel_hub = None

        resp = await client.post("/api/games/chess/move", json=CHESS_BODY)
        assert resp.status_code == 200
        data = resp.json()
        assert data["move"] in LEGAL_MOVES
        assert "not reachable" in data["commentary"].lower()

    async def test_agent_move_via_hub_router_port(self, client):
        app = client._transport.app
        _set_hub_router_port(app, 9999)

        with patch("tinyagentos.routes.games.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = _mock_httpx_response("Best move: e2e4")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            resp = await client.post("/api/games/chess/move", json=CHESS_BODY)

        assert resp.status_code == 200
        data = resp.json()
        assert data["move"] == "e2e4"
        assert "e2e4" in data["commentary"]
        mock_instance.post.assert_awaited_once()
        call_url = mock_instance.post.await_args.args[0]
        assert call_url == "http://localhost:9999/message"

    async def test_agent_move_via_channel_hub_adapter_url(self, client):
        app = client._transport.app
        app.state.channel_hub_router = None
        adapter_mgr = MagicMock()
        adapter_mgr.get_adapter_url.return_value = "http://localhost:8888"
        app.state.channel_hub = adapter_mgr

        with patch("tinyagentos.routes.games.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = _mock_httpx_response("d2d4")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            resp = await client.post("/api/games/chess/move", json=CHESS_BODY)

        assert resp.status_code == 200
        assert resp.json()["move"] == "d2d4"
        adapter_mgr.get_adapter_url.assert_called_once_with("chess-bot")

    async def test_invalid_agent_response_falls_back_to_random_move(self, client):
        app = client._transport.app
        _set_hub_router_port(app, 9999)

        with patch("tinyagentos.routes.games.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = _mock_httpx_response("I cannot decide")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            resp = await client.post("/api/games/chess/move", json=CHESS_BODY)

        assert resp.status_code == 200
        data = resp.json()
        assert data["move"] in LEGAL_MOVES
        assert "Agent returned" in data["commentary"]

    async def test_httpx_error_falls_back_to_random_move(self, client):
        app = client._transport.app
        _set_hub_router_port(app, 9999)

        with patch("tinyagentos.routes.games.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = ConnectionError("connection refused")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            resp = await client.post("/api/games/chess/move", json=CHESS_BODY)

        assert resp.status_code == 200
        data = resp.json()
        assert data["move"] in LEGAL_MOVES
        assert data["commentary"].startswith("Error:")

    async def test_unauthenticated_returns_401(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            resp = await c.post("/api/games/chess/move", json=CHESS_BODY)
            assert resp.status_code in (401, 403)