"""Tests for the taosctl apps command group."""
from __future__ import annotations

from tinyagentos.cli.taosctl import client as cli_client
from tinyagentos.cli.taosctl import __main__ as cli_main


class _FakeClient:
    def __init__(self, *a, **k):
        self.calls = []
        self.base_url = "http://x"
        self.token = "t"
        self._raise = None

    def get(self, path, params=None):
        self.calls.append(("GET", path))
        if self._raise:
            raise self._raise
        return {"items": []}

    def post(self, path, json=None):
        self.calls.append(("POST", path))
        if self._raise:
            raise self._raise
        return {"status": "ok"}


def _run(monkeypatch, argv, fake):
    monkeypatch.setattr(cli_main, "TaosClient", lambda **k: fake)
    return cli_main.main(argv)


def test_apps_list_calls_installed_endpoint(monkeypatch):
    fake = _FakeClient()
    rc = _run(monkeypatch, ["apps", "list"], fake)
    assert rc == 0
    assert ("GET", "/api/apps/installed") in fake.calls


def test_apps_get_targets_app_by_id(monkeypatch):
    fake = _FakeClient()
    rc = _run(monkeypatch, ["apps", "get", "gitea-lxc"], fake)
    assert rc == 0
    assert ("GET", "/api/apps/installed/gitea-lxc") in fake.calls


def test_apps_get_url_encodes_the_id(monkeypatch):
    fake = _FakeClient()
    rc = _run(monkeypatch, ["apps", "get", "a/b c"], fake)
    assert rc == 0
    assert ("GET", "/api/apps/installed/a%2Fb%20c") in fake.calls


def test_apps_installed_calls_optional_endpoint(monkeypatch):
    fake = _FakeClient()
    rc = _run(monkeypatch, ["apps", "installed"], fake)
    assert rc == 0
    assert ("GET", "/api/apps/optional/installed") in fake.calls


def test_apps_install_posts_to_optional_install(monkeypatch):
    fake = _FakeClient()
    rc = _run(monkeypatch, ["apps", "install", "reddit"], fake)
    assert rc == 0
    assert ("POST", "/api/apps/optional/reddit/install") in fake.calls


def test_apps_uninstall_posts_to_optional_uninstall(monkeypatch):
    fake = _FakeClient()
    rc = _run(monkeypatch, ["apps", "uninstall", "reddit"], fake)
    assert rc == 0
    assert ("POST", "/api/apps/optional/reddit/uninstall") in fake.calls


def test_apps_api_error_maps_to_exit_2(monkeypatch, capsys):
    fake = _FakeClient()
    fake._raise = cli_client.ApiError(404, "no such app")
    rc = _run(monkeypatch, ["apps", "get", "ghost"], fake)
    assert rc == 2
    assert "no such app" in capsys.readouterr().err


def test_apps_transport_error_maps_to_exit_1(monkeypatch, capsys):
    fake = _FakeClient()
    fake._raise = cli_client.TransportError("cannot reach http://x: refused")
    rc = _run(monkeypatch, ["apps", "list"], fake)
    assert rc == 1
    assert "cannot reach" in capsys.readouterr().err
