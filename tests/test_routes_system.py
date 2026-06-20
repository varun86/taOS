import pytest
from tinyagentos.restart_orchestrator import RestartOrchestrator


class TestSystemRoutes:
    @pytest.mark.asyncio
    async def test_restart_status_returns_idle_state(self, client, monkeypatch):
        fake_orchestrator = RestartOrchestrator(client._transport.app.state)
        monkeypatch.setattr(
            client._transport.app.state, "orchestrator", fake_orchestrator
        )
        resp = await client.get("/api/system/restart/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "phase" in data
        assert "reason" in data
        assert "started_at" in data
        assert "agents" in data
        assert data["phase"] == "idle"
        assert data["reason"] == ""
        assert data["started_at"] == 0
        assert data["agents"] == {}
