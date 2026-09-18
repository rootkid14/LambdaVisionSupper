from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable
import cv2
import numpy as np

from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame
from app.services.vision_labs.contour_extractor.models import ContourExtractorDefinition, ContourFilterStage
from app.services.vision_labs.contour_extractor.store import ContourStore, contour_metrics


@dataclass
class ContourExtractorResult:
    store: ContourStore
    sources: dict[str, Any]
    stage_summaries: list[dict[str, Any]]
    timings_ms: dict[str, float]


def _to_gray(value: ImageFrame | BinaryMask) -> np.ndarray:
    if isinstance(value, BinaryMask):
        return (np.asarray(value.data) > 0).astype(np.uint8) * 255
    image = np.asarray(value.data)
    if image.ndim == 2:
        return image.astype(np.uint8)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _as_frame(value: ImageFrame | BinaryMask, source_id: str) -> ImageFrame:
    if isinstance(value, ImageFrame):
        return value
    return ImageFrame((_to_gray(value)).astype(np.uint8), color_space=ColorSpace.GRAY, source_id=source_id)


def _run_upstream(raw_image, config, *, load_service=None, run_service=None):
    pin = config.image_service
    if not pin.service_id:
        return raw_image, None
    if load_service is None or run_service is None:
        raise RuntimeError("Contour Source Service requires Lab Service callbacks")
    service = load_service(pin.service_id, pin.version)
    image_inputs = [name for name, port in service.inputs.items() if port.type == "image"]
    if len(service.inputs) != 1 or len(image_inputs) != 1:
        raise ValueError("Contour Source Service must expose exactly one Image input")
    output_name = pin.output_name or next(iter(service.outputs), "")
    if not output_name or output_name not in service.outputs:
        raise KeyError("Choose a valid Contour Source Service output")
    if service.outputs[output_name].type not in {"image", "binary_mask"}:
        raise ValueError("Contour Source Service output must be Image or BinaryMask")
    run = run_service(service, {image_inputs[0]: raw_image})
    return run.outputs[output_name], {
        "service_id": service.service_id,
        "service_version": service.version,
        "output_name": output_name,
    }


def _retrieval_mode(name: str) -> int:
    return {
        "external": cv2.RETR_EXTERNAL,
        "tree": cv2.RETR_TREE,
        "list": cv2.RETR_LIST,
    }.get(str(name), cv2.RETR_LIST)


def _candidate_map(source: ImageFrame | BinaryMask, definition: ContourExtractorDefinition):
    config = definition.source
    gray = _to_gray(source)
    mode = config.source_mode
    direct_mask = isinstance(source, BinaryMask) and mode in {"auto", "mask_boundary"}
    if mode == "mask_boundary" and not isinstance(source, BinaryMask):
        direct_mask = False
    if direct_mask:
        edge = (gray > 0).astype(np.uint8) * 255
        method = "direct_mask_boundary"
    else:
        blur = max(1, int(config.blur_kernel))
        if blur % 2 == 0:
            blur += 1
        work = cv2.GaussianBlur(gray, (blur, blur), 0) if blur > 1 else gray
        edge = cv2.Canny(work, float(config.canny_low), float(config.canny_high))
        method = "canny"
    contours, _ = cv2.findContours(edge, _retrieval_mode(config.retrieval), cv2.CHAIN_APPROX_SIMPLE)
    return edge, contours, method


def _passes_early(metric, config) -> bool:
    early = config.early_filter
    _, _, width, height = metric["bbox"]
    return (
        metric["area_px2"] >= float(early.min_area)
        and metric["perimeter_px"] >= float(early.min_perimeter)
        and width >= int(early.min_bbox_width)
        and height >= int(early.min_bbox_height)
        and metric["point_count"] >= int(early.min_points)
    )


