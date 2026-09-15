from __future__ import annotations

import json
from pathlib import Path
import re

from app.core.config import get_base_dir
from app.services.vision_labs.image.pipeline import ImagePipelineDefinition, model_to_dict


_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class ImagePipelineRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (get_base_dir() / "storage" / "vision_labs" / "image" / "pipelines")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        if not _SAFE_NAME.fullmatch(name):
            raise ValueError("Pipeline name may contain only letters, numbers, dot, underscore and dash")
        return self.root / f"{name}.json"

    def save(self, name: str, definition: ImagePipelineDefinition) -> Path:
        path = self._path(name)
        path.write_text(json.dumps(model_to_dict(definition), indent=2), encoding="utf-8")
        return path

    def load(self, name: str) -> ImagePipelineDefinition:
        path = self._path(name)
        if not path.exists():
            raise FileNotFoundError(f"Image LAB pipeline not found: {name}")
        return ImagePipelineDefinition(**json.loads(path.read_text(encoding="utf-8")))

    def list(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.json"))
