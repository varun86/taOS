"""taosctl apps -- inspect and manage installed apps.

Reference noun: shows the pattern every other noun module follows (a NOUN, a
register() that wires verb subparsers, and small handlers that call the client
and return data for the framework to render).
"""
from __future__ import annotations

from urllib.parse import quote

NOUN = "apps"


def register(subparsers) -> None:
    p = subparsers.add_parser(NOUN, help="Inspect and manage installed apps")
    verbs = p.add_subparsers(dest="verb", required=True, metavar="<verb>")

    lp = verbs.add_parser("list", help="List installed apps with a runtime location")
    lp.set_defaults(func=_list)

    gp = verbs.add_parser("get", help="Get one installed app by id")
    gp.add_argument("app_id", help="App id")
    gp.set_defaults(func=_get)

    ip = verbs.add_parser("installed", help="List optional frontend app install state")
    ip.set_defaults(func=_installed)

    cp = verbs.add_parser("install", help="Install an optional frontend app")
    cp.add_argument("app_id", help="Optional app id")
    cp.set_defaults(func=_install)

    up = verbs.add_parser("uninstall", help="Uninstall an optional frontend app")
    up.add_argument("app_id", help="Optional app id")
    up.set_defaults(func=_uninstall)

    # POST/PATCH/DELETE with file upload, multipart, streaming, or complex
    # nested bodies are skipped: create, update, delete of full app records.


def _list(args, client):
    return client.get("/api/apps/installed")


def _get(args, client):
    return client.get(f"/api/apps/installed/{quote(args.app_id, safe='')}")


def _installed(args, client):
    return client.get("/api/apps/optional/installed")


def _install(args, client):
    return client.post(f"/api/apps/optional/{quote(args.app_id, safe='')}/install")


def _uninstall(args, client):
    return client.post(f"/api/apps/optional/{quote(args.app_id, safe='')}/uninstall")
