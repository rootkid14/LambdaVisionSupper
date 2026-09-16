#!/usr/bin/env python3
"""
Entropy #1 - Curved ROI -> Ordered Centerline Stations
======================================================

Purpose
-------
Split a polygon-valid ROI that may be curved into a sequence of LOCAL square
stations that follow the curve.

Instead of globally PCA-aligning the whole ROI, this version:

    valid polygon mask
        -> skeleton / centerline
        -> longest ordered centerline path
        -> arc-length sampling
        -> local tangent at every station
        -> local square crop aligned to that tangent
        -> resize to 64x64

This solves the failure mode where one long curved ROI becomes one very large
rectangular crop.

Expected input dataset
----------------------
<dataset_root>/
    images/
        <roi>.png
    masks/
        <roi>.png       # thermal-paste GT mask
    valid/
        <roi>.png       # polygon-valid ROI mask

Output
------
<output_root>/
    images/
    masks/
    valid/
    meta/
    debug/
    dataset_summary.json

Important rules
---------------
1) The thermal-paste GT mask NEVER decides station geometry.
2) Station geometry is derived ONLY from the polygon-valid mask.
3) Pixels outside valid polygon are neutralized before station extraction.
4) Each station is aligned to the LOCAL tangent of the centerline.
5) Station order follows arc length along the centerline.
"""

from __future__ import annotations

import heapq
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


# ============================================================
# USER CONFIGURATION
# ============================================================

DATASET_ROOT = Path("/home/hieu/Desktop/Nidec Vision/output")
OUTPUT_ROOT = Path("/home/hieu/Desktop/Nidec Vision/stations_divided")

# Final network input size.
OUTPUT_SIZE = 64

# Consecutive station overlap.
# 0.25 -> stride = 75% of station side.
OVERLAP = 0.25

# A station is discarded when too little of the square belongs to valid ROI.
MIN_VALID_RATIO = 0.15

# ------------------------------------------------------------
# STATION SIZE
# ------------------------------------------------------------

# Fixed side before resize.
# None -> estimate automatically from polygon width using distance transform.
STATION_SIDE_PX = None

# When STATION_SIDE_PX=None:
# estimated local strip width * this factor becomes station square side.
AUTO_SIDE_SCALE = 1.60

# Safety limits for automatic station size.
MIN_STATION_SIDE_PX = 16
MAX_STATION_SIDE_PX = 96

# ------------------------------------------------------------
# CENTERLINE
# ------------------------------------------------------------

# Smooth the extracted centerline before local tangent estimation.
# Must be odd. Larger = smoother direction but less sensitive to tight bends.
CENTERLINE_SMOOTH_WINDOW = 9

# Tangent is estimated using positions approximately this many pixels
# before and after the station center along the resampled centerline.
TANGENT_LOOKAHEAD_PX = 6.0

# ------------------------------------------------------------
# VALID POLYGON MASKING
# ------------------------------------------------------------

APPLY_VALID_MASK_TO_IMAGE = True

# "median", "mean", or "black".
# Median is recommended to avoid a strong artificial black polygon edge.
INVALID_FILL_MODE = "median"

# ------------------------------------------------------------
# DEBUG
# ------------------------------------------------------------

SAVE_DEBUG_PREVIEW = True
DEBUG_DRAW_EVERY_STATION = True


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class StationConfig:
    output_size: int = 64
    overlap: float = 0.25
    min_valid_ratio: float = 0.15

    station_side_px: Optional[int] = None
    auto_side_scale: float = 1.60
    min_station_side_px: int = 16
    max_station_side_px: int = 96

    centerline_smooth_window: int = 9
    tangent_lookahead_px: float = 6.0

    apply_valid_mask_to_image: bool = True
    invalid_fill_mode: str = "median"

    save_debug_preview: bool = True


# ============================================================
# IO
# ============================================================

