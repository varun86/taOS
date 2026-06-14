# tinyagentos/routes/images_edit.py
"""Tier-aware AI image-editing endpoints for the Images Studio.

Mirrors ``tinyagentos/routes/images.py``: source images are resolved from the
workspace generated-images dir, results are saved back there as PNGs, and a
url + image_ref is returned. Routing goes through the backend catalog by
capability, with a fast|quality tier preference over backend type.

Backends:
  ``iopaint``   — LaMa erase/inpaint, rembg RemoveBG plugin, RealESRGAN upscale
                  (https://github.com/Sanster/IOPaint). The fast/CPU/NPU tier.
  ``flux-fill`` — FLUX.1-Fill inpaint/outpaint behind an A1111-style server.
                  The quality/GPU tier (image-editing only).
"""
from __future__ import annotations

import base64
import json
import logging
import time
from pathlib import Path
from typing import Literal, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tinyagentos.routes.images import _image_url_path, _images_dir

logger = logging.getLogger(__name__)

router = APIRouter()

# Tier → backend-type preference per capability. Lower index = more preferred.
# quality prefers the GPU diffusion tier (flux-fill) then falls back to iopaint;
# fast prefers iopaint (CPU/NPU, the LaMa eraser). Background-removal / upscale
# are iopaint-only capabilities, so both tiers resolve to iopaint there.
_TIER_PREFERENCE: dict[str, dict[str, list[str]]] = {
    "image-editing": {
        "quality": ["flux-fill", "iopaint"],
        "fast": ["iopaint", "flux-fill"],
    },
    "background-removal": {
        "quality": ["iopaint"],
        "fast": ["iopaint"],
    },
    "upscale": {
        "quality": ["iopaint"],
        "fast": ["iopaint"],
    },
}


# --------------------------------------------------------------------------- #
#  Request models                                                             #
# --------------------------------------------------------------------------- #
class EditRequest(BaseModel):
    image_ref: str
    op: Literal["erase", "inpaint", "outpaint"]
    mask: str  # base64 png (raw or data-URI; IOPaint strips the prefix)
    prompt: str = ""
    tier: Literal["fast", "quality"] = "fast"


class RemoveBgRequest(BaseModel):
    image_ref: str


class UpscaleRequest(BaseModel):
    image_ref: str
    scale: Literal[2, 4] = 2


# --------------------------------------------------------------------------- #
#  Backend routing                                                            #
# --------------------------------------------------------------------------- #
def _get_edit_backend(
    request: Request, capability: str, tier: str
) -> Optional[tuple[str, str, Optional[str]]]:
    """Pick a healthy backend for *capability*, ordered by the *tier* type
    preference. Returns (url, type, name) or None when none is available.

    Mirrors ``images._get_image_backend``: capability-driven via the live
    catalog, health/enabled/running already filtered by
    ``backends_with_capability``.
    """
    catalog = getattr(request.app.state, "backend_catalog", None)
    if catalog is None:
        return None

    healthy = catalog.backends_with_capability(capability)
    if not healthy:
        return None

    pref = _TIER_PREFERENCE.get(capability, {}).get(tier, [])

    def rank(backend) -> tuple[int, int]:
        try:
            type_rank = pref.index(backend.type)
        except ValueError:
            type_rank = len(pref)  # types not listed go last
        return (type_rank, backend.priority)

    healthy = sorted(healthy, key=rank)
    chosen = healthy[0]
    return chosen.url, chosen.type, chosen.name


def _resolve_source(request: Request, image_ref: str) -> Optional[Path]:
    """Resolve an image_ref (filename) to a path in the generated dir,
    guarding against traversal. Returns None if not found / invalid."""
    if "/" in image_ref or "\\" in image_ref or ".." in image_ref:
        return None
    path = _images_dir(request) / image_ref
    return path if path.exists() else None


def _save_result(request: Request, image_bytes: bytes, *, source_ref: str, op: str) -> dict:
    """Save result PNG into the generated dir, copying the source's prompt
    metadata so the new image is browsable. Returns {url, image_ref, ...}."""
    images_dir = _images_dir(request)
    # Unique stem so two edits of the same op within one second don't collide
    # (int(time.time()) alone overwrote the earlier output).
    stem = f"{int(time.time())}_{op}_{uuid4().hex[:8]}"
    filename = f"{stem}.png"
    (images_dir / filename).write_bytes(image_bytes)

    # Carry forward source metadata where available.
    metadata = {"prompt": "", "model": op, "size": "", "steps": 0, "seed": 0, "guidance_scale": 0}
    src_meta = (images_dir / source_ref).with_suffix(".json")
    if src_meta.exists():
        try:
            prev = json.loads(src_meta.read_text())
            metadata["prompt"] = prev.get("prompt", "")
        except (json.JSONDecodeError, OSError):
            pass
    metadata["model"] = f"edit:{op}"
    (images_dir / f"{stem}.json").write_text(json.dumps(metadata, indent=2))

    return {
        "status": "edited",
        "filename": filename,
        "image_ref": filename,
        "url": _image_url_path(filename),
        "path": _image_url_path(filename),
    }


