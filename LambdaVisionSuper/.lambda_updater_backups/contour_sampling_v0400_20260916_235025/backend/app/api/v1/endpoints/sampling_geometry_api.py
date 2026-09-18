from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.vision_labs.core import ExecutionMode
from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.operators import (
    load_sampling_geometry_operators,
)
from app.services.vision_labs.sampling_geometry.pipeline import (
    SamplingPipelineDefinition,
    SamplingPipelineValidator,
    model_to_dict,
)
from app.services.vision_labs.sampling_geometry.preview import SamplingPreviewEncoder
from app.services.vision_labs.sampling_geometry.registry import (
    SAMPLING_OPERATOR_REGISTRY,
)
from app.services.vision_labs.sampling_geometry.repository import (
    SamplingPipelineRepository,
)
from app.services.vision_labs.sampling_geometry.serialization import artifact_to_json
from app.services.vision_labs.sampling_geometry.source_board import resolve_source_board
from app.services.vision_labs.sampling_geometry.session import (
    SamplingGeometrySessionManager,
)
from app.services.vision_labs.service import (
    LAB_SERVICE_REPOSITORY,
    LAB_SERVICE_RUNTIME,
)


load_sampling_geometry_operators()

router = APIRouter()
session_manager = SamplingGeometrySessionManager()
pipeline_repository = SamplingPipelineRepository()


class SavePipelineRequest(BaseModel):
    name: str
    pipeline: SamplingPipelineDefinition


def _http_error(exc: Exception, status_code: int = 400) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, (KeyError, FileNotFoundError)):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=status_code, detail=str(exc))


def _decode_image(raw: bytes, *, source_id: str) -> ImageFrame:
    if not raw:
        raise ValueError("Uploaded image body is empty")
    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Uploaded body could not be decoded as an image")
    if image.ndim == 2:
        color_space = ColorSpace.GRAY
    elif image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        color_space = ColorSpace.BGR
    else:
        color_space = ColorSpace.BGR
    return ImageFrame(data=image, color_space=color_space, source_id=source_id)


def _decode_mask(raw: bytes) -> BinaryMask:
    if not raw:
        raise ValueError("Uploaded mask body is empty")
    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("Uploaded body could not be decoded as a mask")
    return BinaryMask(data=(image > 0).astype(np.uint8) * 255)


def _source_manifest(value: Any) -> dict[str, Any]:
    if isinstance(value, ImageFrame):
        return {
            "type": "image",
            "shape": list(value.shape),
            "color_space": value.color_space.value,
        }
    if isinstance(value, BinaryMask):
        return {"type": "binary_mask", "shape": list(value.shape)}
    return {"type": type(value).__name__}


@router.get("/operators", summary="Sampling / Geometry LAB operator catalog")
def get_operator_catalog(workspace: str | None = None):
    return {
        "success": True,
        "operators": SAMPLING_OPERATOR_REGISTRY.manifests(workspace),
    }


@router.post("/pipelines/validate", summary="Validate Sampling / Geometry pipeline")
def validate_pipeline(pipeline: SamplingPipelineDefinition):
    errors = SamplingPipelineValidator().validate(
        pipeline,
        raise_on_error=False,
    )
    return {"success": not errors, "valid": not errors, "errors": errors}


@router.get("/pipelines", summary="List saved Sampling / Geometry pipelines")
def list_pipelines():
    return {"success": True, "pipelines": pipeline_repository.list()}


@router.get("/pipelines/{name}", summary="Load saved Sampling / Geometry pipeline")
def load_pipeline(name: str):
    try:
        pipeline = pipeline_repository.load(name)
        return {"success": True, "pipeline": model_to_dict(pipeline)}
    except Exception as exc:
        raise _http_error(exc)


@router.post("/pipelines/save", summary="Save Sampling / Geometry pipeline")
def save_pipeline(request: SavePipelineRequest):
    try:
        errors = SamplingPipelineValidator().validate(
            request.pipeline,
            raise_on_error=False,
        )
        if errors:
            raise ValueError("Pipeline is invalid: " + "; ".join(errors))
        path = pipeline_repository.save(request.name, request.pipeline)
        return {"success": True, "name": request.name, "path": str(path)}
    except Exception as exc:
        raise _http_error(exc)


