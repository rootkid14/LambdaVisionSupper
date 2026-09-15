from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.services.vision_labs.image.registry import IMAGE_OPERATOR_REGISTRY, ImageOperatorRegistry


class Endpoint(BaseModel):
    node_id: str
    port: str


class PipelineConnection(BaseModel):
    source: Endpoint
    target: Endpoint


class OperatorInstance(BaseModel):
    id: str
    operator_id: str
    operator_version: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ImagePipelineDefinition(BaseModel):
    version: int = 1
    nodes: list[OperatorInstance] = Field(default_factory=list)
    connections: list[PipelineConnection] = Field(default_factory=list)
    inputs: dict[str, Endpoint] = Field(default_factory=dict)
    outputs: dict[str, Endpoint] = Field(default_factory=dict)


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class PipelineValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class PipelineValidator:
    def __init__(self, registry: ImageOperatorRegistry | None = None) -> None:
        self.registry = registry or IMAGE_OPERATOR_REGISTRY

    def validate(self, definition: ImagePipelineDefinition, *, raise_on_error: bool = True) -> list[str]:
        errors: list[str] = []
        node_map: dict[str, OperatorInstance] = {}

        for node in definition.nodes:
            if node.id in node_map:
                errors.append(f"Duplicate node id: {node.id}")
                continue
            node_map[node.id] = node
            try:
                opdef = self.registry.get(node.operator_id)
                if node.operator_version and node.operator_version != opdef.version:
                    errors.append(
                        f"Node {node.id}: requested operator version {node.operator_version}, "
                        f"but registry provides {opdef.version}"
                    )
                try:
                    opdef.operator_class.resolve_parameters(node.parameters)
                except Exception as exc:
                    errors.append(f"Node {node.id}: invalid parameters: {exc}")
                if not node.enabled:
                    inputs = list(opdef.operator_class.INPUTS.values())
                    outputs = list(opdef.operator_class.OUTPUTS.values())
                    if len(inputs) != 1 or len(outputs) != 1 or inputs[0].data_type != outputs[0].data_type:
                        errors.append(
                            f"Node {node.id}: disabled/bypass is only supported for 1-input/1-output "
                            "operators with the same data type"
                        )
            except KeyError as exc:
                errors.append(str(exc))

        occupied_targets: set[tuple[str, str]] = set()
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_map}
        indegree: dict[str, int] = {node_id: 0 for node_id in node_map}

        for connection in definition.connections:
            src_node = node_map.get(connection.source.node_id)
            dst_node = node_map.get(connection.target.node_id)
            if src_node is None:
                errors.append(f"Connection source node does not exist: {connection.source.node_id}")
                continue
            if dst_node is None:
                errors.append(f"Connection target node does not exist: {connection.target.node_id}")
                continue
            try:
                src_def = self.registry.get(src_node.operator_id)
                dst_def = self.registry.get(dst_node.operator_id)
            except KeyError:
                continue

            src_port = src_def.operator_class.OUTPUTS.get(connection.source.port)
            dst_port = dst_def.operator_class.INPUTS.get(connection.target.port)
            if src_port is None:
                errors.append(
                    f"Node {src_node.id} has no output port {connection.source.port!r}"
                )
                continue
            if dst_port is None:
                errors.append(
                    f"Node {dst_node.id} has no input port {connection.target.port!r}"
                )
                continue
            if src_port.data_type != dst_port.data_type:
                errors.append(
                    f"Incompatible ports: {src_node.id}.{connection.source.port} "
                    f"({src_port.data_type.value}) -> {dst_node.id}.{connection.target.port} "
                    f"({dst_port.data_type.value})"
                )

            target_key = (connection.target.node_id, connection.target.port)
            if target_key in occupied_targets:
                errors.append(
                    f"Input {connection.target.node_id}.{connection.target.port} has multiple sources"
                )
            occupied_targets.add(target_key)

            if dst_node.id not in adjacency[src_node.id]:
                adjacency[src_node.id].add(dst_node.id)
                indegree[dst_node.id] += 1

        for external_name, endpoint in definition.inputs.items():
            node = node_map.get(endpoint.node_id)
            if node is None:
                errors.append(f"Pipeline input {external_name!r} targets unknown node {endpoint.node_id}")
                continue
            try:
                opdef = self.registry.get(node.operator_id)
            except KeyError:
                continue
            if endpoint.port not in opdef.operator_class.INPUTS:
                errors.append(
                    f"Pipeline input {external_name!r} targets missing port {endpoint.node_id}.{endpoint.port}"
                )
                continue
            target_key = (endpoint.node_id, endpoint.port)
            if target_key in occupied_targets:
                errors.append(
                    f"Input {endpoint.node_id}.{endpoint.port} is connected both internally and externally"
                )
            occupied_targets.add(target_key)

        for node in definition.nodes:
            try:
                opdef = self.registry.get(node.operator_id)
            except KeyError:
                continue
            for port_name, port_spec in opdef.operator_class.INPUTS.items():
                if not port_spec.optional and (node.id, port_name) not in occupied_targets:
                    errors.append(f"Required input is not connected: {node.id}.{port_name}")

        for output_name, endpoint in definition.outputs.items():
            node = node_map.get(endpoint.node_id)
            if node is None:
                errors.append(f"Pipeline output {output_name!r} references unknown node {endpoint.node_id}")
                continue
            try:
                opdef = self.registry.get(node.operator_id)
            except KeyError:
                continue
            if endpoint.port not in opdef.operator_class.OUTPUTS:
                errors.append(
                    f"Pipeline output {output_name!r} references missing port "
                    f"{endpoint.node_id}.{endpoint.port}"
                )

        queue = [node_id for node_id, degree in indegree.items() if degree == 0]
        visited = 0
        while queue:
            node_id = queue.pop(0)
            visited += 1
            for child in adjacency[node_id]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(node_map):
            errors.append("Pipeline contains a cycle")

        if raise_on_error and errors:
            raise PipelineValidationError(errors)
        return errors


