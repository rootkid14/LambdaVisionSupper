from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any
import uuid

from app.services.vision_labs.core import ExecutionContext, ExecutionMode
from app.services.vision_labs.sampling_geometry.pipeline import (
    SamplingPipelineCompiler,
    SamplingPipelineDefinition,
)


@dataclass
class SamplingArtifact:
    artifact_id: str
    node_id: str
    port: str
    value: Any


@dataclass
class SamplingRuntimeResult:
    timings_ms: dict[str, float]
    outputs: dict[str, Any]

    def manifest(self) -> dict[str, Any]:
        return {
            "timings_ms": dict(self.timings_ms),
            "outputs": {
                name: artifact_manifest(value)
                for name, value in self.outputs.items()
            },
        }


def artifact_shape(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return [int(item) for item in shape]
    except Exception:
        return None


def artifact_type_name(value: Any) -> str:
    from app.services.vision_labs.image.types import BinaryMask, ImageFrame
    from app.services.vision_labs.sampling_geometry.types import (
        ContourSet,
        FeatureMatrix,
        FeatureVector,
        Histogram1D,
        MeasurementTable,
        Polyline,
        ProfileSet,
        Spectrum2D,
    )

    mapping = {
        ImageFrame: "image",
        BinaryMask: "binary_mask",
        ContourSet: "contour_set",
        Polyline: "polyline",
        ProfileSet: "profile_set",
        Histogram1D: "histogram_1d",
        FeatureVector: "feature_vector",
        FeatureMatrix: "feature_matrix",
        Spectrum2D: "spectrum_2d",
        MeasurementTable: "measurement_table",
    }
    for cls, name in mapping.items():
        if isinstance(value, cls):
            return name
    return type(value).__name__


def artifact_manifest(value: Any) -> dict[str, Any]:
    return {
        "type": artifact_type_name(value),
        "shape": artifact_shape(value),
    }


class SamplingGeometryRuntime:
    def __init__(
        self,
        definition: SamplingPipelineDefinition,
        *,
        compiler: SamplingPipelineCompiler | None = None,
    ) -> None:
        self.definition = definition
        self.compiled = (compiler or SamplingPipelineCompiler()).compile(definition)
        self.artifacts: dict[tuple[str, str], SamplingArtifact] = {}

    def clear(self) -> None:
        self.artifacts.clear()

    def run(
        self,
        inputs: dict[str, Any],
        *,
        mode: ExecutionMode = ExecutionMode.FINAL,
    ) -> SamplingRuntimeResult:
        self.clear()
        timings: dict[str, float] = {}
        context = ExecutionContext(mode=mode)

        for node_id in self.compiled.order:
            compiled_node = self.compiled.nodes[node_id]
            if not compiled_node.instance.enabled:
                continue

            node_inputs: dict[str, Any] = {}

            for port_name in compiled_node.operator_class.INPUTS:
                external_name = self.compiled.external_inputs.get(
                    (node_id, port_name)
                )
                if external_name is not None:
                    if external_name not in inputs:
                        raise KeyError(
                            f"Missing external input {external_name!r}"
                        )
                    node_inputs[port_name] = inputs[external_name]

            for connection in self.compiled.incoming.get(node_id, []):
                artifact = self.get_artifact(
                    connection.source.node_id,
                    connection.source.port,
                )
                node_inputs[connection.target.port] = artifact.value

            operator = compiled_node.operator_class()
            start = perf_counter()
            outputs = operator.process(
                node_inputs,
                dict(compiled_node.parameters),
                context,
            )
            timings[node_id] = (perf_counter() - start) * 1000.0

            for port_name, value in outputs.items():
                if port_name not in compiled_node.operator_class.OUTPUTS:
                    raise ValueError(
                        f"{compiled_node.instance.operator_id} returned unknown "
                        f"output port {port_name!r}"
                    )
                self.artifacts[(node_id, port_name)] = SamplingArtifact(
                    artifact_id=f"sgart_{uuid.uuid4().hex}",
                    node_id=node_id,
                    port=port_name,
                    value=value,
                )

        final_outputs: dict[str, Any] = {}
        for name, endpoint in self.definition.outputs.items():
            final_outputs[name] = self.get_artifact(
                endpoint.node_id,
                endpoint.port,
            ).value

        return SamplingRuntimeResult(
            timings_ms=timings,
            outputs=final_outputs,
        )

    def get_artifact(self, node_id: str, port: str) -> SamplingArtifact:
        key = (node_id, port)
        if key not in self.artifacts:
            raise KeyError(f"Artifact not available: {node_id}.{port}")
        return self.artifacts[key]
