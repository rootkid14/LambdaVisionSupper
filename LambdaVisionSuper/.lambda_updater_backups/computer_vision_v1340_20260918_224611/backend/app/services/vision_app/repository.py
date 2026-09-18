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


def _migrate_payload(payload: dict) -> dict:
    """Upgrade v0.7 persisted programs to the v0.8 contract in-memory.

    We never delete legacy keys here. Pydantic accepts the fields that still exist on
    WorkingConfig/MasterRoi, which lets old files round-trip safely while the editor
    starts writing the new scope/camera/locator structures.
    """
    data = json.loads(json.dumps(payload))
    data.setdefault("version", 1)
    data.setdefault("camera", {})
    data.setdefault("automation", {"enabled": True, "services": []})
    if "iot" not in data:
        legacy_io = data.get("io", {}) or {}
        data["iot"] = {
            "devices": [
                {
                    "declaration_id": "modbus_1",
                    "alias": "modbus_1",
                    "enabled": bool(legacy_io.get("enabled", False)),
                    "driver": "modbus_tcp",
                    "host": legacy_io.get("host", "192.168.1.177"),
                    "port": legacy_io.get("port", 502),
                    "unit_id": legacy_io.get("device_id", 1),
                    "points": [
                        {"point_id":"x1","alias":"X1","enabled":True,"kind":legacy_io.get("trigger_kind", "discrete_input"),"address":legacy_io.get("trigger_address",0),"description":"Legacy trigger input","pulse_seconds":legacy_io.get("pulse_seconds",1.0)},
                        {"point_id":"y1","alias":"Y1","enabled":True,"kind":"coil","address":legacy_io.get("ok_coil",0),"description":"Legacy OK output","pulse_seconds":legacy_io.get("pulse_seconds",1.0)},
                        {"point_id":"y2","alias":"Y2","enabled":True,"kind":"coil","address":legacy_io.get("ng_coil",1),"description":"Legacy NG output","pulse_seconds":legacy_io.get("pulse_seconds",1.0)},
                    ],
                }
            ]
        }

    master = data.setdefault("master", {})
    if "locator" not in master:
        legacy = None
        for roi in master.get("rois", []):
            if isinstance(roi, dict) and isinstance(roi.get("search"), dict):
                legacy = roi.get("search")
                break
        master["locator"] = legacy or {
            "method": "manual",
            "blur_kernel": 9,
            "template_threshold": 0.65,
            "geometry": {"enabled": True, "search_margin_px": 80, "max_shift_px": 120},
        }

    working = data.setdefault("working", {})
    if "global_scope" not in working:
        legacy_global = working.get("global_services", []) or []
        working["global_scope"] = {
            "enable_filter": False,
            "filter_services": [],
            "enable_logic": bool(legacy_global),
            "logic_services": legacy_global,
            "enable_decision": False,
            "decision": {},
        }
    if "station_scopes" not in working:
        station_scopes = {}
        for station_id, bindings in (working.get("station_services", {}) or {}).items():
            station_scopes[station_id] = {
                "enable_filter": False,
                "filter_services": [],
                "enable_logic": bool(bindings),
                "logic_services": bindings,
                "enable_decision": False,
                "decision": {},
            }
        working["station_scopes"] = station_scopes
    working.setdefault("station_execution", "sequential")

    if "cameras" not in data:
        legacy_camera = data.get("camera", {}) or {}
        driver = legacy_camera.get("driver", "manual")
        mapped = "http" if driver == "url" else "basler" if driver == "basler" else "simulated"
        capture_url = str(legacy_camera.get("capture_url", "http://pi3b.local:8000/capture"))
        host = "pi3b.local"
        port = 8000
        capture_path = "/capture"
        try:
            from urllib.parse import urlparse
            parsed = urlparse(capture_url)
            host = parsed.hostname or host
            port = parsed.port or port
            capture_path = parsed.path or capture_path
            if parsed.query:
                capture_path += "?" + parsed.query
        except Exception:
            pass
        data["cameras"] = {"devices": [{
            "declaration_id": "camera_main",
            "alias": "main",
            "enabled": bool(legacy_camera.get("enabled", True)),
            "driver": mapped,
            "basler_device_id": legacy_camera.get("basler_device_id", ""),
            "exposure_us": legacy_camera.get("exposure_us", 5000.0),
            "grab_timeout_ms": legacy_camera.get("grab_timeout_ms", 5000),
            "host": host,
            "port": port,
            "capture_path": capture_path,
            "stream_path": "",
            "http_timeout_s": legacy_camera.get("http_timeout_s", 8.0),
            "image_slot": "Current_image",
            "stream_slot": "Streaming_frame",
            "custom_apis": [],
        }]}

    if "workspaces" not in data:
        data["workspaces"] = [{
            "workspace_id": "workspace_1",
            "name": "Workspace 1",
            "alias": "workspace_1",
            "enabled": True,
            "camera_id": "camera_main",
            "input_binding": "camera.main.Current_image",
            "master": master,
            "working": working,
        }]
    # v0.13.1: migrate generic image-slot bindings into an explicit one-camera-per-workspace relation.
    cameras = (data.get("cameras") or {}).get("devices", []) or []
    for workspace in data.get("workspaces", []) or []:
        if workspace.get("camera_id"):
            continue
        binding = str(workspace.get("input_binding", ""))
        camera_id = ""
        parts = binding.split(".")
        if len(parts) >= 3 and parts[0] == "camera":
            alias = parts[1]
            for camera in cameras:
                if camera.get("declaration_id") == alias or camera.get("alias") == alias:
                    camera_id = str(camera.get("declaration_id", ""))
                    break
        workspace["camera_id"] = camera_id or (str(cameras[0].get("declaration_id")) if cameras else "")
    data.setdefault("active_workspace_id", (data.get("workspaces") or [{"workspace_id":"workspace_1"}])[0].get("workspace_id", "workspace_1"))
    data.setdefault("simulator", {"enabled": False, "camera_sequence_mode": "fixed", "stream_fps": 4.0})  # legacy hidden
    data["version"] = max(6, int(data.get("version", 1)))
    return data


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
        # v0.13.1: each workspace owns one declared camera. Resolve its stable image slot
        # before persisting so old runtime code can continue consuming input_binding.
        cameras_by_id = {camera.declaration_id: camera for camera in program.cameras.devices}
        for workspace in program.workspaces:
            camera = cameras_by_id.get(workspace.camera_id)
            if camera is not None:
                from app.services.vision_app.endpoint_registry import safe_alias
                workspace.input_binding = f"camera.{safe_alias(camera.alias, camera.declaration_id)}.{camera.image_slot}"
        # Keep the old single-workspace/single-camera fields mirrored so v0.8-v0.12
        # runners and external integrations remain readable during the v5 migration.
        if program.workspaces:
            first = program.workspaces[0]
            program.master = first.master
            program.working = first.working
        if program.cameras.devices:
            camera = program.cameras.devices[0]
            program.camera.enabled = camera.enabled
            if camera.driver == "basler":
                program.camera.driver = "basler"
                program.camera.basler_device_id = camera.basler_device_id
                program.camera.exposure_us = camera.exposure_us
                program.camera.grab_timeout_ms = camera.grab_timeout_ms
            elif camera.driver == "http":
                program.camera.driver = "url"
                program.camera.capture_url = f"http://{camera.host}:{camera.port}{camera.capture_path}"
                program.camera.http_timeout_s = camera.http_timeout_s
            else:
                program.camera.driver = "manual"
        directory = self._dir(program.program_id)
        payload = model_to_dict(program)
        payload["saved_at"] = datetime.now(timezone.utc).isoformat()
        (directory / "program.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return VisionProgramDefinition(**payload)

    def get(self, program_id: str) -> VisionProgramDefinition:
        path = self._dir(program_id, create=False) / "program.json"
        if not path.exists():
            raise FileNotFoundError(f"Vision Program not found: {program_id}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        return VisionProgramDefinition(**_migrate_payload(raw))

    def list(self) -> list[VisionProgramDefinition]:
        programs: list[VisionProgramDefinition] = []
        for directory in sorted(p for p in self.root.iterdir() if p.is_dir()):
            path = directory / "program.json"
            if not path.exists():
                continue
            try:
                programs.append(VisionProgramDefinition(**_migrate_payload(json.loads(path.read_text(encoding="utf-8")))))
            except Exception:
                continue
        return sorted(programs, key=lambda item: item.name.lower())

    def delete(self, program_id: str) -> bool:
        path = self._dir(program_id, create=False)
        if not path.exists():
            return False
        shutil.rmtree(path)
        return True

    def master_path(self, program_id: str, workspace_id: str | None = None) -> Path:
        if not workspace_id or workspace_id == "workspace_1":
            return self._dir(program_id) / "master.png"
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", workspace_id)
        directory = self._dir(program_id) / "workspaces" / safe
        directory.mkdir(parents=True, exist_ok=True)
        return directory / "master.png"

    def has_master(self, program_id: str, workspace_id: str | None = None) -> bool:
        return self.master_path(program_id, workspace_id).exists()

    def save_master_bytes(self, program_id: str, raw: bytes, workspace_id: str | None = None) -> list[int]:
        if not raw:
            raise ValueError("Master image upload body is empty")
        encoded = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Master image could not be decoded")
        path = self.master_path(program_id, workspace_id)
        if not cv2.imwrite(str(path), image):
            raise RuntimeError("Failed to write master image")
        return list(image.shape)

    def load_master(self, program_id: str, workspace_id: str | None = None) -> np.ndarray:
        path = self.master_path(program_id, workspace_id)
        if not path.exists() and workspace_id and workspace_id != "workspace_1":
            legacy = self.master_path(program_id, None)
            if legacy.exists():
                path = legacy
        if not path.exists():
            raise FileNotFoundError(f"Master image not found for program/workspace: {program_id}/{workspace_id or 'workspace_1'}")
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Stored master image could not be read: {path}")
        return image