@dataclass
class InputBinding:
    kind: Literal["external", "node"]
    external_name: str | None = None
    node_id: str | None = None
    port: str | None = None


@dataclass
class CompiledNode:
    instance: OperatorInstance
    operator_class: type
    resolved_parameters: dict[str, Any]


@dataclass
class CompiledPipeline:
    definition: ImagePipelineDefinition
    nodes: dict[str, CompiledNode]
    execution_order: list[str]
    incoming: dict[tuple[str, str], InputBinding]
    downstream: dict[str, set[str]]


class PipelineCompiler:
    def __init__(self, registry: ImageOperatorRegistry | None = None) -> None:
        self.registry = registry or IMAGE_OPERATOR_REGISTRY
        self.validator = PipelineValidator(self.registry)

    def compile(self, definition: ImagePipelineDefinition) -> CompiledPipeline:
        self.validator.validate(definition)

        compiled_nodes: dict[str, CompiledNode] = {}
        for instance in definition.nodes:
            opdef = self.registry.get(instance.operator_id)
            compiled_nodes[instance.id] = CompiledNode(
                instance=instance,
                operator_class=opdef.operator_class,
                resolved_parameters=opdef.operator_class.resolve_parameters(instance.parameters),
            )

        incoming: dict[tuple[str, str], InputBinding] = {}
        downstream: dict[str, set[str]] = {node_id: set() for node_id in compiled_nodes}
        indegree: dict[str, int] = {node_id: 0 for node_id in compiled_nodes}

        for external_name, endpoint in definition.inputs.items():
            incoming[(endpoint.node_id, endpoint.port)] = InputBinding(
                kind="external",
                external_name=external_name,
            )

        for connection in definition.connections:
            incoming[(connection.target.node_id, connection.target.port)] = InputBinding(
                kind="node",
                node_id=connection.source.node_id,
                port=connection.source.port,
            )
            if connection.target.node_id not in downstream[connection.source.node_id]:
                downstream[connection.source.node_id].add(connection.target.node_id)
                indegree[connection.target.node_id] += 1

        queue = [node_id for node_id, degree in indegree.items() if degree == 0]
        order: list[str] = []
        while queue:
            node_id = queue.pop(0)
            order.append(node_id)
            for child in downstream[node_id]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        return CompiledPipeline(
            definition=definition,
            nodes=compiled_nodes,
            execution_order=order,
            incoming=incoming,
            downstream=downstream,
        )
