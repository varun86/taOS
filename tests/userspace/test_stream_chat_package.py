"""Tests for the stream-chat seed userspace app manifest and seeding.

Mirrors the patterns in test_package.py (network permission validation) and
test_seed.py (real bundled app seeding). No live network required.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio

from tinyagentos.userspace.package import parse_manifest, PackageError
from tinyagentos.userspace.seed import seed_bundled_apps, _DEFAULT_SEED_DIR
from tinyagentos.userspace.store import UserspaceAppStore

_STREAM_CHAT_MANIFEST = """
id: stream-chat
name: Stream Chat
version: 1.0.0
app_type: web
entry: index.html
icon: ""
permissions:
  - app.kv
  - network:https://io.socialstream.ninja
  - network:wss://io.socialstream.ninja
"""


async def _make_store(tmp_path: Path) -> UserspaceAppStore:
    store = UserspaceAppStore(tmp_path / "userspace_apps.db")
    await store.init()
    return store


# ---------------------------------------------------------------------------
# Manifest parse
# ---------------------------------------------------------------------------


def test_stream_chat_manifest_parses():
    m = parse_manifest(_STREAM_CHAT_MANIFEST)
    assert m["id"] == "stream-chat"
    assert m["name"] == "Stream Chat"
    assert m["version"] == "1.0.0"
    assert m["app_type"] == "web"
    assert m["entry"] == "index.html"


def test_stream_chat_network_permissions_accepted():
    m = parse_manifest(_STREAM_CHAT_MANIFEST)
    assert "network:https://io.socialstream.ninja" in m["permissions"]
    assert "network:wss://io.socialstream.ninja" in m["permissions"]


def test_stream_chat_kv_permission_present():
    m = parse_manifest(_STREAM_CHAT_MANIFEST)
    assert "app.kv" in m["permissions"]


def test_stream_chat_no_wildcard_origins():
    # Wildcard host (network:*) must be rejected by the parser.
    with pytest.raises(PackageError):
        parse_manifest(
            "id: x\nname: X\nversion: 1.0.0\napp_type: web\n"
            "permissions:\n  - 'network:*'\n"
        )


def test_stream_chat_no_path_in_network_origin():
    # Paths in network origins must be rejected (CSP injection risk).
    with pytest.raises(PackageError):
        parse_manifest(
            "id: x\nname: X\nversion: 1.0.0\napp_type: web\n"
            "permissions:\n  - 'network:https://io.socialstream.ninja/sse/abc'\n"
        )


# ---------------------------------------------------------------------------
# Real bundled stream-chat app seeding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_real_stream_chat_app_seeds(tmp_path):
    """The bundled stream-chat app must seed as first-party from the default seed dir."""
    apps_root = tmp_path / "apps"
    store = await _make_store(tmp_path)

    await seed_bundled_apps(store, apps_root)

    row = await store.get("stream-chat")
    assert row is not None, "stream-chat not found after seeding"
    assert row["trust"] == "first-party"
    assert row["version"] == "1.0.0"
    assert "app.kv" in row["permissions_requested"]
    assert "network:https://io.socialstream.ninja" in row["permissions_requested"]
    assert "network:wss://io.socialstream.ninja" in row["permissions_requested"]
    await store.close()


@pytest.mark.asyncio
async def test_real_stream_chat_seeding_is_idempotent(tmp_path):
    """Seeding stream-chat twice must not change installed_at or downgrade trust."""
    apps_root = tmp_path / "apps"
    store = await _make_store(tmp_path)

    await seed_bundled_apps(store, apps_root)
    first = await store.get("stream-chat")

    await seed_bundled_apps(store, apps_root)
    second = await store.get("stream-chat")

    assert first["installed_at"] == second["installed_at"]
    assert second["trust"] == "first-party"
    await store.close()
