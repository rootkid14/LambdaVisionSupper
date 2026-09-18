from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import cv2
import numpy as np

from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.types import ContourSet


@dataclass
class SourceBoardResult:
    sources: dict[str, Any]
    manifest: dict[str, Any] = field(default_factory=dict)


def _shape(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    return [int(item) for item in shape]


def _entry(name: str, value: Any, *, label: str, origin: str) -> dict[str, Any]:
    if isinstance(value, ImageFrame):
        data_type = "image"
    elif isinstance(value, BinaryMask):
        data_type = "binary_mask"
    elif isinstance(value, ContourSet):
        data_type = "contour_set"
    else:
        data_type = type(value).__name__
    return {
        "name": name,
        "label": label,
        "type": data_type,
        "shape": _shape(value),
        "origin": origin,
    }


def _as_gray(value: ImageFrame | BinaryMask) -> np.ndarray:
    if isinstance(value, BinaryMask):
        return np.asarray(value.data, dtype=np.uint8)

    data = np.asarray(value.data)
    if data.ndim == 2:
        return data.astype(np.uint8)
    if value.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2GRAY)
    if value.color_space == ColorSpace.HSV:
        bgr = cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)


def _image_input_name(service) -> str:
    image_inputs = [name for name, port in service.inputs.items() if port.type == "image"]
    if len(service.inputs) != 1 or len(image_inputs) != 1:
        raise ValueError(
            f"Upstream service {service.service_id!r} must expose exactly one Image input"
        )
    return image_inputs[0]


def _run_upstream(
    raw_image: ImageFrame,
    spec: dict[str, Any] | None,
    *,
    load_service: Callable[[str, int | None], Any] | None,
    run_service: Callable[[Any, dict[str, Any]], Any] | None,
    allowed_output_types: set[str],
) -> tuple[Any | None, dict[str, Any] | None]:
    spec = dict(spec or {})
    service_id = str(spec.get("service_id") or "").strip()
    output_name = str(spec.get("output_name") or "").strip()
    version = spec.get("version")

    if not service_id:
        return None, None
    if not output_name:
        raise ValueError(f"Source Board service {service_id!r} has no output pin selected")
    if load_service is None or run_service is None:
        raise RuntimeError("Source Board upstream service resolver is unavailable")

    service = load_service(service_id, version)
    if service.lab_type != "image_processing":
        raise ValueError(
            f"Source Board currently accepts image_processing services; got {service.lab_type!r}"
        )
    if output_name not in service.outputs:
        raise KeyError(f"Unknown upstream service output: {service_id}.{output_name}")
    binding = service.outputs[output_name]
    if binding.type not in allowed_output_types:
        raise ValueError(
            f"Output {service_id}.{output_name} has type {binding.type!r}; "
            f"expected one of {sorted(allowed_output_types)}"
        )

    input_name = _image_input_name(service)
    run = run_service(service, {input_name: raw_image})
    value = run.outputs[output_name]
    return value, {
        "service_id": service.service_id,
        "service_version": service.version,
        "service_name": service.name,
        "output_name": output_name,
        "output_type": binding.type,
    }


def _contour_map(
    raster: ImageFrame | BinaryMask,
    *,
    canny_low: float,
    canny_high: float,
    blur_kernel: int,
) -> tuple[BinaryMask, ImageFrame, ContourSet]:
    gray = _as_gray(raster)
    kernel = int(blur_kernel)
    if kernel > 1:
        if kernel % 2 == 0:
            kernel += 1
        gray = cv2.GaussianBlur(gray, (kernel, kernel), 0)

    edges = cv2.Canny(
        gray,
        threshold1=float(canny_low),
        threshold2=float(canny_high),
    )
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_NONE,
    )
    normalized = [
        np.asarray(contour, dtype=np.float32).reshape(-1, 2)
        for contour in contours
        if len(contour) >= 2
    ]
    normalized.sort(
        key=lambda contour: cv2.arcLength(
            contour.reshape(-1, 1, 2),
            False,
        ),
        reverse=True,
    )
    contour_set = ContourSet(
        contours=normalized,
        source_shape=(int(edges.shape[0]), int(edges.shape[1])),
        ids=list(range(len(normalized))),
        metadata={
            "origin": "source_board",
            "canny_low": float(canny_low),
            "canny_high": float(canny_high),
            "blur_kernel": int(kernel),
            "retrieval_mode": "RETR_LIST",
        },
    )
    edge_mask = BinaryMask(data=(edges > 0).astype(np.uint8) * 255)
    contour_image = ImageFrame(
        data=edges,
        color_space=ColorSpace.GRAY,
        source_id="contour_image",
    )
    return edge_mask, contour_image, contour_set


