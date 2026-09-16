from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
import threading
from typing import Any
import uuid

from app.services.vision_labs.core import ExecutionMode
from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.pipeline import ImagePipelineDefinition, model_to_dict
from app.services.vision_labs.image.runtime import ImagePipelineRuntime
from app.services.vision_labs.service.models import (
    LabServiceDefinition,
    LabServiceRunManifest,
)


@dataclass
class LabServiceRun:
    manifest: LabServiceRunManifest
    outputs: dict[str, Any]


def _prune_image_pipeline(
    definition: ImagePipelineDefinition,
    service: LabServiceDefinition,
) -> ImagePipelineDefinition:
    """Keep only nodes required to produce the exposed service outputs.

    This makes a checkpoint contract meaningful for performance too: if a
    service exposes nodes 4 and 6 from a ten-node editor stack, nodes 7..10
    are not executed by the deployed service snapshot.
    """
    required = {binding.node_id for binding in service.outputs.values()}
    reverse: dict[str, set[str]] = {}
    for connection in definition.connections:
        reverse.setdefault(connection.target.node_id, set()).add(
            connection.source.node_id
        )

    stack = list(required)
    while stack:
        node_id = stack.pop()
        for parent in reverse.get(node_id, set()):
            if parent not in required:
                required.add(parent)
                stack.append(parent)

    nodes = [node for node in definition.nodes if node.id in required]
    connections = [
        connection
        for connection in definition.connections
        if connection.source.node_id in required
        and connection.target.node_id in required
    ]
    inputs = {
        name: endpoint
        for name, endpoint in definition.inputs.items()
        if endpoint.node_id in required
    }
    outputs = {
        name: {"node_id": binding.node_id, "port": binding.port}
        for name, binding in service.outputs.items()
    }

    payload = model_to_dict(definition)
    payload["nodes"] = [model_to_dict(node) for node in nodes]
    payload["connections"] = [model_to_dict(connection) for connection in connections]
    payload["inputs"] = {name: model_to_dict(endpoint) for name, endpoint in inputs.items()}
    payload["outputs"] = outputs
    return ImagePipelineDefinition(**payload)


class LabServiceRuntime:
    """Generic LAB-service dispatcher.

    Only the image_processing adapter exists today. Future LABs should add an
    adapter here while keeping the public run(service, inputs) contract stable.
    """

    def run(
        self,
        service: LabServiceDefinition,
        inputs: dict[str, Any],
    ) -> LabServiceRun:
        if service.lab_type == "image_processing":
            return self._run_image_processing(service, inputs)
        raise NotImplementedError(
            f"Lab Service runtime adapter is not implemented for {service.lab_type!r}"
        )

    def _run_image_processing(
        self,
        service: LabServiceDefinition,
        inputs: dict[str, Any],
    ) -> LabServiceRun:
        load_builtin_operators()
        editor_definition = ImagePipelineDefinition(**service.pipeline_snapshot)
        definition = _prune_image_pipeline(editor_definition, service)
        runtime = ImagePipelineRuntime(definition)

        start = perf_counter()
        result = runtime.run(inputs, mode=ExecutionMode.FINAL)
        total_ms = (perf_counter() - start) * 1000.0

        output_values: dict[str, Any] = {}
        output_manifest: dict[str, dict[str, Any]] = {}

        for output_name, binding in service.outputs.items():
            artifact = runtime.get_artifact(binding.node_id, binding.port)
            value = artifact.value
            output_values[output_name] = value
            shape = list(value.shape) if hasattr(value, "shape") else None
            output_manifest[output_name] = {
                "type": binding.type,
                "node_id": binding.node_id,
                "port": binding.port,
                "shape": shape,
                "artifact_id": artifact.artifact_id,
            }

        run_id = f"labsrun_{uuid.uuid4().hex}"
        manifest = LabServiceRunManifest(
            run_id=run_id,
            service_id=service.service_id,
            service_version=service.version,
            lab_type=service.lab_type,
            outputs=output_manifest,
            timings_ms=result.timings_ms,
            total_ms=total_ms,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        return LabServiceRun(manifest=manifest, outputs=output_values)


class LabServiceRunStore:
    def __init__(self, max_runs: int = 32) -> None:
        self.max_runs = int(max_runs)
        self._runs: dict[str, LabServiceRun] = {}
        self._order: list[str] = []
        self._lock = threading.RLock()

    def put(self, run: LabServiceRun) -> None:
        with self._lock:
            run_id = run.manifest.run_id
            self._runs[run_id] = run
            self._order.append(run_id)
            while len(self._order) > self.max_runs:
                oldest = self._order.pop(0)
                self._runs.pop(oldest, None)

    def get(self, run_id: str) -> LabServiceRun:
        with self._lock:
            try:
                return self._runs[run_id]
            except KeyError as exc:
                raise KeyError(f"Unknown Lab Service run: {run_id}") from exc
