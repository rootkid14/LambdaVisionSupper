from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.services.vision_labs.sampling_geometry.operator import SamplingGeometryOperator
from app.services.vision_labs.sampling_geometry.registry import (
    SAMPLING_OPERATOR_REGISTRY,
)


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


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


class SamplingPipelineDefinition(BaseModel):
    version: int = 1
    workspace: str
    nodes: list[OperatorInstance] = Field(default_factory=list)
    connections: list[PipelineConnection] = Field(default_factory=list)
    inputs: dict[str, Endpoint] = Field(default_factory=dict)
    outputs: dict[str, Endpoint] = Field(default_factory=dict)


@dataclass(frozen=True)
class CompiledNode:
    instance: OperatorInstance
    operator_class: type[SamplingGeometryOperator]
    parameters: dict[str, Any]


@dataclass(frozen=True)
class CompiledPipeline:
    definition: SamplingPipelineDefinition
    nodes: dict[str, CompiledNode]
    order: list[str]
    incoming: dict[str, list[PipelineConnection]]
    external_inputs: dict[tuple[str, str], str]


class SamplingPipelineValidator:
    VALID_WORKSPACES = {"geometry", "spatial", "spectral"}

    def validate(
        self,
        definition: SamplingPipelineDefinition,
        *,
        raise_on_error: bool = True,
    ) -> list[str]:
        errors: list[str] = []

        if definition.workspace not in self.VALID_WORKSPACES:
            errors.append(f"Unsupported workspace: {definition.workspace}")

        node_map: dict[str, CompiledNode] = {}
        for node in definition.nodes:
            if node.id in node_map:
                errors.append(f"Duplicate node id: {node.id}")
                continue

            try:
                operator_definition = SAMPLING_OPERATOR_REGISTRY.get(
                    node.operator_id,
                    node.operator_version,
                )
            except KeyError as exc:
                errors.append(str(exc))
                continue

            if operator_definition.workspace != definition.workspace:
                errors.append(
                    f"Operator {node.operator_id} belongs to workspace "
                    f"{operator_definition.workspace!r}, not {definition.workspace!r}"
                )

            try:
                params = operator_definition.operator_class.resolve_parameters(
                    node.parameters
                )
            except Exception as exc:
                errors.append(f"{node.id}: {exc}")
                params = {}

            node_map[node.id] = CompiledNode(
                instance=node,
                operator_class=operator_definition.operator_class,
                parameters=params,
            )

        bound_targets: dict[tuple[str, str], str] = {}
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree = {node_id: 0 for node_id in node_map}

        for name, endpoint in definition.inputs.items():
            target_node = node_map.get(endpoint.node_id)
            if target_node is None:
                errors.append(f"Input {name!r} references unknown node {endpoint.node_id}")
                continue
            port = target_node.operator_class.INPUTS.get(endpoint.port)
            if port is None:
                errors.append(
                    f"Input {name!r} references unknown port "
                    f"{endpoint.node_id}.{endpoint.port}"
                )
                continue
            key = (endpoint.node_id, endpoint.port)
            if key in bound_targets:
                errors.append(
                    f"Multiple sources bind {endpoint.node_id}.{endpoint.port}"
                )
            bound_targets[key] = f"input:{name}"

        for connection in definition.connections:
            source_node = node_map.get(connection.source.node_id)
            target_node = node_map.get(connection.target.node_id)
            if source_node is None:
                errors.append(
                    f"Connection source references unknown node "
                    f"{connection.source.node_id}"
                )
                continue
            if target_node is None:
                errors.append(
                    f"Connection target references unknown node "
                    f"{connection.target.node_id}"
                )
                continue

            source_port = source_node.operator_class.OUTPUTS.get(
                connection.source.port
            )
            target_port = target_node.operator_class.INPUTS.get(
                connection.target.port
            )
            if source_port is None:
                errors.append(
                    f"Unknown output port "
                    f"{connection.source.node_id}.{connection.source.port}"
                )
                continue
            if target_port is None:
                errors.append(
                    f"Unknown input port "
                    f"{connection.target.node_id}.{connection.target.port}"
                )
                continue
            if source_port.data_type != target_port.data_type:
                errors.append(
                    f"Type mismatch: {connection.source.node_id}."
                    f"{connection.source.port} ({source_port.data_type}) -> "
                    f"{connection.target.node_id}.{connection.target.port} "
                    f"({target_port.data_type})"
                )

            key = (connection.target.node_id, connection.target.port)
            if key in bound_targets:
                errors.append(
                    f"Multiple sources bind "
                    f"{connection.target.node_id}.{connection.target.port}"
                )
            bound_targets[key] = (
                f"node:{connection.source.node_id}.{connection.source.port}"
            )

            adjacency[connection.source.node_id].append(
                connection.target.node_id
            )
            indegree[connection.target.node_id] = (
                indegree.get(connection.target.node_id, 0) + 1
            )

        for node_id, compiled in node_map.items():
            if not compiled.instance.enabled:
                continue
            for port_name, port in compiled.operator_class.INPUTS.items():
                if port.optional:
                    continue
                if (node_id, port_name) not in bound_targets:
                    errors.append(
                        f"Required input is not bound: {node_id}.{port_name}"
                    )

        for output_name, endpoint in definition.outputs.items():
            node = node_map.get(endpoint.node_id)
            if node is None:
                errors.append(
                    f"Output {output_name!r} references unknown node "
                    f"{endpoint.node_id}"
                )
                continue
            if endpoint.port not in node.operator_class.OUTPUTS:
                errors.append(
                    f"Output {output_name!r} references unknown port "
                    f"{endpoint.node_id}.{endpoint.port}"
                )

        queue = deque(
            sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        )
        visited = 0
        while queue:
            node_id = queue.popleft()
            visited += 1
            for child in adjacency.get(node_id, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        if visited != len(node_map):
            errors.append("Pipeline contains a cycle")

        if errors and raise_on_error:
            raise ValueError("; ".join(errors))
        return errors


class SamplingPipelineCompiler:
    def compile(
        self,
        definition: SamplingPipelineDefinition,
    ) -> CompiledPipeline:
        SamplingPipelineValidator().validate(definition)

        nodes: dict[str, CompiledNode] = {}
        for node in definition.nodes:
            operator_definition = SAMPLING_OPERATOR_REGISTRY.get(
                node.operator_id,
                node.operator_version,
            )
            nodes[node.id] = CompiledNode(
                instance=node,
                operator_class=operator_definition.operator_class,
                parameters=operator_definition.operator_class.resolve_parameters(
                    node.parameters
                ),
            )

        incoming: dict[str, list[PipelineConnection]] = defaultdict(list)
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree = {node_id: 0 for node_id in nodes}
        for connection in definition.connections:
            incoming[connection.target.node_id].append(connection)
            adjacency[connection.source.node_id].append(connection.target.node_id)
            indegree[connection.target.node_id] += 1

        queue = deque(
            sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        )
        order: list[str] = []
        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for child in adjacency.get(node_id, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        external_inputs = {
            (endpoint.node_id, endpoint.port): name
            for name, endpoint in definition.inputs.items()
        }

        return CompiledPipeline(
            definition=definition,
            nodes=nodes,
            order=order,
            incoming=dict(incoming),
            external_inputs=external_inputs,
        )