def find_matching_file(folder: Path, stem: str) -> Optional[Path]:
    if not folder.exists():
        return None
    for ext in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
        p = folder / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def read_rgb(path: Path) -> np.ndarray:
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise RuntimeError(f"Cannot read image: {path}")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def read_mask(path: Path, shape_hw: Tuple[int, int]) -> np.ndarray:
    m = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise RuntimeError(f"Cannot read mask: {path}")
    if m.shape != shape_hw:
        raise ValueError(
            f"Mask shape mismatch: {path}: mask={m.shape}, image={shape_hw}"
        )
    return (m > 127).astype(np.uint8) * 255


def save_rgb(path: Path, rgb: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    if not cv2.imwrite(str(path), bgr):
        raise RuntimeError(f"Failed saving: {path}")


def save_gray(path: Path, gray: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), gray):
        raise RuntimeError(f"Failed saving: {path}")


# ============================================================
# VALID MASK HANDLING
# ============================================================

def largest_component(mask: np.ndarray) -> np.ndarray:
    binary = (mask > 0).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)

    if n <= 1:
        return binary * 255

    # Skip label 0 = background.
    largest_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (labels == largest_label).astype(np.uint8) * 255


def compute_invalid_fill_rgb(
    rgb: np.ndarray,
    valid_mask: np.ndarray,
    mode: str,
) -> np.ndarray:
    mode = mode.lower().strip()

    if mode == "black":
        return np.array([0, 0, 0], dtype=np.uint8)

    pixels = rgb[valid_mask > 0]
    if len(pixels) == 0:
        return np.array([0, 0, 0], dtype=np.uint8)

    if mode == "median":
        fill = np.median(pixels, axis=0)
    elif mode == "mean":
        fill = np.mean(pixels, axis=0)
    else:
        raise ValueError(
            f"INVALID_FILL_MODE must be median/mean/black, got {mode!r}"
        )

    return np.clip(np.round(fill), 0, 255).astype(np.uint8)


def apply_valid_polygon_to_image(
    rgb: np.ndarray,
    valid_mask: np.ndarray,
    fill_rgb: np.ndarray,
) -> np.ndarray:
    out = rgb.copy()
    out[valid_mask == 0] = fill_rgb
    return out


def clip_gt_to_valid(
    gt_mask: np.ndarray,
    valid_mask: np.ndarray,
) -> np.ndarray:
    out = gt_mask.copy()
    out[valid_mask == 0] = 0
    return out


# ============================================================
# SKELETON / CENTERLINE
# ============================================================

def zhang_suen_thinning(binary_mask: np.ndarray) -> np.ndarray:
    """
    Pure NumPy Zhang-Suen thinning fallback.

    Compared with a morphological skeleton, this usually preserves the
    connectivity of a long curved strip much better, which is important
    because station ordering depends on one continuous centerline.
    """
    img = (binary_mask > 0).astype(np.uint8)

    # Keep one zero border around the image.
    img[[0, -1], :] = 0
    img[:, [0, -1]] = 0

    changed = True
    while changed:
        changed = False

        for step in (0, 1):
            p2 = img[:-2, 1:-1]
            p3 = img[:-2, 2:]
            p4 = img[1:-1, 2:]
            p5 = img[2:, 2:]
            p6 = img[2:, 1:-1]
            p7 = img[2:, :-2]
            p8 = img[1:-1, :-2]
            p9 = img[:-2, :-2]
            center = img[1:-1, 1:-1]

            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9

            A = (
                ((p2 == 0) & (p3 == 1)).astype(np.uint8)
                + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
                + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
                + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
                + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
                + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
                + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
                + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
            )

            cond = (
                (center == 1)
                & (B >= 2)
                & (B <= 6)
                & (A == 1)
            )

            if step == 0:
                cond &= ((p2 * p4 * p6) == 0)
                cond &= ((p4 * p6 * p8) == 0)
            else:
                cond &= ((p2 * p4 * p8) == 0)
                cond &= ((p2 * p6 * p8) == 0)

            ys, xs = np.nonzero(cond)
            if len(xs):
                # Offset by +1 because cond corresponds to inner image.
                img[ys + 1, xs + 1] = 0
                changed = True

    return img.astype(np.uint8) * 255


