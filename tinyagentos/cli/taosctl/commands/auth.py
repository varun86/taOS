"""taosctl auth -- configure and check the CLI's connection to a taOS server."""
from __future__ import annotations

import json

from tinyagentos.cli.taosctl import client as _client

NOUN = "auth"


def register(subparsers) -> None:
    p = subparsers.add_parser(NOUN, help="Configure and check the connection")
    verbs = p.add_subparsers(dest="verb", required=True, metavar="<verb>")

    lp = verbs.add_parser("login", help="Save a server URL + token to the config file")
    lp.add_argument("--url", help="Server base URL")
    lp.add_argument("--token", help="API token (Bearer)")
    lp.set_defaults(func=_login)

    sp = verbs.add_parser("status", help="Show the resolved URL + whether a token is set")
    sp.set_defaults(func=_status)

    wp = verbs.add_parser("whoami", help="Verify the token by calling the server")
    wp.set_defaults(func=_whoami)


def _login(args, client):
    url, token = _client.resolve(args.url, args.token)
    _client.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _client.CONFIG_PATH.write_text(json.dumps({"url": url, "token": token}, indent=2))
    return {"saved": str(_client.CONFIG_PATH), "url": url, "token_set": bool(token)}


def _status(args, client):
    return {"url": client.base_url, "token_set": bool(client.token)}


def _whoami(args, client):
    # No dedicated whoami endpoint; a successful authed call to /api/agents
    # confirms the token is accepted by the server.
    client.get("/api/agents")
    return {"url": client.base_url, "authenticated": True}
