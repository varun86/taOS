"""Endpoint tests for tinyagentos/routes/chat_files.py."""

from __future__ import annotations

import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# POST /api/chat/upload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_file_happy(client):
    resp = await client.post(
        "/api/chat/upload",
        files={"file": ("hello.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "hello.txt"
    assert data["content_type"] == "text/plain"
    assert data["size"] == 11
    assert data["id"]
    assert data["url"].startswith("/api/chat/files/")


@pytest.mark.asyncio
async def test_upload_file_with_channel_id(client):
    resp = await client.post(
        "/api/chat/upload",
        params={"channel_id": "ch-123"},
        files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "report.pdf"
    assert data["size"] == 13


@pytest.mark.asyncio
async def test_upload_file_too_large(client):
    big = b"x" * (100 * 1024 * 1024 + 1)
    resp = await client.post(
        "/api/chat/upload",
        files={"file": ("big.bin", io.BytesIO(big), "application/octet-stream")},
    )
    assert resp.status_code == 413
    assert "too large" in resp.json()["error"]


@pytest.mark.asyncio
async def test_upload_file_empty_body_rejected(client):
    """FastAPI rejects an empty body for a multipart upload field."""
    resp = await client.post(
        "/api/chat/upload",
        content=b"",
        headers={"content-type": "multipart/form-data; boundary=----fake"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/chat/files/{filename}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_serve_file_happy(client):
    upload = await client.post(
        "/api/chat/upload",
        files={"file": ("serve_me.txt", io.BytesIO(b"serve content"), "text/plain")},
    )
    assert upload.status_code == 200
    url = upload.json()["url"]
    resp = await client.get(url)
    assert resp.status_code == 200
    assert resp.content == b"serve content"


@pytest.mark.asyncio
async def test_serve_file_not_found(client):
    resp = await client.get("/api/chat/files/nonexistent-file-abc123.txt")
    assert resp.status_code == 404
    assert resp.json()["error"] == "File not found"


@pytest.mark.asyncio
async def test_serve_file_traversal_rejected(client):
    resp = await client.get("/api/chat/files/../../../etc/passwd")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/chat/attachments/from-path
# ---------------------------------------------------------------------------


def _make_workspace_file(data_dir: Path, slug: str, rel_path: str, content: bytes) -> Path:
    """Create a file under data_dir/agent-workspaces/{slug}/ and return its path."""
    base = data_dir / "agent-workspaces" / slug
    dest = base / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return dest


@pytest.mark.asyncio
async def test_attachment_from_path_workspace_happy(client, tmp_path):
    app = client._transport.app
    data_dir = app.state.data_dir
    _make_workspace_file(data_dir, "user", "notes.md", b"# My Notes")
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={"path": "/workspaces/user/notes.md", "source": "workspace"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "notes.md"
    assert data["mime_type"] in ("text/markdown", "application/octet-stream")
    assert data["size"] == 10
    assert data["source"] == "workspace"
    assert data["url"].startswith("/api/chat/files/")


@pytest.mark.asyncio
async def test_attachment_from_path_agent_workspace_happy(client, tmp_path):
    app = client._transport.app
    data_dir = app.state.data_dir
    slug = "agent-1"
    _make_workspace_file(data_dir, slug, "output.csv", b"a,b,c\n1,2,3\n")
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={
            "path": f"/workspaces/{slug}/output.csv",
            "source": "agent-workspace",
            "slug": slug,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "output.csv"
    assert data["size"] == 12
    assert data["source"] == "agent-workspace"


@pytest.mark.asyncio
async def test_attachment_from_path_missing_path(client):
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={"source": "workspace"},
    )
    assert resp.status_code == 400
    assert "path" in resp.json()["error"]


@pytest.mark.asyncio
async def test_attachment_from_path_invalid_source(client):
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={"path": "/workspaces/user/foo.md", "source": "invalid"},
    )
    assert resp.status_code == 400
    assert "source" in resp.json()["error"]


@pytest.mark.asyncio
async def test_attachment_from_path_file_not_found(client, tmp_path):
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={"path": "/workspaces/user/does-not-exist.md", "source": "workspace"},
    )
    assert resp.status_code == 400
    assert "not found" in resp.json()["error"]


@pytest.mark.asyncio
async def test_attachment_from_path_traversal_rejected(client, tmp_path):
    app = client._transport.app
    data_dir = app.state.data_dir
    _make_workspace_file(data_dir, "user", "secret.txt", b"leaked")
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={"path": "/workspaces/user/../admin/secret.txt", "source": "workspace"},
    )
    assert resp.status_code == 400
    assert "traversal" in resp.json()["error"]


@pytest.mark.asyncio
async def test_attachment_from_path_workspace_wrong_owner(client, tmp_path):
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={"path": "/workspaces/other/foo.md", "source": "workspace"},
    )
    assert resp.status_code == 400
    assert "user" in resp.json()["error"]


@pytest.mark.asyncio
async def test_attachment_from_path_agent_workspace_slug_mismatch(client, tmp_path):
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={
            "path": "/workspaces/agent-x/file.txt",
            "source": "agent-workspace",
            "slug": "agent-y",
        },
    )
    assert resp.status_code == 400
    assert "slug" in resp.json()["error"]


@pytest.mark.asyncio
async def test_attachment_from_path_too_large(client, tmp_path):
    app = client._transport.app
    data_dir = app.state.data_dir
    big = b"x" * (100 * 1024 * 1024 + 1)
    _make_workspace_file(data_dir, "user", "huge.bin", big)
    resp = await client.post(
        "/api/chat/attachments/from-path",
        json={"path": "/workspaces/user/huge.bin", "source": "workspace"},
    )
    assert resp.status_code == 413
    assert "too large" in resp.json()["error"]
