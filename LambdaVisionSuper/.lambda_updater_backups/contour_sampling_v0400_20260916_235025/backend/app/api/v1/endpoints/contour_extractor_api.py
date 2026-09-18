from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from app.services.vision_labs.image.session import PreviewEncoder
from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.contour_extractor.models import ContourExtractorDefinition
from app.services.vision_labs.contour_extractor.session import CONTOUR_SESSION_MANAGER
from app.services.vision_labs.service import LAB_SERVICE_REPOSITORY, LAB_SERVICE_RUNTIME

router = APIRouter()


def _error(exc: Exception):
    if isinstance(exc, HTTPException): return exc
    if isinstance(exc, (KeyError, FileNotFoundError)): return HTTPException(404, str(exc))
    return HTTPException(400, str(exc))


def _decode_image(raw: bytes):
    if not raw: raise ValueError("Image body is empty")
    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
    if image is None: raise ValueError("Could not decode image")
    if image.ndim == 2: return ImageFrame(image, color_space=ColorSpace.GRAY, source_id="raw_image")
    if image.ndim == 3 and image.shape[2] == 4: image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return ImageFrame(image, color_space=ColorSpace.BGR, source_id="raw_image")


@router.post("/sessions")
def create_session():
    session = CONTOUR_SESSION_MANAGER.create()
    return {"success": True, "session_id": session.session_id, "revision": session.revision}


@router.delete("/sessions/{session_id}")
def close_session(session_id: str):
    return {"success": CONTOUR_SESSION_MANAGER.close(session_id)}


@router.put("/sessions/{session_id}/definition")
def set_definition(session_id: str, definition: ContourExtractorDefinition):
    try:
        session = CONTOUR_SESSION_MANAGER.get(session_id)
        session.set_definition(definition)
        return {"success": True, "revision": session.revision}
    except Exception as exc: raise _error(exc)


@router.post("/sessions/{session_id}/run")
async def run_session(session_id: str, request: Request):
    try:
        raw = await request.body()
        raw_image = _decode_image(raw)
        session = CONTOUR_SESSION_MANAGER.get(session_id)
        result = session.run(
            raw_image,
            load_service=lambda service_id, version: LAB_SERVICE_REPOSITORY.get(service_id, version=version),
            run_service=LAB_SERVICE_RUNTIME.run,
        )
        return {
            "success": True,
            "revision": session.revision,
            "summary": result.store.summary("final"),
            "stages": result.stage_summaries,
            "timings_ms": result.timings_ms,
            "sources": [
                {"name": "raw_image", "type": "image"},
                {"name": "source_image", "type": "image"},
                {"name": "edge_map", "type": "binary_mask"},
                {"name": "contour_image", "type": "image"},
            ],
        }
    except Exception as exc: raise _error(exc)


@router.get("/sessions/{session_id}/contours")
def list_contours(session_id: str, selection: str = "final", offset: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=1000)):
    try:
        result = CONTOUR_SESSION_MANAGER.get(session_id).result
        if result is None: raise RuntimeError("Run contour extraction first")
        return {"success": True, "summary": result.store.summary(selection), "rows": result.store.metric_rows(selection, offset=offset, limit=limit)}
    except Exception as exc: raise _error(exc)


@router.get("/sessions/{session_id}/contours/geometry")
def contour_geometry(session_id: str, ids: str = ""):
    try:
        result = CONTOUR_SESSION_MANAGER.get(session_id).result
        if result is None: raise RuntimeError("Run contour extraction first")
        parsed = [int(value) for value in ids.split(",") if value.strip()][:200]
        return {"success": True, "contours": result.store.geometry(parsed)}
    except Exception as exc: raise _error(exc)


@router.get("/sessions/{session_id}/preview/{source_name}")
def source_preview(session_id: str, source_name: str, max_width: int = Query(1800, ge=64, le=4096), quality: int = Query(92, ge=20, le=100)):
    try:
        result = CONTOUR_SESSION_MANAGER.get(session_id).result
        if result is None: raise RuntimeError("Run contour extraction first")
        if source_name not in result.sources or source_name == "manifest": raise KeyError(source_name)
        payload, mime = PreviewEncoder.encode(result.sources[source_name], max_width=max_width, quality=quality)
        return Response(content=payload, media_type=mime)
    except Exception as exc: raise _error(exc)
