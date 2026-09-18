from __future__ import annotations

import cv2
import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.contour_extractor.runtime import ContourExtractorRuntime


def _noisy_image() -> ImageFrame:
    image = np.zeros((280, 360, 3), dtype=np.uint8)
    # Two meaningful closed shapes.
    cv2.rectangle(image, (35, 35), (150, 145), (255, 255, 255), 3)
    cv2.circle(image, (255, 175), 65, (255, 255, 255), 3)
    # Many tiny noise marks that should be rejected before ContourStore retention.
    for y in range(10, 270, 12):
        for x in range(10, 350, 13):
            image[y, x] = (255, 255, 255)
    return ImageFrame(data=image, color_space=ColorSpace.BGR)


def test_early_filter_rejects_junk_before_store():
    definition = {
        "version": 1,
        "source": {
            "source_mode": "canny",
            "canny_low": 30,
            "canny_high": 90,
            "blur_kernel": 3,
            "early_filter": {
                "min_area": 30,
                "min_perimeter": 20,
                "min_bbox_width": 4,
                "min_bbox_height": 4,
                "min_points": 4,
                "max_retained": 200,
            },
        },
        "stages": [],
    }
    result = ContourExtractorRuntime(definition).run(_noisy_image())
    summary = result.store.summary("final")
    assert summary["candidate_count"] > summary["retained_geometry_count"]
    assert summary["early_rejected_count"] > 0
    assert summary["retained_geometry_count"] <= 200
    # Filter selections retain IDs; they do not clone another contour geometry set.
    assert result.store.selection("source") == result.store.selection("final")
    assert len(result.store.contours) == summary["retained_geometry_count"]


def test_filter_funnel_changes_ids_without_cloning_geometry():
    definition = {
        "version": 1,
        "source": {
            "source_mode": "canny",
            "canny_low": 30,
            "canny_high": 90,
            "blur_kernel": 3,
            "early_filter": {"min_area": 10, "min_perimeter": 10, "max_retained": 100},
        },
        "stages": [
            {"id": "area", "kind": "metric_filter", "parameters": {"min_area": 100}, "enabled": True},
            {"id": "largest", "kind": "largest_n", "parameters": {"count": 2, "metric": "area"}, "enabled": True},
        ],
    }
    result = ContourExtractorRuntime(definition).run(_noisy_image())
    stored = len(result.store.contours)
    assert len(result.store.selection("area")) <= stored
    assert len(result.store.selection("largest")) <= 2
    assert len(result.store.contours) == stored
    final = result.store.materialize("final")
    assert len(final.contours) == len(result.store.selection("final"))
