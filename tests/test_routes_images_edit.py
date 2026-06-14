"""Tests for the tier-aware image-editing routes (routes/images_edit.py)."""
from types import SimpleNamespace

import pytest

from tinyagentos.app import create_app
from tinyagentos.routes.images_edit import _get_edit_backend


def _backend(name, btype, priority=10):
    return SimpleNamespace(name=name, type=btype, priority=priority, url=f"http://{name}")


class _FakeCatalog:
    def __init__(self, by_cap):
        self._by_cap = by_cap

    def backends_with_capability(self, capability):
        return list(self._by_cap.get(capability, []))


def _request_with_catalog(catalog):
    state = SimpleNamespace(backend_catalog=catalog)
    return SimpleNamespace(app=SimpleNamespace(state=state))


def test_edit_routes_registered():
    """The three edit endpoints + the capabilities probe exist on the app."""
    app = create_app()
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/images/edit" in paths
    assert "/api/images/remove-bg" in paths
    assert "/api/images/upscale" in paths
    assert "/api/images/edit/capabilities" in paths


def test_tier_preference_quality_prefers_flux_fill():
    """quality tier prefers the GPU diffusion backend (flux-fill) over iopaint."""
    catalog = _FakeCatalog(
        {"image-editing": [_backend("io", "iopaint"), _backend("flux", "flux-fill")]}
    )
    req = _request_with_catalog(catalog)
    url, btype, name = _get_edit_backend(req, "image-editing", "quality")
    assert btype == "flux-fill"
    assert name == "flux"


def test_tier_preference_fast_prefers_iopaint():
    """fast tier prefers the CPU/NPU backend (iopaint) over flux-fill."""
    catalog = _FakeCatalog(
        {"image-editing": [_backend("flux", "flux-fill"), _backend("io", "iopaint")]}
    )
    req = _request_with_catalog(catalog)
    url, btype, name = _get_edit_backend(req, "image-editing", "fast")
    assert btype == "iopaint"
    assert name == "io"


def test_tier_preference_falls_back_when_preferred_absent():
    """quality tier still resolves iopaint when no flux-fill backend exists."""
    catalog = _FakeCatalog({"image-editing": [_backend("io", "iopaint")]})
    req = _request_with_catalog(catalog)
    url, btype, name = _get_edit_backend(req, "image-editing", "quality")
    assert btype == "iopaint"


def test_no_backend_returns_none():
    """No healthy backend for the capability → graceful None."""
    catalog = _FakeCatalog({})
    req = _request_with_catalog(catalog)
    assert _get_edit_backend(req, "image-editing", "fast") is None


def test_no_catalog_returns_none():
    """No live catalog (scheduler not started) → None, never raises."""
    req = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(backend_catalog=None)))
    assert _get_edit_backend(req, "upscale", "fast") is None
