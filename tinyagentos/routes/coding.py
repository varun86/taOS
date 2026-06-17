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


def _resolve_jailed(root: Path, rel: str) -> Path | None:
    if _invalid_rel_path(rel):
        return None
    target = (root / rel).resolve()
    if not target.is_relative_to(root) or target == root:
        return None
    return target


async def _workspace_root(request: Request, workspace_id: str) -> tuple[Path | None, JSONResponse | None]:
    store = request.app.state.coding_workspaces
    row = await store.get(workspace_id)
    if row is None:
        return None, JSONResponse({"error": "workspace not found"}, status_code=404)
    return Path(row["path"]).resolve(), None


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
    target = _resolve_jailed(root, subpath)
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
    return {"path": path, "content": target.read_text()}


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