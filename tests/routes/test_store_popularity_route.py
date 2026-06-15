"""Tests for popularity wiring on the Store catalog + /api/store/popularity."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tinyagentos import store_popularity as sp


@pytest.fixture(autouse=True)
def _clear_cache():
    sp._reset_cache_for_tests()
    yield
    sp._reset_cache_for_tests()


def _fake_app(app_id: str, homepage: str):
    a = MagicMock()
    a.id = app_id
    a.name = app_id
    a.type = "plugin"
    a.category = ""
    a.version = "1.0.0"
    a.description = ""
    a.icon = ""
    a.homepage = homepage
    a.requires = {}
    a.install = {}
    a.hardware_tiers = {}
    a.variants = []
    return a


def _patch_registry(app, apps):
    reg = MagicMock()
    reg.list_available = MagicMock(return_value=apps)
    reg.is_installed = MagicMock(return_value=False)
    app.state.registry = reg
    app.state.installation_state = None


def _patch_github(monkeypatch, stars: int | None):
    """Make every GitHub repo lookup return ``stars`` (or 404 when None)."""
    resp = MagicMock()
    resp.status_code = 200 if stars is not None else 404
    resp.json = MagicMock(
        return_value={"stargazers_count": stars} if stars is not None else {}
    )
    fake = MagicMock()
    fake.get = AsyncMock(return_value=resp)
    fake.aclose = AsyncMock()
    fake.__aenter__ = AsyncMock(return_value=fake)
    fake.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(
        "tinyagentos.routes.store.httpx.AsyncClient", lambda *a, **k: fake
    )


class TestStorePopularityRoute:
    @pytest.mark.asyncio
    async def test_catalog_surfaces_stars_and_popularity(self, client, monkeypatch):
        app = client._transport.app
        _patch_registry(app, [_fake_app("jellyfin", "https://github.com/jellyfin/jellyfin")])
        _patch_github(monkeypatch, 35000)

        res = await client.get("/api/store/catalog")
        assert res.status_code == 200
        entry = res.json()[0]
        assert entry["repo"] == "jellyfin/jellyfin"
        assert entry["stars"] == 35000
        assert entry["popularity"] == {
            "github_stars": 35000,
            "installs": None,
            "score": 35000.0,
        }

    @pytest.mark.asyncio
    async def test_non_github_entry_gets_null_popularity(self, client, monkeypatch):
        app = client._transport.app
        _patch_registry(app, [_fake_app("excalidraw", "https://excalidraw.com")])
        _patch_github(monkeypatch, 35000)  # never called for a non-github entry

        res = await client.get("/api/store/catalog")
        entry = res.json()[0]
        assert entry["repo"] is None
        assert entry["stars"] is None
        assert entry["popularity"]["github_stars"] is None
        assert entry["popularity"]["score"] == 0.0

    @pytest.mark.asyncio
    async def test_dedicated_popularity_endpoint(self, client, monkeypatch):
        app = client._transport.app
        _patch_registry(app, [_fake_app("jellyfin", "https://github.com/jellyfin/jellyfin")])
        _patch_github(monkeypatch, 12345)

        res = await client.get("/api/store/popularity")
        assert res.status_code == 200
        body = res.json()
        assert body["jellyfin"]["github_stars"] == 12345
        assert body["jellyfin"]["installs"] is None
