from __future__ import annotations

import json
from pathlib import Path
import re

from app.core.config import get_base_dir
from app.services.vision_labs.sampling_geometry.pipeline import (
    SamplingPipelineDefinition,
    model_to_dict,
)


_SAFE_NAME = re.compile(r"^[A-Za-z0-9_. -]+$")


class SamplingPipelineRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (
            get_base_dir() / "storage" / "vision_labs" / "sampling_geometry" / "pipelines"
        )
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        safe = name.strip()
        if not safe or not _SAFE_NAME.fullmatch(safe):
            raise ValueError("Invalid Sampling / Geometry pipeline name")
        filename = re.sub(r"\s+", "_", safe) + ".json"
        return self.root / filename

    def save(self, name: str, pipeline: SamplingPipelineDefinition) -> Path:
        path = self._path(name)
        path.write_text(
            json.dumps(model_to_dict(pipeline), indent=2),
            encoding="utf-8",
        )
        return path

    def load(self, name: str) -> SamplingPipelineDefinition:
        path = self._path(name)
        if not path.exists():
            raise FileNotFoundError(f"Sampling / Geometry pipeline not found: {name}")
        return SamplingPipelineDefinition(
            **json.loads(path.read_text(encoding="utf-8"))
        )

    def list(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.json"))
