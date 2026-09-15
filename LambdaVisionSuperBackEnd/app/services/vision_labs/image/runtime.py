from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any
import uuid

from app.services.vision_labs.core import DataType, ExecutionContext, ExecutionMode
from app.services.vision_labs.image.pipeline import (
    CompiledPipeline,
    ImagePipelineDefinition,
    PipelineCompiler,
)
from app.services.vision_labs.image.types import BinaryMask, ImageFrame, ROI


@dataclass
class Artifact:
    artifact_id: str
    value: Any
    revision: int
    node_id: str
    port: str

    def manifest(self) -> dict[str, Any]:
        value = self.value
        shape = list(value.shape) if hasattr(value, "shape") else None
        return {
            "artifact_id": self.artifact_id,
            "revision": self.revision,
            "node_id": self.node_id,
            "port": self.port,
            "value_type": type(value).__name__,
            "shape": shape,
        }


class ArtifactStore:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Artifact] = {}

    def get(self, node_id: str, port: str) -> Artifact | None:
        return self._items.get((node_id, port))

    def put(self, artifact: Artifact) -> None:
        self._items[(artifact.node_id, artifact.port)] = artifact

    def invalidate_nodes(self, node_ids: set[str]) -> None:
        for key in list(self._items):
            if key[0] in node_ids:
                del self._items[key]

    def clear(self) -> None:
        self._items.clear()

    def manifests(self) -> list[dict[str, Any]]:
        return [artifact.manifest() for artifact in self._items.values()]


@dataclass
class RuntimeResult:
    outputs: dict[str, Artifact]
    timings_ms: dict[str, float]
    executed_nodes: list[str]
    cached_nodes: list[str]

    def manifest(self) -> dict[str, Any]:
        return {
            "outputs": {name: artifact.manifest() for name, artifact in self.outputs.items()},
            "timings_ms": self.timings_ms,
            "executed_nodes": self.executed_nodes,
            "cached_nodes": self.cached_nodes,
        }