def skeletonize(binary_mask: np.ndarray) -> np.ndarray:
    """
    Prefer opencv-contrib thinning when available.
    Otherwise use Zhang-Suen thinning implemented above.
    """
    try:
        if hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "thinning"):
            src = ((binary_mask > 0).astype(np.uint8) * 255)
            skel = cv2.ximgproc.thinning(src)
            return (skel > 0).astype(np.uint8) * 255
    except Exception:
        pass

    return zhang_suen_thinning(binary_mask)


NEIGHBORS_8 = [
    (-1, -1, math.sqrt(2.0)),
    (0, -1, 1.0),
    (1, -1, math.sqrt(2.0)),
    (-1, 0, 1.0),
    (1, 0, 1.0),
    (-1, 1, math.sqrt(2.0)),
    (0, 1, 1.0),
    (1, 1, math.sqrt(2.0)),
]


def skeleton_nodes(skel: np.ndarray) -> Dict[Tuple[int, int], int]:
    """
    Returns {(x,y): degree}.
    """
    ys, xs = np.nonzero(skel > 0)
    pts = {(int(x), int(y)) for x, y in zip(xs, ys)}

    deg = {}
    for x, y in pts:
        d = 0
        for dx, dy, _ in NEIGHBORS_8:
            if (x + dx, y + dy) in pts:
                d += 1
        deg[(x, y)] = d
    return deg


def dijkstra_skeleton(
    pts: set,
    start: Tuple[int, int],
):
    dist = {start: 0.0}
    prev = {}
    heap = [(0.0, start)]

    while heap:
        d, node = heapq.heappop(heap)
        if d != dist.get(node):
            continue

        x, y = node
        for dx, dy, cost in NEIGHBORS_8:
            nb = (x + dx, y + dy)
            if nb not in pts:
                continue

            nd = d + cost
            if nd < dist.get(nb, float("inf")):
                dist[nb] = nd
                prev[nb] = node
                heapq.heappush(heap, (nd, nb))

    return dist, prev


def reconstruct_path(
    prev: Dict[Tuple[int, int], Tuple[int, int]],
    start: Tuple[int, int],
    end: Tuple[int, int],
) -> List[Tuple[int, int]]:
    path = [end]
    cur = end

    while cur != start:
        if cur not in prev:
            raise RuntimeError("Broken skeleton path")
        cur = prev[cur]
        path.append(cur)

    path.reverse()
    return path


def longest_centerline_path(skel: np.ndarray) -> np.ndarray:
    """
    Extract an ordered main path from skeleton.

    For a normal elongated polygon, the skeleton is approximately a tree.
    Two-pass geodesic search gives its main diameter and naturally ignores
    most short side branches.
    """
    deg = skeleton_nodes(skel)
    if not deg:
        raise ValueError("Skeleton is empty")

    pts = set(deg.keys())
    endpoints = [p for p, d in deg.items() if d <= 1]

    # If endpoints exist use one; otherwise choose arbitrary point (closed loop).
    start0 = endpoints[0] if endpoints else next(iter(pts))

    dist0, _ = dijkstra_skeleton(pts, start0)

    # A clean open curve normally has exactly two endpoints.
    # If thinning leaves <2 endpoints (loop / small branch artifact), use all
    # skeleton pixels for the diameter search instead of collapsing to one point.
    candidate_pool = endpoints if len(endpoints) >= 2 else list(pts)
    start = max(candidate_pool, key=lambda p: dist0.get(p, -1.0))

    dist1, prev1 = dijkstra_skeleton(pts, start)
    end = max(candidate_pool, key=lambda p: dist1.get(p, -1.0))

    path = reconstruct_path(prev1, start, end)

    xy = np.asarray(path, dtype=np.float32)  # already x,y

    # Deterministic orientation:
    # mainly horizontal -> left to right
    # mainly vertical   -> top to bottom
    dx = float(xy[-1, 0] - xy[0, 0])
    dy = float(xy[-1, 1] - xy[0, 1])

    if abs(dx) >= abs(dy):
        if xy[0, 0] > xy[-1, 0]:
            xy = xy[::-1].copy()
    else:
        if xy[0, 1] > xy[-1, 1]:
            xy = xy[::-1].copy()

    return xy


