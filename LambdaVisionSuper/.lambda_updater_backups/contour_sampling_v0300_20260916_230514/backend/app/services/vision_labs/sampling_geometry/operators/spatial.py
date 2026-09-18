from __future__ import annotations

import math

import cv2
import numpy as np

from app.services.vision_labs.core import BoolParam, ExecutionContext, EnumParam, FloatParam, IntParam
from app.services.vision_labs.image.types import ImageFrame
from app.services.vision_labs.sampling_geometry.operator import SamplingGeometryOperator
from app.services.vision_labs.sampling_geometry.registry import sampling_operator
from app.services.vision_labs.sampling_geometry.specs import SamplingPort
from app.services.vision_labs.sampling_geometry.types import FeatureMatrix, FeatureVector, ProfileSet, SamplingHousing
from app.services.vision_labs.sampling_geometry.operators.common import image_channel, image_to_bgr, sample_line


_CHANNELS = ["gray", "r", "g", "b", "h", "s", "v"]


@sampling_operator
class AxisRays(SamplingGeometryOperator):
    CATALOG_VISIBLE = False
    OPERATOR_ID = "sampling.spatial.axis_rays"
    LABEL = "Axis Rays"
    CATEGORY = "Spatial / Rays"
    WORKSPACE = "spatial"
    DESCRIPTION = "Sample evenly distributed horizontal or vertical intensity rays across the image."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"profiles": SamplingPort("profile_set")}
    PARAMETERS = {
        "axis": EnumParam(["x", "y"], default="x", label="Ray direction"),
        "ray_count": IntParam(default=5, min=1, max=64, label="Ray count"),
        "samples": IntParam(default=256, min=16, max=4096, label="Samples / ray"),
        "channel": EnumParam(_CHANNELS, default="gray", label="Channel"),
    }
    GUIDE = {
        "overview": "Cuts the raster into a family of one-dimensional signals aligned with the X or Y axis.",
        "how_it_works": "Ray origins are evenly distributed across the orthogonal image dimension. Bilinear interpolation samples the chosen intensity channel along each full-length ray.",
        "tips": [
            "Start with 3-7 rays to understand the signal before increasing density.",
            "Use RGB/HSV channels when grayscale hides a color-specific defect.",
        ],
        "notes": [
            "Profiles preserve spatial order and can later feed statistics, Fourier analysis or Representation LAB.",
        ],
        "visualization": "axis_rays",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        channel = image_channel(frame, params["channel"])
        h, w = channel.shape[:2]
        count = int(params["ray_count"])
        samples = int(params["samples"])
        axis = params["axis"]
        rays = []
        profiles = []

        if axis == "x":
            positions = np.linspace(0, max(0, h - 1), count + 2)[1:-1] if count > 1 else np.array([(h - 1) / 2.0])
            for y in positions:
                start, end = (0.0, float(y)), (float(w - 1), float(y))
                rays.append([start[0] / max(1, w - 1), start[1] / max(1, h - 1), end[0] / max(1, w - 1), end[1] / max(1, h - 1)])
                profiles.append(sample_line(channel, start, end, samples))
        else:
            positions = np.linspace(0, max(0, w - 1), count + 2)[1:-1] if count > 1 else np.array([(w - 1) / 2.0])
            for x in positions:
                start, end = (float(x), 0.0), (float(x), float(h - 1))
                rays.append([start[0] / max(1, w - 1), start[1] / max(1, h - 1), end[0] / max(1, w - 1), end[1] / max(1, h - 1)])
                profiles.append(sample_line(channel, start, end, samples))

        return {
            "profiles": ProfileSet(
                x=np.linspace(0.0, 1.0, samples, dtype=np.float32),
                series=np.asarray(profiles, dtype=np.float32),
                labels=[f"ray_{i}" for i in range(len(profiles))],
                geometry={"kind": "rays", "rays": rays, "normalized": True},
                units="normalized_position",
                metadata={"channel": params["channel"], "axis": axis},
            )
        }


@sampling_operator
class CrossSampler(SamplingGeometryOperator):
    CATALOG_VISIBLE = False
    OPERATOR_ID = "sampling.spatial.cross"
    LABEL = "Cross Sampler"
    CATEGORY = "Spatial / Rays"
    WORKSPACE = "spatial"
    DESCRIPTION = "Sample horizontal and vertical profiles through a configurable image center."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"profiles": SamplingPort("profile_set")}
    PARAMETERS = {
        "center_x": FloatParam(default=0.5, min=0.0, max=1.0, label="Center X"),
        "center_y": FloatParam(default=0.5, min=0.0, max=1.0, label="Center Y"),
        "length": FloatParam(default=1.0, min=0.05, max=1.5, label="Length ratio"),
        "samples": IntParam(default=256, min=16, max=4096, label="Samples / arm"),
        "channel": EnumParam(_CHANNELS, default="gray", label="Channel"),
    }
    GUIDE = {
        "overview": "Samples a plus-shaped pair of signals through a chosen point.",
        "how_it_works": "One horizontal and one vertical ray are centered at (X,Y). Their length is expressed as a fraction of the image dimensions and values are bilinearly interpolated.",
        "tips": [
            "Use a stable anatomical/fixture center when comparing many images.",
            "If the product can translate, pair this sampler later with a location/alignment source rather than hard-coding the center.",
        ],
        "notes": [
            "The two profiles can be concatenated later in Representation LAB.",
        ],
        "visualization": "cross",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        channel = image_channel(frame, params["channel"])
        h, w = channel.shape[:2]
        cx = float(params["center_x"]) * max(1, w - 1)
        cy = float(params["center_y"]) * max(1, h - 1)
        length = float(params["length"])
        half_w = 0.5 * length * max(1, w - 1)
        half_h = 0.5 * length * max(1, h - 1)
        horizontal = ((cx - half_w, cy), (cx + half_w, cy))
        vertical = ((cx, cy - half_h), (cx, cy + half_h))
        samples = int(params["samples"])
        series = np.stack(
            [
                sample_line(channel, horizontal[0], horizontal[1], samples),
                sample_line(channel, vertical[0], vertical[1], samples),
            ],
            axis=0,
        )
        rays = []
        for start, end in (horizontal, vertical):
            rays.append([
                start[0] / max(1, w - 1),
                start[1] / max(1, h - 1),
                end[0] / max(1, w - 1),
                end[1] / max(1, h - 1),
            ])
        return {
            "profiles": ProfileSet(
                x=np.linspace(-1.0, 1.0, samples, dtype=np.float32),
                series=series.astype(np.float32),
                labels=["horizontal", "vertical"],
                geometry={"kind": "rays", "rays": rays, "normalized": True},
                units="normalized_arm",
                metadata={"channel": params["channel"]},
            )
        }


@sampling_operator
class ConcentricRings(SamplingGeometryOperator):
    CATALOG_VISIBLE = False
    OPERATOR_ID = "sampling.spatial.rings"
    LABEL = "Concentric Rings"
    CATEGORY = "Spatial / Rings"
    WORKSPACE = "spatial"
    DESCRIPTION = "Sample intensity around multiple concentric circular rings."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"profiles": SamplingPort("profile_set")}
    PARAMETERS = {
        "center_x": FloatParam(default=0.5, min=0.0, max=1.0, label="Center X"),
        "center_y": FloatParam(default=0.5, min=0.0, max=1.0, label="Center Y"),
        "rings": IntParam(default=6, min=1, max=32, label="Ring count"),
        "inner_radius": FloatParam(default=0.08, min=0.0, max=0.7, label="Inner radius"),
        "outer_radius": FloatParam(default=0.45, min=0.01, max=0.75, label="Outer radius"),
        "angular_samples": IntParam(default=256, min=32, max=4096, label="Angular samples"),
        "channel": EnumParam(_CHANNELS, default="gray", label="Channel"),
    }
    GUIDE = {
        "overview": "Describes how raster intensity changes around a center as a function of angle and radius.",
        "how_it_works": "Several normalized radii are sampled around 0..360 degrees. Each ring becomes an ordered angular signal.",
        "tips": [
            "Use rings for rotational patterns or when radial distance matters more than Cartesian position.",
            "Keep the outer radius inside the useful product region to avoid border-padding artifacts.",
        ],
        "notes": [
            "Ring profiles are especially useful before 1D Fourier or rotational periodicity analysis.",
        ],
        "visualization": "rings",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        image = image_channel(frame, params["channel"])
        h, w = image.shape[:2]
        cx = float(params["center_x"]) * max(1, w - 1)
        cy = float(params["center_y"]) * max(1, h - 1)
        ring_count = int(params["rings"])
        inner = float(params["inner_radius"])
        outer = float(params["outer_radius"])
        if outer <= inner:
            raise ValueError("outer_radius must be greater than inner_radius")
        radii_norm = np.linspace(inner, outer, ring_count)
        radius_scale = float(min(w, h))
        angles = np.linspace(0.0, 2.0 * math.pi, int(params["angular_samples"]), endpoint=False)
        profiles = []
        for radius_norm in radii_norm:
            radius = radius_norm * radius_scale
            xs = cx + np.cos(angles) * radius
            ys = cy + np.sin(angles) * radius
            map_x = np.clip(xs, 0, max(0, w - 1)).astype(np.float32)[None, :]
            map_y = np.clip(ys, 0, max(0, h - 1)).astype(np.float32)[None, :]
            sampled = cv2.remap(image.astype(np.float32), map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            profiles.append(sampled.reshape(-1))
        return {
            "profiles": ProfileSet(
                x=np.linspace(0.0, 360.0, len(angles), endpoint=False, dtype=np.float32),
                series=np.asarray(profiles, dtype=np.float32),
                labels=[f"ring_{i}" for i in range(ring_count)],
                geometry={
                    "kind": "rings",
                    "center": [float(params["center_x"]), float(params["center_y"])],
                    "radii": radii_norm.astype(float).tolist(),
                    "radius_reference": "min_dimension",
                    "normalized": True,
                },
                units="degree",
                metadata={"channel": params["channel"]},
            )
        }


@sampling_operator
class PatchGridStatistics(SamplingGeometryOperator):
    CATALOG_VISIBLE = False
    OPERATOR_ID = "sampling.spatial.patch_grid"
    LABEL = "Patch Grid Statistics"
    CATEGORY = "Spatial / Patches"
    WORKSPACE = "spatial"
    DESCRIPTION = "Tile the image into a regular grid and extract local gray/RGB statistics per patch."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"features": SamplingPort("feature_matrix")}
    PARAMETERS = {
        "rows": IntParam(default=4, min=1, max=32, label="Rows"),
        "cols": IntParam(default=4, min=1, max=32, label="Columns"),
        "margin": FloatParam(default=0.0, min=0.0, max=0.4, label="Outer margin"),
    }
    GUIDE = {
        "overview": "Converts local image regions into a structured matrix of hand-engineered features.",
        "how_it_works": "A regular grid is placed over the image. For every patch, gray mean/std and B/G/R means are measured, producing one feature row per patch.",
        "tips": [
            "Choose grid size so each patch is large enough for stable statistics but small enough to preserve defect location.",
            "Use the visual grid overlay to confirm that patch boundaries match the product structure.",
        ],
        "notes": [
            "Representation LAB can later reorder, normalize, flatten or concatenate this matrix for an MLP.",
        ],
        "visualization": "patch_grid",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        bgr = image_to_bgr(frame).astype(np.float32)
        gray = cv2.cvtColor(bgr.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        h, w = gray.shape[:2]
        rows = int(params["rows"])
        cols = int(params["cols"])
        margin = float(params["margin"])
        x0 = int(round(margin * w))
        y0 = int(round(margin * h))
        x1 = max(x0 + 1, int(round((1.0 - margin) * w)))
        y1 = max(y0 + 1, int(round((1.0 - margin) * h)))
        xs = np.linspace(x0, x1, cols + 1).astype(int)
        ys = np.linspace(y0, y1, rows + 1).astype(int)
        values = []
        boxes = []
        labels = []
        for row in range(rows):
            for col in range(cols):
                xa, xb = xs[col], xs[col + 1]
                ya, yb = ys[row], ys[row + 1]
                patch_g = gray[ya:yb, xa:xb]
                patch_bgr = bgr[ya:yb, xa:xb]
                if patch_g.size == 0:
                    feature = [0.0] * 5
                else:
                    means = patch_bgr.reshape(-1, 3).mean(axis=0)
                    feature = [
                        float(patch_g.mean()),
                        float(patch_g.std()),
                        float(means[2]),
                        float(means[1]),
                        float(means[0]),
                    ]
                values.append(feature)
                boxes.append([
                    xa / max(1, w),
                    ya / max(1, h),
                    xb / max(1, w),
                    yb / max(1, h),
                ])
                labels.append(f"r{row}c{col}")
        return {
            "features": FeatureMatrix(
                values=np.asarray(values, dtype=np.float32),
                feature_names=[
                    "gray_mean",
                    "gray_std",
                    "r_mean",
                    "g_mean",
                    "b_mean",
                ],
                row_labels=labels,
                geometry={"kind": "boxes", "boxes": boxes, "normalized": True},
                metadata={"rows": rows, "cols": cols},
            )
        }


_CHANNEL_FLAGS = [
    ("gray", "sample_gray"),
    ("r", "sample_r"),
    ("g", "sample_g"),
    ("b", "sample_b"),
    ("h", "sample_h"),
    ("s", "sample_s"),
    ("v", "sample_v"),
    ("lab_l", "sample_lab_l"),
    ("lab_a", "sample_lab_a"),
    ("lab_b", "sample_lab_b"),
]


def _source_shape(frame: ImageFrame) -> tuple[int, int]:
    shape = np.asarray(frame.data).shape
    return int(shape[0]), int(shape[1])


def _housing_geometry(kind: str, elements: list[dict], source_shape: tuple[int, int]) -> dict:
    if kind in {"axis_rays", "cross"}:
        return {
            "kind": "rays",
            "rays": [
                [*element["start"], *element["end"]]
                for element in elements
            ],
            "normalized": True,
        }
    if kind == "rings":
        center = elements[0]["center"] if elements else [0.5, 0.5]
        return {
            "kind": "rings",
            "center": center,
            "radii": [element["radius"] for element in elements],
            "radius_reference": "min_dimension",
            "normalized": True,
        }
    if kind == "patch_grid":
        return {
            "kind": "boxes",
            "boxes": [element["box"] for element in elements],
            "normalized": True,
        }
    return {"kind": kind, "normalized": True}


@sampling_operator
class AxisRayHousing(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spatial.housing.axis_rays"
    LABEL = "Axis Ray Housing"
    CATEGORY = "Sampling Housing / Rays"
    WORKSPACE = "spatial"
    DESCRIPTION = "Define where horizontal or vertical rays live; no intensity data is extracted yet."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"housing": SamplingPort("sampling_housing")}
    PARAMETERS = {
        "axis": EnumParam(["x", "y"], default="x", label="Ray direction"),
        "ray_count": IntParam(default=5, min=1, max=128, label="Ray count"),
        "margin": FloatParam(default=0.0, min=0.0, max=0.45, label="End margin"),
    }
    GUIDE = {
        "overview": "Defines the WHERE of sampling: a family of axis-aligned rays over the image.",
        "how_it_works": "The housing stores normalized line geometry only. Add Data Extractor after it to choose Gray/RGB/HSV/LAB data, sampling density, histograms and statistics.",
        "tips": ["Start sparse so each ray remains visually interpretable."],
        "notes": ["Housing contains no sampled numerical values."],
        "visualization": "axis_rays",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        h, w = _source_shape(frame)
        count = int(params["ray_count"])
        margin = float(params["margin"])
        axis = str(params["axis"])
        elements = []
        positions = np.linspace(margin, 1.0 - margin, count + 2)[1:-1] if count > 1 else np.array([0.5])
        for index, pos in enumerate(positions):
            if axis == "x":
                start, end = [margin, float(pos)], [1.0 - margin, float(pos)]
            else:
                start, end = [float(pos), margin], [float(pos), 1.0 - margin]
            elements.append({"id": f"ray_{index}", "kind": "ray", "start": start, "end": end})
        return {"housing": SamplingHousing("axis_rays", (h, w), elements, _housing_geometry("axis_rays", elements, (h, w)), {"axis": axis})}


@sampling_operator
class CrossHousing(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spatial.housing.cross"
    LABEL = "Cross Housing"
    CATEGORY = "Sampling Housing / Rays"
    WORKSPACE = "spatial"
    DESCRIPTION = "Define a horizontal and vertical sampling cross around a configurable center."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"housing": SamplingPort("sampling_housing")}
    PARAMETERS = {
        "center_x": FloatParam(default=0.5, min=0.0, max=1.0, label="Center X"),
        "center_y": FloatParam(default=0.5, min=0.0, max=1.0, label="Center Y"),
        "length": FloatParam(default=1.0, min=0.05, max=1.5, label="Length ratio"),
    }
    GUIDE = {
        "overview": "Defines a plus-shaped sampling housing without deciding WHAT pixel information to collect.",
        "how_it_works": "Two normalized rays share one center. The next Data Extractor determines channels and numeric representation.",
        "tips": ["Use a stable center or later feed a located center from another service."],
        "notes": ["Housing geometry remains independent from data extraction."],
        "visualization": "cross",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        h, w = _source_shape(frame)
        cx, cy = float(params["center_x"]), float(params["center_y"])
        half = float(params["length"]) * 0.5
        elements = [
            {"id": "horizontal", "kind": "ray", "start": [cx - half, cy], "end": [cx + half, cy]},
            {"id": "vertical", "kind": "ray", "start": [cx, cy - half], "end": [cx, cy + half]},
        ]
        return {"housing": SamplingHousing("cross", (h, w), elements, _housing_geometry("cross", elements, (h, w)), {"center": [cx, cy]})}


@sampling_operator
class RingHousing(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spatial.housing.rings"
    LABEL = "Concentric Ring Housing"
    CATEGORY = "Sampling Housing / Rings"
    WORKSPACE = "spatial"
    DESCRIPTION = "Define concentric circular sampling paths around a center."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"housing": SamplingPort("sampling_housing")}
    PARAMETERS = {
        "center_x": FloatParam(default=0.5, min=0.0, max=1.0, label="Center X"),
        "center_y": FloatParam(default=0.5, min=0.0, max=1.0, label="Center Y"),
        "rings": IntParam(default=6, min=1, max=64, label="Ring count"),
        "inner_radius": FloatParam(default=0.08, min=0.0, max=0.7, label="Inner radius"),
        "outer_radius": FloatParam(default=0.45, min=0.01, max=0.75, label="Outer radius"),
    }
    GUIDE = {
        "overview": "Defines the WHERE for radial/rotational sampling.",
        "how_it_works": "Each element is one normalized ring. Data Extractor can later sample any selected intensity/color channels and summarize them.",
        "tips": ["Keep the outer ring inside the product region."],
        "notes": ["Ring profiles can later be transformed by FFT in a future Representation/Spectral chain."],
        "visualization": "rings",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        h, w = _source_shape(frame)
        count = int(params["rings"])
        inner, outer = float(params["inner_radius"]), float(params["outer_radius"])
        if outer <= inner:
            raise ValueError("outer_radius must be greater than inner_radius")
        center = [float(params["center_x"]), float(params["center_y"])]
        radii = np.linspace(inner, outer, count)
        elements = [{"id": f"ring_{i}", "kind": "ring", "center": center, "radius": float(radius)} for i, radius in enumerate(radii)]
        return {"housing": SamplingHousing("rings", (h, w), elements, _housing_geometry("rings", elements, (h, w)), {"center": center})}


@sampling_operator
class PatchGridHousing(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spatial.housing.patch_grid"
    LABEL = "Patch Grid Housing"
    CATEGORY = "Sampling Housing / Patches"
    WORKSPACE = "spatial"
    DESCRIPTION = "Define a regular patch/grid housing; extraction strategy is configured separately."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"housing": SamplingPort("sampling_housing")}
    PARAMETERS = {
        "rows": IntParam(default=4, min=1, max=32, label="Rows"),
        "cols": IntParam(default=4, min=1, max=32, label="Columns"),
        "margin": FloatParam(default=0.0, min=0.0, max=0.45, label="Outer margin"),
    }
    GUIDE = {
        "overview": "Defines spatial bins/patches but deliberately does not choose their numeric features.",
        "how_it_works": "The usable image area is divided into normalized boxes. Add Data Extractor to choose channels, sampling density, statistics and histograms.",
        "tips": ["Choose a grid aligned with meaningful product structure whenever possible."],
        "notes": ["The same housing can produce very different vectors depending on extractor settings."],
        "visualization": "patch_grid",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        h, w = _source_shape(frame)
        rows, cols = int(params["rows"]), int(params["cols"])
        margin = float(params["margin"])
        elements = []
        for row in range(rows):
            for col in range(cols):
                x0 = margin + (1.0 - 2.0 * margin) * col / cols
                x1 = margin + (1.0 - 2.0 * margin) * (col + 1) / cols
                y0 = margin + (1.0 - 2.0 * margin) * row / rows
                y1 = margin + (1.0 - 2.0 * margin) * (row + 1) / rows
                elements.append({"id": f"patch_r{row}_c{col}", "kind": "box", "box": [x0, y0, x1, y1], "row": row, "col": col})
        return {"housing": SamplingHousing("patch_grid", (h, w), elements, _housing_geometry("patch_grid", elements, (h, w)), {"rows": rows, "cols": cols})}


def _selected_channels(params) -> list[str]:
    selected = [channel for channel, flag in _CHANNEL_FLAGS if bool(params.get(flag))]
    if not selected:
        raise ValueError("Data Extractor needs at least one enabled channel")
    return selected


def _count_for_length(length_px: float, params) -> int:
    mode = str(params["sample_mode"])
    if mode == "full":
        return max(2, int(round(length_px)) + 1)
    if mode == "step":
        return max(2, int(np.floor(length_px / max(1, int(params["sample_step"])))) + 1)
    return max(2, int(params["sample_count"]))


def _element_values(image: np.ndarray, element: dict, source_shape: tuple[int, int], params, *, force_count: int | None = None) -> np.ndarray:
    h, w = source_shape
    kind = element.get("kind")
    if kind == "ray":
        start = element["start"]
        end = element["end"]
        p0 = (float(start[0]) * max(1, w - 1), float(start[1]) * max(1, h - 1))
        p1 = (float(end[0]) * max(1, w - 1), float(end[1]) * max(1, h - 1))
        length = float(np.linalg.norm(np.asarray(p1) - np.asarray(p0)))
        count = force_count or _count_for_length(length, params)
        return sample_line(image, p0, p1, count)
    if kind == "ring":
        center = element["center"]
        radius = float(element["radius"]) * float(min(w, h))
        cx, cy = float(center[0]) * max(1, w - 1), float(center[1]) * max(1, h - 1)
        circumference = 2.0 * math.pi * radius
        count = force_count or _count_for_length(circumference, params)
        angles = np.linspace(0.0, 2.0 * math.pi, count, endpoint=False)
        xs = cx + np.cos(angles) * radius
        ys = cy + np.sin(angles) * radius
        map_x = np.clip(xs, 0, max(0, w - 1)).astype(np.float32)[None, :]
        map_y = np.clip(ys, 0, max(0, h - 1)).astype(np.float32)[None, :]
        return cv2.remap(image.astype(np.float32), map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).reshape(-1)
    if kind == "box":
        x0, y0, x1, y1 = element["box"]
        ix0 = int(np.floor(np.clip(x0, 0.0, 1.0) * max(1, w - 1)))
        ix1 = int(np.ceil(np.clip(x1, 0.0, 1.0) * max(1, w - 1))) + 1
        iy0 = int(np.floor(np.clip(y0, 0.0, 1.0) * max(1, h - 1)))
        iy1 = int(np.ceil(np.clip(y1, 0.0, 1.0) * max(1, h - 1))) + 1
        crop = image[max(0, iy0):min(h, iy1), max(0, ix0):min(w, ix1)].reshape(-1)
        if crop.size == 0:
            return np.zeros((force_count or int(params["sample_count"]),), dtype=np.float32)
        if force_count:
            positions = np.linspace(0, crop.size - 1, force_count)
            return np.interp(positions, np.arange(crop.size), crop).astype(np.float32)
        mode = str(params["sample_mode"])
        if mode == "step":
            return crop[:: max(1, int(params["sample_step"]))].astype(np.float32)
        if mode == "count":
            count = max(2, int(params["sample_count"]))
            positions = np.linspace(0, crop.size - 1, count)
            return np.interp(positions, np.arange(crop.size), crop).astype(np.float32)
        return crop.astype(np.float32)
    raise ValueError(f"Unsupported housing element kind: {kind!r}")


@sampling_operator
class HousingDataExtractor(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spatial.data_extractor"
    LABEL = "Data Extractor"
    CATEGORY = "Data Extraction"
    WORKSPACE = "spatial"
    DESCRIPTION = "Define HOW the housing is sampled: channels, density, statistics, histograms and raw profiles."
    INPUTS = {
        "housing": SamplingPort("sampling_housing"),
        "image": SamplingPort("image", label="Reference image from Source Board"),
    }
    OUTPUTS = {
        "vector": SamplingPort("feature_vector"),
        "matrix": SamplingPort("feature_matrix"),
        "profiles": SamplingPort("profile_set"),
    }
    PARAMETERS = {
        "sample_mode": EnumParam(["full", "step", "count"], default="count", label="Sampling mode"),
        "sample_step": IntParam(default=4, min=1, max=256, label="Sampling step px"),
        "sample_count": IntParam(default=128, min=4, max=4096, label="Samples / element"),
        "profile_samples": IntParam(default=128, min=8, max=2048, label="Preview profile samples"),
        "sample_gray": BoolParam(default=True, label="Gray"),
        "sample_r": BoolParam(default=False, label="R"),
        "sample_g": BoolParam(default=False, label="G"),
        "sample_b": BoolParam(default=False, label="B"),
        "sample_h": BoolParam(default=False, label="H"),
        "sample_s": BoolParam(default=False, label="S"),
        "sample_v": BoolParam(default=False, label="V"),
        "sample_lab_l": BoolParam(default=False, label="LAB L"),
        "sample_lab_a": BoolParam(default=False, label="LAB a"),
        "sample_lab_b": BoolParam(default=False, label="LAB b"),
        "include_mean": BoolParam(default=True, label="Mean"),
        "include_std": BoolParam(default=True, label="Std"),
        "include_minmax": BoolParam(default=False, label="Min / Max"),
        "include_histogram": BoolParam(default=False, label="Histogram"),
        "histogram_bins": IntParam(default=8, min=2, max=64, label="Histogram bins"),
        "include_profiles": BoolParam(default=True, label="Raw profile preview"),
    }
    GUIDE = {
        "overview": "Answers HOW to sample a housing and makes the resulting vector composition explicit.",
        "how_it_works": "For every housing element, the selected image channels are sampled using full-resolution, pixel-step, or fixed-count sampling. Named statistics/histogram bins form a matrix and flattened vector; fixed-length profiles are kept for visual inspection.",
        "tips": [
            "Start with Gray mean/std and inspect the vector schema before adding channels or histogram bins.",
            "Use fixed-count sampling when downstream vector dimensionality must remain stable across image sizes.",
        ],
        "notes": ["Feature names record element ID, channel and extraction operation so Representation LAB never has to guess what a number means."],
        "visualization": "data_extractor",
    }

    def process(self, inputs, params, context: ExecutionContext):
        housing: SamplingHousing = inputs["housing"]
        frame: ImageFrame = inputs["image"]
        channels = _selected_channels(params)
        channel_images = {channel: image_channel(frame, channel) for channel in channels}
        feature_names: list[str] = []
        per_row_names: list[str] = []
        # Build a stable per-element schema.
        for channel in channels:
            if bool(params["include_mean"]): per_row_names.append(f"{channel}.mean")
            if bool(params["include_std"]): per_row_names.append(f"{channel}.std")
            if bool(params["include_minmax"]): per_row_names.extend([f"{channel}.min", f"{channel}.max"])
            if bool(params["include_histogram"]):
                per_row_names.extend([f"{channel}.hist_{i:02d}" for i in range(int(params["histogram_bins"]))])
        if not per_row_names:
            raise ValueError("Enable at least one statistic or histogram output")

        rows = []
        profile_series = []
        profile_labels = []
        for element in housing.elements:
            row = []
            for channel in channels:
                values = _element_values(channel_images[channel], element, housing.source_shape, params)
                if bool(params["include_mean"]): row.append(float(np.mean(values)) if values.size else 0.0)
                if bool(params["include_std"]): row.append(float(np.std(values)) if values.size else 0.0)
                if bool(params["include_minmax"]):
                    row.extend([float(np.min(values)) if values.size else 0.0, float(np.max(values)) if values.size else 0.0])
                if bool(params["include_histogram"]):
                    hist, _ = np.histogram(values, bins=int(params["histogram_bins"]), range=(0.0, 256.0))
                    hist = hist.astype(np.float64)
                    if hist.sum() > 0: hist /= hist.sum()
                    row.extend(hist.tolist())
                if bool(params["include_profiles"]):
                    preview = _element_values(channel_images[channel], element, housing.source_shape, params, force_count=int(params["profile_samples"]))
                    profile_series.append(preview.astype(np.float32))
                    profile_labels.append(f"{element['id']}.{channel}")
            rows.append(row)

        matrix = np.asarray(rows, dtype=np.float32)
        row_labels = [str(element["id"]) for element in housing.elements]
        vector_values = matrix.reshape(-1)
        vector_names = [f"{row_label}.{feature}" for row_label in row_labels for feature in per_row_names]
        feature_names = per_row_names
        if profile_series:
            series = np.asarray(profile_series, dtype=np.float32)
        else:
            series = np.zeros((0, int(params["profile_samples"])), dtype=np.float32)
        composition = {
            "housing_kind": housing.kind,
            "elements": len(housing.elements),
            "channels": channels,
            "sample_mode": params["sample_mode"],
            "per_element_features": per_row_names,
            "vector_dimension": int(vector_values.size),
        }
        return {
            "vector": FeatureVector(vector_values, vector_names, groups=["spatial_sampling"] * len(vector_names), metadata=composition),
            "matrix": FeatureMatrix(matrix, feature_names, row_labels=row_labels, geometry=housing.geometry, metadata=composition),
            "profiles": ProfileSet(
                x=np.linspace(0.0, 1.0, int(params["profile_samples"]), dtype=np.float32),
                series=series,
                labels=profile_labels,
                geometry=housing.geometry,
                units="normalized_sample_position",
                metadata=composition,
            ),
        }
