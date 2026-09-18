from __future__ import annotations

import cv2
import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame


def image_to_bgr(frame: ImageFrame) -> np.ndarray:
    data = np.asarray(frame.data)
    if data.ndim == 2:
        return cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
    if frame.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
    if frame.color_space == ColorSpace.HSV:
        return cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
    return data.copy()


def image_channel(frame: ImageFrame, channel: str) -> np.ndarray:
    bgr = image_to_bgr(frame)
    channel = str(channel).lower()

    if channel == "gray":
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    if channel == "b":
        return bgr[..., 0].astype(np.float32)
    if channel == "g":
        return bgr[..., 1].astype(np.float32)
    if channel == "r":
        return bgr[..., 2].astype(np.float32)
    if channel == "h":
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[..., 0].astype(np.float32)
    if channel == "s":
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[..., 1].astype(np.float32)
    if channel == "v":
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[..., 2].astype(np.float32)
    if channel in {"lab_l", "lab_a", "lab_b"}:
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        index = {"lab_l": 0, "lab_a": 1, "lab_b": 2}[channel]
        return lab[..., index].astype(np.float32)
    raise ValueError(f"Unsupported sampling channel: {channel}")


def sample_line(
    image: np.ndarray,
    start: tuple[float, float],
    end: tuple[float, float],
    samples: int,
) -> np.ndarray:
    height, width = image.shape[:2]
    samples = max(2, int(samples))
    xs = np.linspace(float(start[0]), float(end[0]), samples)
    ys = np.linspace(float(start[1]), float(end[1]), samples)
    map_x = np.clip(xs, 0, max(0, width - 1)).astype(np.float32)[None, :]
    map_y = np.clip(ys, 0, max(0, height - 1)).astype(np.float32)[None, :]
    sampled = cv2.remap(
        image.astype(np.float32),
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return sampled.reshape(-1).astype(np.float32)


def normalized_entropy(values: np.ndarray, bins: int = 64) -> float:
    array = np.asarray(values, dtype=np.float32).reshape(-1)
    if array.size == 0:
        return 0.0
    hist, _ = np.histogram(array, bins=bins, range=(0.0, 256.0))
    total = float(hist.sum())
    if total <= 0:
        return 0.0
    p = hist.astype(np.float64) / total
    p = p[p > 0]
    entropy = float(-(p * np.log2(p)).sum())
    return entropy / max(1.0, np.log2(float(bins)))