def resolve_source_board(
    raw_image: ImageFrame,
    config: dict[str, Any] | None = None,
    *,
    load_service: Callable[[str, int | None], Any] | None = None,
    run_service: Callable[[Any, dict[str, Any]], Any] | None = None,
) -> SourceBoardResult:
    config = dict(config or {})
    image_spec = config.get("image_service") or {}
    geometry_spec = config.get("geometry_service") or {}
    # Backward compatibility: old v0.2 snapshots had no enable_geometry key and
    # therefore keep the old Source Board behavior. New Sampling LAB snapshots
    # explicitly set enable_geometry=False so they never allocate contour maps.
    enable_geometry = bool(config.get("enable_geometry", True))

    processed, image_upstream = _run_upstream(
        raw_image,
        image_spec,
        load_service=load_service,
        run_service=run_service,
        allowed_output_types={"image"},
    )
    inspected_image = processed if isinstance(processed, ImageFrame) else raw_image

    sources: dict[str, Any] = {
        "raw_image": raw_image,
        "inspected_image": inspected_image,
    }
    entries = [
        _entry("raw_image", raw_image, label="Input Image", origin="upload/service input"),
        _entry(
            "inspected_image",
            inspected_image,
            label="Inspected Image",
            origin=(
                f"image service {image_upstream['service_id']}:{image_upstream['output_name']}"
                if image_upstream
                else "raw input (no image-processing pin)"
            ),
        ),
    ]
    manifest = {
        "config": {
            "image_service": dict(image_spec),
            "geometry_service": dict(geometry_spec),
            "enable_geometry": enable_geometry,
            "canny_low": float(config.get("canny_low", 80.0)),
            "canny_high": float(config.get("canny_high", 160.0)),
            "blur_kernel": int(config.get("blur_kernel", 3)),
        },
        "upstream": {"image_service": image_upstream, "geometry_service": None},
        "entries": entries,
        "geometry_contour_count": 0,
    }
    if not enable_geometry:
        return SourceBoardResult(sources=sources, manifest=manifest)

    geometry_raster, geometry_upstream = _run_upstream(
        raw_image,
        geometry_spec,
        load_service=load_service,
        run_service=run_service,
        allowed_output_types={"image", "binary_mask"},
    )
    if geometry_raster is None:
        geometry_raster = raw_image
        geometry_origin = "raw_input_default_canny"
    else:
        geometry_origin = "geometry_source_service_then_canny"

    canny_low = float(config.get("canny_low", 80.0))
    canny_high = float(config.get("canny_high", 160.0))
    blur_kernel = int(config.get("blur_kernel", 3))
    edge_map, contour_image, master_contours = _contour_map(
        geometry_raster,
        canny_low=canny_low,
        canny_high=canny_high,
        blur_kernel=blur_kernel,
    )
    sources.update({
        "geometry_raster": geometry_raster,
        "edge_map": edge_map,
        "contour_image": contour_image,
        "master_contours": master_contours,
    })
    entries.extend([
        _entry(
            "geometry_raster", geometry_raster, label="Geometry Raster",
            origin=(f"geometry source {geometry_upstream['service_id']}:{geometry_upstream['output_name']}" if geometry_upstream else "raw input"),
        ),
        _entry("edge_map", edge_map, label="Canny Edge Map", origin=geometry_origin),
        _entry("contour_image", contour_image, label="Contour Image", origin="edge_map raster view"),
        _entry("master_contours", master_contours, label="Master Contour Map", origin="Canny → findContours"),
    ])
    manifest["upstream"]["geometry_service"] = geometry_upstream
    manifest["entries"] = entries
    manifest["geometry_contour_count"] = len(master_contours.contours)
    return SourceBoardResult(sources=sources, manifest=manifest)


def resolve_pipeline_inputs(definition, sources: dict[str, Any]) -> dict[str, Any]:
    source_map = dict(getattr(definition, "input_sources", {}) or {})
    resolved: dict[str, Any] = {}
    for external_name in definition.inputs:
        source_name = source_map.get(external_name, external_name)
        if source_name not in sources:
            raise KeyError(
                f"Pipeline external input {external_name!r} is bound to missing Source Board data {source_name!r}"
            )
        resolved[external_name] = sources[source_name]
    return resolved
