from unittest.mock import AsyncMock, patch

import pytest


class TestMemoryStats:
    @pytest.mark.asyncio
    async def test_get_stats_returns_200(self, client, monkeypatch):
        mock_backend = AsyncMock()
        mock_backend.get_stats = AsyncMock(return_value={
            "agents": 0,
            "total_entries": 0,
            "stores": [],
        })

        def _mock_backend(request):
            return mock_backend

        monkeypatch.setattr(
            "tinyagentos.routes.memory_management._backend",
            _mock_backend,
        )

        resp = await client.get("/api/memory/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        assert "total_entries" in data
        assert "stores" in data


class TestMemorySettings:
    @pytest.mark.asyncio
    async def test_get_settings_returns_200(self, client, monkeypatch):
        mock_backend = AsyncMock()
        mock_backend.get_settings = AsyncMock(return_value={
            "retention_days": 30,
            "auto_cleanup": True,
        })

        def _mock_backend(request):
            return mock_backend

        monkeypatch.setattr(
            "tinyagentos.routes.memory_management._backend",
            _mock_backend,
        )

        resp = await client.get("/api/memory/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestMemoryBackendCapabilities:
    @pytest.mark.asyncio
    async def test_get_capabilities_returns_200(self, client, monkeypatch):
        mock_backend = AsyncMock()
        mock_backend.name = "taosmd"
        mock_backend.version = "0.3.0"
        mock_backend.capabilities = ["kg", "vector", "archive"]

        import taosmd
        monkeypatch.setattr(taosmd, "TaOSmdBackend", mock_backend)

        resp = await client.get("/api/memory/backend/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "version" in data
        assert "capabilities" in data
        assert isinstance(data["capabilities"], list)


class TestMemoryBackendSettingsSchema:
    @pytest.mark.asyncio
    async def test_get_settings_schema_returns_200(self, client, monkeypatch):
        mock_backend = AsyncMock()
        mock_backend.get_settings_schema = AsyncMock(return_value={
            "type": "object",
            "properties": {},
        })

        def _mock_backend(request):
            return mock_backend

        monkeypatch.setattr(
            "tinyagentos.routes.memory_management._backend",
            _mock_backend,
        )

        resp = await client.get("/api/memory/backend/settings-schema")
        assert resp.status_code == 200
        data = resp.json()
        assert "type" in data
