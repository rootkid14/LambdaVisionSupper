import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.program import (
    SamplingProgramDefinition,
    sampling_program_sample_signature,
)
from app.services.vision_labs.sampling_geometry.program_runtime import SamplingProgramRuntime
from app.services.vision_labs.sampling_geometry.session import SamplingGeometrySession


def _frame():
    image = np.zeros((80, 120, 3), dtype=np.uint8)
    image[..., 0] = np.tile(np.arange(120, dtype=np.uint8), (80, 1))
    image[..., 1] = 100
    image[..., 2] = np.tile(np.arange(80, dtype=np.uint8)[:, None], (1, 120))
    return ImageFrame(image, ColorSpace.BGR)


def _program(local_layout="matrix", matrix_axis="patch_rows", vector_order="patch_major"):
    return SamplingProgramDefinition(**{
        "global_domain": {
            "methods": [
                {
                    "id": "hist",
                    "kind": "histogram",
                    "channels": ["gray"],
                    "measures": ["histogram"],
                    "histogram_bins": 8,
                }
            ]
        },
        "local_domain": {
            "grid": {"rows": 2, "cols": 3},
            "methods": [
                {
                    "id": "stats",
                    "kind": "statistics",
                    "channels": ["gray", "r"],
                    "measures": ["mean", "std"],
                },
                {
                    "id": "cross",
                    "kind": "cross",
                    "channels": ["gray"],
                    "measures": ["profile"],
                    "placement": {"mode": "center"},
                    "sample_count": 6,
                    "parameters": {"length_ratio": 0.8},
                },
            ],
        },
        "output_shape": {
            "local_layout": local_layout,
            "local_matrix_axis": matrix_axis,
            "local_vector_order": vector_order,
        },
    })


def test_v0600_sampling_program_never_materializes_tensor_depth():
    run = SamplingProgramRuntime(_program()).run(_frame())
    assert len(run.local_data.shape) == 2
    assert run.local_data.layout == "matrix"
    assert run.local_data.metadata["rows_semantic"] == "patches"
    assert run.local_data.metadata["columns_semantic"] == "features"
    assert "feature_depth" not in run.local_data.metadata


def test_formulation_reuses_one_sample_for_multiple_shapes():
    runtime = SamplingProgramRuntime(_program())
    sample = runtime.sample(_frame())
    matrix = runtime.formulate(sample, _program(local_layout="matrix").output_shape)
    vector = runtime.formulate(sample, _program(local_layout="vector").output_shape)
    columns = runtime.formulate(sample, _program(local_layout="matrix", matrix_axis="patch_columns").output_shape)

    assert matrix.local_data.shape[0] == 6
    assert len(vector.local_data.shape) == 1
    assert vector.local_data.shape[0] == np.asarray(matrix.local_data.values).size
    assert columns.local_data.shape == matrix.local_data.shape[::-1]
    assert matrix.method_summaries is sample.method_summaries


def test_formulation_changes_do_not_change_sampling_signature():
    a = _program(local_layout="matrix", matrix_axis="patch_rows")
    b = _program(local_layout="vector", vector_order="feature_major")
    assert sampling_program_sample_signature(a) == sampling_program_sample_signature(b)
    b.local_domain.grid.cols = 4
    assert sampling_program_sample_signature(a) != sampling_program_sample_signature(b)


def test_session_cache_rejects_changed_sampling_definition():
    session = SamplingGeometrySession()
    program = _program()
    sample = SamplingProgramRuntime(program).sample(_frame())
    signature = sampling_program_sample_signature(program)
    session.set_program_sample(sample, signature)
    assert session.get_program_sample(signature) is sample

    changed = _program()
    changed.local_domain.grid.rows = 3
    try:
        session.get_program_sample(sampling_program_sample_signature(changed))
    except RuntimeError as exc:
        assert "Run Program again" in str(exc)
    else:
        raise AssertionError("Expected stale sample cache to be rejected")


def test_vector_metadata_explains_patch_and_feature_structure():
    run = SamplingProgramRuntime(_program(local_layout="vector", vector_order="patch_major")).run(_frame())
    metadata = run.local_data.metadata
    assert metadata["representation"] == "vector"
    assert metadata["patch_count"] == 6
    assert metadata["features_per_patch"] > 0
    assert metadata["feature_groups"]
    assert metadata["item_groups"]
