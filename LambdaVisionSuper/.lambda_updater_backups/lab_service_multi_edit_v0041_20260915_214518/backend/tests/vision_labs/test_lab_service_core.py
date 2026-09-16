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


def test_service_repository_versions_and_runtime(tmp_path: Path):
    load_builtin_operators()
    repository = LabServiceRepository(tmp_path / "services")
    pipeline = _pipeline()

    first = repository.deploy(
        name="Smoke Service",
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
    second = repository.deploy(
        name="Smoke Service",
        service_id=first.service_id,
        lab_type="image_processing",
        inputs=first.inputs,
        outputs=first.outputs,
        pipeline_snapshot=_dump(pipeline),
    )

    assert first.version == 1
    assert second.version == 2
    assert repository.get(first.service_id).version == 2
    assert [item.version for item in repository.list_versions(first.service_id)] == [2, 1]

    image = np.zeros((64, 80, 3), dtype=np.uint8)
    image[20:40, 20:60] = 255
    frame = ImageFrame(image, color_space=ColorSpace.BGR)
    run = LabServiceRuntime().run(second, {"image": frame})

    assert set(run.outputs) == {"gray", "blurred"}
    assert run.outputs["gray"].shape == (64, 80)
    assert run.outputs["blurred"].shape == (64, 80)
    assert run.manifest.service_version == 2
    assert run.manifest.total_ms >= 0
