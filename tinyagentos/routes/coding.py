from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()


class CreateWorkspaceBody(BaseModel):
    name: str


class WriteFileBody(BaseModel):
    path: str
    content: str


def _invalid_rel_path(rel: str) -> bool:
    if rel.startswith("/") or "://" in rel or rel.startswith("//"):
        return True
    return ".." in Path(rel).parts


_MAX_READ_BYTES = 1_000_000


def _resolve_jailed(root: Path, rel: str, *, allow_root: bool = False) -> Path | None:
    if _invalid_rel_path(rel):
        return None
    target = (root / rel).resolve() if rel else root.resolve()
    if not target.is_relative_to(root):
        return None
    if target == root and not allow_root:
        return None
    return target


async def _workspace_root(request: Request, workspace_id: str) -> tuple[Path | None, JSONResponse | None]:
    store = request.app.state.coding_workspaces
    row = await store.get(workspace_id)
    if row is None:
        return None, JSONResponse({"error": "workspace not found"}, status_code=404)
    root = store.workspaces_root.resolve()
    workspace = Path(row["path"]).resolve()
    if not workspace.is_relative_to(root) or workspace == root:
        return None, JSONResponse({"error": "workspace not found"}, status_code=404)
    return workspace, None


@router.post("/api/coding/workspaces")
async def create_workspace(request: Request, body: CreateWorkspaceBody):
    name = (body.name or "").strip()
    if not name:
        return JSONResponse({"error": "name is required"}, status_code=400)
    store = request.app.state.coding_workspaces
    row = await store.create(name)
    return row


@router.get("/api/coding/workspaces")
async def list_workspaces(request: Request):
    store = request.app.state.coding_workspaces
    return await store.list()


@router.get("/api/coding/workspaces/{workspace_id}/files")
async def list_files(request: Request, workspace_id: str, subpath: str = ""):
    root, err = await _workspace_root(request, workspace_id)
    if err is not None:
        return err
    target = _resolve_jailed(root, subpath, allow_root=True)
    if target is None:
        return JSONResponse({"error": "invalid path"}, status_code=400)
    if not target.is_dir():
        return JSONResponse({"error": "not found"}, status_code=404)
    entries = []
    for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        entries.append({"name": child.name, "is_dir": child.is_dir()})
    return entries


@router.get("/api/coding/workspaces/{workspace_id}/file")
async def read_file(request: Request, workspace_id: str, path: str):
    root, err = await _workspace_root(request, workspace_id)
    if err is not None:
        return err
    target = _resolve_jailed(root, path)
    if target is None:
        return JSONResponse({"error": "invalid path"}, status_code=400)
    if not target.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    if target.stat().st_size > _MAX_READ_BYTES:
        return JSONResponse({"error": "file too large"}, status_code=400)
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return JSONResponse({"error": "binary file"}, status_code=400)
    return {"path": path, "content": content}


@router.put("/api/coding/workspaces/{workspace_id}/file")
async def write_file(request: Request, workspace_id: str, body: WriteFileBody):
    root, err = await _workspace_root(request, workspace_id)
    if err is not None:
        return err
    rel = body.path or ""
    target = _resolve_jailed(root, rel)
    if target is None:
        return JSONResponse({"error": "invalid path"}, status_code=400)
    if target == root or target.is_dir():
        return JSONResponse({"error": "invalid path"}, status_code=400)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.content)
    return {"path": rel, "ok": True}


@router.delete("/api/coding/workspaces/{workspace_id}")
async def delete_workspace(request: Request, workspace_id: str):
    store = request.app.state.coding_workspaces
    removed = await store.delete(workspace_id)
    if not removed:
        return JSONResponse({"error": "workspace not found"}, status_code=404)
    return {"ok": True}