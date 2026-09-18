import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.operators import load_sampling_geometry_operators
from app.services.vision_labs.sampling_geometry.registry import SAMPLING_OPERATOR_REGISTRY
from app.services.vision_labs.core import ExecutionContext


def image():
    y, x = np.indices((192, 256))
    gray = ((np.sin(x / 5.0) + 1.0) * 90 + (np.sin(y / 17.0) + 1.0) * 30).astype(np.uint8)
    bgr = np.repeat(gray[..., None], 3, axis=2)
    return ImageFrame(bgr, color_space=ColorSpace.BGR)


def op(operator_id):
    load_sampling_geometry_operators()
    definition = SAMPLING_OPERATOR_REGISTRY.get(operator_id)
    return definition.operator_class()


def test_cross_grid_has_many_centers_and_rays():
    operator = op("sampling.spatial.housing.cross")
    out = operator.process({"image": image()}, {"center_rows": 2, "center_cols": 3, "margin": .1, "length": .2}, ExecutionContext())
    housing = out["housing"]
    assert len(housing.metadata["centers"]) == 6
    assert len(housing.elements) == 12


def test_ring_grid_has_multiple_centers():
    operator = op("sampling.spatial.housing.rings")
    out = operator.process({"image": image()}, {"center_rows": 2, "center_cols": 2, "margin": .15, "rings": 3, "inner_radius": .02, "outer_radius": .08}, ExecutionContext())
    housing = out["housing"]
    assert len(housing.metadata["centers"]) == 4
    assert len(housing.elements) == 12


def test_local_fft_outputs_spatial_energy_matrix():
    operator = op("sampling.spectral.local_fft_energy")
    out = operator.process({"image": image()}, {"channel": "gray", "rows": 4, "cols": 5, "band_low": .1, "band_high": .5, "window": "hann", "normalize": True}, ExecutionContext())
    matrix = out["energy_map"]
    assert matrix.values.shape == (4, 5)
    assert float(matrix.values.max()) <= 1.0001
