from __future__ import annotations

import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.operators import load_sampling_geometry_operators
from app.services.vision_labs.sampling_geometry.pipeline import SamplingPipelineDefinition
from app.services.vision_labs.sampling_geometry.registry import SAMPLING_OPERATOR_REGISTRY
from app.services.vision_labs.sampling_geometry.runtime import SamplingGeometryRuntime
from app.services.vision_labs.sampling_geometry.serialization import artifact_to_json
from app.services.vision_labs.sampling_geometry.source_board import resolve_pipeline_inputs, resolve_source_board


def _image() -> ImageFrame:
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    image[35:105, 50:140] = (40, 180, 240)
    image[125:220, 170:295] = (220, 90, 70)
    return ImageFrame(data=image, color_space=ColorSpace.BGR)


def test_source_board_is_shared_and_builds_master_contours():
    board = resolve_source_board(
        _image(),
        {"canny_low": 25, "canny_high": 90, "blur_kernel": 3},
    )
    assert set(board.sources) >= {
        "raw_image",
        "inspected_image",
        "geometry_raster",
        "edge_map",
        "contour_image",
        "master_contours",
    }
    assert board.manifest["geometry_contour_count"] >= 2
    payload = artifact_to_json(board.sources["master_contours"])
    assert payload["type"] == "contour_set"
    assert payload["count"] == len(payload["metrics"])
    assert {"area_px2", "perimeter_px", "circularity", "solidity"} <= set(payload["metrics"][0])


def test_geometry_filter_preserves_master_contour_identity():
    load_sampling_geometry_operators()
    board = resolve_source_board(_image(), {"canny_low": 25, "canny_high": 90, "blur_kernel": 3})
    definition = SamplingPipelineDefinition(
        version=2,
        workspace="geometry",
        nodes=[{
            "id": "filter",
            "operator_id": "sampling.geometry.contour_filter",
            "parameters": {"min_perimeter": 20.0},
            "enabled": True,
        }],
        connections=[],
        inputs={"primary__filter__contours": {"node_id": "filter", "port": "contours"}},
        input_sources={"primary__filter__contours": "master_contours"},
        outputs={"contours": {"node_id": "filter", "port": "contours"}},
    )
    runtime = SamplingGeometryRuntime(definition)
    result = runtime.run(resolve_pipeline_inputs(definition, board.sources))
    output = result.outputs["contours"]
    assert set(output.ids).issubset(set(board.sources["master_contours"].ids))
    assert output.metadata["operation"] == "contour_filter"


def test_spatial_housing_is_separate_from_data_extraction():
    load_sampling_geometry_operators()
    board = resolve_source_board(_image(), {})
    definition = SamplingPipelineDefinition(
        version=2,
        workspace="spatial",
        nodes=[
            {
                "id": "housing",
                "operator_id": "sampling.spatial.housing.axis_rays",
                "parameters": {"ray_count": 3},
                "enabled": True,
            },
            {
                "id": "extract",
                "operator_id": "sampling.spatial.data_extractor",
                "parameters": {
                    "sample_gray": True,
                    "sample_r": True,
                    "include_histogram": True,
                    "histogram_bins": 4,
                    "sample_count": 64,
                    "profile_samples": 48,
                },
                "enabled": True,
            },
        ],
        connections=[{
            "source": {"node_id": "housing", "port": "housing"},
            "target": {"node_id": "extract", "port": "housing"},
        }],
        inputs={
            "primary__housing__image": {"node_id": "housing", "port": "image"},
            "ref__extract__image": {"node_id": "extract", "port": "image"},
        },
        input_sources={
            "primary__housing__image": "inspected_image",
            "ref__extract__image": "inspected_image",
        },
        outputs={
            "vector": {"node_id": "extract", "port": "vector"},
            "matrix": {"node_id": "extract", "port": "matrix"},
            "profiles": {"node_id": "extract", "port": "profiles"},
        },
    )
    runtime = SamplingGeometryRuntime(definition)
    result = runtime.run(resolve_pipeline_inputs(definition, board.sources))
    assert result.outputs["matrix"].shape[0] == 3
    assert result.outputs["vector"].shape[0] == result.outputs["matrix"].values.size
    assert result.outputs["profiles"].shape == (6, 48)
    names = result.outputs["vector"].names
    assert any(name.startswith("ray_0.gray") for name in names)
    assert any(name.startswith("ray_0.r") for name in names)


def test_fft_artifact_contains_visual_diagnostics():
    load_sampling_geometry_operators()
    board = resolve_source_board(_image(), {})
    definition = SamplingPipelineDefinition(
        version=2,
        workspace="spectral",
        nodes=[{
            "id": "fft",
            "operator_id": "sampling.spectral.fft2d",
            "parameters": {},
            "enabled": True,
        }],
        connections=[],
        inputs={"primary__fft__image": {"node_id": "fft", "port": "image"}},
        input_sources={"primary__fft__image": "contour_image"},
        outputs={"spectrum": {"node_id": "fft", "port": "spectrum"}},
    )
    runtime = SamplingGeometryRuntime(definition)
    result = runtime.run(resolve_pipeline_inputs(definition, board.sources))
    metadata = result.outputs["spectrum"].metadata
    assert len(metadata["radial_energy"]) == 32
    assert len(metadata["angular_energy"]) == 36
    assert 0 <= metadata["dominant_radial_band"] < 32


def test_v2_catalog_focuses_on_contour_selection_and_sampling_housing():
    load_sampling_geometry_operators()
    manifests = SAMPLING_OPERATOR_REGISTRY.manifests()
    ids = {item["id"] for item in manifests}
    assert "sampling.geometry.contour_filter" in ids
    assert "sampling.spatial.housing.axis_rays" in ids
    assert "sampling.spatial.data_extractor" in ids
    assert "sampling.geometry.contours" not in ids  # source board owns initial contour extraction
    assert "sampling.spatial.axis_rays" not in ids  # legacy combined housing+sampling remains loadable but hidden
