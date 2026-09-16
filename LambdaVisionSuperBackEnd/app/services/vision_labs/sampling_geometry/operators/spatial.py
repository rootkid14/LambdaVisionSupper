from __future__ import annotations

import math

import cv2
import numpy as np

from app.services.vision_labs.core import ExecutionContext, EnumParam, FloatParam, IntParam
from app.services.vision_labs.image.types import ImageFrame
from app.services.vision_labs.sampling_geometry.operator import SamplingGeometryOperator
from app.services.vision_labs.sampling_geometry.registry import sampling_operator
from app.services.vision_labs.sampling_geometry.specs import SamplingPort
from app.services.vision_labs.sampling_geometry.types import FeatureMatrix, ProfileSet
from app.services.vision_labs.sampling_geometry.operators.common import image_channel, image_to_bgr, sample_line


_CHANNELS = ["gray", "r", "g", "b", "h", "s", "v"]


@sampling_operator
class AxisRays(SamplingGeometryOperator):
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
