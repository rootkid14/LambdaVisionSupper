from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import cv2
import numpy as np

from app.services.vision_labs.contour_extractor.fourier import contour_fourier_descriptor
from app.services.vision_labs.contour_extractor.store import ContourStore, contour_metrics


StageExecutor = Callable[[ContourStore, list[int], dict[str, Any]], list[int]]


@dataclass(frozen=True)
class ContourStageManifest:
    kind: str
    label: str
    category: str
    description: str
    parameters: dict[str, dict[str, Any]] = field(default_factory=dict)
    guide: dict[str, Any] = field(default_factory=dict)


_STAGE_EXECUTORS: dict[str, StageExecutor] = {}
_STAGE_MANIFESTS: dict[str, ContourStageManifest] = {}


def contour_stage(manifest: ContourStageManifest):
    def decorator(func: StageExecutor):
        _STAGE_EXECUTORS[manifest.kind] = func
        _STAGE_MANIFESTS[manifest.kind] = manifest
        return func
    return decorator


def stage_catalog() -> list[dict[str, Any]]:
    return [
        {
            "kind": item.kind,
            "label": item.label,
            "category": item.category,
            "description": item.description,
            "parameters": item.parameters,
            "guide": item.guide,
        }
        for item in _STAGE_MANIFESTS.values()
    ]


def apply_stage(store: ContourStore, ids: list[int], kind: str, parameters: dict[str, Any]) -> list[int]:
    executor = _STAGE_EXECUTORS.get(str(kind))
    if executor is None:
        raise ValueError(f"Unsupported contour stage kind: {kind}")
    return executor(store, list(ids), dict(parameters or {}))


def _number(default, label, minimum=None, maximum=None, description=""):
    return {"type": "number", "default": default, "label": label, "min": minimum, "max": maximum, "description": description}


def _enum(default, label, choices, description=""):
    return {"type": "enum", "default": default, "label": label, "choices": choices, "description": description}


@contour_stage(ContourStageManifest(
    kind="metric_filter",
    label="Metric Filter",
    category="Filter / Geometry",
    description="Keep contours whose geometric metrics lie inside explicit ranges.",
    parameters={
        "min_area": _number(0.0, "Min area", 0, None, "Reject contours smaller than this filled area."),
        "max_area": _number(1e9, "Max area", 0, None),
        "min_perimeter": _number(0.0, "Min perimeter", 0, None),
        "max_perimeter": _number(1e9, "Max perimeter", 0, None),
        "min_circularity": _number(0.0, "Min circularity", 0, 1),
        "min_solidity": _number(0.0, "Min solidity", 0, 1),
        "min_aspect": _number(0.0, "Min aspect", 0, None),
        "max_aspect": _number(1e9, "Max aspect", 0, None),
    },
    guide={
        "question": "Which contours are geometrically plausible?",
        "visual": "before_after_contours",
        "notes": ["This stage stores only IDs; contour coordinates are not duplicated."],
    },
))
def _metric_filter(store: ContourStore, ids: list[int], params: dict[str, Any]) -> list[int]:
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


@contour_stage(ContourStageManifest(
    kind="largest_n",
    label="Keep Largest N",
    category="Filter / Ranking",
    description="Rank remaining contours by area or perimeter and keep the top N.",
    parameters={
        "count": _number(10, "Count", 1, 10000),
        "metric": _enum("area", "Ranking metric", ["area", "perimeter"]),
    },
    guide={"question": "Which contours dominate the scene?", "visual": "ranked_contours"},
))
def _largest_n(store: ContourStore, ids: list[int], params: dict[str, Any]) -> list[int]:
    n = max(1, int(params.get("count", 1)))
    key = "perimeter_px" if str(params.get("metric", "area")) == "perimeter" else "area_px2"
    return sorted(ids, key=lambda contour_id: store.metrics[contour_id][key], reverse=True)[:n]


