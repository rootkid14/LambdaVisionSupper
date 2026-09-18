import cv2
import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.program import (
    LegacySamplingProgramDefinition,
    sampling_program_catalog,
)
from app.services.vision_labs.sampling_geometry.program_runtime import SamplingProgramRuntime


def _frame():
    image = np.zeros((120, 180, 3), dtype=np.uint8)
    image[..., 1] = np.tile(np.arange(180, dtype=np.uint8), (120, 1))
    cv2.circle(image, (90, 60), 28, (220, 80, 40), -1)
    return ImageFrame(image, ColorSpace.BGR)


def _program(order="patch_major", layout="spatial_tensor"):
    return LegacySamplingProgramDefinition(**{
        "global_domain": {
            "methods": [
                {
                    "id": "hist",
                    "kind": "histogram",
                    "channels": ["gray"],
                    "measures": ["histogram"],
                    "histogram_bins": 8,
                },
                {
                    "id": "rays",
                    "kind": "rays",
                    "channels": ["gray", "h"],
                    "measures": ["profile", "mean", "std"],
                    "sampling_mode": "count",
                    "sample_count": 16,
                    "parameters": {"axis": "both", "ray_count": 2},
                },
            ]
        },
        "local_domain": {
            "grid": {"rows": 2, "cols": 3},
            "methods": [
                {
                    "id": "cross",
                    "kind": "cross",
                    "channels": ["gray"],
                    "measures": ["profile", "mean"],
                    "placement": {"mode": "auto_grid", "rows": 2, "cols": 2},
                    "sample_count": 8,
                    "parameters": {"length_ratio": 0.8},
                },
                {
                    "id": "stats",
                    "kind": "statistics",
                    "channels": ["r", "g", "b"],
                    "measures": ["mean", "std"],
                },
            ],
        },
        "output_shape": {
            "local_layout": layout,
            "local_order": order,
        },
    })


def test_catalog_excludes_frequency_domain_methods():
    kinds = {item["kind"] for item in sampling_program_catalog()}
    assert kinds == {"histogram", "statistics", "rays", "cross", "rings"}
    assert "fft" not in kinds


def test_global_local_sampling_program_materializes_stable_shapes():
    run = SamplingProgramRuntime(_program()).run(_frame())
    assert run.global_data.shape[0] > 8
    assert run.local_data.shape[:2] == (2, 3)
    assert run.local_data.shape[2] > 0
    assert len(run.local_patch_blocks) == 6
    assert len(run.local_patch_blocks[0].blocks) > 0
    assert run.combined_data.shape[0] == run.global_data.shape[0] + np.asarray(run.local_data.values).size


def test_feature_major_spatial_tensor_moves_feature_depth_first():
    run = SamplingProgramRuntime(_program(order="feature_major")).run(_frame())
    assert run.local_data.shape[1:] == (2, 3)
    assert run.local_data.shape[0] > 0
    assert run.local_data.metadata["order"] == "feature_major"


def test_patch_matrix_shape_is_patch_by_feature_for_patch_major():
    run = SamplingProgramRuntime(_program(layout="patch_matrix")).run(_frame())
    assert run.local_data.shape[0] == 6
    assert run.local_data.shape[1] > 0


def test_auto_grid_cross_creates_repeated_local_sampling_geometry():
    run = SamplingProgramRuntime(_program()).run(_frame())
    summary = run.method_summaries["local:cross"]
    assert summary["geometry"]["kind"] == "crosses"
    assert len(summary["geometry"]["elements"]) == 4