class ImagePipelineRuntime:
    """Executable Image LAB pipeline with incremental cache invalidation."""

    def __init__(
        self,
        definition: ImagePipelineDefinition,
        *,
        compiler: PipelineCompiler | None = None,
    ) -> None:
        self.compiler = compiler or PipelineCompiler()
        self.compiled: CompiledPipeline = self.compiler.compile(definition)
        self.artifacts = ArtifactStore()
        self.external_inputs: dict[str, Any] = {}
        self._artifact_revision = 0

    @property
    def definition(self) -> ImagePipelineDefinition:
        return self.compiled.definition

    def recompile(self, definition: ImagePipelineDefinition) -> None:
        self.compiled = self.compiler.compile(definition)
        self.artifacts.clear()

    def _next_revision(self) -> int:
        self._artifact_revision += 1
        return self._artifact_revision

    def _descendants_including_self(self, node_id: str) -> set[str]:
        if node_id not in self.compiled.nodes:
            raise KeyError(f"Unknown pipeline node: {node_id}")
        affected: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            if current in affected:
                continue
            affected.add(current)
            stack.extend(self.compiled.downstream.get(current, ()))
        return affected

    def update_parameters(
        self,
        node_id: str,
        changes: dict[str, Any],
        *,
        mode: ExecutionMode = ExecutionMode.INTERACTIVE,
    ) -> RuntimeResult:
        node = self.compiled.nodes.get(node_id)
        if node is None:
            raise KeyError(f"Unknown pipeline node: {node_id}")

        merged = dict(node.resolved_parameters)
        merged.update(changes)
        node.resolved_parameters = node.operator_class.resolve_parameters(merged)
        node.instance.parameters = dict(node.resolved_parameters)

        affected = self._descendants_including_self(node_id)
        self.artifacts.invalidate_nodes(affected)
        return self.run(mode=mode)

    def run(
        self,
        inputs: dict[str, Any] | None = None,
        *,
        mode: ExecutionMode = ExecutionMode.FINAL,
    ) -> RuntimeResult:
        if inputs is not None:
            self.external_inputs = dict(inputs)
            self.artifacts.clear()

        missing_external = set(self.definition.inputs) - set(self.external_inputs)
        if missing_external:
            raise ValueError(f"Missing pipeline input(s): {sorted(missing_external)}")

        timings: dict[str, float] = {}
        executed: list[str] = []
        cached: list[str] = []

        for node_id in self.compiled.execution_order:
            compiled_node = self.compiled.nodes[node_id]
            output_ports = compiled_node.operator_class.OUTPUTS

            if output_ports and all(
                self.artifacts.get(node_id, port_name) is not None
                for port_name in output_ports
            ):
                cached.append(node_id)
                continue

            node_inputs: dict[str, Any] = {}
            for input_name in compiled_node.operator_class.INPUTS:
                binding = self.compiled.incoming.get((node_id, input_name))
                if binding is None:
                    continue
                if binding.kind == "external":
                    node_inputs[input_name] = self.external_inputs[binding.external_name]
                else:
                    artifact = self.artifacts.get(binding.node_id, binding.port)
                    if artifact is None:
                        raise RuntimeError(
                            f"Upstream artifact missing for {node_id}.{input_name}: "
                            f"{binding.node_id}.{binding.port}"
                        )
                    node_inputs[input_name] = artifact.value

            start = perf_counter()
            if not compiled_node.instance.enabled:
                in_names = list(compiled_node.operator_class.INPUTS)
                out_names = list(compiled_node.operator_class.OUTPUTS)
                outputs = {out_names[0]: node_inputs[in_names[0]]}
            else:
                operator = compiled_node.operator_class()
                outputs = operator.process(
                    node_inputs,
                    dict(compiled_node.resolved_parameters),
                    ExecutionContext(mode=mode),
                )
            timings[node_id] = (perf_counter() - start) * 1000.0
            executed.append(node_id)

            if not isinstance(outputs, dict):
                raise TypeError(f"Operator {node_id} must return dict[str, value]")

            expected_outputs = compiled_node.operator_class.OUTPUTS
            unknown_outputs = set(outputs) - set(expected_outputs)
            if unknown_outputs:
                raise ValueError(f"Operator {node_id} returned unknown output(s): {sorted(unknown_outputs)}")
            missing_outputs = set(expected_outputs) - set(outputs)
            if missing_outputs:
                raise ValueError(f"Operator {node_id} did not return output(s): {sorted(missing_outputs)}")

            for port_name, value in outputs.items():
                self._validate_runtime_value(
                    expected_outputs[port_name].data_type,
                    value,
                    node_id=node_id,
                    port_name=port_name,
                )
                self.artifacts.put(
                    Artifact(
                        artifact_id=f"art_{uuid.uuid4().hex}",
                        value=value,
                        revision=self._next_revision(),
                        node_id=node_id,
                        port=port_name,
                    )
                )

        pipeline_outputs: dict[str, Artifact] = {}
        for output_name, endpoint in self.definition.outputs.items():
            artifact = self.artifacts.get(endpoint.node_id, endpoint.port)
            if artifact is None:
                raise RuntimeError(
                    f"Pipeline output artifact missing: {endpoint.node_id}.{endpoint.port}"
                )
            pipeline_outputs[output_name] = artifact

        return RuntimeResult(
            outputs=pipeline_outputs,
            timings_ms=timings,
            executed_nodes=executed,
            cached_nodes=cached,
        )

    def get_artifact(self, node_id: str, port: str) -> Artifact:
        artifact = self.artifacts.get(node_id, port)
        if artifact is None:
            raise KeyError(f"No cached artifact for {node_id}.{port}")
        return artifact

    def _validate_runtime_value(
        self,
        data_type: DataType,
        value: Any,
        *,
        node_id: str,
        port_name: str,
    ) -> None:
        expected = {
            DataType.IMAGE: ImageFrame,
            DataType.BINARY_MASK: BinaryMask,
            DataType.ROI: ROI,
        }[data_type]
        if not isinstance(value, expected):
            raise TypeError(
                f"Operator {node_id}.{port_name} expected {expected.__name__}, "
                f"got {type(value).__name__}"
            )