@contour_stage(ContourStageManifest(
    kind="region_filter",
    label="Region Filter",
    category="Filter / Spatial",
    description="Keep contours whose centroids fall inside a normalized rectangular region.",
    parameters={
        "x0": _number(0.0, "X0", 0, 1), "y0": _number(0.0, "Y0", 0, 1),
        "x1": _number(1.0, "X1", 0, 1), "y1": _number(1.0, "Y1", 0, 1),
    },
    guide={"question": "Where in the image can the target shape exist?", "visual": "roi_filter"},
))
def _region_filter(store: ContourStore, ids: list[int], params: dict[str, Any]) -> list[int]:
    x0, y0, x1, y1 = map(float, (params.get("x0", 0), params.get("y0", 0), params.get("x1", 1), params.get("y1", 1)))
    h, w = store.source_shape
    result = []
    for contour_id in ids:
        cx, cy = store.metrics[contour_id]["centroid"]
        nx = cx / max(1, w - 1); ny = cy / max(1, h - 1)
        if min(x0, x1) <= nx <= max(x0, x1) and min(y0, y1) <= ny <= max(y0, y1):
            result.append(contour_id)
    return result


@contour_stage(ContourStageManifest(
    kind="simplify",
    label="Contour Simplify",
    category="Transform / Geometry",
    description="Reduce point count with Douglas-Peucker while preserving the overall contour shape.",
    parameters={"epsilon_ratio": _number(0.002, "Epsilon / perimeter", 0, 0.1)},
    guide={"question": "Can the same shape be represented with fewer points?", "visual": "simplify"},
))
def _simplify(store: ContourStore, ids: list[int], params: dict[str, Any]) -> list[int]:
    epsilon_ratio = max(0.0, float(params.get("epsilon_ratio", 0.002)))
    for contour_id in ids:
        points = store.contours[contour_id].reshape(-1, 1, 2).astype(np.float32)
        epsilon = epsilon_ratio * max(1.0, cv2.arcLength(points, True))
        simplified = cv2.approxPolyDP(points, epsilon, True).reshape(-1, 2)
        store.contours[contour_id] = simplified.astype(np.float32)
        store.metrics[contour_id] = contour_metrics(simplified, contour_id)
    return list(ids)


@contour_stage(ContourStageManifest(
    kind="fourier_shape_filter",
    label="Fourier Shape Match",
    category="Advanced / Shape Pattern",
    description="Keep contours whose normalized Fourier shape descriptor resembles a selected master contour.",
    parameters={
        "master_contour_id": _number(0, "Master contour ID", 0, None, "Select a contour in the inspector then use it as the master."),
        "harmonics": _number(12, "Harmonics", 2, 64, "Low harmonics describe coarse shape; higher harmonics add fine detail."),
        "resample_points": _number(128, "Resample points", 32, 512),
        "max_distance": _number(0.22, "Max descriptor distance", 0, 2),
    },
    guide={
        "question": "Which contours have the same overall shape pattern as this master?",
        "visual": "fourier_shape",
        "notes": [
            "Descriptor magnitudes are translation/scale/rotation tolerant.",
            "This stage is the first advanced shape-pattern primitive; future master libraries can reuse the same contract.",
        ],
    },
))
def _fourier_shape_filter(store: ContourStore, ids: list[int], params: dict[str, Any]) -> list[int]:
    master_id = int(params.get("master_contour_id", -1))
    if master_id not in store.contours:
        raise ValueError(f"Master contour #{master_id} is not retained in ContourStore")
    harmonics = max(2, int(params.get("harmonics", 12)))
    points = max(32, int(params.get("resample_points", 128)))
    threshold = max(0.0, float(params.get("max_distance", 0.22)))
    master = contour_fourier_descriptor(store.contours[master_id], harmonics=harmonics, sample_count=points)
    result = []
    for contour_id in ids:
        descriptor = contour_fourier_descriptor(store.contours[contour_id], harmonics=harmonics, sample_count=points)
        length = min(len(master), len(descriptor))
        distance = float(np.linalg.norm(master[:length] - descriptor[:length])) if length else float("inf")
        store.metrics[contour_id]["fourier_distance"] = distance
        if distance <= threshold:
            result.append(contour_id)
    return result
