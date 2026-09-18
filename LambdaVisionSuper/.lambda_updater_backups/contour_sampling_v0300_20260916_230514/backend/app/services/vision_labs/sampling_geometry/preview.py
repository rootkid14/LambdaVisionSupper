from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from app.services.vision_labs.image.session import PreviewEncoder
from app.services.vision_labs.image.types import ColorSpace, ImageFrame
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


def _canvas(width: int = 1200, height: int = 720) -> np.ndarray:
    return np.full((height, width, 3), 24, dtype=np.uint8)


def _normalize_u8(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32)
    finite = np.isfinite(array)
    if not finite.any():
        return np.zeros(array.shape, dtype=np.uint8)
    lo = float(np.min(array[finite]))
    hi = float(np.max(array[finite]))
    if hi <= lo + 1e-12:
        return np.zeros(array.shape, dtype=np.uint8)
    norm = (array - lo) / (hi - lo)
    norm[~finite] = 0
    return np.clip(norm * 255.0, 0, 255).astype(np.uint8)


def _plot_series(series: np.ndarray, labels: list[str] | None = None) -> ImageFrame:
    canvas = _canvas()
    h, w = canvas.shape[:2]
    left, right, top, bottom = 80, 30, 40, 70
    cv2.rectangle(canvas, (left, top), (w - right, h - bottom), (75, 75, 75), 1)

    arr = np.asarray(series, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[None, :]
    if arr.size == 0:
        return ImageFrame(canvas, color_space=ColorSpace.BGR)

    finite = np.isfinite(arr)
    lo = float(np.min(arr[finite])) if finite.any() else 0.0
    hi = float(np.max(arr[finite])) if finite.any() else 1.0
    if hi <= lo + 1e-12:
        hi = lo + 1.0

    palette = [
        (246, 180, 138),
        (129, 201, 149),
        (253, 214, 99),
        (242, 139, 130),
        (189, 193, 198),
        (174, 203, 250),
    ]

    for index, row in enumerate(arr[:12]):
        if row.size < 2:
            continue
        xs = np.linspace(left, w - right, row.size)
        ys = (h - bottom) - (np.nan_to_num(row, nan=lo) - lo) / (hi - lo) * (h - bottom - top)
        pts = np.column_stack([xs, ys]).astype(np.int32)
        cv2.polylines(canvas, [pts], False, palette[index % len(palette)], 2, cv2.LINE_AA)

    cv2.putText(canvas, f"min {lo:.4g}", (10, h - bottom + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)
    cv2.putText(canvas, f"max {hi:.4g}", (10, top + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)
    if labels:
        cv2.putText(canvas, ", ".join(labels[:6]), (left, h - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
    return ImageFrame(canvas, color_space=ColorSpace.BGR)


def _render_vector(value: FeatureVector) -> ImageFrame:
    canvas = _canvas()
    h, w = canvas.shape[:2]
    values = np.asarray(value.values, dtype=np.float64).reshape(-1)
    if values.size == 0:
        return ImageFrame(canvas, color_space=ColorSpace.BGR)

    normalized = _normalize_u8(values).astype(float) / 255.0
    left, top, bottom = 55, 45, 90
    usable_w = w - left - 30
    count = len(values)
    bar_w = max(1, int(usable_w / max(1, count)))
    for i, norm in enumerate(normalized):
        x1 = left + i * bar_w
        x2 = min(w - 30, x1 + max(1, bar_w - 1))
        y2 = h - bottom
        y1 = int(y2 - norm * (h - top - bottom))
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (246, 180, 138), -1)

    cv2.putText(canvas, f"FeatureVector {count}D", (left, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (232, 234, 237), 1, cv2.LINE_AA)
    for i, name in enumerate(value.names[:16]):
        cv2.putText(canvas, f"{i}: {name} = {values[i]:.4g}", (left + (i // 8) * 420, h - 68 + (i % 8) * 8), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (170, 170, 170), 1, cv2.LINE_AA)
    return ImageFrame(canvas, color_space=ColorSpace.BGR)


def _render_matrix(value: FeatureMatrix) -> ImageFrame:
    matrix = np.asarray(value.values, dtype=np.float32)
    if matrix.ndim != 2 or matrix.size == 0:
        return ImageFrame(_canvas(), color_space=ColorSpace.BGR)
    image = _normalize_u8(matrix)
    image = cv2.applyColorMap(image, cv2.COLORMAP_VIRIDIS)
    image = cv2.resize(image, (1000, 620), interpolation=cv2.INTER_NEAREST)
    canvas = _canvas()
    canvas[60:680, 100:1100] = image
    cv2.putText(canvas, f"FeatureMatrix {matrix.shape[0]} x {matrix.shape[1]}", (100, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (232, 234, 237), 1, cv2.LINE_AA)
    return ImageFrame(canvas, color_space=ColorSpace.BGR)


def _render_geometry(value: Any) -> ImageFrame:
    if isinstance(value, ContourSet):
        height, width = value.source_shape
        scale = min(1000.0 / max(1, width), 620.0 / max(1, height))
        canvas = _canvas()
        offset_x, offset_y = 100, 50
        for contour in value.contours:
            pts = np.asarray(contour).reshape(-1, 2).astype(np.float32)
            pts *= scale
            pts[:, 0] += offset_x
            pts[:, 1] += offset_y
            cv2.polylines(canvas, [pts.astype(np.int32)], True, (129, 201, 149), 2, cv2.LINE_AA)
        return ImageFrame(canvas, color_space=ColorSpace.BGR)

    if isinstance(value, Polyline):
        canvas = _canvas()
        pts = np.asarray(value.points, dtype=np.float32).reshape(-1, 2)
        if pts.size == 0:
            return ImageFrame(canvas, color_space=ColorSpace.BGR)
        if value.source_shape:
            height, width = value.source_shape
        else:
            width = max(1.0, float(np.max(pts[:, 0]) + 1))
            height = max(1.0, float(np.max(pts[:, 1]) + 1))
        scale = min(1000.0 / width, 620.0 / height)
        draw = pts.copy()
        draw *= scale
        draw[:, 0] += 100
        draw[:, 1] += 50
        cv2.polylines(canvas, [draw.astype(np.int32)], bool(value.closed), (246, 180, 138), 2, cv2.LINE_AA)
        for point in draw[:: max(1, len(draw) // 40)]:
            cv2.circle(canvas, tuple(point.astype(int)), 3, (253, 214, 99), -1, cv2.LINE_AA)
        return ImageFrame(canvas, color_space=ColorSpace.BGR)

    return ImageFrame(_canvas(), color_space=ColorSpace.BGR)



def _render_housing(value: SamplingHousing) -> ImageFrame:
    canvas = _canvas()
    h, w = value.source_shape
    sx = 1000.0 / max(1, w)
    sy = 620.0 / max(1, h)
    offset_x, offset_y = 100, 50
    for element in value.elements:
        kind = element.get("kind")
        if kind == "ray":
            start, end = element["start"], element["end"]
            p0 = (int(offset_x + start[0] * w * sx), int(offset_y + start[1] * h * sy))
            p1 = (int(offset_x + end[0] * w * sx), int(offset_y + end[1] * h * sy))
            cv2.line(canvas, p0, p1, (246, 180, 138), 2, cv2.LINE_AA)
        elif kind == "ring":
            center = element["center"]
            radius = float(element["radius"]) * min(w, h)
            center_px = (int(offset_x + center[0] * w * sx), int(offset_y + center[1] * h * sy))
            cv2.circle(canvas, center_px, int(radius * min(sx, sy)), (246, 180, 138), 2, cv2.LINE_AA)
        elif kind == "box":
            x0, y0, x1, y1 = element["box"]
            p0 = (int(offset_x + x0 * w * sx), int(offset_y + y0 * h * sy))
            p1 = (int(offset_x + x1 * w * sx), int(offset_y + y1 * h * sy))
            cv2.rectangle(canvas, p0, p1, (246, 180, 138), 1, cv2.LINE_AA)
    cv2.putText(canvas, f"SamplingHousing {value.kind} · {len(value.elements)} elements", (100, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (232,234,237), 1, cv2.LINE_AA)
    return ImageFrame(canvas, color_space=ColorSpace.BGR)


def _render_table(value: MeasurementTable) -> ImageFrame:
    canvas = _canvas()
    y = 40
    cv2.putText(canvas, " | ".join(value.columns), (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (232, 234, 237), 1, cv2.LINE_AA)
    y += 28
    for row in value.rows[:20]:
        text = " | ".join(str(row.get(column, "")) for column in value.columns)
        cv2.putText(canvas, text[:150], (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (189, 193, 198), 1, cv2.LINE_AA)
        y += 26
    return ImageFrame(canvas, color_space=ColorSpace.BGR)


class SamplingPreviewEncoder:
    @staticmethod
    def encode(
        value: Any,
        *,
        max_width: int = 1200,
        quality: int = 88,
    ) -> tuple[bytes, str]:
        try:
            return PreviewEncoder.encode(
                value,
                max_width=max_width,
                quality=quality,
            )
        except TypeError:
            pass

        if isinstance(value, Spectrum2D):
            image = _normalize_u8(np.log1p(np.maximum(value.magnitude, 0.0)))
            frame = ImageFrame(image, color_space=ColorSpace.GRAY)
        elif isinstance(value, ProfileSet):
            frame = _plot_series(value.series, value.labels)
        elif isinstance(value, Histogram1D):
            frame = _plot_series(value.values, [value.channel])
        elif isinstance(value, FeatureVector):
            frame = _render_vector(value)
        elif isinstance(value, FeatureMatrix):
            frame = _render_matrix(value)
        elif isinstance(value, (ContourSet, Polyline)):
            frame = _render_geometry(value)
        elif isinstance(value, SamplingHousing):
            frame = _render_housing(value)
        elif isinstance(value, MeasurementTable):
            frame = _render_table(value)
        else:
            raise TypeError(
                f"Sampling preview is not supported for {type(value).__name__}"
            )

        return PreviewEncoder.encode(
            frame,
            max_width=max_width,
            quality=quality,
        )