@router.post("/sessions", summary="Create Sampling / Geometry interactive session")
def create_session():
    session = session_manager.create()
    return {
        "success": True,
        "session_id": session.session_id,
        "revision": session.revision,
    }


@router.delete("/sessions/{session_id}", summary="Close Sampling / Geometry session")
def close_session(session_id: str):
    closed = session_manager.close(session_id)
    if not closed:
        raise HTTPException(status_code=404, detail=f"Unknown session: {session_id}")
    return {"success": True}


@router.post(
    "/sessions/{session_id}/source-board",
    summary="Build the shared Sampling / Geometry Source Board from one raw image",
)
async def build_source_board(
    session_id: str,
    request: Request,
    image_service_id: str | None = None,
    image_output_name: str | None = None,
    image_version: int | None = None,
    geometry_service_id: str | None = None,
    geometry_output_name: str | None = None,
    geometry_version: int | None = None,
    canny_low: float = Query(80.0, ge=0.0, le=255.0),
    canny_high: float = Query(160.0, ge=0.0, le=255.0),
    blur_kernel: int = Query(3, ge=1, le=31),
    enable_geometry: bool = Query(False),
):
    try:
        raw = await request.body()
        frame = _decode_image(raw, source_id="raw_image")
        config = {
            "image_service": {
                "service_id": image_service_id or "",
                "version": image_version,
                "output_name": image_output_name or "",
            },
            "geometry_service": {
                "service_id": geometry_service_id or "",
                "version": geometry_version,
                "output_name": geometry_output_name or "",
            },
            "canny_low": canny_low,
            "canny_high": canny_high,
            "blur_kernel": blur_kernel,
            "enable_geometry": bool(enable_geometry),
        }
        resolved = resolve_source_board(
            frame,
            config,
            load_service=lambda service_id, version: LAB_SERVICE_REPOSITORY.get(
                service_id,
                version=version,
            ),
            run_service=LAB_SERVICE_RUNTIME.run,
        )
        session = session_manager.get(session_id)
        session.set_source_board(resolved.sources, resolved.manifest)
        return {
            "success": True,
            "session_id": session_id,
            "revision": session.revision,
            "source_board": resolved.manifest,
        }
    except Exception as exc:
        raise _http_error(exc)


@router.get(
    "/sessions/{session_id}/source-board",
    summary="Read shared Sampling / Geometry Source Board manifest",
)
def get_source_board(session_id: str):
    try:
        session = session_manager.get(session_id)
        return {
            "success": True,
            "revision": session.revision,
            "source_board": session.source_board_manifest,
        }
    except Exception as exc:
        raise _http_error(exc)


@router.get(
    "/sessions/{session_id}/source-board/{source_name}/artifact",
    summary="Inspect a typed Source Board artifact as JSON",
)
def get_source_board_artifact(session_id: str, source_name: str):
    try:
        value = session_manager.get(session_id).get_source(source_name)
        return {
            "success": True,
            "source_name": source_name,
            "artifact": artifact_to_json(value),
        }
    except Exception as exc:
        raise _http_error(exc)


@router.post("/sessions/{session_id}/input/{source_name}", summary="Upload Sampling / Geometry source")
async def upload_input(
    session_id: str,
    source_name: str,
    request: Request,
    input_type: str = Query("image", regex="^(image|binary_mask)$"),
):
    try:
        raw = await request.body()
        value: Any
        if input_type == "binary_mask":
            value = _decode_mask(raw)
        else:
            value = _decode_image(raw, source_id=source_name)
        session = session_manager.get(session_id)
        session.set_source(source_name, value)
        return {
            "success": True,
            "session_id": session_id,
            "source_name": source_name,
            "revision": session.revision,
            "source": _source_manifest(value),
        }
    except Exception as exc:
        raise _http_error(exc)