# --------------------------------------------------------------------------- #
#  IOPaint adapter (async httpx client)                                        #
# --------------------------------------------------------------------------- #
class IOPaintClient:
    """Thin async client for the IOPaint HTTP API.

    Endpoints (IOPaint >= 1.x, github.com/Sanster/IOPaint):
      POST /api/v1/inpaint           — erase/inpaint/outpaint (LaMa or diffusion)
      POST /api/v1/run_plugin_gen_image — RemoveBG / RealESRGAN plugins
    Both take base64 image(s) in JSON and return raw image bytes (image/png).
    """

    def __init__(self, base_url: str, *, timeout: float = 300.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    async def inpaint(
        self,
        image_b64: str,
        mask_b64: str,
        *,
        prompt: str = "",
        outpaint: bool = False,
    ) -> bytes:
        payload: dict = {
            "image": image_b64,
            "mask": mask_b64,
            "prompt": prompt,
            "sd_seed": -1,
        }
        if outpaint:
            # enable_extender grows the canvas before diffusion outpaint.
            payload["enable_extender"] = True
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base}/api/v1/inpaint", json=payload)
            resp.raise_for_status()
            return resp.content

    async def run_plugin(self, name: str, image_b64: str, *, scale: float = 2.0) -> bytes:
        payload = {"name": name, "image": image_b64, "scale": float(scale), "clicks": []}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base}/api/v1/run_plugin_gen_image", json=payload
            )
            resp.raise_for_status()
            return resp.content


# --------------------------------------------------------------------------- #
#  Error helpers                                                               #
# --------------------------------------------------------------------------- #
_NO_BACKEND = {
    "error": "No image-editing backend installed. Install IOPaint from the Store."
}


def _backend_error_response(exc: Exception) -> JSONResponse:
    if isinstance(exc, httpx.ConnectError):
        return JSONResponse(
            {"error": "Cannot connect to the editing backend. Is it running?"},
            status_code=503,
        )
    if isinstance(exc, httpx.TimeoutException):
        return JSONResponse(
            {"error": "Image edit timed out. The backend may be busy."},
            status_code=504,
        )
    if isinstance(exc, httpx.HTTPStatusError):
        return JSONResponse(
            {"error": f"Editing backend returned error: {exc.response.status_code}"},
            status_code=502,
        )
    logger.exception("image edit failed")
    return JSONResponse({"error": f"Unexpected error: {exc}"}, status_code=500)


# --------------------------------------------------------------------------- #
#  Endpoints                                                                   #
# --------------------------------------------------------------------------- #
@router.post("/api/images/edit")
async def edit_image(request: Request, body: EditRequest):
    """Erase / inpaint / outpaint a region of an image via the editing backend."""
    source = _resolve_source(request, body.image_ref)
    if source is None:
        return JSONResponse({"error": f"Image '{body.image_ref}' not found"}, status_code=404)

    backend = _get_edit_backend(request, "image-editing", body.tier)
    if backend is None:
        return JSONResponse(_NO_BACKEND, status_code=503)
    url, backend_type, _name = backend
    if backend_type != "iopaint":
        # Only the IOPaint client is implemented today; flux-fill (the quality
        # inpaint/outpaint tier) is routed by the catalog but its client is a
        # follow-up. _get_edit_backend already falls back to iopaint when no
        # flux-fill backend is healthy, so this only triggers if one exists.
        return JSONResponse(
            {
                "error": f"Edit backend '{backend_type}' has no client wired yet "
                "(FLUX Fill pending); try the fast tier."
            },
            status_code=503,
        )

    image_b64 = base64.b64encode(source.read_bytes()).decode()
    client = IOPaintClient(url)
    try:
        result_bytes = await client.inpaint(
            image_b64,
            body.mask,
            prompt=body.prompt,
            outpaint=body.op == "outpaint",
        )
    except Exception as exc:  # noqa: BLE001 — mapped to a clean HTTP response
        return _backend_error_response(exc)

    return _save_result(request, result_bytes, source_ref=body.image_ref, op=body.op)


@router.post("/api/images/remove-bg")
async def remove_background(request: Request, body: RemoveBgRequest):
    """Remove the background of an image via the rembg (RemoveBG) plugin."""
    source = _resolve_source(request, body.image_ref)
    if source is None:
        return JSONResponse({"error": f"Image '{body.image_ref}' not found"}, status_code=404)

    backend = _get_edit_backend(request, "background-removal", "fast")
    if backend is None:
        return JSONResponse(_NO_BACKEND, status_code=503)
    url, _backend_type, _name = backend

    image_b64 = base64.b64encode(source.read_bytes()).decode()
    client = IOPaintClient(url)
    try:
        result_bytes = await client.run_plugin("RemoveBG", image_b64)
    except Exception as exc:  # noqa: BLE001
        return _backend_error_response(exc)

    return _save_result(request, result_bytes, source_ref=body.image_ref, op="removebg")


@router.post("/api/images/upscale")
async def upscale_image(request: Request, body: UpscaleRequest):
    """Upscale an image 2x or 4x via the RealESRGAN plugin."""
    source = _resolve_source(request, body.image_ref)
    if source is None:
        return JSONResponse({"error": f"Image '{body.image_ref}' not found"}, status_code=404)

    backend = _get_edit_backend(request, "upscale", "fast")
    if backend is None:
        return JSONResponse(_NO_BACKEND, status_code=503)
    url, _backend_type, _name = backend

    image_b64 = base64.b64encode(source.read_bytes()).decode()
    client = IOPaintClient(url)
    try:
        result_bytes = await client.run_plugin("RealESRGAN", image_b64, scale=float(body.scale))
    except Exception as exc:  # noqa: BLE001
        return _backend_error_response(exc)

    return _save_result(request, result_bytes, source_ref=body.image_ref, op="upscale")


@router.get("/api/images/edit/capabilities")
async def edit_capabilities(request: Request):
    """Report which editing capabilities currently have a healthy backend,
    so the frontend can gate ops."""
    catalog = getattr(request.app.state, "backend_catalog", None)

    def has(capability: str) -> bool:
        if catalog is None:
            return False
        return bool(catalog.backends_with_capability(capability))

    return {
        "image_editing": has("image-editing"),
        "background_removal": has("background-removal"),
        "upscale": has("upscale"),
    }
