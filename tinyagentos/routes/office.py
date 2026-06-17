from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from tinyagentos.userspace.data_store import UserspaceDataStore

router = APIRouter()

OFFICE_APP_ID = "office-suite"
DOCS_KEY = "documents"
VALID_KINDS = frozenset({"write", "calc", "db", "slides"})


async def _store(request: Request) -> UserspaceDataStore:
    store = request.app.state.userspace_data
    if store._db is None:
        await store.init()
    return store


async def _load_docs(store: UserspaceDataStore) -> list[dict[str, Any]]:
    docs = await store.kv_get(OFFICE_APP_ID, DOCS_KEY)
    return docs if isinstance(docs, list) else []


async def _save_docs(store: UserspaceDataStore, docs: list[dict[str, Any]]) -> None:
    await store.kv_set(OFFICE_APP_ID, DOCS_KEY, docs)


def _find_doc(docs: list[dict[str, Any]], doc_id: str) -> dict[str, Any] | None:
    for doc in docs:
        if doc.get("id") == doc_id:
            return doc
    return None


def _list_item(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": doc["id"],
        "kind": doc["kind"],
        "title": doc["title"],
        "updated_at": doc.get("updated_at"),
    }


def _validate_kind(kind: str | None) -> str | None:
    if kind is None or kind not in VALID_KINDS:
        return None
    return kind


def _validate_title(title: Any) -> str | None:
    if not isinstance(title, str) or not title.strip():
        return None
    return title.strip()


@router.post("/api/office/docs")
async def create_doc(request: Request):
    body = await request.json()
    kind = _validate_kind(body.get("kind"))
    if kind is None:
        return JSONResponse({"error": "kind must be one of write, calc, db, slides"}, status_code=400)
    title = _validate_title(body.get("title"))
    if title is None:
        return JSONResponse({"error": "title is required"}, status_code=400)
    content = body.get("content", "")
    if not isinstance(content, str):
        return JSONResponse({"error": "content must be a string"}, status_code=400)

    store = await _store(request)
    docs = await _load_docs(store)
    now = int(time.time())
    doc = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "title": title,
        "content": content,
        "updated_at": now,
    }
    docs.append(doc)
    await _save_docs(store, docs)
    return doc


@router.get("/api/office/docs")
async def list_docs(request: Request):
    store = await _store(request)
    docs = await _load_docs(store)
    return [_list_item(doc) for doc in docs]


@router.get("/api/office/docs/{doc_id}")
async def get_doc(request: Request, doc_id: str):
    store = await _store(request)
    docs = await _load_docs(store)
    doc = _find_doc(docs, doc_id)
    if doc is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return doc


@router.put("/api/office/docs/{doc_id}")
async def update_doc(request: Request, doc_id: str):
    body = await request.json()
    store = await _store(request)
    docs = await _load_docs(store)
    doc = _find_doc(docs, doc_id)
    if doc is None:
        return JSONResponse({"error": "not found"}, status_code=404)

    if "kind" in body:
        kind = _validate_kind(body.get("kind"))
        if kind is None:
            return JSONResponse({"error": "kind must be one of write, calc, db, slides"}, status_code=400)
        doc["kind"] = kind
    if "title" in body:
        title = _validate_title(body.get("title"))
        if title is None:
            return JSONResponse({"error": "title is required"}, status_code=400)
        doc["title"] = title
    if "content" in body:
        content = body.get("content")
        if not isinstance(content, str):
            return JSONResponse({"error": "content must be a string"}, status_code=400)
        doc["content"] = content

    doc["updated_at"] = int(time.time())
    await _save_docs(store, docs)
    return doc


@router.delete("/api/office/docs/{doc_id}")
async def delete_doc(request: Request, doc_id: str):
    store = await _store(request)
    docs = await _load_docs(store)
    before = len(docs)
    docs = [doc for doc in docs if doc.get("id") != doc_id]
    if len(docs) == before:
        return JSONResponse({"error": "not found"}, status_code=404)
    await _save_docs(store, docs)
    return {"status": "deleted", "id": doc_id}