from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from app.services.vision_labs.image.types import BinaryMask, ImageFrame
from app.services.vision_labs.sampling_geometry.types import (
    ContourSet,
    FeatureMatrix,
    FeatureVector,
    Histogram1D,
    MeasurementTable,
    Polyline,
    ProfileSet,
    SamplingHousing,
    Spectrum2D,
)


def _float_list(array: np.ndarray) -> list:
    return np.asarray(array, dtype=np.float64).tolist()


def _contour_metric(contour: np.ndarray, contour_id: int) -> dict[str, Any]:
    pts = np.asarray(contour, dtype=np.float32).reshape(-1, 1, 2)
    area = float(abs(cv2.contourArea(pts)))
    perimeter_closed = float(cv2.arcLength(pts, True))
    perimeter_open = float(cv2.arcLength(pts, False))
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
    circularity = (
        float(4.0 * np.pi * area / (perimeter_closed * perimeter_closed))
        if perimeter_closed > 1e-9
        else 0.0
    )
    solidity = area / hull_area if hull_area > 1e-9 else 0.0
    aspect = float(w) / float(h) if h > 0 else 0.0
    return {
        "id": int(contour_id),
        "point_count": int(len(pts)),
        "area_px2": area,
        "perimeter_px": perimeter_closed,
        "open_length_px": perimeter_open,
        "bbox": [int(x), int(y), int(w), int(h)],
        "centroid": [cx, cy],
        "aspect_ratio": aspect,
        "circularity": circularity,
        "solidity": solidity,
    }


def artifact_to_json(value: Any) -> dict[str, Any]:
    if isinstance(value, ImageFrame):
        return {
            "type": "image",
            "shape": list(value.shape),
            "color_space": value.color_space.value,
        }

    if isinstance(value, BinaryMask):
        return {
            "type": "binary_mask",
            "shape": list(value.shape),
        }

    if isinstance(value, ContourSet):
        contours = []
        metrics = []
        ids = value.ids if len(value.ids) == len(value.contours) else list(range(len(value.contours)))
        for contour_id, contour in zip(ids, value.contours):
            points = np.asarray(contour).reshape(-1, 2)
            metrics.append(_contour_metric(points, int(contour_id)))
            if len(points) > 3000:
                step = max(1, len(points) // 3000)
                points = points[::step]
            contours.append(points.astype(float).tolist())
        return {
            "type": "contour_set",
            "source_shape": list(value.source_shape),
            "contours": contours,
            "contour_ids": [int(item) for item in ids],
            "metrics": metrics,
            "count": len(contours),
            "metadata": value.metadata,
        }

    if isinstance(value, Polyline):
        points = np.asarray(value.points).reshape(-1, 2)
        segment = np.linalg.norm(np.diff(points, axis=0), axis=1) if len(points) > 1 else np.array([], dtype=float)
        arc = float(segment.sum())
        if value.closed and len(points) > 1:
            arc += float(np.linalg.norm(points[0] - points[-1]))
        return {
            "type": "polyline",
            "points": points.astype(float).tolist(),
            "closed": bool(value.closed),
            "source_shape": list(value.source_shape) if value.source_shape else None,
            "point_count": int(len(points)),
            "arc_length_px": arc,
            "metadata": value.metadata,
        }

    if isinstance(value, SamplingHousing):
        return {
            "type": "sampling_housing",
            "kind": value.kind,
            "source_shape": list(value.source_shape),
            "elements": value.elements,
            "element_count": len(value.elements),
            "geometry": value.geometry,
            "metadata": value.metadata,
        }

    if isinstance(value, ProfileSet):
        series = np.asarray(value.series, dtype=np.float64)
        if series.ndim == 1:
            series = series[None, :]
        return {
            "type": "profile_set",
            "x": _float_list(value.x),
            "series": _float_list(series),
            "labels": list(value.labels),
            "geometry": value.geometry,
            "units": value.units,
            "metadata": value.metadata,
        }

    if isinstance(value, Histogram1D):
        return {
            "type": "histogram_1d",
            "bins": _float_list(value.bins),
            "values": _float_list(value.values),
            "channel": value.channel,
            "normalized": value.normalized,
        }

    if isinstance(value, FeatureVector):
        return {
            "type": "feature_vector",
            "values": _float_list(value.values),
            "names": list(value.names),
            "groups": list(value.groups) if value.groups else None,
            "metadata": value.metadata,
            "dimension": int(np.asarray(value.values).size),
        }

    if isinstance(value, FeatureMatrix):
        return {
            "type": "feature_matrix",
            "values": _float_list(value.values),
            "feature_names": list(value.feature_names),
            "row_labels": list(value.row_labels),
            "geometry": value.geometry,
            "metadata": value.metadata,
            "shape": list(np.asarray(value.values).shape),
        }

    if isinstance(value, Spectrum2D):
        return {
            "type": "spectrum_2d",
            "shape": list(value.magnitude.shape),
            "source_shape": list(value.source_shape),
            "window": value.window,
            "channel": value.channel,
            "metadata": value.metadata,
        }

    if isinstance(value, MeasurementTable):
        return {
            "type": "measurement_table",
            "columns": list(value.columns),
            "rows": value.rows,
            "metadata": value.metadata,
        }

    raise TypeError(f"Unsupported Sampling/Geometry artifact {type(value).__name__}")
