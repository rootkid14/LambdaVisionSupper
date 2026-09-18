from __future__ import annotations

import re
from typing import Any

from app.services.vision_app.automation_models import EndpointSpec, VisionRunSnapshot
from app.services.vision_app.models import VisionProgramDefinition

_SAFE = re.compile(r"[^A-Za-z0-9_]+")


def safe_alias(value: str, fallback: str) -> str:
    text = _SAFE.sub("_", (value or fallback).strip()).strip("_")
    if not text:
        text = fallback
    if text[0].isdigit():
        text = f"_{text}"
    return text


def _flatten(prefix: str, value: Any, *, source: str, out: list[EndpointSpec]) -> None:
    if isinstance(value, dict):
        out.append(EndpointSpec(path=prefix, kind="data", data_type="object", description="Structured output object", source=source, last_value=value))
        for key, child in value.items():
            _flatten(f"{prefix}.{safe_alias(str(key), 'value')}", child, source=source, out=out)
        return
    if isinstance(value, list):
        out.append(EndpointSpec(path=prefix, kind="data", data_type="array", description=f"Array output ({len(value)} item(s))", source=source, last_value=value))
        return
    dtype = "bool" if isinstance(value, bool) else "number" if isinstance(value, (int, float)) else "string" if isinstance(value, str) else "any"
    allowed = ["ON", "OFF"] if dtype == "bool" else []
    out.append(EndpointSpec(path=prefix, kind="data", data_type=dtype, description="Logic-service exposed output", source=source, last_value=value, allowed_values=allowed))


