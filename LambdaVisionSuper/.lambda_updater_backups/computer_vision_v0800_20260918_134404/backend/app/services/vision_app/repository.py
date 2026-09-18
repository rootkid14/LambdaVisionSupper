from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

import cv2
import numpy as np

from app.core.config import get_base_dir
from app.services.vision_app.models import VisionProgramDefinition, model_to_dict

_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return (text or "vision-program")[:80]


class VisionProgramRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (get_base_dir() / "storage" / "vision_apps" / "programs")
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, program_id: str, *, create: bool = True) -> Path:
        if not _SAFE_ID.fullmatch(program_id):
            raise ValueError("Vision Program id may contain only letters, numbers, dot, underscore and dash")
        path = self.root / program_id
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def allocate_id(self, name: str) -> str:
        base = _slugify(name)
        candidate = base
        suffix = 2
        while (self.root / candidate / "program.json").exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def save(self, program: VisionProgramDefinition) -> VisionProgramDefinition:
        directory = self._dir(program.program_id)
        payload = model_to_dict(program)
        payload["saved_at"] = datetime.now(timezone.utc).isoformat()
        (directory / "program.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return VisionProgramDefinition(**payload)

    def get(self, program_id: str) -> VisionProgramDefinition:
        path = self._dir(program_id, create=False) / "program.json"
        if not path.exists():
            raise FileNotFoundError(f"Vision Program not found: {program_id}")
        return VisionProgramDefinition(**json.loads(path.read_text(encoding="utf-8")))

    def list(self) -> list[VisionProgramDefinition]:
        programs: list[VisionProgramDefinition] = []
        for directory in sorted(p for p in self.root.iterdir() if p.is_dir()):
            path = directory / "program.json"
            if not path.exists():
                continue
            try:
                programs.append(VisionProgramDefinition(**json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return sorted(programs, key=lambda item: item.name.lower())

    def delete(self, program_id: str) -> bool:
        path = self._dir(program_id, create=False)
        if not path.exists():
            return False
        shutil.rmtree(path)
        return True

    def master_path(self, program_id: str) -> Path:
        return self._dir(program_id) / "master.png"

    def has_master(self, program_id: str) -> bool:
        return self.master_path(program_id).exists()

    def save_master_bytes(self, program_id: str, raw: bytes) -> list[int]:
        if not raw:
            raise ValueError("Master image upload body is empty")
        encoded = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Master image could not be decoded")
        if not cv2.imwrite(str(self.master_path(program_id)), image):
            raise RuntimeError("Failed to write master image")
        return list(image.shape)

    def load_master(self, program_id: str) -> np.ndarray:
        path = self.master_path(program_id)
        if not path.exists():
            raise FileNotFoundError(f"Master image not found for program: {program_id}")
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Stored master image could not be read: {path}")
        return image
