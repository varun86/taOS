"""Tests for the tier-aware image-editing routes (routes/images_edit.py)."""
import base64
import io
from types import SimpleNamespace

import httpx
import pytest
import respx
from PIL import Image

from tinyagentos.app import create_app
from tinyagentos.routes.images_edit import (
    EditRequest,
    FluxFillClient,
    _get_edit_backend,
    edit_image,
)


def _png_b64(width=8, height=8, color=(20, 120, 200)) -> str:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _backend(name, btype, priority=10):
    return SimpleNamespace(name=name, type=btype, priority=priority, url=f"http://{name}")


class _FakeCatalog:
    def __init__(self, by_cap):
        self._by_cap = by_cap

    def backends_with_capability(self, capability):
        return list(self._by_cap.get(capability, []))


def _request_with_catalog(catalog):
    state = SimpleNamespace(backend_catalog=catalog)
    return SimpleNamespace(app=SimpleNamespace(state=state))


def test_edit_routes_registered():
    """The three edit endpoints + the capabilities probe exist on the app."""
    app = create_app()
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/images/edit" in paths
    assert "/api/images/remove-bg" in paths
    assert "/api/images/upscale" in paths
    assert "/api/images/edit/capabilities" in paths


def test_tier_preference_quality_prefers_flux_fill():
    """quality tier prefers the GPU diffusion backend (flux-fill) over iopaint."""
    catalog = _FakeCatalog(
        {"image-editing": [_backend("io", "iopaint"), _backend("flux", "flux-fill")]}
    )
    req = _request_with_catalog(catalog)
    url, btype, name = _get_edit_backend(req, "image-editing", "quality")
    assert btype == "flux-fill"
    assert name == "flux"


def test_tier_preference_fast_prefers_iopaint():
    """fast tier prefers the CPU/NPU backend (iopaint) over flux-fill."""
    catalog = _FakeCatalog(
        {"image-editing": [_backend("flux", "flux-fill"), _backend("io", "iopaint")]}
    )
    req = _request_with_catalog(catalog)
    url, btype, name = _get_edit_backend(req, "image-editing", "fast")
    assert btype == "iopaint"
    assert name == "io"


def test_tier_preference_falls_back_when_preferred_absent():
    """quality tier still resolves iopaint when no flux-fill backend exists."""
    catalog = _FakeCatalog({"image-editing": [_backend("io", "iopaint")]})
    req = _request_with_catalog(catalog)
    url, btype, name = _get_edit_backend(req, "image-editing", "quality")
    assert btype == "iopaint"


def test_no_backend_returns_none():
    """No healthy backend for the capability → graceful None."""
    catalog = _FakeCatalog({})
    req = _request_with_catalog(catalog)
    assert _get_edit_backend(req, "image-editing", "fast") is None


def test_no_catalog_returns_none():
    """No live catalog (scheduler not started) → None, never raises."""
    req = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(backend_catalog=None)))
    assert _get_edit_backend(req, "upscale", "fast") is None


# --------------------------------------------------------------------------- #
#  FluxFillClient (A1111 img2img inpaint)                                      #
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
@respx.mock
async def test_flux_fill_inpaint_posts_a1111_img2img():
    """inpaint() POSTs base64 init_images + mask to /sdapi/v1/img2img and
    decodes images[0] from the JSON response back to PNG bytes."""
    result_b64 = _png_b64(color=(255, 0, 0))
    route = respx.post("http://flux:7864/sdapi/v1/img2img").mock(
        return_value=httpx.Response(200, json={"images": [result_b64]})
    )

    client = FluxFillClient("http://flux:7864")
    out = await client.inpaint(_png_b64(width=37, height=53), _png_b64(width=37, height=53, color=(0, 0, 0)), prompt="a cat")

    assert route.called
    sent = route.calls.last.request
    import json

    payload = json.loads(sent.content)
    assert sent.url.path == "/sdapi/v1/img2img"
    assert isinstance(payload["init_images"], list) and len(payload["init_images"]) == 1
    # init_images[0] and mask are valid base64 PNGs.
    assert Image.open(io.BytesIO(base64.b64decode(payload["init_images"][0]))).format == "PNG"
    assert Image.open(io.BytesIO(base64.b64decode(payload["mask"]))).format == "PNG"
    # width/height are pinned to the source image so the server does not fall
    # back to a default 512x512 size and wrongly resize the result.
    assert (payload["width"], payload["height"]) == (37, 53)
    assert payload["prompt"] == "a cat"
    assert payload["cfg_scale"] == pytest.approx(30.0)
    # Returned bytes are the decoded result PNG.
    assert out == base64.b64decode(result_b64)


