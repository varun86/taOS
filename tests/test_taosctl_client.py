"""Direct unit tests for the taosctl HTTP client.

The noun command tests use fake clients, so they cannot catch a real
TaosClient signature or URL-building regression. These tests exercise the
real client against a stubbed urlopen.
"""
from __future__ import annotations

from tinyagentos.cli.taosctl import client as cli_client


class _FakeResp:
    def __init__(self, body=b'{"ok": true}'):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body


def _capture(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"] = req.full_url
        seen["method"] = req.get_method()
        return _FakeResp()

    monkeypatch.setattr(cli_client.urllib.request, "urlopen", fake_urlopen)
    return seen


def test_delete_threads_query_params_into_url(monkeypatch):
    seen = _capture(monkeypatch)
    c = cli_client.TaosClient(url="http://x", token=None)
    c.delete("/api/bookmarks/b1", params={"profile_id": "p1"})
    assert seen["method"] == "DELETE"
    assert seen["url"] == "http://x/api/bookmarks/b1?profile_id=p1"


def test_delete_without_params_has_no_query(monkeypatch):
    seen = _capture(monkeypatch)
    c = cli_client.TaosClient(url="http://x", token=None)
    c.delete("/api/bookmarks/b1")
    assert seen["url"] == "http://x/api/bookmarks/b1"


def test_get_drops_none_valued_params(monkeypatch):
    seen = _capture(monkeypatch)
    c = cli_client.TaosClient(url="http://x", token=None)
    c.get("/api/things", params={"a": "1", "b": None})
    assert seen["url"] == "http://x/api/things?a=1"
