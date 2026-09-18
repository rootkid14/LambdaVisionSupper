from __future__ import annotations

import cv2
import numpy as np

from app.services.vision_labs.core import ExecutionContext, FloatParam, IntParam
from app.services.vision_labs.image.types import BinaryMask
from app.services.vision_labs.sampling_geometry.operator import SamplingGeometryOperator
from app.services.vision_labs.sampling_geometry.registry import sampling_operator
from app.services.vision_labs.sampling_geometry.specs import SamplingPort
from app.services.vision_labs.sampling_geometry.types import (
    ContourSet,
    MeasurementTable,
    Polyline,
    ProfileSet,
)


@sampling_operator
class ExtractContours(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.geometry.contours"
    LABEL = "Extract Contours"
    CATEGORY = "Geometry / Shape"
    WORKSPACE = "geometry"
    DESCRIPTION = "Extract external blob contours from a BinaryMask."
    INPUTS = {"mask": SamplingPort("binary_mask")}
    OUTPUTS = {"contours": SamplingPort("contour_set")}
    PARAMETERS = {
        "min_area": FloatParam(
            default=25.0,
            min=0.0,
            max=10000000.0,
            label="Minimum area",
            description="Discard contours smaller than this many pixels squared.",
        ),
        "approx_epsilon": FloatParam(
            default=0.0,
            min=0.0,
            max=20.0,
            label="Approx epsilon",
            description="Douglas-Peucker approximation tolerance in pixels; 0 keeps the original contour.",
        ),
    }
    GUIDE = {
        "overview": "Turns a binary foreground mask into explicit ordered boundary curves.",
        "how_it_works": "OpenCV contour tracing follows each connected external foreground boundary. Small contours can be removed by area and optional Douglas-Peucker approximation reduces point count.",
        "tips": [
            "Clean threshold noise before contour extraction rather than setting an extremely large min_area.",
            "Keep approx_epsilon near zero for metrology; increase it when the contour is only used as a coarse shape descriptor.",
        ],
        "notes": [
            "The contour points remain in source-image pixel coordinates.",
            "This operator does not choose which contour is semantically important.",
        ],
        "visualization": "contour",
    }

    def process(self, inputs, params, context: ExecutionContext):
        mask: BinaryMask = inputs["mask"]
        binary = (np.asarray(mask.data) > 0).astype(np.uint8) * 255
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )
        selected: list[np.ndarray] = []
        for contour in contours:
            if cv2.contourArea(contour) < float(params["min_area"]):
                continue
            epsilon = float(params["approx_epsilon"])
            if epsilon > 0:
                contour = cv2.approxPolyDP(contour, epsilon, True)
            selected.append(contour.reshape(-1, 2).astype(np.float32))
        selected.sort(key=lambda contour: cv2.contourArea(contour.reshape(-1, 1, 2)), reverse=True)
        return {
            "contours": ContourSet(
                contours=selected,
                source_shape=(binary.shape[0], binary.shape[1]),
            )
        }


