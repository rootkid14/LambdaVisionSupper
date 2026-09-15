import numpy as np

from app.services.vision_labs.core import ExecutionMode
from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.pipeline import ImagePipelineDefinition
from app.services.vision_labs.image.runtime import ImagePipelineRuntime
from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame


load_builtin_operators()


def _pipeline():
    return ImagePipelineDefinition(
        nodes=[
            {"id": "gray", "operator_id": "image.color.grayscale"},
            {
                "id": "blur",
                "operator_id": "image.filter.gaussian",
                "parameters": {"kernel_size": 5, "sigma": 0.0},
            },
            {
                "id": "threshold",
                "operator_id": "image.threshold.binary",
                "parameters": {"threshold": 100},
            },
            {
                "id": "close",
                "operator_id": "image.morphology.close",
                "parameters": {"kernel_size": 3, "iterations": 1},
            },
        ],
        connections=[
            {
                "source": {"node_id": "gray", "port": "image"},
                "target": {"node_id": "blur", "port": "image"},
            },
            {
                "source": {"node_id": "blur", "port": "image"},
                "target": {"node_id": "threshold", "port": "image"},
            },
            {
                "source": {"node_id": "threshold", "port": "mask"},
                "target": {"node_id": "close", "port": "mask"},
            },
        ],
        inputs={"image": {"node_id": "gray", "port": "image"}},
        outputs={"mask": {"node_id": "close", "port": "mask"}},
    )


def test_pipeline_and_incremental_cache():
    data = np.zeros((64, 64, 3), dtype=np.uint8)
    data[16:48, 16:48] = 180
    image = ImageFrame(data=data, color_space=ColorSpace.BGR)

    runtime = ImagePipelineRuntime(_pipeline())
    first = runtime.run({"image": image})
    assert isinstance(first.outputs["mask"].value, BinaryMask)

    blur_before = runtime.get_artifact("blur", "image").artifact_id
    threshold_before = runtime.get_artifact("threshold", "mask").artifact_id

    second = runtime.update_parameters(
        "threshold",
        {"threshold": 150},
        mode=ExecutionMode.INTERACTIVE,
    )

    assert "gray" in second.cached_nodes
    assert "blur" in second.cached_nodes
    assert runtime.get_artifact("blur", "image").artifact_id == blur_before
    assert runtime.get_artifact("threshold", "mask").artifact_id != threshold_before
    assert "threshold" in second.executed_nodes
    assert "close" in second.executed_nodes
