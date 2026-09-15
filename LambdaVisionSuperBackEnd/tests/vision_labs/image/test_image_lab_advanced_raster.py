import numpy as np

from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.registry import IMAGE_OPERATOR_REGISTRY
from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame


def _frame() -> ImageFrame:
    image = np.zeros((96, 128), dtype=np.uint8)
    image[30:66, 15:113] = 180
    image[42:54, 20:108] = 255
    return ImageFrame(image, color_space=ColorSpace.GRAY)


def _mask() -> BinaryMask:
    data = np.zeros((96, 128), dtype=np.uint8)
    data[20:76, 30:98] = 255
    return BinaryMask(data)


def test_advanced_pack_is_registered():
    load_builtin_operators()
    ids = {definition.operator_id for definition in IMAGE_OPERATOR_REGISTRY.list()}

    expected = {
        "image.illumination.shading_correction",
        "image.illumination.homomorphic",
        "image.illumination.single_scale_retinex",
        "image.filter.guided",
        "image.filter.anisotropic_diffusion",
        "image.structure.hessian_ridge",
        "image.structure.frangi_ridge",
        "image.distance.transform",
        "image.skeleton.zhang_suen",
        "image.reconstruction.open",
        "image.threshold.sauvola",
        "image.frequency.spectrum",
        "image.frequency.filter",
        "image.texture.gabor_bank_max",
        "image.texture.local_entropy",
        "image.multiscale.dog",
        "image.segment.region_grow",
        "image.segment.grabcut_rect",
        "image.restore.wiener",
    }
    assert expected.issubset(ids)
    assert len(ids) >= 70


def test_comparison_multi_image_operators_hidden_from_image_lab_catalog():
    load_builtin_operators()
    manifest_ids = {
        item["id"]
        for item in IMAGE_OPERATOR_REGISTRY.manifests()
    }

    hidden = {
        "image.arithmetic.absdiff",
        "image.arithmetic.weighted_blend",
        "image.arithmetic.bitwise_and",
    }
    assert manifest_ids.isdisjoint(hidden)

    for operator_id in hidden:
        assert IMAGE_OPERATOR_REGISTRY.get(operator_id).operator_id == operator_id


def test_sauvola_returns_binary_mask():
    load_builtin_operators()
    definition = IMAGE_OPERATOR_REGISTRY.get("image.threshold.sauvola")
    operator = definition.operator_class()
    params = definition.operator_class.resolve_parameters({})
    result = operator.process({"image": _frame()}, params, None)["mask"]
    assert result.data.shape == (96, 128)
    assert result.data.dtype == np.uint8
    assert set(np.unique(result.data)).issubset({0, 255})


def test_distance_transform_returns_grayscale_image():
    load_builtin_operators()
    definition = IMAGE_OPERATOR_REGISTRY.get("image.distance.transform")
    operator = definition.operator_class()
    params = definition.operator_class.resolve_parameters({})
    result = operator.process({"mask": _mask()}, params, None)["image"]
    assert result.data.shape == (96, 128)
    assert result.data.dtype == np.uint8
    assert result.color_space == ColorSpace.GRAY
    assert result.data.max() > 0


def test_zhang_suen_is_binary_and_thinner_than_source():
    load_builtin_operators()
    definition = IMAGE_OPERATOR_REGISTRY.get("image.skeleton.zhang_suen")
    operator = definition.operator_class()
    params = definition.operator_class.resolve_parameters({})
    source = _mask()
    result = operator.process({"mask": source}, params, None)["mask"]
    assert set(np.unique(result.data)).issubset({0, 255})
    assert np.count_nonzero(result.data) < np.count_nonzero(source.data)


def test_frangi_and_fft_spectrum_smoke():
    load_builtin_operators()
    frame = _frame()

    for operator_id in (
        "image.structure.frangi_ridge",
        "image.frequency.spectrum",
    ):
        definition = IMAGE_OPERATOR_REGISTRY.get(operator_id)
        operator = definition.operator_class()
        params = definition.operator_class.resolve_parameters({})
        result = operator.process({"image": frame}, params, None)["image"]
        assert result.data.shape == frame.data.shape
        assert result.data.dtype == np.uint8