@sampling_operator
class LargestContour(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.geometry.largest_contour"
    LABEL = "Select Largest Contour"
    CATEGORY = "Geometry / Shape"
    WORKSPACE = "geometry"
    DESCRIPTION = "Select the largest contour and expose it as one Polyline."
    INPUTS = {"contours": SamplingPort("contour_set")}
    OUTPUTS = {"curve": SamplingPort("polyline")}
    PARAMETERS = {}
    GUIDE = {
        "overview": "Reduces a ContourSet to the largest boundary curve.",
        "how_it_works": "The contour with maximum enclosed area is selected. This is useful when the expected foreground object dominates the mask.",
        "tips": [
            "Use contour filtering before this operator if nuisance blobs can be larger than the real object.",
        ],
        "notes": [
            "Largest is a geometric heuristic, not semantic object recognition.",
        ],
        "visualization": "largest_contour",
    }

    def process(self, inputs, params, context: ExecutionContext):
        contours: ContourSet = inputs["contours"]
        if not contours.contours:
            raise ValueError("ContourSet is empty")
        contour = max(
            contours.contours,
            key=lambda item: cv2.contourArea(np.asarray(item).reshape(-1, 1, 2)),
        )
        return {
            "curve": Polyline(
                points=np.asarray(contour, dtype=np.float32).reshape(-1, 2),
                closed=True,
                source_shape=contours.source_shape,
            )
        }


@sampling_operator
class ResampleCurve(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.geometry.resample_curve"
    LABEL = "Arc-Length Resample"
    CATEGORY = "Geometry / Curve"
    WORKSPACE = "geometry"
    DESCRIPTION = "Resample a Polyline at approximately uniform arc-length positions."
    INPUTS = {"curve": SamplingPort("polyline")}
    OUTPUTS = {"curve": SamplingPort("polyline")}
    PARAMETERS = {
        "samples": IntParam(
            default=128,
            min=8,
            max=4096,
            label="Samples",
            description="Number of evenly spaced points along the curve.",
        )
    }
    GUIDE = {
        "overview": "Creates a stable coordinate axis along an irregularly spaced curve.",
        "how_it_works": "Cumulative segment length is used as the independent coordinate; X/Y are linearly interpolated at evenly spaced arc positions.",
        "tips": [
            "Use enough samples to preserve the smallest bend that matters, but avoid thousands of points when downstream features are low dimensional.",
        ],
        "notes": [
            "Uniform arc-length sampling is usually a better basis for profiles than raw contour point order.",
        ],
        "visualization": "resample_curve",
    }

    def process(self, inputs, params, context: ExecutionContext):
        curve: Polyline = inputs["curve"]
        points = np.asarray(curve.points, dtype=np.float64).reshape(-1, 2)
        if len(points) < 2:
            raise ValueError("Polyline must contain at least two points")
        if curve.closed:
            work = np.vstack([points, points[0]])
        else:
            work = points
        segment = np.linalg.norm(np.diff(work, axis=0), axis=1)
        cumulative = np.concatenate([[0.0], np.cumsum(segment)])
        total = float(cumulative[-1])
        if total <= 1e-9:
            raise ValueError("Polyline has zero arc length")
        count = int(params["samples"])
        target = np.linspace(0.0, total, count, endpoint=not curve.closed)
        x = np.interp(target, cumulative, work[:, 0])
        y = np.interp(target, cumulative, work[:, 1])
        return {
            "curve": Polyline(
                points=np.column_stack([x, y]).astype(np.float32),
                closed=curve.closed,
                source_shape=curve.source_shape,
            )
        }


@sampling_operator
class CurvatureProfile(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.geometry.curvature"
    LABEL = "Curvature Profile"
    CATEGORY = "Geometry / Measurement"
    WORKSPACE = "geometry"
    DESCRIPTION = "Estimate local turning curvature along an ordered Polyline."
    INPUTS = {"curve": SamplingPort("polyline")}
    OUTPUTS = {"profile": SamplingPort("profile_set")}
    PARAMETERS = {
        "smooth_window": IntParam(
            default=5,
            min=1,
            max=101,
            odd=True,
            label="Smooth window",
            description="Odd moving-average window applied to the curvature signal.",
        )
    }
    GUIDE = {
        "overview": "Converts an ordered curve into a one-dimensional bend/curvature signal.",
        "how_it_works": "Neighboring segment directions are differentiated with respect to arc length. The absolute turning rate is then optionally smoothed.",
        "tips": [
            "Resample the curve uniformly before curvature measurement.",
            "Increase smoothing only enough to suppress pixel stair-step noise.",
        ],
        "notes": [
            "Curvature is sensitive to contour noise and point spacing.",
        ],
        "visualization": "curve_profile",
    }

    def process(self, inputs, params, context: ExecutionContext):
        curve: Polyline = inputs["curve"]
        points = np.asarray(curve.points, dtype=np.float64).reshape(-1, 2)
        if len(points) < 5:
            raise ValueError("Curvature needs at least five curve points")
        if curve.closed:
            prev = np.roll(points, 1, axis=0)
            nxt = np.roll(points, -1, axis=0)
        else:
            prev = np.vstack([points[0], points[:-1]])
            nxt = np.vstack([points[1:], points[-1]])
        tangent = nxt - prev
        angle = np.unwrap(np.arctan2(tangent[:, 1], tangent[:, 0]))
        ds = np.linalg.norm(np.diff(points, axis=0), axis=1)
        s = np.concatenate([[0.0], np.cumsum(ds)])
        gradient = np.gradient(angle, s, edge_order=1)
        curvature = np.abs(np.nan_to_num(gradient))
        window = int(params["smooth_window"])
        if window > 1:
            kernel = np.ones(window, dtype=np.float64) / float(window)
            curvature = np.convolve(curvature, kernel, mode="same")
        geometry = {
            "kind": "polyline",
            "points": points.astype(float).tolist(),
            "source_shape": list(curve.source_shape) if curve.source_shape else None,
        }
        return {
            "profile": ProfileSet(
                x=s.astype(np.float32),
                series=curvature.astype(np.float32)[None, :],
                labels=["curvature"],
                geometry=geometry,
                units="arc_length_px",
            )
        }


@sampling_operator
class ContourMeasurements(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.geometry.contour_measurements"
    LABEL = "Contour Measurements"
    CATEGORY = "Geometry / Measurement"
    WORKSPACE = "geometry"
    DESCRIPTION = "Compute area, perimeter and bounding-box measurements for each contour."
    INPUTS = {"contours": SamplingPort("contour_set")}
    OUTPUTS = {"table": SamplingPort("measurement_table")}
    PARAMETERS = {}
    GUIDE = {
        "overview": "Turns boundary geometry into explicit numeric measurements.",
        "how_it_works": "For each contour it computes area, perimeter and axis-aligned bounding rectangle using standard planar geometry.",
        "tips": [
            "Filter tiny contours before measuring to avoid long tables dominated by threshold noise.",
        ],
        "notes": [
            "All values are in pixel units in v1; physical calibration belongs to a later geometry/calibration layer.",
        ],
        "visualization": "measurement_table",
    }

    def process(self, inputs, params, context: ExecutionContext):
        contours: ContourSet = inputs["contours"]
        rows = []
        for index, contour in enumerate(contours.contours):
            pts = np.asarray(contour, dtype=np.float32).reshape(-1, 1, 2)
            x, y, w, h = cv2.boundingRect(pts)
            rows.append(
                {
                    "index": index,
                    "area_px2": round(float(cv2.contourArea(pts)), 4),
                    "perimeter_px": round(float(cv2.arcLength(pts, True)), 4),
                    "bbox_x": int(x),
                    "bbox_y": int(y),
                    "bbox_w": int(w),
                    "bbox_h": int(h),
                }
            )
        return {
            "table": MeasurementTable(
                columns=[
                    "index",
                    "area_px2",
                    "perimeter_px",
                    "bbox_x",
                    "bbox_y",
                    "bbox_w",
                    "bbox_h",
                ],
                rows=rows,
            )
        }