@router.post(
    "/sessions/{session_id}/input/{source_name}/from-lab-service",
    summary="Resolve a Sampling / Geometry source by directly invoking a deployed Lab Service",
)
async def bind_input_from_lab_service(
    session_id: str,
    source_name: str,
    request: Request,
    service_id: str,
    output_name: str,
    version: int | None = None,
):
    try:
        service = LAB_SERVICE_REPOSITORY.get(service_id, version=version)
        if service.lab_type != "image_processing":
            raise ValueError(
                "Sampling / Geometry v1 currently accepts upstream image_processing Lab Services"
            )
        image_inputs = [
            name
            for name, port in service.inputs.items()
            if port.type == "image"
        ]
        if len(service.inputs) != 1 or len(image_inputs) != 1:
            raise ValueError(
                "Upstream service must currently expose exactly one Image input"
            )
        if output_name not in service.outputs:
            raise KeyError(f"Unknown upstream service output: {output_name}")
        binding = service.outputs[output_name]
        if binding.type not in {"image", "binary_mask"}:
            raise ValueError(
                "Sampling / Geometry source binding currently supports Image or BinaryMask service outputs"
            )

        raw = await request.body()
        frame = _decode_image(raw, source_id="upstream_service_input")
        run = LAB_SERVICE_RUNTIME.run(
            service,
            {image_inputs[0]: frame},
        )
        value = run.outputs[output_name]
        if not isinstance(value, (ImageFrame, BinaryMask)):
            raise TypeError(
                f"Upstream output {output_name!r} is not a raster source"
            )

        session = session_manager.get(session_id)
        session.set_source(source_name, value)
        return {
            "success": True,
            "session_id": session_id,
            "source_name": source_name,
            "revision": session.revision,
            "source": _source_manifest(value),
            "upstream": {
                "service_id": service.service_id,
                "service_version": service.version,
                "output_name": output_name,
                "lab_type": service.lab_type,
            },
        }
    except Exception as exc:
        raise _http_error(exc)


@router.put("/sessions/{session_id}/pipeline", summary="Set Sampling / Geometry session pipeline")
def set_session_pipeline(
    session_id: str,
    pipeline: SamplingPipelineDefinition,
):
    try:
        session = session_manager.get(session_id)
        session.set_pipeline(pipeline)
        return {
            "success": True,
            "revision": session.revision,
            "pipeline": model_to_dict(pipeline),
        }
    except Exception as exc:
        raise _http_error(exc)


@router.post("/sessions/{session_id}/run", summary="Run Sampling / Geometry session")
def run_session(session_id: str):
    try:
        session = session_manager.get(session_id)
        result = session.run(mode=ExecutionMode.FINAL)
        return {
            "success": True,
            "revision": session.revision,
            "result": result.manifest(),
        }
    except Exception as exc:
        raise _http_error(exc)


@router.get("/sessions/{session_id}/preview/source/{source_name}")
def preview_source(
    session_id: str,
    source_name: str,
    max_width: int = Query(1600, ge=64, le=4096),
    quality: int = Query(90, ge=20, le=100),
):
    try:
        session = session_manager.get(session_id)
        payload, mime = SamplingPreviewEncoder.encode(
            session.get_source(source_name),
            max_width=max_width,
            quality=quality,
        )
        return Response(content=payload, media_type=mime)
    except Exception as exc:
        raise _http_error(exc)


@router.get("/sessions/{session_id}/artifact/{node_id}/{port}")
def get_artifact_json(session_id: str, node_id: str, port: str):
    try:
        artifact = session_manager.get(session_id).get_artifact(node_id, port)
        return {
            "success": True,
            "artifact_id": artifact.artifact_id,
            "node_id": node_id,
            "port": port,
            "artifact": artifact_to_json(artifact.value),
        }
    except Exception as exc:
        raise _http_error(exc)


@router.get("/sessions/{session_id}/preview/node/{node_id}/{port}")
def preview_artifact(
    session_id: str,
    node_id: str,
    port: str,
    max_width: int = Query(1600, ge=64, le=4096),
    quality: int = Query(90, ge=20, le=100),
):
    try:
        artifact = session_manager.get(session_id).get_artifact(node_id, port)
        payload, mime = SamplingPreviewEncoder.encode(
            artifact.value,
            max_width=max_width,
            quality=quality,
        )
        return Response(content=payload, media_type=mime)
    except Exception as exc:
        raise _http_error(exc)

