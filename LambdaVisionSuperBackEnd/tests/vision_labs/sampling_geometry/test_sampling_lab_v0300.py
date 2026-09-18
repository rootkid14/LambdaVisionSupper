from __future__ import annotations

import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.operators import load_sampling_geometry_operators
from app.services.vision_labs.sampling_geometry.pipeline import SamplingPipelineDefinition
from app.services.vision_labs.sampling_geometry.runtime import SamplingGeometryRuntime
from app.services.vision_labs.sampling_geometry.source_board import resolve_pipeline_inputs, resolve_source_board


def _image() -> ImageFrame:
    y, x = np.mgrid[0:180, 0:240]
    gray = ((x * 3 + y * 5) % 256).astype(np.uint8)
    bgr = np.dstack([gray, np.roll(gray, 10, axis=1), np.roll(gray, 15, axis=0)])
    return ImageFrame(data=bgr, color_space=ColorSpace.BGR)


def test_sampling_source_board_does_not_allocate_geometry_when_disabled():
    board = resolve_source_board(_image(), {"enable_geometry": False})
    assert set(board.sources) == {"raw_image", "inspected_image"}
    assert "master_contours" not in board.sources


def test_sampling_unit_emits_semantic_blocks_and_composed_layout():
    load_sampling_geometry_operators()
    board = resolve_source_board(_image(), {"enable_geometry": False})
    definition = SamplingPipelineDefinition(
        version=3,
        workspace="spatial",
        nodes=[
            {"id": "housing", "operator_id": "sampling.spatial.housing.axis_rays", "parameters": {"ray_count": 2}, "enabled": True},
            {"id": "extract", "operator_id": "sampling.spatial.data_extractor", "parameters": {
                "sample_gray": True,
                "sample_h": True,
                "include_mean": True,
                "include_std": True,
                "include_histogram": True,
                "histogram_bins": 8,
                "include_profiles": True,
                "profile_samples": 32,
                "layout_mode": "stack_rows",
                "order_mode": "channel_major",
            }, "enabled": True},
        ],
        connections=[{"source": {"node_id": "housing", "port": "housing"}, "target": {"node_id": "extract", "port": "housing"}}],
        inputs={
            "primary__housing__image": {"node_id": "housing", "port": "image"},
            "ref__extract__image": {"node_id": "extract", "port": "image"},
        },
        input_sources={
            "primary__housing__image": "inspected_image",
            "ref__extract__image": "inspected_image",
        },
        outputs={
            "blocks": {"node_id": "extract", "port": "blocks"},
            "data": {"node_id": "extract", "port": "data"},
        },
        source_board={"enable_geometry": False},
    )
    result = SamplingGeometryRuntime(definition).run(resolve_pipeline_inputs(definition, board.sources))
    blocks = result.outputs["blocks"]
    data = result.outputs["data"]
    assert len(blocks.blocks) > 0
    assert any(block.channel == "gray" for block in blocks.blocks)
    assert any(block.channel == "h" for block in blocks.blocks)
    assert all(block.label and block.shape for block in blocks.blocks)
    assert data.layout == "stack_rows"
    assert len(data.shape) == 2
    assert data.metadata["block_count"] == len(blocks.blocks)