def smooth_polyline(xy: np.ndarray, window: int) -> np.ndarray:
    if len(xy) < 3 or window <= 1:
        return xy.astype(np.float32)

    window = int(window)
    if window % 2 == 0:
        window += 1

    window = min(window, len(xy) if len(xy) % 2 == 1 else len(xy) - 1)
    if window < 3:
        return xy.astype(np.float32)

    pad = window // 2
    kernel = np.ones(window, dtype=np.float32) / float(window)

    out = np.empty_like(xy, dtype=np.float32)
    for axis in range(2):
        v = np.pad(xy[:, axis], (pad, pad), mode="edge")
        out[:, axis] = np.convolve(v, kernel, mode="valid")

    return out


def polyline_arclength(xy: np.ndarray) -> np.ndarray:
    if len(xy) == 0:
        return np.zeros((0,), dtype=np.float32)

    d = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    return np.concatenate(
        [np.array([0.0], dtype=np.float32), np.cumsum(d).astype(np.float32)]
    )


def resample_polyline(xy: np.ndarray, step: float = 1.0):
    s = polyline_arclength(xy)
    if len(xy) < 2 or s[-1] <= 0:
        return xy.copy(), s.copy()

    sample_s = np.arange(0.0, float(s[-1]) + 1e-6, step, dtype=np.float32)
    if sample_s[-1] < s[-1]:
        sample_s = np.append(sample_s, s[-1]).astype(np.float32)

    x = np.interp(sample_s, s, xy[:, 0])
    y = np.interp(sample_s, s, xy[:, 1])

    return np.stack([x, y], axis=1).astype(np.float32), sample_s


