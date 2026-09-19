from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event, RLock, Thread
from time import monotonic
from typing import Any, Callable

import cv2
import numpy as np

from app.services.vision_app.endpoint_registry import safe_alias
from app.services.vision_app.models import CameraDeclaration, SoftTriggerConfig, VisionProgramDefinition
from app.services.vision_app.workspace_runtime import workspace_by_alias


@dataclass
class SoftTriggerRuntimeState:
    workspace_alias: str
    camera_alias: str
    config: SoftTriggerConfig
    armed: bool = True
    pixel_count: int = 0
    active_ratio: float = 0.0
    roi_pixels: int = 0
    fires: int = 0
    last_fire_monotonic: float = 0.0
    last_fire_sequence: int = 0
    last_error: str = ""
    frame_counter: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace_alias,
            "camera": self.camera_alias,
            "enabled": self.config.enabled,
            "armed": self.armed,
            "pixel_count": self.pixel_count,
            "active_ratio": self.active_ratio,
            "roi_pixels": self.roi_pixels,
            "fires": self.fires,
            "last_fire_sequence": self.last_fire_sequence,
            "last_error": self.last_error,
        }


@dataclass
class StreamSession:
    program_id: str
    workspace_alias: str
    camera_alias: str
    camera: CameraDeclaration
    reasons: set[str] = field(default_factory=set)
    stop: Event = field(default_factory=Event)
    thread: Thread | None = None
    running: bool = False
    sequence: int = 0
    fps: float = 0.0
    last_error: str = ""
    width: int = 0
    height: int = 0
    latest_image: np.ndarray | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace_alias,
            "camera": self.camera_alias,
            "driver": self.camera.driver,
            "running": self.running,
            "sequence": self.sequence,
            "fps": self.fps,
            "last_error": self.last_error,
            "width": self.width,
            "height": self.height,
            "consumers": sorted(self.reasons),
        }


