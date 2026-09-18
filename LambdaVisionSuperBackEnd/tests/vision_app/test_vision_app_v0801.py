from __future__ import annotations

import cv2
import numpy as np

from app.services.vision_app.models import MasterRoi, NormalizedRect, RoiSearchConfig
from app.services.vision_app.roi_search import locate_blur_template


def _roi() -> MasterRoi:
    return MasterRoi(
        roi_id="r1",
        name="Station 1",
        rect=NormalizedRect(x=60 / 220, y=50 / 160, w=45 / 220, h=45 / 160),
        search=RoiSearchConfig(method="blur_template", blur_kernel=5, template_threshold=0.4),
    )


def test_low_texture_template_uses_context_and_refines_to_object_edge():
    master = np.zeros((160, 220, 3), dtype=np.uint8)
    cv2.rectangle(master, (60, 50), (105, 95), (255, 255, 255), -1)
    test = np.zeros_like(master)
    cv2.rectangle(test, (72, 58), (117, 103), (255, 255, 255), -1)

    found = locate_blur_template(_roi(), master, test)

    assert found.found
    assert abs(found.rect.x * 220 - 72) <= 2
    assert abs(found.rect.y * 160 - 58) <= 2
    assert "refined on grayscale" in found.message


def test_textured_template_still_localizes_after_coarse_to_fine_refine():
    master = np.zeros((160, 220, 3), dtype=np.uint8)
    patch = master[50:95, 60:105]
    patch[:] = (30, 30, 30)
    cv2.line(patch, (4, 5), (39, 35), (230, 230, 230), 3)
    cv2.circle(patch, (30, 12), 5, (120, 120, 120), -1)

    test = np.zeros_like(master)
    test[58:103, 72:117] = patch

    found = locate_blur_template(_roi(), master, test)

    assert found.found
    assert abs(found.rect.x * 220 - 72) <= 1
    assert abs(found.rect.y * 160 - 58) <= 1
