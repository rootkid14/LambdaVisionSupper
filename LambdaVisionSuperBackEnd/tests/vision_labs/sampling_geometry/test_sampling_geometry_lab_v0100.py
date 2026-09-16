from datetime import datetime, timezone

import numpy as np

from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.operators import load_sampling_geometry_operators
from app.services.vision_labs.sampling_geometry.pipeline import SamplingPipelineDefinition
from app.services.vision_labs.sampling_geometry.registry import SAMPLING_OPERATOR_REGISTRY
from app.services.vision_labs.sampling_geometry.runtime import SamplingGeometryRuntime
from app.services.vision_labs.service.models import (
    LabServiceDefinition,
    LabServiceOutputBinding,
    LabServicePort,
)
from app.services.vision_labs.service.runtime import LabServiceRuntime


def _image():
    image = np.zeros((128, 160, 3), dtype=np.uint8)
    image[..., 0] = np.arange(160, dtype=np.uint8)[None, :]
    image[..., 1] = 120
    image[..., 2] = 200
    return ImageFrame(image, color_space=ColorSpace.BGR)


def test_operator_catalog_has_three_workspaces():
    load_sampling_geometry_operators()
    assert len(SAMPLING_OPERATOR_REGISTRY.manifests("geometry")) >= 5
    assert len(SAMPLING_OPERATOR_REGISTRY.manifests("spatial")) >= 4
    assert len(SAMPLING_OPERATOR_REGISTRY.manifests("spectral")) >= 5


def test_geometry_pipeline_produces_curvature_profile():
    load_sampling_geometry_operators()
    mask = np.zeros((128, 160), dtype=np.uint8)
    mask[30:95, 40:120] = 255
    pipeline = SamplingPipelineDefinition(
        workspace="geometry",
        nodes=[
            {"id": "c", "operator_id": "sampling.geometry.contours", "parameters": {"min_area": 10.0, "approx_epsilon": 0.0}},
            {"id": "l", "operator_id": "sampling.geometry.largest_contour", "parameters": {}},
            {"id": "r", "operator_id": "sampling.geometry.resample_curve", "parameters": {"samples": 64}},
            {"id": "k", "operator_id": "sampling.geometry.curvature", "parameters": {"smooth_window": 5}},
        ],
        connections=[
            {"source": {"node_id": "c", "port": "contours"}, "target": {"node_id": "l", "port": "contours"}},
            {"source": {"node_id": "l", "port": "curve"}, "target": {"node_id": "r", "port": "curve"}},
            {"source": {"node_id": "r", "port": "curve"}, "target": {"node_id": "k", "port": "curve"}},
        ],
        inputs={"input": {"node_id": "c", "port": "mask"}},
        outputs={"result": {"node_id": "k", "port": "profile"}},
    )
    result = SamplingGeometryRuntime(pipeline).run({"input": BinaryMask(data=mask)})
    assert result.outputs["result"].shape == (1, 64)


def test_spatial_ray_profiles_and_patch_features():
    load_sampling_geometry_operators()
    rays = SamplingPipelineDefinition(
        workspace="spatial",
        nodes=[{"id": "ray", "operator_id": "sampling.spatial.axis_rays", "parameters": {"axis": "x", "ray_count": 5, "samples": 64, "channel": "gray"}}],
        inputs={"input": {"node_id": "ray", "port": "image"}},
        outputs={"result": {"node_id": "ray", "port": "profiles"}},
    )
    result = SamplingGeometryRuntime(rays).run({"input": _image()})
    assert result.outputs["result"].shape == (5, 64)

    patches = SamplingPipelineDefinition(
        workspace="spatial",
        nodes=[{"id": "patch", "operator_id": "sampling.spatial.patch_grid", "parameters": {"rows": 4, "cols": 4, "margin": 0.0}}],
        inputs={"input": {"node_id": "patch", "port": "image"}},
        outputs={"result": {"node_id": "patch", "port": "features"}},
    )
    result = SamplingGeometryRuntime(patches).run({"input": _image()})
    assert result.outputs["result"].shape == (16, 5)


def test_spectral_fft_to_radial_service():
    load_sampling_geometry_operators()
    pipeline = SamplingPipelineDefinition(
        workspace="spectral",
        nodes=[
            {"id": "fft", "operator_id": "sampling.spectral.fft2d", "parameters": {"channel": "gray", "window": "hann", "remove_mean": True}},
            {"id": "bands", "operator_id": "sampling.spectral.radial_bands", "parameters": {"bands": 8, "normalize": True}},
        ],
        connections=[
            {"source": {"node_id": "fft", "port": "spectrum"}, "target": {"node_id": "bands", "port": "spectrum"}},
        ],
        inputs={"input": {"node_id": "fft", "port": "image"}},
        outputs={"result": {"node_id": "bands", "port": "features"}},
    )
    result = SamplingGeometryRuntime(pipeline).run({"input": _image()})
    assert result.outputs["result"].shape == (8,)
    assert abs(float(result.outputs["result"].values.sum()) - 1.0) < 1e-4

    now = datetime.now(timezone.utc).isoformat()
    service = LabServiceDefinition(
        service_id="spectral-test",
        name="Spectral Test",
        lab_type="sampling_geometry",
        workspace_type="spectral",
        version=1,
        inputs={"input": LabServicePort(type="image")},
        outputs={
            "features": LabServiceOutputBinding(
                type="feature_vector",
                node_id="bands",
                port="features",
            )
        },
        pipeline_snapshot=(pipeline.model_dump() if hasattr(pipeline, "model_dump") else pipeline.dict()),
        created_at=now,
        deployed_at=now,
    )
    run = LabServiceRuntime().run(service, {"input": _image()})
    assert run.manifest.workspace_type == "spectral"
    assert run.manifest.outputs["features"]["type"] == "feature_vector"
