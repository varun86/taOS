"""Store app popularity, sourced from GitHub stars today and structured to
accept real install telemetry later (#15).

The popularity shape is telemetry-ready and forward-compatible:

    {
        "github_stars": int | None,   # live star count, None when unknown
        "installs": int | None,       # None today; filled by #15 telemetry
        "score": float,               # derived from whatever signals exist
    }

GitHub stars are fetched unauthenticated from api.github.com (allowed by the
network policy) and cached in-memory with a multi-hour TTL so the Store list
endpoint never hammers GitHub. Any GitHub failure (rate-limit, 404, network)
degrades the entry to github_stars=None and never raises.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Cache GitHub star lookups for a few hours. Stars move slowly; the Store list
# endpoint is hit often, so a long TTL keeps it fast and well under the
# unauthenticated rate limit (60 req/hr/IP).
_STAR_TTL = 6 * 60 * 60  # 6 hours

# key (owner/repo) -> (timestamp, github_stars | None)
_star_cache: dict[str, tuple[float, int | None]] = {}

_GITHUB_HOST = "github.com"


def parse_repo(homepage: str | None) -> str | None:
    """Return owner/repo if homepage points at a GitHub repo, else None.

    Accepts the forms taOS manifests use, e.g.
    https://github.com/owner/repo or https://github.com/owner/repo/.
    Non-GitHub homepages (excalidraw.com, gitea.io, ...) and bare profile
    URLs (github.com/owner) return None: only an owner/repo pair yields stars.
    """
    if not homepage or _GITHUB_HOST not in homepage:
        return None
    m = re.search(r"github\.com/([^/\s]+)/([^/\s#?]+)", homepage)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if not owner or not repo:
        return None
    return f"{owner}/{repo.removesuffix('.git')}"


def _compute_score(github_stars: int | None, installs: int | None) -> float:
    """Combine the available signals into a single popularity score.

    Today only stars exist, so the score is the star count. When #15 lands
    real install telemetry, installs weigh in here without changing the shape
    or any caller. An entry with no signals scores 0.0.
    """
    score = 0.0
    if github_stars:
        score += float(github_stars)
    if installs:
        # Installs are a stronger signal than a star; weight them when present.
        score += float(installs) * 10.0
    return score


def popularity_shape(github_stars: int | None, installs: int | None = None) -> dict[str, Any]:
    """Build the telemetry-ready popularity dict from the known signals."""
    return {
        "github_stars": github_stars,
        "installs": installs,
        "score": _compute_score(github_stars, installs),
    }


async def fetch_stars(repo: str, *, client: httpx.AsyncClient | None = None) -> int | None:
    """Return the GitHub star count for owner/repo, or None on any failure.

    Cached for _STAR_TTL per repo. Rate-limit (403/429) and 404 both yield
    None and are cached so we do not retry a known-bad repo on every request.
    Never raises.
    """
    cached = _star_cache.get(repo)
    if cached is not None:
        ts, stars = cached
        if time.monotonic() - ts < _STAR_TTL:
            return stars

    owns_client = client is None
    try:
        if owns_client:
            client = httpx.AsyncClient(timeout=8)
        assert client is not None
        resp = await client.get(
            f"https://api.github.com/repos/{repo}",
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code == 200:
            stars = resp.json().get("stargazers_count")
            stars = int(stars) if isinstance(stars, (int, float)) else None
        else:
            # 403/429 rate-limit, 404 not-found, anything else: degrade to None.
            stars = None
    except Exception as exc:  # network error, bad JSON, etc.
        logger.debug("GitHub star fetch failed for %s: %s", repo, exc)
        stars = None
    finally:
        if owns_client and client is not None:
            await client.aclose()

    _star_cache[repo] = (time.monotonic(), stars)
    return stars


async def popularity_for_homepage(
    homepage: str | None, *, client: httpx.AsyncClient | None = None
) -> dict[str, Any]:
    """Resolve the popularity shape for a catalog entry from its homepage.

    Entries whose homepage is not a GitHub repo get a popularity shape with
    github_stars=None (no stars are fabricated). installs is always None until
    #15.
    """
    repo = parse_repo(homepage)
    stars = await fetch_stars(repo, client=client) if repo else None
    return popularity_shape(stars)


def _reset_cache_for_tests() -> None:
    """Clear the star cache. For tests only."""
    _star_cache.clear()
