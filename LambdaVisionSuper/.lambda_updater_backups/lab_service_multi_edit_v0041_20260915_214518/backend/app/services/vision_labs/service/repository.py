from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from app.core.config import get_base_dir
from app.services.vision_labs.service.models import LabServiceDefinition


_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value:
        value = "lab-service"
    return value[:80]


class LabServiceRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (
            get_base_dir() / "storage" / "vision_labs" / "services"
        )
        self.root.mkdir(parents=True, exist_ok=True)

    def _service_dir(self, service_id: str) -> Path:
        if not _SAFE_ID.fullmatch(service_id):
            raise ValueError(
                "Lab Service id may contain only letters, numbers, dot, underscore and dash"
            )
        path = self.root / service_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _version_filename(version: int) -> str:
        return f"v{int(version):04d}.json"

    def _next_version(self, service_id: str) -> int:
        service_dir = self._service_dir(service_id)
        versions: list[int] = []
        for path in service_dir.glob("v*.json"):
            match = re.fullmatch(r"v(\d+)\.json", path.name)
            if match:
                versions.append(int(match.group(1)))
        return (max(versions) if versions else 0) + 1

    def deploy(
        self,
        *,
        name: str,
        lab_type: str,
        inputs,
        outputs,
        pipeline_snapshot: dict,
        service_id: str | None = None,
        description: str | None = None,
    ) -> LabServiceDefinition:
        resolved_id = service_id or _slugify(name)
        if not _SAFE_ID.fullmatch(resolved_id):
            raise ValueError("Invalid Lab Service id")

        version = self._next_version(resolved_id)
        now = _now_iso()
        definition = LabServiceDefinition(
            service_id=resolved_id,
            name=name.strip(),
            lab_type=lab_type,
            version=version,
            status="deployed",
            inputs=inputs,
            outputs=outputs,
            pipeline_snapshot=pipeline_snapshot,
            description=description,
            created_at=now,
            deployed_at=now,
        )

        service_dir = self._service_dir(resolved_id)
        payload = json.dumps(model_to_dict(definition), indent=2)
        (service_dir / self._version_filename(version)).write_text(
            payload,
            encoding="utf-8",
        )
        (service_dir / "active.json").write_text(payload, encoding="utf-8")
        return definition

    def get(self, service_id: str, version: int | None = None) -> LabServiceDefinition:
        service_dir = self._service_dir(service_id)
        path = (
            service_dir / self._version_filename(version)
            if version is not None
            else service_dir / "active.json"
        )
        if not path.exists():
            if version is None:
                raise FileNotFoundError(f"Lab Service not found: {service_id}")
            raise FileNotFoundError(
                f"Lab Service version not found: {service_id}@v{version}"
            )
        return LabServiceDefinition(**json.loads(path.read_text(encoding="utf-8")))

    def list_active(self) -> list[LabServiceDefinition]:
        services: list[LabServiceDefinition] = []
        for service_dir in sorted(path for path in self.root.iterdir() if path.is_dir()):
            active = service_dir / "active.json"
            if not active.exists():
                continue
            try:
                services.append(
                    LabServiceDefinition(
                        **json.loads(active.read_text(encoding="utf-8"))
                    )
                )
            except Exception:
                continue
        return sorted(services, key=lambda item: item.name.lower())

    def list_versions(self, service_id: str) -> list[LabServiceDefinition]:
        service_dir = self._service_dir(service_id)
        definitions: list[LabServiceDefinition] = []
        for path in sorted(service_dir.glob("v*.json")):
            try:
                definitions.append(
                    LabServiceDefinition(
                        **json.loads(path.read_text(encoding="utf-8"))
                    )
                )
            except Exception:
                continue
        return sorted(definitions, key=lambda item: item.version, reverse=True)
