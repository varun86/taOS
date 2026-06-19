"""Tests for tinyagentos/install_progress.py: InstallProgress data class and
InstallProgressStore lifecycle (start, update, finish, get, list, prune)."""
from __future__ import annotations

import time

import pytest

from tinyagentos.install_progress import (
    INSTALL_PROGRESS_TTL_S,
    InstallProgress,
    InstallProgressStore,
    get_global_store,
)


# ---- InstallProgress data class ------------------------------------------------


class TestInstallProgress:
    def _make(self, **kw):
        defaults = dict(
            install_id="i1",
            app_id="app1",
            target_remote="remote1",
            state="queued",
            bytes_downloaded=0,
            bytes_total=0,
            started_at=1000.0,
            updated_at=1000.0,
            finished_at=None,
            error=None,
            detail="",
        )
        defaults.update(kw)
        return InstallProgress(**defaults)

    def test_percent_none_when_bytes_total_zero(self):
        p = self._make(bytes_total=0)
        assert p.percent is None

    def test_percent_none_when_bytes_total_negative(self):
        p = self._make(bytes_total=-1)
        assert p.percent is None

    def test_percent_computed_from_ratio(self):
        p = self._make(bytes_downloaded=50, bytes_total=200)
        assert p.percent == 25.0

    def test_percent_caps_at_100(self):
        p = self._make(bytes_downloaded=300, bytes_total=200)
        assert p.percent == 100.0

    def test_to_dict_round_trip(self):
        p = self._make(
            bytes_downloaded=100,
            bytes_total=200,
            state="downloading",
            detail="fetching model",
        )
        d = p.to_dict()
        assert d["install_id"] == "i1"
        assert d["app_id"] == "app1"
        assert d["target_remote"] == "remote1"
        assert d["state"] == "downloading"
        assert d["bytes_downloaded"] == 100
        assert d["bytes_total"] == 200
        assert d["percent"] == 50.0
        assert d["detail"] == "fetching model"
        assert d["error"] is None
        assert d["finished_at"] is None

    def test_to_dict_with_no_remote(self):
        p = self._make(target_remote=None)
        d = p.to_dict()
        assert d["target_remote"] is None


# ---- InstallProgressStore -----------------------------------------------------


