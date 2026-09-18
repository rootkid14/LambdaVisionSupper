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
from app.services.vision_labs.sampling_geometry.operators import load_sampling_geometry_operators
from app.services.vision_labs.sampling_geometry.pipeline import SamplingPipelineDefinition, model_to_dict as sampling_model_to_dict
from app.services.vision_labs.sampling_geometry.runtime import SamplingGeometryRuntime, artifact_shape
from app.services.vision_labs.service.models import LabServiceDefinition, LabServiceRunManifest

@dataclass
class LabServiceRun:
    manifest: LabServiceRunManifest
    outputs: dict[str, Any]


def _required_nodes(definition, service):
    required = {binding.node_id for binding in service.outputs.values()}
    reverse: dict[str, set[str]] = {}
    for connection in definition.connections:
        reverse.setdefault(connection.target.node_id, set()).add(connection.source.node_id)
    stack = list(required)
    while stack:
        node_id = stack.pop()
        for parent in reverse.get(node_id, set()):
            if parent not in required:
                required.add(parent)
                stack.append(parent)
    return required


def _prune_image_pipeline(definition: ImagePipelineDefinition, service: LabServiceDefinition) -> ImagePipelineDefinition:
    required = _required_nodes(definition, service)
    payload = model_to_dict(definition)
    payload["nodes"] = [model_to_dict(n) for n in definition.nodes if n.id in required]
    payload["connections"] = [model_to_dict(c) for c in definition.connections if c.source.node_id in required and c.target.node_id in required]
    payload["inputs"] = {name: model_to_dict(ep) for name, ep in definition.inputs.items() if ep.node_id in required}
    payload["outputs"] = {name: {"node_id": b.node_id, "port": b.port} for name, b in service.outputs.items()}
    return ImagePipelineDefinition(**payload)


def _prune_sampling_pipeline(definition: SamplingPipelineDefinition, service: LabServiceDefinition) -> SamplingPipelineDefinition:
    required = _required_nodes(definition, service)
    payload = sampling_model_to_dict(definition)
    payload["nodes"] = [sampling_model_to_dict(n) for n in definition.nodes if n.id in required]
    payload["connections"] = [sampling_model_to_dict(c) for c in definition.connections if c.source.node_id in required and c.target.node_id in required]
    payload["inputs"] = {name: sampling_model_to_dict(ep) for name, ep in definition.inputs.items() if ep.node_id in required}
    payload["outputs"] = {name: {"node_id": b.node_id, "port": b.port} for name, b in service.outputs.items()}
    return SamplingPipelineDefinition(**payload)


class LabServiceRuntime:
    def run(self, service: LabServiceDefinition, inputs: dict[str, Any]) -> LabServiceRun:
        if service.lab_type == "image_processing":
            return self._run_image_processing(service, inputs)
        if service.lab_type == "sampling_geometry":
            return self._run_sampling_geometry(service, inputs)
        raise NotImplementedError(f"Lab Service runtime adapter is not implemented for {service.lab_type!r}")

    def _manifest(self, service, output_values, output_meta, timings, total_ms):
        return LabServiceRunManifest(
            run_id=f"labsrun_{uuid.uuid4().hex}",
            service_id=service.service_id,
            service_version=service.version,
            lab_type=service.lab_type,
            workspace_type=service.workspace_type,
            outputs=output_meta,
            timings_ms=timings,
            total_ms=total_ms,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

    def _run_image_processing(self, service, inputs):
        load_builtin_operators()
        definition = _prune_image_pipeline(ImagePipelineDefinition(**service.pipeline_snapshot), service)
        runtime = ImagePipelineRuntime(definition)
        start = perf_counter()
        result = runtime.run(inputs, mode=ExecutionMode.FINAL)
        total_ms = (perf_counter() - start) * 1000.0
        values, meta = {}, {}
        for name, binding in service.outputs.items():
            artifact = runtime.get_artifact(binding.node_id, binding.port)
            value = artifact.value
            values[name] = value
            meta[name] = {"type": binding.type, "node_id": binding.node_id, "port": binding.port, "shape": list(value.shape) if hasattr(value, "shape") else None, "artifact_id": artifact.artifact_id}
        manifest = self._manifest(service, values, meta, result.timings_ms, total_ms)
        return LabServiceRun(manifest=manifest, outputs=values)

    def _run_sampling_geometry(self, service, inputs):
        load_sampling_geometry_operators()
        editor = SamplingPipelineDefinition(**service.pipeline_snapshot)
        definition = _prune_sampling_pipeline(editor, service)
        runtime = SamplingGeometryRuntime(definition)
        start = perf_counter()
        result = runtime.run(inputs, mode=ExecutionMode.FINAL)
        total_ms = (perf_counter() - start) * 1000.0
        values, meta = {}, {}
        for name, binding in service.outputs.items():
            artifact = runtime.get_artifact(binding.node_id, binding.port)
            value = artifact.value
            values[name] = value
            meta[name] = {"type": binding.type, "node_id": binding.node_id, "port": binding.port, "shape": artifact_shape(value), "artifact_id": artifact.artifact_id}
        manifest = self._manifest(service, values, meta, result.timings_ms, total_ms)
        manifest.workspace_type = service.workspace_type or definition.workspace
        return LabServiceRun(manifest=manifest, outputs=values)

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
                self._runs.pop(self._order.pop(0), None)
    def get(self, run_id: str) -> LabServiceRun:
        with self._lock:
            try: return self._runs[run_id]
            except KeyError as exc: raise KeyError(f"Unknown Lab Service run: {run_id}") from exc