def _apply_stage(store: ContourStore, ids: list[int], stage: ContourFilterStage) -> list[int]:
    if not stage.enabled:
        return list(ids)
    params = dict(stage.parameters or {})
    if stage.kind == "metric_filter":
        result = []
        for contour_id in ids:
            m = store.metrics[contour_id]
            if m["area_px2"] < float(params.get("min_area", 0.0)): continue
            if m["area_px2"] > float(params.get("max_area", 1e18)): continue
            if m["perimeter_px"] < float(params.get("min_perimeter", 0.0)): continue
            if m["perimeter_px"] > float(params.get("max_perimeter", 1e18)): continue
            if m["circularity"] < float(params.get("min_circularity", 0.0)): continue
            if m["solidity"] < float(params.get("min_solidity", 0.0)): continue
            if m["aspect_ratio"] < float(params.get("min_aspect", 0.0)): continue
            if m["aspect_ratio"] > float(params.get("max_aspect", 1e18)): continue
            result.append(contour_id)
        return result
    if stage.kind == "largest_n":
        n = max(1, int(params.get("count", 1)))
        metric = str(params.get("metric", "area"))
        key = "perimeter_px" if metric == "perimeter" else "area_px2"
        return sorted(ids, key=lambda contour_id: store.metrics[contour_id][key], reverse=True)[:n]
    if stage.kind == "region_filter":
        x0 = float(params.get("x0", 0.0)); y0 = float(params.get("y0", 0.0))
        x1 = float(params.get("x1", 1.0)); y1 = float(params.get("y1", 1.0))
        h, w = store.source_shape
        result = []
        for contour_id in ids:
            cx, cy = store.metrics[contour_id]["centroid"]
            nx = cx / max(1, w - 1); ny = cy / max(1, h - 1)
            if min(x0,x1) <= nx <= max(x0,x1) and min(y0,y1) <= ny <= max(y0,y1):
                result.append(contour_id)
        return result
    if stage.kind == "simplify":
        # Simplification intentionally mutates shared geometry once instead of
        # cloning the whole ContourSet for every stage.
        epsilon_ratio = max(0.0, float(params.get("epsilon_ratio", 0.002)))
        for contour_id in ids:
            points = store.contours[contour_id].reshape(-1,1,2).astype(np.float32)
            epsilon = epsilon_ratio * max(1.0, cv2.arcLength(points, True))
            simplified = cv2.approxPolyDP(points, epsilon, True).reshape(-1,2)
            store.contours[contour_id] = simplified.astype(np.float32)
            store.metrics[contour_id] = contour_metrics(simplified, contour_id)
        return list(ids)
    raise ValueError(f"Unsupported contour stage kind: {stage.kind}")


class ContourExtractorRuntime:
    def __init__(self, definition: ContourExtractorDefinition | dict[str, Any]):
        self.definition = definition if isinstance(definition, ContourExtractorDefinition) else ContourExtractorDefinition(**definition)

    def run(self, raw_image: ImageFrame, *, load_service: Callable | None = None, run_service: Callable | None = None) -> ContourExtractorResult:
        timings: dict[str, float] = {}
        started = perf_counter()
        source, upstream = _run_upstream(raw_image, self.definition.source, load_service=load_service, run_service=run_service)
        timings["source"] = (perf_counter() - started) * 1000.0

        started = perf_counter()
        edge, candidates, method = _candidate_map(source, self.definition)
        h, w = edge.shape[:2]
        store = ContourStore(source_shape=(h, w), candidate_count=len(candidates))
        kept: list[tuple[float, np.ndarray, dict[str, Any]]] = []
        rejected = 0
        for candidate in candidates:
            points = np.asarray(candidate, dtype=np.float32).reshape(-1,2)
            metric = contour_metrics(points, -1)
            if not _passes_early(metric, self.definition.source):
                rejected += 1
                continue
            score = float(metric["area_px2"]) + float(metric["perimeter_px"]) * 0.05
            kept.append((score, points, metric))
        # Release OpenCV candidate list before the editor sees the result.
        del candidates
        kept.sort(key=lambda item: item[0], reverse=True)
        cap = max(1, int(self.definition.source.early_filter.max_retained))
        capped_count = max(0, len(kept) - cap)
        kept = kept[:cap]
        for contour_id, (_, points, metric) in enumerate(kept):
            metric = dict(metric); metric["id"] = contour_id
            store.add(contour_id, points, metric)
        store.early_rejected_count = rejected
        store.capped_count = capped_count
        current = store.set_selection("source", list(store.contours))
        timings["candidate_extract_and_early_filter"] = (perf_counter() - started) * 1000.0

        stage_summaries = []
        for stage in self.definition.stages:
            before = len(current)
            started = perf_counter()
            current = _apply_stage(store, current, stage)
            elapsed = (perf_counter() - started) * 1000.0
            store.set_selection(stage.id, current)
            stage_summaries.append({
                "id": stage.id,
                "kind": stage.kind,
                "input_count": before,
                "output_count": len(current),
                "removed_count": max(0, before-len(current)),
                "timing_ms": elapsed,
            })
        store.set_selection("final", current)

        contour_image = np.zeros((h, w), dtype=np.uint8)
        if current:
            cv2.drawContours(contour_image, [store.contours[i].reshape(-1,1,2).astype(np.int32) for i in current], -1, 255, 1, cv2.LINE_8)
        sources = {
            "raw_image": raw_image,
            "source_image": _as_frame(source, "contour_source"),
            "edge_map": BinaryMask(edge > 0),
            "contour_image": ImageFrame(contour_image, color_space=ColorSpace.GRAY, source_id="contour_image"),
        }
        manifest = store.summary("final")
        manifest.update({"method": method, "upstream": upstream})
        sources["manifest"] = manifest
        return ContourExtractorResult(store=store, sources=sources, stage_summaries=stage_summaries, timings_ms=timings)