class TestInstallProgressStore:
    def _store(self):
        return InstallProgressStore()

    def test_start_returns_entry_with_defaults(self, monkeypatch):
        fake_id = "abc123"
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid.uuid4",
            type("F", (), {"hex": fake_id})(),
        )
        # uuid.uuid4() returns an object whose .hex attribute is the id;
        # monkeypatch the call to return a simple namespace.
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex=fake_id)),
        )
        store = self._store()
        entry = store.start("myapp", "myremote")
        assert entry.install_id == fake_id
        assert entry.app_id == "myapp"
        assert entry.target_remote == "myremote"
        assert entry.state == "queued"
        assert entry.bytes_downloaded == 0
        assert entry.bytes_total == 0
        assert entry.finished_at is None
        assert entry.error is None

    def test_start_without_remote(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="x1")),
        )
        store = self._store()
        entry = store.start("myapp")
        assert entry.target_remote is None

    def test_get_returns_entry(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="x1")),
        )
        store = self._store()
        started = store.start("app1")
        fetched = store.get(started.install_id)
        assert fetched is not None
        assert fetched.install_id == started.install_id

    def test_get_returns_none_for_unknown_id(self):
        store = self._store()
        assert store.get("nope") is None

    def test_update_mutates_fields(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="x1")),
        )
        store = self._store()
        entry = store.start("app1")
        store.update(
            entry.install_id,
            state="downloading",
            bytes_downloaded=10,
            bytes_total=100,
            detail="working",
        )
        updated = store.get(entry.install_id)
        assert updated.state == "downloading"
        assert updated.bytes_downloaded == 10
        assert updated.bytes_total == 100
        assert updated.detail == "working"

    def test_update_ignores_unknown_id(self):
        store = self._store()
        # must not raise
        store.update("ghost", state="downloading")

    def test_update_only_set_fields(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="x1")),
        )
        store = self._store()
        entry = store.start("app1")
        store.update(entry.install_id, bytes_downloaded=5)
        updated = store.get(entry.install_id)
        assert updated.state == "queued"
        assert updated.bytes_downloaded == 5
        assert updated.detail == ""

    def test_finish_success(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="x1")),
        )
        store = self._store()
        entry = store.start("app1")
        store.finish(entry.install_id, success=True, detail="all done")
        done = store.get(entry.install_id)
        assert done.state == "installed"
        assert done.finished_at is not None
        assert done.detail == "all done"
        assert done.error is None

    def test_finish_failure(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="x1")),
        )
        store = self._store()
        entry = store.start("app1")
        store.finish(entry.install_id, success=False, error="disk full")
        done = store.get(entry.install_id)
        assert done.state == "failed"
        assert done.error == "disk full"
        assert done.finished_at is not None

    def test_finish_ignores_unknown_id(self):
        store = self._store()
        store.finish("ghost", success=True)

    def test_list_by_app_filters_and_sorts_newest_first(self, monkeypatch):
        import types
        ids = ["id1", "id2", "id3"]
        counter = iter(ids)
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex=next(counter))),
        )
        store = self._store()
        store.start("app1")
        store.start("app2")
        store.start("app1")
        results = store.list_by_app("app1")
        assert len(results) == 2
        assert all(e.app_id == "app1" for e in results)
        assert results[0].started_at >= results[1].started_at

    def test_list_by_app_returns_empty_for_unknown(self):
        store = self._store()
        assert store.list_by_app("nope") == []

    def test_list_all_returns_all_entries(self, monkeypatch):
        import types
        ids = ["a1", "a2"]
        counter = iter(ids)
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex=next(counter))),
        )
        store = self._store()
        store.start("x")
        store.start("y")
        all_entries = store.list_all()
        assert len(all_entries) == 2

    def test_prune_removes_stale_finished_entries(self, monkeypatch):
        import types
        ids = ["keep", "stale"]
        counter = iter(ids)
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex=next(counter))),
        )
        store = self._store()
        fresh = store.start("app1")
        old = store.start("app1")
        store.finish(old.install_id, success=True)

        # Make the old entry's finished_at far in the past
        old_entry = store._entries[old.install_id]
        old_entry.finished_at = time.time() - INSTALL_PROGRESS_TTL_S - 1
        old_entry.started_at = old_entry.finished_at - 10

        # Access should trigger prune
        result = store.get(fresh.install_id)
        assert result is not None
        assert store.get(old.install_id) is None

    def test_prune_keeps_recent_finished_entries(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="r1")),
        )
        store = self._store()
        entry = store.start("app1")
        store.finish(entry.install_id, success=True)
        # finished_at is "now", well within TTL
        assert store.get(entry.install_id) is not None

    def test_prune_keeps_unfinished_entries_forever(self, monkeypatch):
        import types
        monkeypatch.setattr(
            "tinyagentos.install_progress.uuid",
            types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="u1")),
        )
        store = self._store()
        entry = store.start("app1")
        # Artificially age started_at but leave finished_at None
        e = store._entries[entry.install_id]
        e.started_at = 0.0
        e.updated_at = 0.0
        assert store.get(entry.install_id) is not None


# ---- Global store singleton ---------------------------------------------------


class TestGlobalStore:
    def test_get_global_store_returns_singleton(self, monkeypatch):
        import tinyagentos.install_progress as mod
        monkeypatch.setattr(mod, "_GLOBAL", None)
        s1 = get_global_store()
        s2 = get_global_store()
        assert s1 is s2

    def test_get_global_store_creates_on_first_call(self, monkeypatch):
        import tinyagentos.install_progress as mod
        monkeypatch.setattr(mod, "_GLOBAL", None)
        store = get_global_store()
        assert isinstance(store, InstallProgressStore)
        assert mod._GLOBAL is store
