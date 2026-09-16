from pathlib import Path

import numpy as np

from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.pipeline import ImagePipelineDefinition
from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.service.models import (
    LabServiceOutputBinding,
    LabServicePort,
)
from app.services.vision_labs.service.repository import LabServiceRepository
from app.services.vision_labs.service.runtime import LabServiceRuntime


def _pipeline():
    return ImagePipelineDefinition(
        nodes=[
            {
                "id": "gray",
                "operator_id": "image.color.grayscale",
                "parameters": {},
                "enabled": True,
            },
            {
                "id": "blur",
                "operator_id": "image.filter.gaussian",
                "parameters": {"kernel_size": 5, "sigma": 0.0},
                "enabled": True,
            },
        ],
        connections=[
            {
                "source": {"node_id": "gray", "port": "image"},
                "target": {"node_id": "blur", "port": "image"},
            }
        ],
        inputs={"image": {"node_id": "gray", "port": "image"}},
        outputs={"result": {"node_id": "blur", "port": "image"}},
    )


def _dump(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _deploy(repository, *, name="Smoke Service", service_id=None):
    pipeline = _pipeline()
    return repository.deploy(
        name=name,
        service_id=service_id,
        lab_type="image_processing",
        inputs={"image": LabServicePort(type="image")},
        outputs={
            "gray": LabServiceOutputBinding(
                type="image",
                node_id="gray",
                port="image",
            ),
            "blurred": LabServiceOutputBinding(
                type="image",
                node_id="blur",
                port="image",
            ),
        },
        pipeline_snapshot=_dump(pipeline),
    )


def test_multiple_services_and_versioned_modify(tmp_path: Path):
    repository = LabServiceRepository(tmp_path / "services")

    service_a = _deploy(repository, name="ROI Preprocess")
    service_b = _deploy(repository, name="ROI Preprocess")

    assert service_a.service_id != service_b.service_id
    assert service_a.version == 1
    assert service_b.version == 1
    assert len(repository.list_active()) == 2

    updated_a = _deploy(
        repository,
        name="ROI Preprocess Tuned",
        service_id=service_a.service_id,
    )

    assert updated_a.service_id == service_a.service_id
    assert updated_a.version == 2
    assert updated_a.name == "ROI Preprocess Tuned"
    assert repository.get(service_a.service_id).version == 2
    assert repository.get(service_b.service_id).version == 1
    assert [item.version for item in repository.list_versions(service_a.service_id)] == [2, 1]


def test_service_runtime_still_executes_deployed_snapshot(tmp_path: Path):
    load_builtin_operators()
    repository = LabServiceRepository(tmp_path / "services")
    service = _deploy(repository)

    image = np.zeros((64, 80, 3), dtype=np.uint8)
    image[20:40, 20:60] = 255
    frame = ImageFrame(image, color_space=ColorSpace.BGR)
    run = LabServiceRuntime().run(service, {"image": frame})

    assert set(run.outputs) == {"gray", "blurred"}
    assert run.outputs["gray"].shape == (64, 80)
    assert run.outputs["blurred"].shape == (64, 80)
    assert run.manifest.service_version == 1
    assert run.manifest.total_ms >= 0