class StreamingServiceManager:
    """Workspace-owned backend stream plane.

    A workspace owns its Camera declarations, so stream identity is
    (program_id, workspace_alias), not camera alias alone. This allows every
    workspace to use a camera alias like ``main`` without frame/session leakage.

    v0.14.1 implements persistent native Basler streaming. HTTP/TCP fields remain
    declaration scaffolding for a later Raspberry Pi / URL streaming transport.
    Browser preview is a lazy consumer; Soft Trigger reads the in-memory frame
    directly and therefore does not depend on browser JPEG transport.
    """

    def __init__(
        self,
        repository,
        camera_controller,
        *,
        on_trigger: Callable[[str, str, str, np.ndarray, int], None] | None = None,
        on_status: Callable[[str, str, str, dict[str, Any], dict[str, Any]], None] | None = None,
    ) -> None:
        self.repository = repository
        self.camera_controller = camera_controller
        self.on_trigger = on_trigger
        self.on_status = on_status
        self._sessions: dict[tuple[str, str], StreamSession] = {}
        self._soft: dict[tuple[str, str], SoftTriggerRuntimeState] = {}
        self._lock = RLock()

    @staticmethod
    def camera_alias(camera: CameraDeclaration) -> str:
        return safe_alias(camera.alias, camera.declaration_id)

    @staticmethod
    def workspace_camera(program: VisionProgramDefinition, workspace_alias: str) -> tuple[Any, CameraDeclaration]:
        workspace = workspace_by_alias(program, workspace_alias)
        camera = next(
            (
                c for c in workspace.cameras.devices
                if c.enabled and c.declaration_id == workspace.camera_id
            ),
            None,
        )
        if camera is None:
            raise RuntimeError(f"Workspace {workspace.name} has no enabled assigned camera")
        return workspace, camera

    @staticmethod
    def _device_info(pylon: Any, device_id: str):
        info = pylon.DeviceInfo()
        if "." in device_id and device_id.replace(".", "").isdigit():
            info.SetPropertyValue("IpAddress", device_id)
        else:
            info.SetPropertyValue("SerialNumber", device_id)
        return info

    @staticmethod
    def analyze_frame(image: np.ndarray, config: SoftTriggerConfig) -> dict[str, Any]:
        if config.roi is None:
            return {"pixel_count": 0, "active_ratio": 0.0, "roi_pixels": 0, "valid": False}
        h, w = image.shape[:2]
        rect = config.roi
        x1 = max(0, min(w - 1, int(round(rect.x * w))))
        y1 = max(0, min(h - 1, int(round(rect.y * h))))
        x2 = max(x1 + 1, min(w, int(round((rect.x + rect.w) * w))))
        y2 = max(y1 + 1, min(h, int(round((rect.y + rect.h) * h))))
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            return {"pixel_count": 0, "active_ratio": 0.0, "roi_pixels": 0, "valid": False}
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
        mask = gray <= int(config.pixel_threshold) if config.threshold_mode == "dark" else gray >= int(config.pixel_threshold)
        count = int(np.count_nonzero(mask))
        total = int(mask.size)
        return {
            "pixel_count": count,
            "active_ratio": float(count) / float(total) if total else 0.0,
            "roi_pixels": total,
            "valid": True,
        }

    def _notify(self, program_id: str, workspace_alias: str) -> None:
        if self.on_status is None:
            return
        with self._lock:
            session = self._sessions.get((program_id, workspace_alias))
            stream = session.as_dict() if session else {
                "workspace": workspace_alias, "camera": "", "running": False,
                "sequence": 0, "fps": 0.0, "last_error": "",
                "width": 0, "height": 0, "consumers": [],
            }
            soft = self._soft.get((program_id, workspace_alias))
            soft_dict = soft.as_dict() if soft else {}
            camera_alias = session.camera_alias if session else soft_dict.get("camera", "")
        self.on_status(program_id, workspace_alias, camera_alias, stream, soft_dict)

    def status(self, program_id: str, workspace_alias: str) -> dict[str, Any]:
        with self._lock:
            session = self._sessions.get((program_id, workspace_alias))
            stream = session.as_dict() if session else {
                "workspace": workspace_alias, "camera": "", "running": False,
                "sequence": 0, "fps": 0.0, "last_error": "",
                "width": 0, "height": 0, "consumers": [],
            }
            soft = self._soft.get((program_id, workspace_alias))
        return {"stream": stream, "soft_trigger": soft.as_dict() if soft else None}

    def latest_frame(self, program_id: str, workspace_alias: str) -> tuple[np.ndarray, int]:
        with self._lock:
            session = self._sessions.get((program_id, workspace_alias))
            if session is None or session.latest_image is None:
                raise RuntimeError(f"No Streaming_frame available for workspace {workspace_alias}")
            return np.ascontiguousarray(session.latest_image.copy()), int(session.sequence)

    def jpeg(self, program_id: str, workspace_alias: str, quality: int = 82) -> tuple[bytes, int]:
        image, seq = self.latest_frame(program_id, workspace_alias)
        ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            raise RuntimeError("Unable to encode Streaming_frame")
        return encoded.tobytes(), seq

    def _process_soft(self, program_id: str, workspace_alias: str, camera_alias: str, image: np.ndarray, sequence: int) -> None:
        with self._lock:
            state = self._soft.get((program_id, workspace_alias))
        if state is None:
            return
        state.frame_counter += 1
        if state.frame_counter % max(1, int(state.config.frame_stride)):
            return

        metrics = self.analyze_frame(image, state.config)
        state.pixel_count = int(metrics["pixel_count"])
        state.active_ratio = float(metrics["active_ratio"])
        state.roi_pixels = int(metrics["roi_pixels"])

        if not metrics["valid"] or not state.config.enabled:
            return

        if not state.armed:
            if state.pixel_count <= min(int(state.config.reset_pixel_count), int(state.config.trigger_pixel_count)):
                state.armed = True
            return

        now = monotonic()
        cooldown_s = max(0.0, float(state.config.cooldown_ms) / 1000.0)
        if state.pixel_count < int(state.config.trigger_pixel_count):
            return
        if (now - state.last_fire_monotonic) < cooldown_s:
            return

        state.armed = False
        state.fires += 1
        state.last_fire_monotonic = now
        state.last_fire_sequence = sequence

        if self.on_trigger is not None:
            Thread(
                target=self.on_trigger,
                args=(program_id, workspace_alias, camera_alias, np.ascontiguousarray(image.copy()), sequence),
                daemon=True,
                name=f"soft-trigger-{program_id}-{workspace_alias}",
            ).start()

    def _run_basler(self, session: StreamSession) -> None:
        declaration = session.camera
        device_id = declaration.basler_device_id.strip()
        if not device_id:
            session.last_error = "Basler device id/IP is blank"
            self._notify(session.program_id, session.workspace_alias)
            return

        pylon = self.camera_controller._load_pylon()
        factory = pylon.TlFactory.GetInstance()
        camera = pylon.InstantCamera(factory.CreateDevice(self._device_info(pylon, device_id)))
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        last_ts = monotonic()
        ema_fps = 0.0
        target_interval = 1.0 / max(0.5, float(declaration.stream_max_fps))

        try:
            camera.Open()
            try:
                camera.ExposureTime.SetValue(float(declaration.exposure_us))
            except Exception:
                pass
            camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            session.running = True
            self._notify(session.program_id, session.workspace_alias)

            while not session.stop.is_set():
                loop_started = monotonic()
                try:
                    result = camera.RetrieveResult(
                        min(int(declaration.grab_timeout_ms), 1000),
                        pylon.TimeoutHandling_ThrowException,
                    )
                except Exception as exc:
                    session.last_error = str(exc)
                    self._notify(session.program_id, session.workspace_alias)
                    if session.stop.wait(0.02):
                        break
                    continue

                try:
                    if not result.GrabSucceeded():
                        session.last_error = "Basler stream grab did not succeed"
                        continue
                    image = np.ascontiguousarray(converter.Convert(result).GetArray())
                finally:
                    result.Release()

                now = monotonic()
                inst = 1.0 / max(1e-6, now - last_ts)
                ema_fps = inst if ema_fps <= 0.0 else ema_fps * 0.85 + inst * 0.15
                last_ts = now
                session.sequence += 1
                session.latest_image = image
                session.fps = ema_fps
                session.width = int(image.shape[1])
                session.height = int(image.shape[0])
                session.last_error = ""
                self._process_soft(
                    session.program_id,
                    session.workspace_alias,
                    session.camera_alias,
                    image,
                    session.sequence,
                )
                self._notify(session.program_id, session.workspace_alias)

                elapsed = monotonic() - loop_started
                if elapsed < target_interval:
                    session.stop.wait(target_interval - elapsed)
        except Exception as exc:
            session.last_error = str(exc)
        finally:
            session.running = False
            try:
                if camera.IsGrabbing():
                    camera.StopGrabbing()
            except Exception:
                pass
            try:
                camera.Close()
            except Exception:
                pass
            self._notify(session.program_id, session.workspace_alias)

    def ensure(self, program_id: str, workspace_alias: str, camera: CameraDeclaration, reason: str) -> dict[str, Any]:
        if camera.driver != "basler":
            raise RuntimeError(
                "Streaming v0.14.1 supports native Basler streaming only. "
                "HTTP/Raspberry Pi URL/TCP streaming remains pending."
            )
        ws_alias = safe_alias(workspace_alias, workspace_alias)
        camera_alias = self.camera_alias(camera)
        key = (program_id, ws_alias)
        with self._lock:
            session = self._sessions.get(key)
            if session is None:
                session = StreamSession(
                    program_id=program_id,
                    workspace_alias=ws_alias,
                    camera_alias=camera_alias,
                    camera=camera,
                )
                self._sessions[key] = session
            session.camera = camera
            session.camera_alias = camera_alias
            session.reasons.add(reason)
            if session.thread is None or not session.thread.is_alive():
                session.stop = Event()
                session.thread = Thread(
                    target=self._run_basler,
                    args=(session,),
                    daemon=True,
                    name=f"vision-stream-{program_id}-{ws_alias}",
                )
                session.thread.start()
        self._notify(program_id, ws_alias)
        return self.status(program_id, ws_alias)

    def release(self, program_id: str, workspace_alias: str, reason: str) -> dict[str, Any]:
        ws_alias = safe_alias(workspace_alias, workspace_alias)
        with self._lock:
            session = self._sessions.get((program_id, ws_alias))
            if session is None:
                return self.status(program_id, ws_alias)
            session.reasons.discard(reason)
            if not session.reasons:
                session.stop.set()
        self._notify(program_id, ws_alias)
        return self.status(program_id, ws_alias)

    def arm_workspace(self, program: VisionProgramDefinition, workspace_alias: str, reason_prefix: str = "soft") -> dict[str, Any]:
        workspace, camera = self.workspace_camera(program, workspace_alias)
        ws_alias = safe_alias(workspace.alias, workspace.workspace_id)
        if not workspace.soft_trigger.enabled:
            raise RuntimeError(f"Soft Trigger is disabled for workspace {workspace.name}")
        if workspace.soft_trigger.roi is None:
            raise RuntimeError(f"Soft Trigger ROI is not configured for workspace {workspace.name}")
        if camera.driver != "basler":
            raise RuntimeError("Soft Trigger v0.14.1 requires a Basler streaming camera")

        state = SoftTriggerRuntimeState(
            workspace_alias=ws_alias,
            camera_alias=self.camera_alias(camera),
            config=workspace.soft_trigger,
            armed=True,
        )
        with self._lock:
            self._soft[(program.program_id, ws_alias)] = state
        self.ensure(program.program_id, ws_alias, camera, f"{reason_prefix}:{ws_alias}")
        self._notify(program.program_id, ws_alias)
        return state.as_dict()

    def disarm_workspace(self, program: VisionProgramDefinition, workspace_alias: str, reason_prefix: str = "soft") -> None:
        workspace = workspace_by_alias(program, workspace_alias)
        ws_alias = safe_alias(workspace.alias, workspace.workspace_id)
        with self._lock:
            self._soft.pop((program.program_id, ws_alias), None)
        self.release(program.program_id, ws_alias, f"{reason_prefix}:{ws_alias}")

    def arm_program(self, program: VisionProgramDefinition) -> None:
        for workspace in program.workspaces:
            if not workspace.enabled or not workspace.soft_trigger.enabled:
                continue
            try:
                self.arm_workspace(program, workspace.alias)
            except Exception as exc:
                ws_alias = safe_alias(workspace.alias, workspace.workspace_id)
                with self._lock:
                    self._soft[(program.program_id, ws_alias)] = SoftTriggerRuntimeState(
                        workspace_alias=ws_alias,
                        camera_alias="",
                        config=workspace.soft_trigger,
                        armed=False,
                        last_error=str(exc),
                    )
                self._notify(program.program_id, ws_alias)

    def disarm_program(self, program: VisionProgramDefinition) -> None:
        for workspace in program.workspaces:
            if workspace.enabled and workspace.soft_trigger.enabled:
                try:
                    self.disarm_workspace(program, workspace.alias)
                except Exception:
                    pass

    def stop_program(self, program_id: str) -> None:
        with self._lock:
            sessions = [s for (pid, _), s in self._sessions.items() if pid == program_id]
            for session in sessions:
                session.reasons.clear()
                session.stop.set()
            for key in [key for key in self._soft if key[0] == program_id]:
                del self._soft[key]
