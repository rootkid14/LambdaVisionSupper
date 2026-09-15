import numpy as np

from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.registry import IMAGE_OPERATOR_REGISTRY
from app.services.vision_labs.image.types import ColorSpace, ImageFrame


def test_basic_family_registry_has_representative_operators():
    load_builtin_operators()
    ids = {item.operator_id for item in IMAGE_OPERATOR_REGISTRY.list()}

    expected = {
        "image.color.bgr_to_hsv",
        "image.enhance.clahe",
        "image.filter.median",
        "image.sharpen.unsharp",
        "image.threshold.otsu",
        "image.edge.canny",
        "image.morphology.erode",
        "image.morphology.remove_small",
        "image.transform.rotate",
        "image.arithmetic.add_scalar",
    }
    assert expected.issubset(ids)
    assert len(ids) >= 35


def test_canny_produces_binary_mask():
    load_builtin_operators()
    definition = IMAGE_OPERATOR_REGISTRY.get("image.edge.canny")
    op = definition.operator_class()
    image = np.zeros((64, 64), dtype=np.uint8)
    image[16:48, 16:48] = 255
    frame = ImageFrame(image, color_space=ColorSpace.GRAY)
    params = definition.operator_class.resolve_parameters({})
    result = op.process({"image": frame}, params, None)
    mask = result["mask"]
    assert mask.data.shape == image.shape
    assert mask.data.dtype == np.uint8


def test_crop_normalized_changes_shape():
    load_builtin_operators()
    definition = IMAGE_OPERATOR_REGISTRY.get("image.transform.crop_normalized")
    op = definition.operator_class()
    frame = ImageFrame(np.zeros((100, 200, 3), dtype=np.uint8))
    params = definition.operator_class.resolve_parameters(
        {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5}
    )
    result = op.process({"image": frame}, params, None)["image"]
    assert result.shape == (50, 100, 3)