class EndpointRegistry:
    """Typed live object graph for devices, cameras, workspaces and Vision outputs."""

    def _declared_iot(self, program: VisionProgramDefinition, specs: list[EndpointSpec]) -> None:
        specs.append(EndpointSpec(path="device", kind="data", data_type="namespace", description="Declared hardware device namespace", source="device", object_type="namespace"))
        for device in program.iot.devices:
            if not device.enabled:
                continue
            device_alias = safe_alias(device.alias, device.declaration_id)
            root = f"device.{device_alias}"
            desc = "Simulated I/O device" if device.driver == "simulated" else f"Modbus TCP {device.host}:{device.port} · unit {device.unit_id}"
            specs.append(EndpointSpec(path=root, kind="data", data_type="modbus_tcp_device" if device.driver == "modbus_tcp" else "simulated_iot_device", description=desc, source=root, object_type=device.driver))
            for point in device.points:
                if not point.enabled:
                    continue
                point_alias = safe_alias(point.alias, point.point_id)
                path = f"{root}.{point_alias}"
                specs.append(EndpointSpec(
                    path=path, kind="state", data_type=point.data_type, readable=True, writable=point.writable,
                    description=point.description or f"{point.kind} address {point.address}", source=root,
                    example=f"if {path} == ON:" if point.data_type == "bool" else f"value = {path}",
                    allowed_values=["ON", "OFF"] if point.data_type == "bool" else [], object_type=point.kind,
                ))
                if point.kind == "coil":
                    specs.append(EndpointSpec(path=f"{path}.pulse", kind="action", callable=True, readable=False, data_type="action", description=f"Pulse output; default {point.pulse_seconds:g}s", source=root, example=f"{path}.pulse({point.pulse_seconds:g})", object_type="pulse_action"))

    def _declared_cameras(self, program: VisionProgramDefinition, specs: list[EndpointSpec], state: Any | None) -> None:
        specs.append(EndpointSpec(path="camera", kind="data", data_type="namespace", description="Declared camera resources", source="camera", object_type="namespace"))
        for camera in program.cameras.devices:
            if not camera.enabled:
                continue
            alias = safe_alias(camera.alias, camera.declaration_id)
            root = f"camera.{alias}"
            specs.append(EndpointSpec(path=root, kind="data", data_type="camera", description=f"{camera.driver} camera resource", source=root, object_type=camera.driver))
            specs.append(EndpointSpec(path=f"{root}.{camera.image_slot}", kind="data", data_type="image_slot", description="Latest stable captured frame", source=root, object_type="image_slot"))
            specs.append(EndpointSpec(path=f"{root}.{camera.stream_slot}", kind="data", data_type="stream_slot", description="Volatile engineering stream frame", source=root, object_type="stream_slot"))
            specs.append(EndpointSpec(path=f"{root}.capture", kind="action", callable=True, readable=False, description=f"Capture into {camera.image_slot}", source=root, example=f"{root}.capture()", object_type="camera_action"))
            specs.append(EndpointSpec(path=f"{root}.start_stream", kind="action", callable=True, readable=False, description="Enable engineering stream polling", source=root, example=f"{root}.start_stream()", object_type="camera_action"))
            specs.append(EndpointSpec(path=f"{root}.stop_stream", kind="action", callable=True, readable=False, description="Disable engineering stream polling", source=root, example=f"{root}.stop_stream()", object_type="camera_action"))
            specs.append(EndpointSpec(path=f"{root}.exposure_us", kind="state", data_type="number", readable=True, writable=camera.driver == "basler", description="Camera exposure in microseconds", source=root, unit="µs", object_type="camera_property"))
            specs.append(EndpointSpec(path=f"{root}.streaming", kind="state", data_type="bool", readable=True, writable=False, description="Engineering stream preview state", source=root, allowed_values=["ON", "OFF"], object_type="camera_property"))
            for custom in camera.custom_apis:
                if not custom.enabled:
                    continue
                api_alias = safe_alias(custom.alias, custom.api_id)
                example_args = ", ".join(f"{p.name}={repr(p.default)}" for p in custom.parameters if p.default is not None)
                params = [{"name": p.name, "data_type": p.data_type, "default": p.default, "description": p.description} for p in custom.parameters]
                specs.append(EndpointSpec(path=f"{root}.{api_alias}", kind="action", callable=True, readable=False, data_type="action", description=custom.description or f"HTTP {custom.method} {custom.path_template}", source=root, example=f"{root}.{api_alias}({example_args})", object_type="camera_custom_api", parameters=params))

    def _declared_workspace_vision(self, program: VisionProgramDefinition, workspace, snapshot: VisionRunSnapshot | None, specs: list[EndpointSpec]) -> None:
        ws_alias = safe_alias(workspace.alias, workspace.workspace_id)
        vision_root = f"workspace.{ws_alias}.vision"
        specs.append(EndpointSpec(path=vision_root, kind="data", data_type="namespace", description=f"Vision outputs for {workspace.name}", source=f"workspace.{ws_alias}", object_type="vision_namespace"))
        specs.append(EndpointSpec(path=f"{vision_root}.global_scope", kind="data", data_type="scope", description="Whole-image scope", source=vision_root))
        specs.append(EndpointSpec(path=f"{vision_root}.global_scope.logic", kind="data", data_type="namespace", description="Global Logic services", source=vision_root))
        for binding in (workspace.working.global_scope.logic_services if workspace.working.global_scope.enable_logic else []):
            if not binding.enabled:
                continue
            alias = safe_alias(binding.alias or binding.label or binding.service_id, binding.binding_id)
            root = f"{vision_root}.global_scope.logic.{alias}"
            specs.append(EndpointSpec(path=root, kind="data", data_type="logic_service", description=binding.label or binding.service_id, source=vision_root))
            specs.append(EndpointSpec(path=f"{root}.outputs", kind="data", data_type="object", description="Outputs populated after workspace run", source=vision_root))
        specs.append(EndpointSpec(path=f"{vision_root}.roi", kind="data", data_type="namespace", description="Workspace ROI/station objects", source=vision_root))
        snapshot_meta = snapshot.roi_meta if snapshot else {}
        for roi in workspace.master.rois:
            if not roi.enabled:
                continue
            roi_alias = safe_alias(roi.alias or roi.name, roi.roi_id)
            root = f"{vision_root}.roi.{roi_alias}"
            meta = snapshot_meta.get(roi_alias, {}) if snapshot else {}
            specs.append(EndpointSpec(path=root, kind="data", data_type="roi", description=roi.name, source=root, last_value=meta or None))
            specs.append(EndpointSpec(path=f"{root}.found", kind="data", data_type="bool", description="Latest locator result", source=root, last_value=meta.get("located") if meta else None, allowed_values=["ON", "OFF"]))
            specs.append(EndpointSpec(path=f"{root}.score", kind="data", data_type="number", description="Latest locator score", source=root, last_value=meta.get("score") if meta else None))
            scope = workspace.working.station_scopes.get(roi.roi_id)
            specs.append(EndpointSpec(path=f"{root}.logic", kind="data", data_type="namespace", description="ROI Logic services", source=root))
            for binding in (scope.logic_services if scope and scope.enable_logic else []):
                if not binding.enabled:
                    continue
                alias = safe_alias(binding.alias or binding.label or binding.service_id, binding.binding_id)
                lr = f"{root}.logic.{alias}"
                specs.append(EndpointSpec(path=lr, kind="data", data_type="logic_service", description=binding.label or binding.service_id, source=root))
                specs.append(EndpointSpec(path=f"{lr}.outputs", kind="data", data_type="object", description="Outputs populated after workspace run", source=root))
        if snapshot is not None:
            for alias, outputs in snapshot.global_logic.items():
                _flatten(f"{vision_root}.global_scope.logic.{safe_alias(alias, 'logic')}.outputs", outputs, source=vision_root, out=specs)
            for roi_alias, logic_map in snapshot.roi_logic.items():
                for logic_alias, outputs in logic_map.items():
                    _flatten(f"{vision_root}.roi.{safe_alias(roi_alias, 'roi')}.logic.{safe_alias(logic_alias, 'logic')}.outputs", outputs, source=vision_root, out=specs)

    def _declared_workspaces(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None, specs: list[EndpointSpec], state: Any | None) -> None:
        specs.append(EndpointSpec(path="workspace", kind="data", data_type="namespace", description="Inspection workspace namespace", source="workspace", object_type="namespace"))
        active = getattr(state, "active_workspace", program.active_workspace_id)
        results = getattr(state, "workspace_results", {}) or {}
        for workspace in program.workspaces:
            if not workspace.enabled:
                continue
            alias = safe_alias(workspace.alias, workspace.workspace_id)
            root = f"workspace.{alias}"
            result = results.get(alias, "NONE")
            specs.append(EndpointSpec(path=root, kind="data", data_type="workspace", description=workspace.name, source=root, object_type="workspace"))
            specs.append(EndpointSpec(path=f"{root}.active", kind="state", data_type="bool", description="Whether this is the active UI/inspection workspace", source=root, last_value=(active == alias), allowed_values=["ON", "OFF"]))
            specs.append(EndpointSpec(path=f"{root}.result", kind="state", data_type="inspection_result", description="Latest workspace result", source=root, last_value=result, allowed_values=["OK", "NG", "NONE", "ERROR"]))
            specs.append(EndpointSpec(path=f"{root}.input_binding", kind="data", data_type="string", description="Configured image-slot binding", source=root, last_value=workspace.input_binding))
            specs.append(EndpointSpec(path=f"{root}.activate", kind="action", callable=True, readable=False, description="Make this the active workspace/UI context", source=root, example=f"{root}.activate()"))
            specs.append(EndpointSpec(path=f"{root}.run_inspection", kind="action", callable=True, readable=False, description="Run this workspace using its bound image slot", source=root, example=f"{root}.run_inspection()"))
            specs.append(EndpointSpec(path=f"{root}.clear", kind="action", callable=True, readable=False, description="Clear this workspace Working state", source=root, example=f"{root}.clear()"))
            specs.append(EndpointSpec(path=f"{root}.logic_ready", kind="event", description="Workspace Filter/Logic pipeline completed", source=root))
            specs.append(EndpointSpec(path=f"{root}.run_finish", kind="event", description="Workspace run finished", source=root))
            # The single latest snapshot is associated with the latest-run workspace by AutomationManager.
            snap = snapshot if getattr(state, "last_workspace", None) in {None, alias} else None
            self._declared_workspace_vision(program, workspace, snap, specs)

    def _legacy_vision_aliases(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None, specs: list[EndpointSpec]) -> None:
        """v0.12 compatibility namespace pointing at the latest/legacy workspace."""
        specs.extend([
            EndpointSpec(path="vision", kind="data", data_type="namespace", description="Latest workspace Vision compatibility namespace", source="vision"),
            EndpointSpec(path="vision.global_scope", kind="data", data_type="scope", description="Latest workspace Global scope", source="vision"),
            EndpointSpec(path="vision.global_scope.logic", kind="data", data_type="namespace", description="Latest workspace Global Logic", source="vision"),
            EndpointSpec(path="vision.roi", kind="data", data_type="namespace", description="Latest workspace ROI objects", source="vision"),
        ])
        for binding in (program.working.global_scope.logic_services if program.working.global_scope.enable_logic else []):
            if binding.enabled:
                alias=safe_alias(binding.alias or binding.label or binding.service_id,binding.binding_id); root=f"vision.global_scope.logic.{alias}"
                specs.append(EndpointSpec(path=root,kind="data",data_type="logic_service",description=binding.label or binding.service_id,source="vision"))
                specs.append(EndpointSpec(path=f"{root}.outputs",kind="data",data_type="object",description="Latest outputs",source="vision"))
        meta=snapshot.roi_meta if snapshot else {}
        for roi in program.master.rois:
            if not roi.enabled: continue
            alias=safe_alias(roi.alias or roi.name,roi.roi_id); root=f"vision.roi.{alias}"; m=meta.get(alias,{})
            specs.append(EndpointSpec(path=root,kind="data",data_type="roi",description=roi.name,source=root,last_value=m or None))
            specs.append(EndpointSpec(path=f"{root}.found",kind="data",data_type="bool",description="Latest locator result",source=root,last_value=m.get("located") if m else None,allowed_values=["ON","OFF"]))
            specs.append(EndpointSpec(path=f"{root}.score",kind="data",data_type="number",description="Latest locator score",source=root,last_value=m.get("score") if m else None))
            scope=program.working.station_scopes.get(roi.roi_id)
            for binding in (scope.logic_services if scope and scope.enable_logic else []):
                if binding.enabled:
                    la=safe_alias(binding.alias or binding.label or binding.service_id,binding.binding_id); lr=f"{root}.logic.{la}"
                    specs.append(EndpointSpec(path=lr,kind="data",data_type="logic_service",description=binding.label or binding.service_id,source=root))
                    specs.append(EndpointSpec(path=f"{lr}.outputs",kind="data",data_type="object",description="Latest outputs",source=root))
        if snapshot is not None:
            for alias,outputs in snapshot.global_logic.items(): _flatten(f"vision.global_scope.logic.{safe_alias(alias,'logic')}.outputs",outputs,source="vision",out=specs)
            for roi_alias,logic_map in snapshot.roi_logic.items():
                for logic_alias,outputs in logic_map.items(): _flatten(f"vision.roi.{safe_alias(roi_alias,'roi')}.logic.{safe_alias(logic_alias,'logic')}.outputs",outputs,source="vision",out=specs)

    def _keyboard(self, specs: list[EndpointSpec], state: Any | None) -> None:
        specs.append(EndpointSpec(path="keyboard", kind="data", data_type="namespace", description="Application keyboard signal namespace", source="keyboard", object_type="namespace"))
        keys = ["space", "enter", "escape", "arrow_up", "arrow_down", "arrow_left", "arrow_right"] + [f"f{i}" for i in range(1, 13)]
        values = getattr(state, "keyboard_states", {}) if state is not None else {}
        for key in keys:
            specs.append(EndpointSpec(path=f"keyboard.{key}", kind="state", data_type="bool", description=f"Keyboard {key} is currently pressed", source="keyboard", last_value=bool(values.get(key, False)), allowed_values=["ON", "OFF"], object_type="keyboard_key"))

    @staticmethod
    def _dedupe(specs: list[EndpointSpec]) -> list[EndpointSpec]:
        by_path: dict[str, EndpointSpec] = {}
        for spec in specs:
            current = by_path.get(spec.path)
            if current is None or spec.last_value is not None or current.last_value is None:
                by_path[spec.path] = spec
        return list(by_path.values())

    def build(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None = None, state: Any | None = None) -> list[EndpointSpec]:
        specs: list[EndpointSpec] = [
            EndpointSpec(path="system", kind="data", data_type="namespace", description="Program control namespace", source="system"),
            EndpointSpec(path="system.online", kind="state", data_type="bool", description="Whole Computer Vision program online state", source="system", last_value=getattr(state, "online", False), allowed_values=["ON", "OFF"]),
            EndpointSpec(path="system.run_state", kind="state", data_type="enum", description="Current execution state", source="system", last_value=getattr(state, "run_state", "IDLE"), allowed_values=["IDLE", "CAPTURING", "INSPECTING", "DECIDING", "FINISHED", "ERROR"]),
            EndpointSpec(path="system.result", kind="state", data_type="inspection_result", description="Committed product result", source="system", last_value=getattr(state, "result", "NONE"), allowed_values=["OK", "NG", "NONE", "ERROR"]),
            EndpointSpec(path="system.run_id", kind="state", data_type="string", description="Latest run id", source="system", last_value=getattr(state, "run_id", "")),
            EndpointSpec(path="system.last_run_ms", kind="state", data_type="number", description="Latest cycle time", source="system", last_value=getattr(state, "last_run_ms", None), unit="ms"),
            EndpointSpec(path="system.run_inspection", kind="action", callable=True, readable=False, description="Run active workspace", source="system", example="system.run_inspection()"),
            EndpointSpec(path="system.commit_result", kind="action", callable=True, readable=False, description="Commit final product result", source="system", example="system.commit_result(OK)"),
            EndpointSpec(path="system.clear_working_screen", kind="action", callable=True, readable=False, description="Clear active workspace", source="system"),
            EndpointSpec(path="system.run_started", kind="event", description="Program/workspace cycle started", source="system"),
            EndpointSpec(path="vision.logic_ready", kind="event", description="Compatibility event for latest workspace Logic completion", source="vision"),
            EndpointSpec(path="system.run_finish", kind="event", description="Final product result committed", source="system"),
            EndpointSpec(path="system.run_error", kind="event", description="Inspection/automation error", source="system"),
        ]
        self._declared_iot(program, specs)
        self._declared_cameras(program, specs, state)
        self._declared_workspaces(program, snapshot, specs, state)
        self._keyboard(specs, state)
        self._legacy_vision_aliases(program, snapshot, specs)
        specs.extend([
            EndpointSpec(path="event", kind="data", data_type="namespace", description="Current Event-service payload", source="event"),
            EndpointSpec(path="event.name", kind="data", data_type="string", description="Current event name", source="event"),
            EndpointSpec(path="event.result", kind="data", data_type="inspection_result", description="Event result", source="event", allowed_values=["OK", "NG", "NONE", "ERROR"]),
            EndpointSpec(path="event.run_id", kind="data", data_type="string", description="Event run id", source="event"),
        ])
        return self._dedupe(specs)

    def as_dict(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None = None, state: Any | None = None) -> list[dict[str, Any]]:
        return [spec.model_dump() if hasattr(spec, "model_dump") else spec.dict() for spec in self.build(program, snapshot, state)]
