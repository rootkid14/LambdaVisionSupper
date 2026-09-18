from __future__ import annotations

from typing import Any

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
    Spectrum2D,
)


def _float_list(array: np.ndarray) -> list:
    return np.asarray(array, dtype=np.float64).tolist()


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
        for contour in value.contours:
            points = np.asarray(contour).reshape(-1, 2)
            if len(points) > 2000:
                step = max(1, len(points) // 2000)
                points = points[::step]
            contours.append(points.astype(float).tolist())
        return {
            "type": "contour_set",
            "source_shape": list(value.source_shape),
            "contours": contours,
        }

    if isinstance(value, Polyline):
        points = np.asarray(value.points).reshape(-1, 2)
        return {
            "type": "polyline",
            "points": points.astype(float).tolist(),
            "closed": bool(value.closed),
            "source_shape": list(value.source_shape) if value.source_shape else None,
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
        }

    if isinstance(value, FeatureMatrix):
        return {
            "type": "feature_matrix",
            "values": _float_list(value.values),
            "feature_names": list(value.feature_names),
            "row_labels": list(value.row_labels),
            "geometry": value.geometry,
            "metadata": value.metadata,
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
