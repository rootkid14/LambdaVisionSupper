from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Any
import uuid

from app.services.vision_labs.core import ExecutionMode
from app.services.vision_labs.sampling_geometry.pipeline import (
    SamplingPipelineDefinition,
)
from app.services.vision_labs.sampling_geometry.runtime import (
    SamplingGeometryRuntime,
    SamplingRuntimeResult,
)
from app.services.vision_labs.sampling_geometry.source_board import resolve_pipeline_inputs


@dataclass
class SamplingGeometrySession:
    session_id: str = field(default_factory=lambda: f"sglab_{uuid.uuid4().hex}")
    sources: dict[str, Any] = field(default_factory=dict)
    source_board_manifest: dict[str, Any] = field(default_factory=dict)
    pipeline_definition: SamplingPipelineDefinition | None = None
    runtime: SamplingGeometryRuntime | None = None
    program_sample: Any | None = None
    program_sample_signature: str | None = None
    revision: int = 0
    last_activity: float = field(default_factory=time.time)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def touch(self) -> None:
        self.last_activity = time.time()

    def set_source(self, name: str, value: Any) -> None:
        with self._lock:
            self.sources[name] = value
            self.revision += 1
            self.touch()
            if self.runtime is not None:
                self.runtime.clear()
            self.clear_program_sample()


    def set_source_board(self, sources: dict[str, Any], manifest: dict[str, Any]) -> None:
        with self._lock:
            self.sources = dict(sources)
            self.source_board_manifest = dict(manifest)
            self.revision += 1
            self.touch()
            if self.runtime is not None:
                self.runtime.clear()
            self.clear_program_sample()

    def set_pipeline(self, definition: SamplingPipelineDefinition) -> None:
        with self._lock:
            self.pipeline_definition = definition
            self.runtime = SamplingGeometryRuntime(definition)
            self.revision += 1
            self.touch()

    def run(
        self,
        *,
        mode: ExecutionMode = ExecutionMode.FINAL,
    ) -> SamplingRuntimeResult:
        with self._lock:
            if self.runtime is None:
                raise RuntimeError("No Sampling / Geometry pipeline configured")
            self.touch()
            resolved_inputs = resolve_pipeline_inputs(
                self.pipeline_definition,
                self.sources,
            )
            return self.runtime.run(resolved_inputs, mode=mode)


    def clear_program_sample(self) -> None:
        self.program_sample = None
        self.program_sample_signature = None

    def set_program_sample(self, sample: Any, signature: str) -> None:
        with self._lock:
            self.program_sample = sample
            self.program_sample_signature = signature
            self.touch()

    def get_program_sample(self, signature: str) -> Any:
        with self._lock:
            if self.program_sample is None:
                raise RuntimeError("No cached Sampling Program Data Blocks. Run Program first.")
            if self.program_sample_signature != signature:
                raise RuntimeError("Sampling definition changed. Run Program again before Formulate.")
            self.touch()
            return self.program_sample

    def get_source(self, name: str) -> Any:
        try:
            return self.sources[name]
        except KeyError as exc:
            raise KeyError(f"Unknown Sampling / Geometry source: {name}") from exc

    def get_artifact(self, node_id: str, port: str):
        if self.runtime is None:
            raise RuntimeError("No Sampling / Geometry pipeline configured")
        return self.runtime.get_artifact(node_id, port)


class SamplingGeometrySessionManager:
    def __init__(self, *, ttl_seconds: float = 3600.0) -> None:
        self._sessions: dict[str, SamplingGeometrySession] = {}
        self._lock = threading.RLock()
        self.ttl_seconds = float(ttl_seconds)

    def create(self) -> SamplingGeometrySession:
        session = SamplingGeometrySession()
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> SamplingGeometrySession:
        with self._lock:
            try:
                session = self._sessions[session_id]
            except KeyError as exc:
                raise KeyError(
                    f"Unknown Sampling / Geometry session: {session_id}"
                ) from exc
        session.touch()
        return session

    def close(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
