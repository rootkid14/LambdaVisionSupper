from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable
import cv2
import numpy as np

from app.services.vision_labs.sampling_geometry.types import ContourSet


def contour_metrics(points: np.ndarray, contour_id: int) -> dict[str, Any]:
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    area = float(abs(cv2.contourArea(pts)))
    perimeter = float(cv2.arcLength(pts, True))
    x, y, w, h = cv2.boundingRect(pts)
    moments = cv2.moments(pts)
    if abs(moments.get("m00", 0.0)) > 1e-12:
        cx = float(moments["m10"] / moments["m00"])
        cy = float(moments["m01"] / moments["m00"])
    else:
        flat = pts.reshape(-1, 2)
        cx = float(np.mean(flat[:, 0])) if len(flat) else 0.0
        cy = float(np.mean(flat[:, 1])) if len(flat) else 0.0
    hull = cv2.convexHull(pts)
    hull_area = float(abs(cv2.contourArea(hull)))
    circularity = float(4.0 * np.pi * area / (perimeter * perimeter)) if perimeter > 1e-9 else 0.0
    solidity = area / hull_area if hull_area > 1e-9 else 0.0
    aspect = float(w) / float(h) if h > 0 else 0.0
    return {
        "id": int(contour_id),
        "point_count": int(len(pts)),
        "area_px2": area,
        "perimeter_px": perimeter,
        "bbox": [int(x), int(y), int(w), int(h)],
        "centroid": [cx, cy],
        "aspect_ratio": aspect,
        "circularity": circularity,
        "solidity": solidity,
    }


@dataclass
class ContourStore:
    source_shape: tuple[int, int]
    contours: dict[int, np.ndarray] = field(default_factory=dict)
    metrics: dict[int, dict[str, Any]] = field(default_factory=dict)
    selections: dict[str, list[int]] = field(default_factory=dict)
    candidate_count: int = 0
    early_rejected_count: int = 0
    capped_count: int = 0

    def add(self, contour_id: int, points: np.ndarray, metric: dict[str, Any] | None = None) -> None:
        array = np.asarray(points, dtype=np.float32).reshape(-1, 2)
        self.contours[int(contour_id)] = array
        self.metrics[int(contour_id)] = metric or contour_metrics(array, int(contour_id))

    def set_selection(self, name: str, ids: Iterable[int]) -> list[int]:
        clean = [int(value) for value in ids if int(value) in self.contours]
        self.selections[str(name)] = clean
        return clean

    def selection(self, name: str = "final") -> list[int]:
        if name in self.selections:
            return list(self.selections[name])
        return list(self.contours)

    def summary(self, selection: str = "final") -> dict[str, Any]:
        ids = self.selection(selection)
        return {
            "source_shape": list(self.source_shape),
            "candidate_count": int(self.candidate_count),
            "retained_geometry_count": int(len(self.contours)),
            "selection_count": int(len(ids)),
            "early_rejected_count": int(self.early_rejected_count),
            "capped_count": int(self.capped_count),
            "selection": selection,
        }

    def metric_rows(self, selection: str = "final", *, offset: int = 0, limit: int = 200) -> list[dict[str, Any]]:
        ids = self.selection(selection)
        window = ids[max(0, int(offset)): max(0, int(offset)) + max(1, int(limit))]
        return [dict(self.metrics[contour_id]) for contour_id in window]

    def geometry(self, ids: Iterable[int]) -> list[dict[str, Any]]:
        result = []
        for contour_id in ids:
            contour_id = int(contour_id)
            points = self.contours.get(contour_id)
            if points is None:
                continue
            result.append({"id": contour_id, "points": points.astype(float).tolist()})
        return result

    def materialize(self, selection: str = "final") -> ContourSet:
        ids = self.selection(selection)
        return ContourSet(
            contours=[self.contours[contour_id] for contour_id in ids],
            ids=ids,
            source_shape=self.source_shape,
            metadata={
                "store_summary": self.summary(selection),
                "selection": selection,
            },
        )