@pytest.mark.asyncio
@respx.mock
async def test_flux_fill_outpaint_pads_canvas():
    """Outpaint pre-pads the init image + mask larger than the source, since
    sd.cpp img2img does not natively grow the canvas."""
    src_b64 = _png_b64(width=16, height=16)
    respx.post("http://flux:7864/sdapi/v1/img2img").mock(
        return_value=httpx.Response(200, json={"images": [_png_b64()]})
    )

    client = FluxFillClient("http://flux:7864")
    await client.inpaint(src_b64, _png_b64(width=16, height=16, color=(0, 0, 0)), outpaint=True)

    import json

    payload = json.loads(respx.calls.last.request.content)
    padded = Image.open(io.BytesIO(base64.b64decode(payload["init_images"][0])))
    mask = Image.open(io.BytesIO(base64.b64decode(payload["mask"])))
    assert padded.size[0] > 16 and padded.size[1] > 16
    assert mask.size == padded.size
    # width/height match the padded canvas actually sent, not the 16x16 source.
    assert (payload["width"], payload["height"]) == padded.size
    # The outpaint mask border is white (paint) and the centre is black (keep).
    assert mask.convert("L").getpixel((0, 0)) == 255
    assert mask.convert("L").getpixel((mask.size[0] // 2, mask.size[1] // 2)) == 0


@pytest.mark.asyncio
@respx.mock
async def test_flux_fill_missing_images_raises():
    """A response without images raises, which edit_image maps to an error."""
    respx.post("http://flux:7864/sdapi/v1/img2img").mock(
        return_value=httpx.Response(200, json={"images": []})
    )
    client = FluxFillClient("http://flux:7864")
    with pytest.raises(Exception):
        await client.inpaint(_png_b64(), _png_b64())


# --------------------------------------------------------------------------- #
#  edit_image dispatch → FluxFillClient on the quality tier                    #
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
@respx.mock
async def test_edit_image_quality_routes_to_flux_fill(tmp_path):
    """A healthy flux-fill backend on the quality tier dispatches to
    FluxFillClient (POST /sdapi/v1/img2img) and saves the returned bytes."""
    # Workspace: config_path.parent/workspace/images/generated/
    images_dir = tmp_path / "workspace" / "images" / "generated"
    images_dir.mkdir(parents=True)
    src_bytes = base64.b64decode(_png_b64())
    (images_dir / "src.png").write_bytes(src_bytes)

    result_b64 = _png_b64(color=(7, 8, 9))
    route = respx.post("http://flux/sdapi/v1/img2img").mock(
        return_value=httpx.Response(200, json={"images": [result_b64]})
    )

    catalog = _FakeCatalog({"image-editing": [_backend("flux", "flux-fill")]})
    state = SimpleNamespace(backend_catalog=catalog, config_path=str(tmp_path / "config.json"))
    request = SimpleNamespace(app=SimpleNamespace(state=state))

    body = EditRequest(image_ref="src.png", op="inpaint", mask=_png_b64(), prompt="sky", tier="quality")
    result = await edit_image(request, body)

    assert route.called
    assert result["status"] == "edited"
    saved = (images_dir / result["filename"]).read_bytes()
    assert saved == base64.b64decode(result_b64)


@pytest.mark.asyncio
@respx.mock
async def test_edit_image_quality_falls_back_to_iopaint(tmp_path):
    """With no flux-fill backend, the quality tier still uses iopaint
    (POST /api/v1/inpaint), leaving the fast path untouched."""
    images_dir = tmp_path / "workspace" / "images" / "generated"
    images_dir.mkdir(parents=True)
    (images_dir / "src.png").write_bytes(base64.b64decode(_png_b64()))

    result_png = base64.b64decode(_png_b64(color=(1, 2, 3)))
    route = respx.post("http://io/api/v1/inpaint").mock(
        return_value=httpx.Response(200, content=result_png, headers={"content-type": "image/png"})
    )

    catalog = _FakeCatalog({"image-editing": [_backend("io", "iopaint")]})
    state = SimpleNamespace(backend_catalog=catalog, config_path=str(tmp_path / "config.json"))
    request = SimpleNamespace(app=SimpleNamespace(state=state))

    body = EditRequest(image_ref="src.png", op="inpaint", mask=_png_b64(), tier="quality")
    result = await edit_image(request, body)

    assert route.called
    assert (images_dir / result["filename"]).read_bytes() == result_png
