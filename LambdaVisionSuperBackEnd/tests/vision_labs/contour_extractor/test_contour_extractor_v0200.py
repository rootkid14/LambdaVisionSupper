import cv2
import numpy as np

from app.services.vision_labs.image.session import PreviewEncoder
from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.contour_extractor.fourier import contour_fourier_descriptor
from app.services.vision_labs.contour_extractor.runtime import ContourExtractorRuntime
from app.services.vision_labs.contour_extractor.stage_registry import stage_catalog


def frame():
    image = np.zeros((260, 340, 3), dtype=np.uint8)
    cv2.rectangle(image, (20, 30), (110, 150), (255, 255, 255), 3)
    cv2.rectangle(image, (150, 35), (245, 155), (255, 255, 255), 3)
    for y in range(5, 250, 9):
        for x in range(5, 330, 11):
            image[y, x] = 255
    return ImageFrame(image, color_space=ColorSpace.BGR)


def test_preview_mask_and_memory_gate_are_safe():
    result = ContourExtractorRuntime({"source": {"early_filter": {"max_retained": 80}}}).run(frame())
    assert len(result.store.contours) <= 80
    payload, mime = PreviewEncoder.encode(result.sources["edge_map"])
    assert payload and mime == "image/png"


def test_stage_catalog_is_extensible_and_has_fourier_shape():
    kinds = {item["kind"] for item in stage_catalog()}
    assert {"metric_filter", "largest_n", "region_filter", "simplify", "fourier_shape_filter"} <= kinds


def test_fourier_descriptor_can_compare_similar_shapes():
    a = np.array([[0,0],[100,0],[100,50],[0,50]], np.float32)
    b = a * 2 + np.array([40,80], np.float32)
    da = contour_fourier_descriptor(a, harmonics=8)
    db = contour_fourier_descriptor(b, harmonics=8)
    assert np.linalg.norm(da - db) < 1e-3
