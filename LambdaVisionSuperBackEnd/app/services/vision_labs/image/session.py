from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading
import time
from typing import Any
import uuid

import cv2
import numpy as np

from app.services.vision_labs.core import ExecutionMode
from app.services.vision_labs.image.pipeline import ImagePipelineDefinition, PipelineCompiler
from app.services.vision_labs.image.runtime import Artifact, ImagePipelineRuntime, RuntimeResult
from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame


class PreviewEncoder:
    @staticmethod
    def encode(
        value: Any,
        *,
        max_width: int = 1200,
        quality: int = 82,
    ) -> tuple[bytes, str]:
        if isinstance(value, ImageFrame):
            data = value.data
            if value.color_space == ColorSpace.RGB and data.ndim == 3:
                data = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
            elif value.color_space == ColorSpace.HSV and data.ndim == 3:
                data = cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
            ext = ".jpg"
            params = [cv2.IMWRITE_JPEG_QUALITY, int(max(20, min(100, quality)))]
            mime = "image/jpeg"
        elif isinstance(value, BinaryMask):
            data = value.data
            ext = ".png"
            params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
            mime = "image/png"
        else:
            raise TypeError(f"Preview is not supported for {type(value).__name__}")

        if max_width > 0 and data.shape[1] > max_width:
            scale = max_width / float(data.shape[1])
            new_size = (max_width, max(1, int(round(data.shape[0] * scale))))
            data = cv2.resize(data, new_size, interpolation=cv2.INTER_AREA)

        ok, encoded = cv2.imencode(ext, data, params)
        if not ok:
            raise RuntimeError("Failed to encode preview image")
        return encoded.tobytes(), mime


@dataclass
class ViewSubscription:
    viewer_id: str
    node_id: str | None = None
    port: str | None = None
    source_name: str | None = None
    max_width: int = 1200
    quality: int = 82


class RealtimeController:
    """One-slot queue: intermediate slider updates are coalesced; latest revision wins."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1)
        self.latest_client_revision: int = -1

    def submit(self, payload: dict[str, Any]) -> None:
        revision = int(payload.get("revision", self.latest_client_revision + 1))
        self.latest_client_revision = max(self.latest_client_revision, revision)
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        try:
            self._queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass

    async def next(self) -> dict[str, Any]:
        return await self._queue.get()

    def done(self) -> None:
        self._queue.task_done()

    def is_stale(self, revision: int) -> bool:
        return revision < self.latest_client_revision


@dataclass
class ImageLabSession:
    session_id: str = field(default_factory=lambda: f"imglab_{uuid.uuid4().hex}")
    sources: dict[str, ImageFrame] = field(default_factory=dict)
    pipeline_definition: ImagePipelineDefinition | None = None
    runtime: ImagePipelineRuntime | None = None
    viewers: dict[str, ViewSubscription] = field(default_factory=dict)
    revision: int = 0
    last_activity: float = field(default_factory=time.time)
    realtime: RealtimeController = field(default_factory=RealtimeController)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def touch(self) -> None:
        self.last_activity = time.time()

    def set_source(self, name: str, image: ImageFrame) -> None:
        with self._lock:
            self.sources[name] = image
            self.revision += 1
            self.touch()
            if self.runtime is not None:
                self.runtime.artifacts.clear()

    def set_pipeline(self, definition: ImagePipelineDefinition) -> None:
        with self._lock:
            runtime = ImagePipelineRuntime(definition, compiler=PipelineCompiler())
            self.pipeline_definition = definition
            self.runtime = runtime
            self.revision += 1
            self.touch()

    def run(self, *, mode: ExecutionMode = ExecutionMode.FINAL) -> RuntimeResult:
        with self._lock:
            if self.runtime is None:
                raise RuntimeError("No pipeline has been configured for this session")
            self.touch()
            return self.runtime.run(self.sources, mode=mode)

    def update_parameters(
        self,
        node_id: str,
        changes: dict[str, Any],
        *,
        mode: ExecutionMode = ExecutionMode.INTERACTIVE,
    ) -> RuntimeResult:
        with self._lock:
            if self.runtime is None or self.pipeline_definition is None:
                raise RuntimeError("No pipeline has been configured for this session")

            found = False
            for node in self.pipeline_definition.nodes:
                if node.id == node_id:
                    node.parameters.update(changes)
                    found = True
                    break
            if not found:
                raise KeyError(f"Unknown pipeline node: {node_id}")

            self.revision += 1
            self.touch()
            return self.runtime.update_parameters(node_id, changes, mode=mode)

    def get_source(self, name: str) -> ImageFrame:
        try:
            return self.sources[name]
        except KeyError as exc:
            raise KeyError(f"Unknown session source: {name}") from exc

    def get_artifact(self, node_id: str, port: str) -> Artifact:
        if self.runtime is None:
            raise RuntimeError("No pipeline has been configured for this session")
        return self.runtime.get_artifact(node_id, port)


class ImageLabSessionManager:
    def __init__(self, *, ttl_seconds: float = 3600.0) -> None:
        self._sessions: dict[str, ImageLabSession] = {}
        self._lock = threading.RLock()
        self.ttl_seconds = float(ttl_seconds)

    def create(self) -> ImageLabSession:
        session = ImageLabSession()
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> ImageLabSession:
        with self._lock:
            try:
                session = self._sessions[session_id]
            except KeyError as exc:
                raise KeyError(f"Unknown Image LAB session: {session_id}") from exc
        session.touch()
        return session

    def close(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def list_ids(self) -> list[str]:
        with self._lock:
            return list(self._sessions)

    def cleanup_expired(self) -> list[str]:
        cutoff = time.time() - self.ttl_seconds
        removed: list[str] = []
        with self._lock:
            for session_id, session in list(self._sessions.items()):
                if session.last_activity < cutoff:
                    del self._sessions[session_id]
                    removed.append(session_id)
        return removed
