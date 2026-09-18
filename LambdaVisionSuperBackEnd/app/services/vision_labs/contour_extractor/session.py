from __future__ import annotations

from dataclasses import dataclass, field
import threading, time, uuid
from typing import Any

from app.services.vision_labs.image.types import ImageFrame
from app.services.vision_labs.contour_extractor.models import ContourExtractorDefinition
from app.services.vision_labs.contour_extractor.runtime import ContourExtractorRuntime, ContourExtractorResult


@dataclass
class ContourExtractorSession:
    session_id: str = field(default_factory=lambda: f"contourlab_{uuid.uuid4().hex}")
    definition: ContourExtractorDefinition = field(default_factory=ContourExtractorDefinition)
    raw_image: ImageFrame | None = None
    result: ContourExtractorResult | None = None
    revision: int = 0
    last_activity: float = field(default_factory=time.time)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def touch(self): self.last_activity = time.time()

    def set_definition(self, definition: ContourExtractorDefinition):
        with self._lock:
            self.definition = definition
            self.revision += 1
            self.touch()

    def run(self, raw_image: ImageFrame, definition: ContourExtractorDefinition | None = None, *, load_service=None, run_service=None):
        with self._lock:
            self.raw_image = raw_image
            if definition is not None:
                self.definition = definition
            self.result = ContourExtractorRuntime(self.definition).run(raw_image, load_service=load_service, run_service=run_service)
            self.revision += 1; self.touch()
            return self.result


class ContourSessionManager:
    def __init__(self):
        self._sessions: dict[str, ContourExtractorSession] = {}
        self._lock = threading.RLock()
    def create(self):
        session = ContourExtractorSession()
        with self._lock: self._sessions[session.session_id] = session
        return session
    def get(self, session_id: str):
        with self._lock:
            if session_id not in self._sessions: raise KeyError(f"Unknown Contour Extractor session: {session_id}")
            return self._sessions[session_id]
    def close(self, session_id: str):
        with self._lock: return self._sessions.pop(session_id, None) is not None


CONTOUR_SESSION_MANAGER = ContourSessionManager()
