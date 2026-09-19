from __future__ import annotations

from collections import defaultdict, deque
from threading import Event, RLock, Thread
from time import monotonic, perf_counter
from typing import Any

import cv2
import numpy as np

from app.services.vision_app.automation_models import (
    AutomationExecutionResult, AutomationServiceDefinition, AutomationSystemState,
    AutomationTraceEntry, VisionRunSnapshot,
)
from app.services.vision_app.automation_runtime import AutomationExecutionContext, SafeAutomationInterpreter, validate_script
from app.services.vision_app.camera_runtime import CameraController
from app.services.vision_app.camera_resource_runtime import CameraResourceController
from app.services.vision_app.endpoint_registry import EndpointRegistry, safe_alias
from app.services.vision_app.frame_slot_store import VISION_FRAME_SLOTS
from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.streaming_runtime import StreamingServiceManager
from app.services.vision_app.models import VisionProgramDefinition, model_to_dict
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.runtime import VisionProgramRuntime
from app.services.vision_app.workspace_runtime import projected_program, workspace_by_alias


class AutomationManager:
    """Computer Vision control plane.

    v0.13 adds declared cameras, frame slots and multiple inspection workspaces while
    retaining the v0.11 scheduler/DSL contract. Program Automation remains global;
    scripts can explicitly orchestrate any workspace/camera object.
    """

    def __init__(self, repository=None, runtime=None, camera=None, io=None) -> None:
        self.repository = repository or VisionProgramRepository()
        self.runtime = runtime or VisionProgramRuntime()
        self.camera = camera or CameraController()
        self.camera_resources = CameraResourceController(self.camera)
        self.io = io or ModbusIOController()
        self.registry = EndpointRegistry()
        self.streaming = StreamingServiceManager(
            self.repository,
            self.camera,
            on_trigger=self._on_soft_trigger,
            on_status=self._on_stream_status,
        )
        self._states: dict[str, AutomationSystemState] = {}
        self._snapshots: dict[str, VisionRunSnapshot] = {}
        self._latest_frames: dict[tuple[str, str], np.ndarray] = {}
        self._trace: dict[str, deque[AutomationTraceEntry]] = defaultdict(lambda: deque(maxlen=800))
        self._threads: dict[str, Thread] = {}
        self._stops: dict[str, Event] = {}
        self._lock = RLock()

    def state(self, program_id: str) -> AutomationSystemState:
        with self._lock:
            state = self._states.get(program_id)
            if state is None:
                active = 'workspace_1'
                try:
                    program = self.repository.get(program_id)
                    active = safe_alias(workspace_by_alias(program, program.active_workspace_id).alias, 'workspace_1')
                except Exception:
                    pass
                state = AutomationSystemState(program_id=program_id, active_workspace=active)
                self._states[program_id] = state
            return state

    def snapshot(self, program_id: str) -> VisionRunSnapshot | None:
        return self._snapshots.get(program_id)

    def trace(self, program_id: str) -> list[AutomationTraceEntry]:
        return list(self._trace[program_id])

    def clear_trace(self, program_id: str) -> None:
        self._trace[program_id].clear()

    @staticmethod
    def normalize_key(key: str) -> str:
        raw_original = (key or "").strip()
        if raw_original.lower().startswith("key."):
            return "key." + raw_original.split(".", 1)[1].upper().replace("-", "_")
        raw = raw_original.lower()
        mapping = {
            " ": "key.SPACE", "space": "key.SPACE", "spacebar": "key.SPACE",
            "enter": "key.ENTER", "escape": "key.ESCAPE", "esc": "key.ESCAPE",
            "arrowup": "key.ARROW_UP", "arrowdown": "key.ARROW_DOWN",
            "arrowleft": "key.ARROW_LEFT", "arrowright": "key.ARROW_RIGHT",
        }
        if raw in mapping:
            return mapping[raw]
        if len(raw_original) == 1 and raw_original.isalpha():
            return f"key.{raw_original.upper()}"
        if len(raw_original) == 1 and raw_original.isdigit():
            return f"key.NUM_{raw_original}"
        if raw.startswith("f") and raw[1:].isdigit():
            return f"key.{raw.upper()}"
        return "key." + raw_original.upper().replace("-", "_").replace(" ", "_")

    def set_keyboard_state(self, program_id: str, key: str, pressed: bool) -> AutomationSystemState:
        state = self.state(program_id)
        canonical = self.normalize_key(key)
        state.keyboard_states[canonical] = bool(pressed)
        # Preserve old short aliases so existing scripts continue working.
        reverse = {
            "key.SPACE": "space", "key.ENTER": "enter", "key.ESCAPE": "escape",
            "key.ARROW_UP": "arrow_up", "key.ARROW_DOWN": "arrow_down",
            "key.ARROW_LEFT": "arrow_left", "key.ARROW_RIGHT": "arrow_right",
        }
        if canonical in reverse:
            state.keyboard_states[reverse[canonical]] = bool(pressed)
        if canonical.startswith("key.F"):
            state.keyboard_states[canonical.split(".", 1)[1].lower()] = bool(pressed)
        return state

    def _on_stream_status(self, program_id: str, workspace_alias: str, camera_alias: str, stream: dict[str, Any], soft: dict[str, Any]) -> None:
        state = self.state(program_id)
        state.stream_states[workspace_alias] = dict(stream)
        state.soft_trigger_states[workspace_alias] = dict(soft) if soft else {}

    def _on_soft_trigger(self, program_id: str, workspace_alias: str, camera_alias: str, image: np.ndarray, sequence: int) -> None:
        """Run outside the Basler stream thread so inspection cannot stall acquisition."""
        try:
            program = self.repository.get(program_id)
            workspace = workspace_by_alias(program, workspace_alias)
            if workspace.soft_trigger.snapshot_to_image_slot:
                self.set_latest_frame(program_id, image, workspace_alias=workspace_alias, announce=False)
            payload = {"workspace": workspace_alias, "camera": camera_alias, "sequence": sequence}
            self.emit(program, f"workspace.{workspace_alias}.soft_triggered", payload)
            self._append_trace(program_id, AutomationTraceEntry(
                service_id="soft_trigger", service_name=f"Soft Trigger · {workspace.name}",
                phase="stream", level="info", message="Soft Trigger threshold crossed",
                endpoint=f"workspace.{workspace_alias}.soft_triggered", value=payload,
            ))
            if workspace.soft_trigger.run_inspection:
                self.run_inspection(program_id, image=image, workspace_alias=workspace_alias)
        except Exception as exc:
            state = self.state(program_id)
            state.last_error = f"Soft Trigger {workspace_alias}: {exc}"
            soft = state.soft_trigger_states.setdefault(workspace_alias, {})
            soft["last_error"] = str(exc)

    def _append_trace(self, program_id: str, entry: AutomationTraceEntry) -> None:
        self._trace[program_id].append(entry)

    def _active_program(self, program: VisionProgramDefinition) -> VisionProgramDefinition:
        state = self.state(program.program_id)
        workspace = workspace_by_alias(program, state.active_workspace or program.active_workspace_id)
        return projected_program(program, workspace)

    def catalog(self, program_id: str) -> list[dict[str, Any]]:
        program = self._active_program(self.repository.get(program_id))
        return self.registry.as_dict(program, self.snapshot(program_id), self.state(program_id))

    @staticmethod
    def _camera(program: VisionProgramDefinition, alias: str | None = None):
        enabled = [c for c in program.cameras.devices if c.enabled]
        if not enabled:
            raise RuntimeError('No enabled camera declaration')
        if alias:
            for camera in enabled:
                if camera.declaration_id == alias or safe_alias(camera.alias, camera.declaration_id) == alias:
                    return camera
            raise KeyError(f'Camera not found: {alias}')
        return enabled[0]

    def capture(self, program_id: str, camera_alias: str | None = None) -> np.ndarray:
        raw_program = self.repository.get(program_id)
        state = self.state(program_id)
        workspace = workspace_by_alias(raw_program, state.active_workspace or raw_program.active_workspace_id)
        program = projected_program(raw_program, workspace)
        camera = self._camera(program, camera_alias)
        alias = safe_alias(camera.alias, camera.declaration_id)
        state.run_state = 'CAPTURING'
        image = self.camera_resources.capture(program_id, camera)
        self.set_latest_frame(program_id, image, workspace_alias=safe_alias(workspace.alias, workspace.workspace_id), announce=False)
        state.frame_sequence += 1
        state.last_event = f'camera.{alias}.frame_ready'
        if state.run_state == 'CAPTURING':
            state.run_state = 'IDLE'
        self.emit(program, f'camera.{alias}.frame_ready', {'camera': alias, 'workspace': safe_alias(workspace.alias, workspace.workspace_id)})
        return image

    def latest_frame_jpeg(self, program_id: str, workspace_alias: str | None = None, quality: int = 94) -> bytes:
        program = self.repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_alias or self.state(program_id).active_workspace)
        image = self._workspace_input(program, workspace)
        ok, encoded = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            raise RuntimeError('Latest frame JPEG encoding failed')
        return encoded.tobytes()

    def set_latest_frame(self, program_id: str, image: np.ndarray, *, workspace_alias: str | None = None, announce: bool = False) -> None:
        alias = workspace_alias or self.state(program_id).active_workspace or 'workspace_1'
        self._latest_frames[(program_id, alias)] = np.ascontiguousarray(image.copy())
        if announce:
            self.state(program_id).frame_sequence += 1

    def _workspace_input(self, program: VisionProgramDefinition, workspace) -> np.ndarray:
        binding = (workspace.input_binding or '').strip()
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        # Stable frames are keyed by Workspace first. This prevents identical local
        # camera aliases (for example camera.main) from leaking frames across tabs.
        frame = self._latest_frames.get((program.program_id, alias))
        if frame is not None:
            return np.ascontiguousarray(frame.copy())
        if binding.startswith('camera.'):
            parts = binding.split('.')
            if len(parts) >= 3:
                projected = projected_program(program, workspace)
                camera = self._camera(projected, parts[1])
                image = self.camera_resources.capture(program.program_id, camera)
                self.set_latest_frame(program.program_id, image, workspace_alias=alias, announce=False)
                return np.ascontiguousarray(image.copy())
        raise RuntimeError(f'Workspace {workspace.name} has no image in input binding {binding!r}')

    @staticmethod
    def _snapshot_from_run(program: VisionProgramDefinition, run) -> VisionRunSnapshot:
        global_logic: dict[str, Any] = {}
        if run.global_scope:
            for item in run.global_scope.logic_services:
                global_logic[safe_alias(item.alias or item.service_id, item.binding_id)] = item.outputs
        roi_logic: dict[str, dict[str, Any]] = {}
        roi_meta: dict[str, Any] = {}
        roi_name = {roi.roi_id: safe_alias(roi.alias or roi.name, roi.roi_id) for roi in program.master.rois}
        for station in run.stations:
            alias = roi_name.get(station.station_id, safe_alias(station.station_name, station.station_id))
            roi_meta[alias] = {'station_id': station.station_id, 'located': station.located, 'score': station.search_score, 'ok': station.ok}
            logic_map: dict[str, Any] = {}
            if station.scope:
                for item in station.scope.logic_services:
                    logic_map[safe_alias(item.alias or item.service_id, item.binding_id)] = item.outputs
            roi_logic[alias] = logic_map
        return VisionRunSnapshot(
            program_id=program.program_id, run_id=run.run_id, global_ok=run.global_ok,
            overall_ok=run.overall_ok, total_ms=run.total_ms, global_logic=global_logic,
            roi_logic=roi_logic, roi_meta=roi_meta,
            benchmarks=[model_to_dict(item) for item in run.benchmarks],
        )

    def activate_workspace(self, program_id: str, workspace_alias: str) -> AutomationSystemState:
        program = self.repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_alias)
        state = self.state(program_id)
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        if state.active_workspace != alias:
            state.active_workspace = alias
            state.workspace_activation_sequence += 1
        return state

    def run_inspection(self, program_id: str, image: np.ndarray | None = None, workspace_alias: str | None = None):
        program = self.repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_alias or self.state(program_id).active_workspace)
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        projected = projected_program(program, workspace)
        state = self.state(program_id)
        if state.run_state in {'INSPECTING', 'DECIDING'}:
            raise RuntimeError('Inspection is already running')
        started = perf_counter()
        try:
            state.run_state = 'INSPECTING'; state.last_error = ''; state.last_workspace = alias
            self.emit(program, 'system.run_started', {'workspace': alias})
            if image is None:
                image = self._workspace_input(program, workspace)
            else:
                self.set_latest_frame(program_id, image, workspace_alias=alias, announce=False)
            master = self.repository.load_master(program_id, workspace.workspace_id)
            run = self.runtime.run_test(projected, master, image)
            snapshot = self._snapshot_from_run(projected, run)
            self._snapshots[program_id] = snapshot
            workspace_result = 'OK' if run.overall_ok else 'NG'
            state.workspace_results[alias] = workspace_result
            state.run_id = run.run_id; state.last_run_ms = run.total_ms; state.run_state = 'DECIDING'
            payload = {'run_id': run.run_id, 'result': workspace_result, 'workspace': alias}
            self.emit(program, f'workspace.{alias}.logic_ready', payload)
            self.emit(program, 'vision.logic_ready', payload)  # compatibility/latest-workspace event
            # Preserve single-workspace behavior. Multi-workspace product result belongs to Automation IDE.
            if len([w for w in program.workspaces if w.enabled]) == 1 and state.result == 'NONE':
                self.commit_result(program_id, workspace_result)
            state.run_state = 'FINISHED'; state.last_event = f'workspace.{alias}.run_finish'
            self.emit(program, f'workspace.{alias}.run_finish', payload)
            return run
        except Exception as exc:
            state.run_state = 'ERROR'; state.workspace_results[alias] = 'ERROR'; state.last_error = str(exc)
            self.emit(program, 'system.run_error', {'workspace': alias, 'result': 'ERROR'})
            raise
        finally:
            if state.last_run_ms is None:
                state.last_run_ms = (perf_counter() - started) * 1000.0

    def commit_result(self, program_id: str, result: Any) -> None:
        value = str(result).upper()
        if value not in {'OK', 'NG'}:
            raise ValueError('system.commit_result expects OK or NG')
        state = self.state(program_id); state.result = value; state.result_sequence += 1
        program = self.repository.get(program_id)
        self.emit(program, 'system.run_finish', {'result': value, 'run_id': state.run_id, 'workspace': state.last_workspace})

    def clear_working_screen(self, program_id: str, workspace_alias: str | None = None) -> None:
        state = self.state(program_id); state.clear_sequence += 1
        if workspace_alias:
            state.workspace_results[safe_alias(workspace_alias, workspace_alias)] = 'NONE'
        else:
            state.result = 'NONE'; state.result_sequence += 1
        if state.run_state not in {'INSPECTING', 'DECIDING'}:
            state.run_state = 'IDLE'

    def _declared_point(self, program: VisionProgramDefinition, path: str):
        parts = path.split('.')
        if len(parts) < 3 or parts[0] != 'device': return None
        for device in program.iot.devices:
            if not device.enabled or safe_alias(device.alias, device.declaration_id) != parts[1]: continue
            for point in device.points:
                if point.enabled and safe_alias(point.alias, point.point_id) == parts[2]: return device, point
        return None

    def _camera_path(self, program: VisionProgramDefinition, path: str):
        parts = path.split('.')
        if len(parts) < 3 or parts[0] != 'camera': return None
        camera = self._camera(program, parts[1])
        return camera, parts[2:]

    def _workspace_path(self, program: VisionProgramDefinition, path: str):
        parts = path.split('.')
        if len(parts) < 3 or parts[0] != 'workspace': return None
        workspace = workspace_by_alias(program, parts[1])
        return workspace, parts[2:]

    def _read_path(self, program: VisionProgramDefinition, event: dict[str, Any], path: str) -> Any:
        state = self.state(program.program_id)
        if path == 'system.online': return state.online
        if path == 'system.run_state': return state.run_state
        if path == 'system.result': return state.result
        if path == 'system.run_id': return state.run_id
        if path == 'system.last_run_ms': return state.last_run_ms
        declared = self._declared_point(program, path)
        if declared is not None:
            return self.io.read_declared_point(*declared)
        workspace_path = self._workspace_path(program, path)
        if workspace_path is not None:
            workspace, rest = workspace_path; alias = safe_alias(workspace.alias, workspace.workspace_id)
            if rest == ['active']: return state.active_workspace == alias
            if rest == ['result']: return state.workspace_results.get(alias, 'NONE')
            if rest == ['input_binding']: return workspace.input_binding
            soft_state = state.soft_trigger_states.get(alias, {})
            if rest == ['soft_trigger', 'enabled']: return workspace.soft_trigger.enabled
            if rest == ['soft_trigger', 'armed']: return bool(soft_state.get('armed', False))
            if rest == ['soft_trigger', 'pixel_count']: return int(soft_state.get('pixel_count', 0))
            if rest == ['soft_trigger', 'active_ratio']: return float(soft_state.get('active_ratio', 0.0))
            if rest == ['soft_trigger', 'fires']: return int(soft_state.get('fires', 0))
            if rest and rest[0] == 'vision':
                snap = self.snapshot(program.program_id)
                if snap is None or state.last_workspace != alias: raise KeyError(f'No snapshot for {alias}')
                # Translate workspace.<alias>.vision.* into the legacy snapshot traversal.
                legacy = 'vision.' + '.'.join(rest[1:])
                return self._read_snapshot_path(snap, legacy)
        if path.startswith('keyboard.'):
            suffix = path.split('.', 1)[1]
            if suffix.startswith('key.'):
                key = self.normalize_key(suffix)
            else:
                key = self.normalize_key(suffix)
            return bool(self.state(program.program_id).keyboard_states.get(key, self.state(program.program_id).keyboard_states.get(suffix, False)))
        camera_path = self._camera_path(program, path)
        if camera_path is not None:
            camera, rest = camera_path
            camera_alias = safe_alias(camera.alias, camera.declaration_id)
            stream_state = self.state(program.program_id).stream_states.get(self.state(program.program_id).active_workspace, {})
            if rest == ['exposure_us']: return camera.exposure_us
            if rest == ['streaming']: return bool(stream_state.get('running', VISION_FRAME_SLOTS.streaming(program.program_id, camera_alias)))
            if rest == ['stream_fps']: return stream_state.get('fps', 0.0)
            if rest == ['stream_sequence']: return stream_state.get('sequence', 0)
            if rest == ['stream_error']: return stream_state.get('last_error', '')
            slot = '.'.join(['camera', camera_alias] + rest)
            if VISION_FRAME_SLOTS.has(program.program_id, slot): return {'slot': slot, 'sequence': VISION_FRAME_SLOTS.sequence(program.program_id, slot)}
        if path.startswith('event.'):
            return event.get(path.split('.', 1)[1])
        # v0.12 compatibility aliases point at the latest workspace snapshot.
        snap = self.snapshot(program.program_id)
        if path.startswith('vision.') and snap is not None:
            return self._read_snapshot_path(snap, path)
        raise KeyError(f'Unknown/read-protected endpoint: {path}')

    @staticmethod
    def _read_snapshot_path(snap: VisionRunSnapshot, path: str) -> Any:
        parts = path.split('.')
        if parts[:3] == ['vision', 'global_scope', 'logic'] and len(parts) >= 5:
            data: Any = snap.global_logic.get(parts[3], {}); rest = parts[5:] if parts[4] == 'outputs' else parts[4:]
        elif len(parts) >= 4 and parts[:2] == ['vision', 'roi']:
            roi_alias = parts[2]
            if len(parts) == 4 and parts[3] in {'found', 'score'}:
                meta = snap.roi_meta.get(roi_alias, {}); return meta.get('located' if parts[3] == 'found' else 'score')
            if len(parts) >= 6 and parts[3] == 'logic':
                data = snap.roi_logic.get(roi_alias, {}).get(parts[4], {}); rest = parts[6:] if parts[5] == 'outputs' else parts[5:]
            else: raise KeyError(f'Unknown Vision endpoint: {path}')
        else: raise KeyError(f'Unknown Vision endpoint: {path}')
        for key in rest:
            if isinstance(data, dict) and key in data: data = data[key]
            elif isinstance(data, list) and key.isdigit(): data = data[int(key)]
            else: raise KeyError(f'Endpoint path not found: {path}')
        return data

    def _write_path(self, program: VisionProgramDefinition, path: str, value: Any, dry_run: bool) -> None:
        declared = self._declared_point(program, path)
        if declared is not None:
            device, point = declared
            if not point.writable: raise KeyError(f'Endpoint is not writable: {path}')
            if not dry_run: self.io.write_declared_point(device, point, value)
            return
        camera_path = self._camera_path(program, path)
        if camera_path is not None:
            camera, rest = camera_path
            if rest == ['exposure_us'] and camera.driver == 'basler':
                if not dry_run:
                    camera.exposure_us = float(value)
                    workspace = workspace_by_alias(program, program.active_workspace_id)
                    local = next((item for item in workspace.cameras.devices if item.declaration_id == camera.declaration_id), None)
                    if local is not None:
                        local.exposure_us = camera.exposure_us
                    self.repository.save(program)
                return
        raise KeyError(f'Endpoint is not writable: {path}')

    def _call_action(self, program: VisionProgramDefinition, path: str, args: list[Any], kwargs: dict[str, Any], dry_run: bool) -> Any:
        if path == 'system.run_inspection':
            return 'WOULD_RUN_INSPECTION' if dry_run else self.run_inspection(program.program_id)
        if path == 'system.commit_result':
            if not args: raise ValueError('system.commit_result requires OK or NG')
            if not dry_run: self.commit_result(program.program_id, args[0])
            return args[0]
        if path == 'system.clear_working_screen':
            if not dry_run: self.clear_working_screen(program.program_id)
            return True
        workspace_path = self._workspace_path(program, path)
        if workspace_path is not None:
            workspace, rest = workspace_path; alias = safe_alias(workspace.alias, workspace.workspace_id)
            if rest == ['activate']:
                if not dry_run: self.activate_workspace(program.program_id, alias)
                return True
            if rest == ['run_inspection']:
                return f'WOULD_RUN_{alias}' if dry_run else self.run_inspection(program.program_id, workspace_alias=alias)
            if rest == ['clear']:
                if not dry_run: self.clear_working_screen(program.program_id, alias)
                return True
            if rest == ['soft_trigger', 'arm']:
                if not dry_run:
                    self.streaming.arm_workspace(program, alias, reason_prefix='ide_soft')
                return True
            if rest == ['soft_trigger', 'disarm']:
                if not dry_run:
                    self.streaming.disarm_workspace(program, alias, reason_prefix='ide_soft')
                    self.state(program.program_id).soft_trigger_states.pop(alias, None)
                return True
        camera_path = self._camera_path(program, path)
        if camera_path is not None:
            camera, rest = camera_path; alias = safe_alias(camera.alias, camera.declaration_id)
            if rest == ['capture']:
                return f'WOULD_CAPTURE_{alias}' if dry_run else bool(self.capture(program.program_id, alias) is not None)
            if rest == ['start_stream']:
                if not dry_run: self.streaming.ensure(program.program_id, self.state(program.program_id).active_workspace, camera, f'ide:{alias}')
                return True
            if rest == ['stop_stream']:
                if not dry_run: self.streaming.release(program.program_id, self.state(program.program_id).active_workspace, f'ide:{alias}')
                return True
            custom_alias = rest[0] if rest else ''
            for custom in camera.custom_apis:
                if custom.enabled and safe_alias(custom.alias, custom.api_id) == custom_alias:
                    if dry_run: return f'WOULD_CALL_{alias}_{custom_alias}'
                    values = {p.name: (kwargs[p.name] if p.name in kwargs else args[i] if i < len(args) else p.default) for i, p in enumerate(custom.parameters)}
                    unknown = set(kwargs) - {p.name for p in custom.parameters}
                    if unknown: raise ValueError(f"Unknown camera API parameter(s): {', '.join(sorted(unknown))}")
                    return self.camera_resources.call_custom(camera, custom, values)
        if path.endswith('.pulse'):
            declared = self._declared_point(program, path.rsplit('.pulse', 1)[0])
            if declared is not None:
                device, point = declared; seconds = float(args[0]) if args else point.pulse_seconds
                if not dry_run: self.io.pulse_declared_point(device, point, seconds)
                return True
        raise KeyError(f'Unknown action endpoint: {path}')

    def execute_service(self, program: VisionProgramDefinition, service: AutomationServiceDefinition, *, dry_run: bool = False, event: dict[str, Any] | None = None) -> AutomationExecutionResult:
        event = event or {'name': 'manual'}
        target = event.get('workspace') or self.state(program.program_id).active_workspace or program.active_workspace_id
        runtime_program = projected_program(program, workspace_by_alias(program, str(target)))
        ctx = AutomationExecutionContext(
            program=runtime_program, snapshot=self.snapshot(program.program_id), event=event,
            read_endpoint=lambda path: self._read_path(runtime_program, event, path),
            write_endpoint=lambda path, value, dr: self._write_path(runtime_program, path, value, dr),
            call_action=lambda path, args, kwargs, dr: self._call_action(runtime_program, path, args, kwargs, dr),
            trace=lambda entry: self._append_trace(program.program_id, entry), dry_run=dry_run,
        )
        return SafeAutomationInterpreter(ctx, service).execute(service.script)

    def emit(self, program: VisionProgramDefinition, event_name: str, payload: dict[str, Any]) -> None:
        state = self.state(program.program_id); state.last_event = event_name
        for service in program.automation.services:
            if not program.automation.enabled or not service.enabled or service.mode != 'event' or service.event != event_name: continue
            result = self.execute_service(program, service, event={**payload, 'name': event_name})
            if not result.ok: state.last_error = f'Automation service {service.name} failed'

    def run_service(self, program_id: str, service_id: str, *, dry_run: bool = False) -> AutomationExecutionResult:
        program = self.repository.get(program_id)
        service = next((item for item in program.automation.services if item.service_id == service_id), None)
        if service is None: raise FileNotFoundError(f'Automation service not found: {service_id}')
        state = self.state(program_id)
        return self.execute_service(program, service, dry_run=dry_run, event={'name': 'manual', 'result': state.result, 'run_id': state.run_id})

    def validate(self, script: str): return validate_script(script)

    def start(self, program_id: str) -> AutomationSystemState:
        self.repository.get(program_id)
        with self._lock:
            thread = self._threads.get(program_id)
            if thread and thread.is_alive():
                state = self.state(program_id); state.scheduler_running = True; return state
            stop = Event(); self._stops[program_id] = stop
            thread = Thread(target=self._scheduler_loop, args=(program_id, stop), daemon=True, name=f'vision-automation-{program_id}')
            self._threads[program_id] = thread; self.state(program_id).scheduler_running = True; thread.start()
        return self.state(program_id)

    def stop(self, program_id: str) -> AutomationSystemState:
        stop = self._stops.get(program_id)
        if stop: stop.set()
        self.state(program_id).scheduler_running = False
        return self.state(program_id)

    def online(self, program_id: str) -> AutomationSystemState:
        program = self.repository.get(program_id)
        state = self.start(program_id)
        state.online = True
        self.streaming.arm_program(program)
        return state

    def offline(self, program_id: str) -> AutomationSystemState:
        program = self.repository.get(program_id)
        self.streaming.disarm_program(program)
        state = self.stop(program_id)
        state.online = False
        state.soft_trigger_states = {}
        return state

    def shutdown_program(self, program_id: str) -> None:
        try:
            self.offline(program_id)
        except Exception:
            self.stop(program_id)
            self.streaming.stop_program(program_id)

    def _scheduler_loop(self, program_id: str, stop: Event) -> None:
        due: dict[str, float] = {}
        while not stop.is_set():
            try:
                program = self.repository.get(program_id)
                if not program.automation.enabled:
                    stop.wait(0.25); continue
                now = monotonic(); loops = [s for s in program.automation.services if s.enabled and s.mode == 'loop']
                active = {s.service_id for s in loops}; due = {k:v for k,v in due.items() if k in active}
                for service in loops:
                    target = due.get(service.service_id, now)
                    if now < target: continue
                    due[service.service_id] = now + max(0.025, service.interval_ms / 1000.0)
                    result = self.execute_service(program, service, event={'name':'loop','result':self.state(program_id).result,'run_id':self.state(program_id).run_id})
                    if not result.ok: self.state(program_id).last_error = f'Loop service {service.name} failed'
                stop.wait(0.02)
            except Exception as exc:
                self.state(program_id).last_error = str(exc); stop.wait(0.25)
        self.state(program_id).scheduler_running = False