@router.get("/sessions/{session_id}/fft-reconstruction/{node_id}")
def fft_reconstruction(
    session_id: str,
    node_id: str,
    mode: str = Query("radial", regex="^(radial|angular|single)$"),
    center: float = Query(0.25, ge=0.0, le=1.0),
    width: float = Query(0.08, ge=0.001, le=1.0),
    angle_deg: float = Query(0.0, ge=0.0, le=180.0),
    angle_width_deg: float = Query(10.0, ge=0.5, le=90.0),
    fx: float = Query(0.0, ge=-1.0, le=1.0),
    fy: float = Query(0.0, ge=-1.0, le=1.0),
):
    """Educational inverse-FFT view for selected frequencies/bands.

    Global FFT answers WHAT frequencies exist, not WHERE a localized defect is.
    This endpoint reconstructs the image contribution of a selected radial band,
    orientation sector, or one conjugate frequency pair.
    """
    try:
        session = session_manager.get(session_id)
        definition = session.pipeline_definition
        if definition is None:
            raise RuntimeError("No Sampling pipeline configured")
        node = next((item for item in definition.nodes if item.id == node_id), None)
        if node is None or node.operator_id != "sampling.spectral.fft2d":
            raise ValueError("FFT reconstruction requires a 2D Fourier Spectrum node")
        source_name = None
        for alias, endpoint in definition.inputs.items():
            if endpoint.node_id == node_id and endpoint.port == "image":
                source_name = (definition.input_sources or {}).get(alias, alias)
                break
        if not source_name:
            raise ValueError("FFT node image input must be bound to a Source Board image")
        frame = session.get_source(source_name)
        from app.services.vision_labs.sampling_geometry.operators.common import image_channel
        params = dict(node.parameters or {})
        channel = params.get("channel", "gray")
        image = image_channel(frame, channel).astype(np.float32)
        h, w = image.shape[:2]
        if bool(params.get("remove_mean", True)):
            image = image - float(image.mean())
        if params.get("window", "hann") == "hann":
            image = image * np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
        spectrum = np.fft.fftshift(np.fft.fft2(image))
        yy, xx = np.indices((h, w), dtype=np.float64)
        cx = (w - 1) / 2.0; cy = (h - 1) / 2.0
        dx = xx - cx; dy = yy - cy
        radius = np.sqrt(dx*dx + dy*dy); radius /= max(1e-9, float(radius.max()))
        angle = np.mod(np.arctan2(dy, dx), np.pi)
        mask = np.zeros((h,w), dtype=bool)
        if mode == "radial":
            half = float(width) * 0.5
            mask = (radius >= max(0.0, center-half)) & (radius <= min(1.0, center+half))
        elif mode == "angular":
            target = np.deg2rad(float(angle_deg))
            half = np.deg2rad(float(angle_width_deg)) * 0.5
            delta = np.abs(np.angle(np.exp(1j*(angle-target))))
            delta = np.minimum(delta, np.abs(np.pi-delta))
            mask = delta <= half
        else:
            px = int(round(cx + float(fx) * cx)); py = int(round(cy + float(fy) * cy))
            px = int(np.clip(px, 0, w-1)); py = int(np.clip(py, 0, h-1))
            sx = int(round(2*cx-px)); sy = int(round(2*cy-py))
            sx = int(np.clip(sx, 0, w-1)); sy = int(np.clip(sy, 0, h-1))
            mask[py,px] = True; mask[sy,sx] = True
        filtered = np.zeros_like(spectrum)
        filtered[mask] = spectrum[mask]
        reconstruction = np.real(np.fft.ifft2(np.fft.ifftshift(filtered))).astype(np.float32)
        lo, hi = float(reconstruction.min()), float(reconstruction.max())
        normalized = np.zeros_like(reconstruction, dtype=np.uint8) if hi <= lo + 1e-12 else np.clip((reconstruction-lo)/(hi-lo)*255.0,0,255).astype(np.uint8)
        frame_out = ImageFrame(normalized, color_space=ColorSpace.GRAY, source_id="fft_reconstruction")
        payload, mime = SamplingPreviewEncoder.encode(frame_out, max_width=1800, quality=92)
        return Response(content=payload, media_type=mime)
    except Exception as exc:
        raise _http_error(exc)

