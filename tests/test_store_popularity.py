"""Tests for store popularity: GitHub stars, caching, graceful degradation."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tinyagentos import store_popularity as sp


@pytest.fixture(autouse=True)
def _clear_cache():
    sp._reset_cache_for_tests()
    yield
    sp._reset_cache_for_tests()


def _client_returning(status_code: int, json_body: dict | None = None):
    """Build a fake httpx.AsyncClient whose .get returns the given response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_body or {})
    client = MagicMock()
    client.get = AsyncMock(return_value=resp)
    return client


class TestParseRepo:
    def test_github_repo_homepage(self):
        assert sp.parse_repo("https://github.com/jellyfin/jellyfin") == "jellyfin/jellyfin"

    def test_trailing_slash_and_git_suffix(self):
        assert sp.parse_repo("https://github.com/owner/repo/") == "owner/repo"
        assert sp.parse_repo("https://github.com/owner/repo.git") == "owner/repo"

    def test_non_github_homepage(self):
        assert sp.parse_repo("https://excalidraw.com") is None

    def test_bare_profile_url(self):
        assert sp.parse_repo("https://github.com/owner") is None

    def test_empty(self):
        assert sp.parse_repo("") is None
        assert sp.parse_repo(None) is None


class TestFetchStars:
    @pytest.mark.asyncio
    async def test_github_homepage_gets_stars(self):
        client = _client_returning(200, {"stargazers_count": 72400})
        pop = await sp.popularity_for_homepage(
            "https://github.com/jellyfin/jellyfin", client=client
        )
        assert pop["github_stars"] == 72400
        assert pop["installs"] is None
        assert pop["score"] == 72400.0
        client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_404_yields_null_without_raising(self):
        client = _client_returning(404, {})
        pop = await sp.popularity_for_homepage(
            "https://github.com/owner/missing-repo", client=client
        )
        assert pop["github_stars"] is None
        assert pop["score"] == 0.0

    @pytest.mark.asyncio
    async def test_rate_limit_yields_null_without_raising(self):
        client = _client_returning(403, {"message": "rate limit exceeded"})
        pop = await sp.popularity_for_homepage(
            "https://github.com/owner/repo", client=client
        )
        assert pop["github_stars"] is None

    @pytest.mark.asyncio
    async def test_network_error_yields_null_without_raising(self):
        client = MagicMock()
        client.get = AsyncMock(side_effect=RuntimeError("boom"))
        stars = await sp.fetch_stars("owner/repo", client=client)
        assert stars is None

    @pytest.mark.asyncio
    async def test_non_github_homepage_no_call_no_stars(self):
        client = _client_returning(200, {"stargazers_count": 5})
        pop = await sp.popularity_for_homepage("https://excalidraw.com", client=client)
        assert pop["github_stars"] is None
        client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_caching_avoids_second_call_within_ttl(self):
        client = _client_returning(200, {"stargazers_count": 100})
        first = await sp.fetch_stars("owner/repo", client=client)
        second = await sp.fetch_stars("owner/repo", client=client)
        assert first == second == 100
        client.get.assert_awaited_once()  # second call served from cache


class TestScore:
    def test_score_is_stars_today(self):
        assert sp.popularity_shape(500)["score"] == 500.0

    def test_score_with_no_signals_is_zero(self):
        assert sp.popularity_shape(None)["score"] == 0.0

    def test_installs_weighed_when_present_forward_compat(self):
        # #15: installs fill in without a shape change; weighted above a star.
        shape = sp.popularity_shape(100, installs=10)
        assert shape["installs"] == 10
        assert shape["score"] == 100.0 + 10 * 10.0