def point_and_tangent_at_s(
    xy: np.ndarray,
    s: np.ndarray,
    query_s: float,
    lookahead: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interpolate center point and tangent from +/- lookahead along arc length.
    """
    q = float(np.clip(query_s, s[0], s[-1]))

    cx = np.interp(q, s, xy[:, 0])
    cy = np.interp(q, s, xy[:, 1])
    center = np.array([cx, cy], dtype=np.float32)

    s0 = max(float(s[0]), q - lookahead)
    s1 = min(float(s[-1]), q + lookahead)

    if s1 - s0 < 1e-3:
        s0 = max(float(s[0]), q - 1.0)
        s1 = min(float(s[-1]), q + 1.0)

    x0 = np.interp(s0, s, xy[:, 0])
    y0 = np.interp(s0, s, xy[:, 1])
    x1 = np.interp(s1, s, xy[:, 0])
    y1 = np.interp(s1, s, xy[:, 1])

    tangent = np.array([x1 - x0, y1 - y0], dtype=np.float32)
    norm = float(np.linalg.norm(tangent))

    if norm < 1e-6:
        tangent = np.array([1.0, 0.0], dtype=np.float32)
    else:
        tangent /= norm

    return center, tangent


# ============================================================
# STATION GEOMETRY
# ============================================================

def estimate_station_side(
    valid_mask: np.ndarray,
    centerline_xy: np.ndarray,
    cfg: StationConfig,
) -> int:
    if cfg.station_side_px is not None:
        return int(cfg.station_side_px)

    # Distance transform returns local distance to polygon boundary.
    binary = (valid_mask > 0).astype(np.uint8)
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

    h, w = valid_mask.shape
    x = np.clip(np.round(centerline_xy[:, 0]).astype(int), 0, w - 1)
    y = np.clip(np.round(centerline_xy[:, 1]).astype(int), 0, h - 1)

    radii = dist[y, x]
    radii = radii[radii > 0.5]

    if len(radii) == 0:
        ys, xs = np.nonzero(valid_mask > 0)
        if len(xs) == 0:
            raise ValueError("valid mask is empty")
        raw = min(int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
        side = raw
    else:
        # full local strip width ~= 2 * distance to nearest boundary
        median_width = 2.0 * float(np.median(radii))
        side = int(round(median_width * cfg.auto_side_scale))

    side = max(cfg.min_station_side_px, side)
    side = min(cfg.max_station_side_px, side)
    return int(side)


def build_station_s_positions(
    total_length: float,
    side: int,
    overlap: float,
) -> List[float]:
    if total_length <= 0:
        return [0.0]

    stride = max(1.0, side * (1.0 - overlap))

    # Put stations from start to end. The valid-mask ratio filter handles
    # partial end stations.
    positions = list(np.arange(0.0, total_length + 1e-6, stride, dtype=float))

    if not positions:
        positions = [0.0]

    if total_length - positions[-1] > 0.35 * stride:
        positions.append(float(total_length))

    return positions


def source_to_station_affine(
    center_xy: np.ndarray,
    tangent_xy: np.ndarray,
    side: int,
) -> np.ndarray:
    """
    Source -> local station coordinates.

    tangent maps to station +X.
    local normal maps to station +Y.
    """
    cx, cy = map(float, center_xy)
    ux, uy = map(float, tangent_xy)
    half = (side - 1) / 2.0

    # x' =  ux*(x-cx) + uy*(y-cy) + half
    # y' = -uy*(x-cx) + ux*(y-cy) + half
    M = np.array(
        [
            [ux, uy, half - ux * cx - uy * cy],
            [-uy, ux, half + uy * cx - ux * cy],
        ],
        dtype=np.float32,
    )
    return M


def extract_station(
    rgb: np.ndarray,
    gt: np.ndarray,
    valid: np.ndarray,
    center_xy: np.ndarray,
    tangent_xy: np.ndarray,
    side: int,
    output_size: int,
    fill_rgb: np.ndarray,
):
    M = source_to_station_affine(center_xy, tangent_xy, side)

    img_patch = cv2.warpAffine(
        rgb,
        M,
        (side, side),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=tuple(int(v) for v in fill_rgb),
    )

    gt_patch = cv2.warpAffine(
        gt,
        M,
        (side, side),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    valid_patch = cv2.warpAffine(
        valid,
        M,
        (side, side),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    valid_patch = (valid_patch > 127).astype(np.uint8) * 255
    gt_patch = (gt_patch > 127).astype(np.uint8) * 255
    gt_patch[valid_patch == 0] = 0
    img_patch[valid_patch == 0] = fill_rgb

    valid_ratio = float((valid_patch > 0).mean())
    paste_ratio = float((gt_patch > 0).mean())

    interp = cv2.INTER_AREA if side > output_size else cv2.INTER_LINEAR

    img_out = cv2.resize(
        img_patch,
        (output_size, output_size),
        interpolation=interp,
    )
    gt_out = cv2.resize(
        gt_patch,
        (output_size, output_size),
        interpolation=cv2.INTER_NEAREST,
    )
    valid_out = cv2.resize(
        valid_patch,
        (output_size, output_size),
        interpolation=cv2.INTER_NEAREST,
    )

    gt_out = (gt_out > 127).astype(np.uint8) * 255
    valid_out = (valid_out > 127).astype(np.uint8) * 255

    # Re-apply after interpolation.
    gt_out[valid_out == 0] = 0
    img_out[valid_out == 0] = fill_rgb

    angle_deg = math.degrees(
        math.atan2(float(tangent_xy[1]), float(tangent_xy[0]))
    )

    return img_out, gt_out, valid_out, valid_ratio, paste_ratio, M, angle_deg


def station_square_corners(
    center_xy: np.ndarray,
    tangent_xy: np.ndarray,
    side: int,
) -> np.ndarray:
    c = np.asarray(center_xy, dtype=np.float32)
    u = np.asarray(tangent_xy, dtype=np.float32)
    v = np.array([-u[1], u[0]], dtype=np.float32)
    h = side / 2.0

    return np.stack(
        [
            c - h * u - h * v,
            c + h * u - h * v,
            c + h * u + h * v,
            c - h * u + h * v,
        ],
        axis=0,
    )


# ============================================================
# DEBUG PREVIEW
# ============================================================

def build_debug_preview(
    rgb_original: np.ndarray,
    valid: np.ndarray,
    centerline_xy: np.ndarray,
    station_geometries: List[Tuple[np.ndarray, np.ndarray, int]],
) -> np.ndarray:
    # Debug is only for visual inspection; use the unmasked ROI as background.
    bgr = cv2.cvtColor(rgb_original, cv2.COLOR_RGB2BGR).copy()

    contours, _ = cv2.findContours(
        (valid > 0).astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    cv2.drawContours(bgr, contours, -1, (0, 255, 255), 1)

    if len(centerline_xy) >= 2:
        pts = np.round(centerline_xy).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(bgr, [pts], False, (255, 0, 0), 1, cv2.LINE_AA)

    for idx, (center, tangent, side) in enumerate(station_geometries):
        corners = np.round(
            station_square_corners(center, tangent, side)
        ).astype(np.int32).reshape(-1, 1, 2)

        cv2.polylines(bgr, [corners], True, (0, 255, 0), 1, cv2.LINE_AA)

        c = tuple(np.round(center).astype(int))
        cv2.circle(bgr, c, 2, (0, 0, 255), -1)

        if DEBUG_DRAW_EVERY_STATION:
            cv2.putText(
                bgr,
                str(idx),
                (c[0] + 3, c[1] - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


# ============================================================
# PROCESS ONE ROI
# ============================================================

def process_one_roi(
    image_path: Path,
    gt_path: Path,
    valid_path: Path,
    out_root: Path,
    cfg: StationConfig,
):
    stem = image_path.stem

    rgb_original = read_rgb(image_path)
    h, w = rgb_original.shape[:2]

    gt = read_mask(gt_path, (h, w))
    valid = read_mask(valid_path, (h, w))

    # Use only the selected polygon component.
    valid = largest_component(valid)

    # GT semantics are meaningful only inside valid polygon.
    gt = clip_gt_to_valid(gt, valid)

    fill_rgb = compute_invalid_fill_rgb(
        rgb_original,
        valid,
        cfg.invalid_fill_mode,
    )

    rgb = rgb_original.copy()
    if cfg.apply_valid_mask_to_image:
        rgb = apply_valid_polygon_to_image(rgb, valid, fill_rgb)

    # 1) valid polygon -> centerline
    skel = skeletonize(valid)
    skel = largest_component(skel)

    raw_centerline = longest_centerline_path(skel)
    smooth_centerline = smooth_polyline(
        raw_centerline,
        cfg.centerline_smooth_window,
    )

    # Resample at ~1 pixel arc-length resolution.
    centerline_xy, centerline_s = resample_polyline(
        smooth_centerline,
        step=1.0,
    )

    if len(centerline_xy) < 2:
        raise ValueError("Centerline is too short")

    total_length = float(centerline_s[-1])

    # 2) choose ONE equal square side for this ROI
    side = estimate_station_side(valid, centerline_xy, cfg)

    # 3) station centers along curved arc length
    station_s = build_station_s_positions(
        total_length,
        side,
        cfg.overlap,
    )

    saved_meta = []
    debug_geometries = []

    for idx, s_query in enumerate(station_s):
        center, tangent = point_and_tangent_at_s(
            centerline_xy,
            centerline_s,
            s_query,
            cfg.tangent_lookahead_px,
        )

        (
            img64,
            gt64,
            valid64,
            valid_ratio,
            paste_ratio,
            affine,
            angle_deg,
        ) = extract_station(
            rgb=rgb,
            gt=gt,
            valid=valid,
            center_xy=center,
            tangent_xy=tangent,
            side=side,
            output_size=cfg.output_size,
            fill_rgb=fill_rgb,
        )

        # Geometry filtering uses ONLY valid mask, never paste GT.
        if valid_ratio < cfg.min_valid_ratio:
            continue

        name = f"{stem}__st_{idx:04d}"

        image_out = out_root / "images" / f"{name}.png"
        mask_out = out_root / "masks" / f"{name}.png"
        valid_out = out_root / "valid" / f"{name}.png"
        meta_out = out_root / "meta" / f"{name}.json"

        save_rgb(image_out, img64)
        save_gray(mask_out, gt64)
        save_gray(valid_out, valid64)

        meta = {
            "station_name": name,
            "source_roi": image_path.name,
            "source_gt_mask": gt_path.name,
            "source_valid_mask": valid_path.name,

            "centerline": {
                "arc_position_px": float(s_query),
                "arc_length_total_px": total_length,
                "s_norm": (
                    float(s_query / total_length)
                    if total_length > 1e-9
                    else 0.0
                ),
                "center_xy_source": [
                    float(center[0]),
                    float(center[1]),
                ],
                "tangent_xy": [
                    float(tangent[0]),
                    float(tangent[1]),
                ],
                "tangent_angle_deg": float(angle_deg),
            },

            "station": {
                "index": idx,
                "side_px_before_resize": int(side),
                "output_size": [cfg.output_size, cfg.output_size],
                "overlap": float(cfg.overlap),
                "valid_ratio_before_resize": float(valid_ratio),

                # Diagnostic only. GT did NOT decide station geometry.
                "thermal_paste_ratio_before_resize": float(paste_ratio),

                "source_to_station_affine_2x3": affine.tolist(),
            },

            "valid_polygon": {
                "applied_to_image": cfg.apply_valid_mask_to_image,
                "invalid_fill_mode": cfg.invalid_fill_mode,
                "invalid_fill_rgb": [int(v) for v in fill_rgb],
            },
        }

        meta_out.parent.mkdir(parents=True, exist_ok=True)
        meta_out.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        saved_meta.append(meta)
        debug_geometries.append((center, tangent, side))

    if cfg.save_debug_preview:
        preview = build_debug_preview(
            rgb_original,
            valid,
            centerline_xy,
            debug_geometries,
        )
        save_rgb(
            out_root / "debug" / f"{stem}__stations.png",
            preview,
        )

        save_gray(
            out_root / "debug" / f"{stem}__skeleton.png",
            skel,
        )

    roi_summary = {
        "source_roi": image_path.name,
        "centerline_length_px": total_length,
        "station_side_px": int(side),
        "stations_saved": len(saved_meta),
    }

    return saved_meta, roi_summary


# ============================================================
# DATASET
# ============================================================

def process_dataset(
    dataset_root: Path,
    output_root: Path,
    cfg: StationConfig,
):
    images_dir = dataset_root / "images"
    masks_dir = dataset_root / "masks"
    valid_dir = dataset_root / "valid"

    if not images_dir.exists():
        raise FileNotFoundError(f"Missing images folder: {images_dir}")
    if not masks_dir.exists():
        raise FileNotFoundError(f"Missing masks folder: {masks_dir}")
    if not valid_dir.exists():
        raise FileNotFoundError(
            f"Missing valid folder: {valid_dir}. "
            "Curved station geometry requires polygon-valid masks."
        )

    output_root.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(
        p for p in images_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTS
    )

    total_stations = 0
    roi_summaries = []
    skipped = []

    for i, image_path in enumerate(image_paths, 1):
        stem = image_path.stem

        gt_path = find_matching_file(masks_dir, stem)
        valid_path = find_matching_file(valid_dir, stem)

        if gt_path is None:
            print(f"[SKIP] {stem}: GT mask missing")
            skipped.append({"roi": stem, "reason": "gt_mask_missing"})
            continue

        if valid_path is None:
            print(f"[SKIP] {stem}: valid polygon mask missing")
            skipped.append({"roi": stem, "reason": "valid_mask_missing"})
            continue

        try:
            stations, roi_summary = process_one_roi(
                image_path=image_path,
                gt_path=gt_path,
                valid_path=valid_path,
                out_root=output_root,
                cfg=cfg,
            )

            total_stations += len(stations)
            roi_summaries.append(roi_summary)

            print(
                f"[{i:04d}/{len(image_paths):04d}] {stem}: "
                f"{len(stations)} stations, "
                f"side={roi_summary['station_side_px']} px, "
                f"curve={roi_summary['centerline_length_px']:.1f} px"
            )

        except Exception as exc:
            print(f"[ERROR] {stem}: {exc}")
            skipped.append({"roi": stem, "reason": str(exc)})

    summary = {
        "dataset_root": str(dataset_root.resolve()),
        "output_root": str(output_root.resolve()),
        "config": asdict(cfg),
        "source_rois": len(image_paths),
        "stations_saved": total_stations,
        "roi_summaries": roi_summaries,
        "skipped": skipped,
    }

    (output_root / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== DONE ===")
    print(f"Source ROIs    : {len(image_paths)}")
    print(f"Stations saved : {total_stations}")
    print(f"Output         : {output_root}")


# ============================================================
# MAIN
# ============================================================

def main():
    if not (0.0 <= OVERLAP < 0.95):
        raise ValueError("OVERLAP must be in [0, 0.95)")

    if not (0.0 <= MIN_VALID_RATIO <= 1.0):
        raise ValueError("MIN_VALID_RATIO must be in [0, 1]")

    if OUTPUT_SIZE <= 0:
        raise ValueError("OUTPUT_SIZE must be > 0")

    if STATION_SIDE_PX is not None and STATION_SIDE_PX < 2:
        raise ValueError("STATION_SIDE_PX must be None or >= 2")

    if CENTERLINE_SMOOTH_WINDOW < 1:
        raise ValueError("CENTERLINE_SMOOTH_WINDOW must be >= 1")

    if CENTERLINE_SMOOTH_WINDOW % 2 == 0:
        raise ValueError("CENTERLINE_SMOOTH_WINDOW must be odd")

    cfg = StationConfig(
        output_size=OUTPUT_SIZE,
        overlap=OVERLAP,
        min_valid_ratio=MIN_VALID_RATIO,

        station_side_px=STATION_SIDE_PX,
        auto_side_scale=AUTO_SIDE_SCALE,
        min_station_side_px=MIN_STATION_SIDE_PX,
        max_station_side_px=MAX_STATION_SIDE_PX,

        centerline_smooth_window=CENTERLINE_SMOOTH_WINDOW,
        tangent_lookahead_px=TANGENT_LOOKAHEAD_PX,

        apply_valid_mask_to_image=APPLY_VALID_MASK_TO_IMAGE,
        invalid_fill_mode=INVALID_FILL_MODE,

        save_debug_preview=SAVE_DEBUG_PREVIEW,
    )

    print("=== Entropy #1 Curved Station Builder ===")
    print(f"Dataset root       : {DATASET_ROOT}")
    print(f"Output root        : {OUTPUT_ROOT}")
    print(f"Final station size : {OUTPUT_SIZE}x{OUTPUT_SIZE}")
    print(f"Overlap            : {OVERLAP:.2f}")
    print(f"Station side       : {STATION_SIDE_PX if STATION_SIDE_PX else 'AUTO'}")
    print(f"Auto side scale    : {AUTO_SIDE_SCALE:.2f}")
    print(f"Centerline smooth  : {CENTERLINE_SMOOTH_WINDOW}")
    print(f"Tangent lookahead  : {TANGENT_LOOKAHEAD_PX:.1f}px")
    print(f"Mask invalid area  : {APPLY_VALID_MASK_TO_IMAGE}")
    print(f"Invalid fill       : {INVALID_FILL_MODE}")
    print()

    process_dataset(
        DATASET_ROOT,
        OUTPUT_ROOT,
        cfg,
    )


if __name__ == "__main__":
    main()