from __future__ import annotations

from collections import defaultdict, deque
from threading import Event, RLock, Thread
from time import monotonic, perf_counter
from typing import Any

import cv2
import numpy as np

from app.services.vision_app.automation_models import (
    AutomationExecutionResult,
    AutomationServiceDefinition,
    AutomationSystemState,
    AutomationTraceEntry,
    VisionRunSnapshot,
)
from app.services.vision_app.automation_runtime import AutomationExecutionContext, SafeAutomationInterpreter, validate_script
from app.services.vision_app.camera_runtime import CameraController
from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.models import VisionProgramDefinition, model_to_dict
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.runtime import VisionProgramRuntime


def _safe_alias(value: str, fallback: str) -> str:
    text = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (value or fallback).strip())
    return text.strip("_") or fallback


class AutomationManager:
    """Execution/control layer underneath the Computer Vision App.

    v1 intentionally keeps one scheduler thread per Vision Program. Event services execute synchronously
    so an inspection can deterministically reach `logic_ready -> commit_result -> run_finish`.
    """

    def __init__(self, repository=None, runtime=None, camera=None, io=None) -> None:
        self.repository = repository or VisionProgramRepository()
        self.runtime = runtime or VisionProgramRuntime()
        self.camera = camera or CameraController()
        self.io = io or ModbusIOController()
        self.registry = EndpointRegistry()
        self._states: dict[str, AutomationSystemState] = {}
        self._snapshots: dict[str, VisionRunSnapshot] = {}
        self._latest_frames: dict[str, np.ndarray] = {}
        self._trace: dict[str, deque[AutomationTraceEntry]] = defaultdict(lambda: deque(maxlen=600))
        self._threads: dict[str, Thread] = {}
        self._stops: dict[str, Event] = {}
        self._lock = RLock()

    def state(self, program_id: str) -> AutomationSystemState:
        with self._lock:
            return self._states.setdefault(program_id, AutomationSystemState(program_id=program_id))

    def snapshot(self, program_id: str) -> VisionRunSnapshot | None:
        return self._snapshots.get(program_id)

    def trace(self, program_id: str) -> list[AutomationTraceEntry]:
        return list(self._trace[program_id])

    def clear_trace(self, program_id: str) -> None:
        self._trace[program_id].clear()

    def _append_trace(self, program_id: str, entry: AutomationTraceEntry) -> None:
        self._trace[program_id].append(entry)

    def catalog(self, program_id: str) -> list[dict[str, Any]]:
        program = self.repository.get(program_id)
        return self.registry.as_dict(program, self.snapshot(program_id), self.state(program_id))

    def capture(self, program_id: str) -> np.ndarray:
        program = self.repository.get(program_id)
        state = self.state(program_id)
        state.run_state = "CAPTURING"
        image = self.camera.capture(program.camera)
        self._latest_frames[program_id] = np.ascontiguousarray(image.copy())
        state.frame_sequence += 1
        state.last_event = "camera.main.frame_ready"
        if state.run_state == "CAPTURING":
            state.run_state = "IDLE"
        self.emit(program, "camera.main.frame_ready", {"name": "camera.main.frame_ready"})
        return image

    def latest_frame_jpeg(self, program_id: str, quality: int = 94) -> bytes:
        image = self._latest_frames.get(program_id)
        if image is None:
            raise FileNotFoundError("No backend camera/test frame is available yet")
        ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            raise RuntimeError("Latest frame JPEG encoding failed")
        return encoded.tobytes()

    def set_latest_frame(self, program_id: str, image: np.ndarray, *, announce: bool = False) -> None:
        self._latest_frames[program_id] = np.ascontiguousarray(image.copy())
        if announce:
            self.state(program_id).frame_sequence += 1

    def _snapshot_from_run(self, program: VisionProgramDefinition, run) -> VisionRunSnapshot:
        global_logic: dict[str, Any] = {}
        if run.global_scope:
            for item in run.global_scope.logic_services:
                global_logic[_safe_alias(item.alias or item.service_id, item.binding_id)] = item.outputs
        roi_logic: dict[str, dict[str, Any]] = {}
        roi_meta: dict[str, Any] = {}
        roi_name = {roi.roi_id: _safe_alias(roi.alias or roi.name, roi.roi_id) for roi in program.master.rois}
        for station in run.stations:
            alias = roi_name.get(station.station_id, _safe_alias(station.station_name, station.station_id))
            roi_meta[alias] = {"station_id": station.station_id, "located": station.located, "score": station.search_score, "ok": station.ok}
            logic_map: dict[str, Any] = {}
            if station.scope:
                for item in station.scope.logic_services:
                    logic_map[_safe_alias(item.alias or item.service_id, item.binding_id)] = item.outputs
            roi_logic[alias] = logic_map
        return VisionRunSnapshot(
            program_id=program.program_id,
            run_id=run.run_id,
            global_ok=run.global_ok,
            overall_ok=run.overall_ok,
            total_ms=run.total_ms,
            global_logic=global_logic,
            roi_logic=roi_logic,
            roi_meta=roi_meta,
            benchmarks=[model_to_dict(item) for item in run.benchmarks],
        )

    def run_inspection(self, program_id: str, image: np.ndarray | None = None):
        program = self.repository.get(program_id)
        state = self.state(program_id)
        if state.run_state in {"INSPECTING", "DECIDING"}:
            raise RuntimeError("Inspection is already running")
        started = perf_counter()
        try:
            state.result = "NONE"
            state.run_state = "INSPECTING"
            state.last_error = ""
            self.emit(program, "system.run_started", {"name": "system.run_started"})
            if image is None:
                image = self._latest_frames.get(program_id)
                if image is None:
                    if program.camera.enabled and program.camera.driver != "manual":
                        image = self.capture(program_id)
                    else:
                        raise RuntimeError("No latest frame. Capture/upload an image before system.run_inspection().")
            else:
                self.set_latest_frame(program_id, image, announce=False)
            master = self.repository.load_master(program_id)
            run = self.runtime.run_test(program, master, image)
            snapshot = self._snapshot_from_run(program, run)
            self._snapshots[program_id] = snapshot
            state.run_id = run.run_id
            state.last_run_ms = run.total_ms
            state.run_state = "DECIDING"
            self.emit(program, "vision.logic_ready", {"name": "vision.logic_ready", "run_id": run.run_id, "result": "OK" if run.overall_ok else "NG"})
            if state.result == "NONE":
                self.commit_result(program_id, "OK" if run.overall_ok else "NG")
            run.overall_ok = state.result == "OK"
            state.run_state = "FINISHED"
            state.last_event = "system.run_finish"
            self.emit(program, "system.run_finish", {"name": "system.run_finish", "run_id": run.run_id, "result": state.result})
            return run
        except Exception as exc:
            state.run_state = "ERROR"
            state.result = "ERROR"
            state.last_error = str(exc)
            state.result_sequence += 1
            self.emit(program, "system.run_error", {"name": "system.run_error", "result": "ERROR"})
            raise
        finally:
            if state.last_run_ms is None:
                state.last_run_ms = (perf_counter() - started) * 1000.0

    def commit_result(self, program_id: str, result: Any) -> None:
        value = str(result).upper()
        if value not in {"OK", "NG"}:
            raise ValueError("system.commit_result expects OK or NG")
        state = self.state(program_id)
        state.result = value
        state.result_sequence += 1

    def clear_working_screen(self, program_id: str) -> None:
        state = self.state(program_id)
        state.clear_sequence += 1
        state.result = "NONE"
        state.result_sequence += 1
        if state.run_state not in {"INSPECTING", "DECIDING"}:
            state.run_state = "IDLE"


    def _declared_point(self, program: VisionProgramDefinition, path: str):
        parts = path.split(".")
        if len(parts) < 3 or parts[0] != "device":
            return None
        device_alias, point_alias = parts[1], parts[2]
        for device in program.iot.devices:
            if not device.enabled or _safe_alias(device.alias, device.declaration_id) != device_alias:
                continue
            for point in device.points:
                if point.enabled and _safe_alias(point.alias, point.point_id) == point_alias:
                    return device, point
        return None

    def _read_path(self, program: VisionProgramDefinition, event: dict[str, Any], path: str) -> Any:
        state = self.state(program.program_id)
        if path == "system.run_state": return state.run_state
        if path == "system.result": return state.result
        if path == "system.run_id": return state.run_id
        if path == "system.last_run_ms": return state.last_run_ms
        if path == "camera.main.frame_sequence": return state.frame_sequence
        declared = self._declared_point(program, path)
        if declared is not None:
            device, point = declared
            if hasattr(self.io, "read_declared_point"):
                return self.io.read_declared_point(device, point)
            # Compatibility for v0.11 test/adapters that only implement the legacy IO contract.
            return self.io.read_point(program.io, point.kind, point.address)
        if path.startswith("event."):
            return event.get(path.split(".", 1)[1])
        snap = self.snapshot(program.program_id)
        if path.startswith("vision.") and snap is not None:
            data: Any
            parts = path.split(".")
            if parts[:3] == ["vision", "global_scope", "logic"] and len(parts) >= 5:
                data = snap.global_logic.get(parts[3], {})
                rest = parts[5:] if parts[4] == "outputs" else parts[4:]
            elif len(parts) >= 4 and parts[:2] == ["vision", "roi"]:
                roi_alias = parts[2]
                if len(parts) == 4 and parts[3] in {"found", "score"}:
                    meta = snap.roi_meta.get(roi_alias, {})
                    return meta.get("located" if parts[3] == "found" else "score")
                if len(parts) >= 6 and parts[3] == "logic":
                    data = snap.roi_logic.get(roi_alias, {}).get(parts[4], {})
                    rest = parts[6:] if parts[5] == "outputs" else parts[5:]
                else:
                    raise KeyError(f"Unknown Vision endpoint: {path}")
            else:
                raise KeyError(f"Unknown Vision endpoint: {path}")
            for key in rest:
                if isinstance(data, dict) and key in data: data = data[key]
                elif isinstance(data, list) and key.isdigit(): data = data[int(key)]
                else: raise KeyError(f"Endpoint path not found: {path}")
            return data
        raise KeyError(f"Unknown/read-protected endpoint: {path}")

    def _write_path(self, program: VisionProgramDefinition, path: str, value: Any, dry_run: bool) -> None:
        declared = self._declared_point(program, path)
        if declared is not None:
            device, point = declared
            if not point.writable:
                raise KeyError(f"Endpoint is not writable: {path}")
            if not dry_run:
                if hasattr(self.io, "write_declared_point"):
                    self.io.write_declared_point(device, point, value)
                elif point.kind == "coil":
                    self.io.set_coil(program.io, point.address, bool(value))
                else:
                    raise RuntimeError("Legacy IO adapter cannot write holding registers")
            return
        raise KeyError(f"Endpoint is not writable: {path}")

    def _call_action(self, program: VisionProgramDefinition, path: str, args: list[Any], dry_run: bool) -> Any:
        if path == "system.run_inspection":
            if dry_run: return "WOULD_RUN_INSPECTION"
            return self.run_inspection(program.program_id)
        if path == "camera.main.capture":
            if dry_run: return "WOULD_CAPTURE"
            self.capture(program.program_id); return True
        if path == "system.commit_result":
            if not args: raise ValueError("system.commit_result requires OK or NG")
            if not dry_run: self.commit_result(program.program_id, args[0])
            return args[0]
        if path == "system.clear_working_screen":
            if not dry_run: self.clear_working_screen(program.program_id)
            return True
        if path.endswith(".pulse"):
            declared = self._declared_point(program, path.rsplit(".pulse", 1)[0])
            if declared is not None:
                device, point = declared
                seconds = float(args[0]) if args else point.pulse_seconds
                if not dry_run:
                    if hasattr(self.io, "pulse_declared_point"):
                        self.io.pulse_declared_point(device, point, seconds)
                    elif point.kind == "coil":
                        ok = point.address == program.io.ok_coil
                        self.io.pulse_result(program.io, ok=ok, seconds=seconds)
                    else:
                        raise RuntimeError("Legacy IO adapter cannot pulse this point")
                return True
        raise KeyError(f"Unknown action endpoint: {path}")

    def execute_service(self, program: VisionProgramDefinition, service: AutomationServiceDefinition, *, dry_run: bool = False, event: dict[str, Any] | None = None) -> AutomationExecutionResult:
        event = event or {"name": "manual"}
        ctx = AutomationExecutionContext(
            program=program,
            snapshot=self.snapshot(program.program_id),
            event=event,
            read_endpoint=lambda path: self._read_path(program, event, path),
            write_endpoint=lambda path, value, dr: self._write_path(program, path, value, dr),
            call_action=lambda path, args, dr: self._call_action(program, path, args, dr),
            trace=lambda entry: self._append_trace(program.program_id, entry),
            dry_run=dry_run,
        )
        return SafeAutomationInterpreter(ctx, service).execute(service.script)

    def emit(self, program: VisionProgramDefinition, event_name: str, payload: dict[str, Any]) -> None:
        state = self.state(program.program_id)
        state.last_event = event_name
        for service in program.automation.services:
            if not program.automation.enabled or not service.enabled or service.mode != "event" or service.event != event_name:
                continue
            result = self.execute_service(program, service, event={**payload, "name": event_name})
            if not result.ok:
                state.last_error = f"Automation service {service.name} failed"

    def run_service(self, program_id: str, service_id: str, *, dry_run: bool = False) -> AutomationExecutionResult:
        program = self.repository.get(program_id)
        service = next((item for item in program.automation.services if item.service_id == service_id), None)
        if service is None:
            raise FileNotFoundError(f"Automation service not found: {service_id}")
        return self.execute_service(program, service, dry_run=dry_run, event={"name": "manual", "result": self.state(program_id).result, "run_id": self.state(program_id).run_id})

    def validate(self, script: str):
        return validate_script(script)

    def start(self, program_id: str) -> AutomationSystemState:
        program = self.repository.get(program_id)
        with self._lock:
            thread = self._threads.get(program_id)
            if thread and thread.is_alive():
                state = self.state(program_id); state.scheduler_running = True; return state
            stop = Event(); self._stops[program_id] = stop
            thread = Thread(target=self._scheduler_loop, args=(program_id, stop), daemon=True, name=f"vision-automation-{program_id}")
            self._threads[program_id] = thread
            self.state(program_id).scheduler_running = True
            thread.start()
        return self.state(program_id)

    def stop(self, program_id: str) -> AutomationSystemState:
        stop = self._stops.get(program_id)
        if stop: stop.set()
        self.state(program_id).scheduler_running = False
        return self.state(program_id)

    def _scheduler_loop(self, program_id: str, stop: Event) -> None:
        due: dict[str, float] = {}
        while not stop.is_set():
            try:
                program = self.repository.get(program_id)
                if not program.automation.enabled:
                    stop.wait(0.25); continue
                now = monotonic()
                loop_services = [s for s in program.automation.services if s.enabled and s.mode == "loop"]
                active_ids = {s.service_id for s in loop_services}
                due = {key: val for key, val in due.items() if key in active_ids}
                for service in loop_services:
                    target = due.get(service.service_id, now)
                    if now < target: continue
                    due[service.service_id] = now + max(0.025, service.interval_ms / 1000.0)
                    result = self.execute_service(program, service, event={"name": "loop", "result": self.state(program_id).result, "run_id": self.state(program_id).run_id})
                    if not result.ok:
                        self.state(program_id).last_error = f"Loop service {service.name} failed"
                stop.wait(0.02)
            except Exception as exc:
                self.state(program_id).last_error = str(exc)
                stop.wait(0.25)
        self.state(program_id).scheduler_running = False
