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
    out.append(EndpointSpec(path=prefix, kind="data", data_type=dtype, description="Logic-service exposed output", source=source, last_value=value))


class EndpointRegistry:
    """Build the live object graph visible to the Automation IDE.

    Declared IOT devices, ROIs and configured Logic aliases appear immediately,
    before any inspection has run. Runtime snapshots only enrich those objects with
    actual output leaves and last values.
    """

    def _declared_iot(self, program: VisionProgramDefinition, specs: list[EndpointSpec]) -> None:
        specs.append(EndpointSpec(path="device", kind="data", data_type="namespace", description="Declared hardware device namespace", source="device"))
        for device in program.iot.devices:
            if not device.enabled:
                continue
            device_alias = safe_alias(device.alias, device.declaration_id)
            root = f"device.{device_alias}"
            specs.append(EndpointSpec(path=root, kind="data", data_type="modbus_tcp_device", description=f"Modbus TCP device {device.host}:{device.port} · unit {device.unit_id}", source=f"device.{device_alias}"))
            for point in device.points:
                if not point.enabled:
                    continue
                point_alias = safe_alias(point.alias, point.point_id)
                path = f"{root}.{point_alias}"
                specs.append(EndpointSpec(
                    path=path,
                    kind="state",
                    data_type=point.data_type,
                    readable=True,
                    writable=point.writable,
                    description=point.description or f"{point.kind} address {point.address}",
                    source=f"device.{device_alias}",
                    example=f"{path} = ON" if point.writable and point.data_type == "bool" else f"value = {path}",
                ))
                if point.kind == "coil":
                    specs.append(EndpointSpec(
                        path=f"{path}.pulse",
                        kind="action",
                        callable=True,
                        readable=False,
                        description=f"Pulse coil {point.address}; default {point.pulse_seconds:g}s",
                        source=f"device.{device_alias}",
                        example=f"{path}.pulse({point.pulse_seconds:g})",
                    ))

    def _declared_vision(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None, specs: list[EndpointSpec]) -> None:
        specs.extend([
            EndpointSpec(path="vision", kind="data", data_type="namespace", description="Vision runtime namespace", source="vision"),
            EndpointSpec(path="vision.global_scope", kind="data", data_type="scope", description="Whole-image Working scope", source="vision.global_scope"),
            EndpointSpec(path="vision.global_scope.logic", kind="data", data_type="namespace", description="Global Logic-service objects", source="vision.global_scope"),
            EndpointSpec(path="vision.roi", kind="data", data_type="namespace", description="Declared Master ROI/station objects", source="vision.roi"),
        ])

        global_bindings = program.working.global_scope.logic_services if program.working.global_scope.enable_logic else []
        for binding in global_bindings:
            if not binding.enabled:
                continue
            alias = safe_alias(binding.alias or binding.label or binding.service_id, binding.binding_id)
            root = f"vision.global_scope.logic.{alias}"
            specs.append(EndpointSpec(path=root, kind="data", data_type="logic_service", description=binding.label or binding.service_id, source="vision.global_scope"))
            specs.append(EndpointSpec(path=f"{root}.outputs", kind="data", data_type="object", description="Exposed Logic-service outputs; populated after a run", source="vision.global_scope"))

        snapshot_roi_meta = snapshot.roi_meta if snapshot else {}
        for roi in program.master.rois:
            if not roi.enabled:
                continue
            roi_alias = safe_alias(roi.alias or roi.name, roi.roi_id)
            root = f"vision.roi.{roi_alias}"
            meta = snapshot_roi_meta.get(roi_alias, {}) if snapshot else {}
            specs.append(EndpointSpec(path=root, kind="data", data_type="roi", description=f"ROI / station: {roi.name}", source=root, last_value=meta or None))
            specs.append(EndpointSpec(path=f"{root}.found", kind="data", data_type="bool", description="Whether ROI was located in latest run", source=root, last_value=meta.get("located") if meta else None))
            specs.append(EndpointSpec(path=f"{root}.score", kind="data", data_type="number", description="Latest ROI locator score", source=root, last_value=meta.get("score") if meta else None))
            specs.append(EndpointSpec(path=f"{root}.logic", kind="data", data_type="namespace", description="Logic-service objects inside this ROI", source=root))
            scope = program.working.station_scopes.get(roi.roi_id)
            for binding in (scope.logic_services if scope and scope.enable_logic else []):
                if not binding.enabled:
                    continue
                alias = safe_alias(binding.alias or binding.label or binding.service_id, binding.binding_id)
                logic_root = f"{root}.logic.{alias}"
                specs.append(EndpointSpec(path=logic_root, kind="data", data_type="logic_service", description=binding.label or binding.service_id, source=root))
                specs.append(EndpointSpec(path=f"{logic_root}.outputs", kind="data", data_type="object", description="Exposed Logic-service outputs; populated after a run", source=root))

        if snapshot is not None:
            for alias, outputs in snapshot.global_logic.items():
                _flatten(f"vision.global_scope.logic.{safe_alias(alias, 'logic')}.outputs", outputs, source="vision.global_scope", out=specs)
            for roi_alias, logic_map in snapshot.roi_logic.items():
                safe_roi = safe_alias(roi_alias, "roi")
                for logic_alias, outputs in logic_map.items():
                    _flatten(f"vision.roi.{safe_roi}.logic.{safe_alias(logic_alias, 'logic')}.outputs", outputs, source=f"vision.roi.{safe_roi}", out=specs)

    @staticmethod
    def _dedupe(specs: list[EndpointSpec]) -> list[EndpointSpec]:
        by_path: dict[str, EndpointSpec] = {}
        for spec in specs:
            current = by_path.get(spec.path)
            if current is None:
                by_path[spec.path] = spec
                continue
            # Runtime leaf values are more useful than declaration placeholders.
            if spec.last_value is not None or current.last_value is None:
                by_path[spec.path] = spec
        return list(by_path.values())

    def build(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None = None, state: Any | None = None) -> list[EndpointSpec]:
        specs: list[EndpointSpec] = [
            EndpointSpec(path="system", kind="data", data_type="namespace", description="Vision system control namespace", source="system"),
            EndpointSpec(path="system.run_state", kind="state", data_type="enum", description="Current Vision execution state", source="system", last_value=getattr(state, "run_state", "IDLE")),
            EndpointSpec(path="system.result", kind="state", data_type="enum", description="Current committed result: NONE/OK/NG/ERROR", source="system", last_value=getattr(state, "result", "NONE")),
            EndpointSpec(path="system.run_id", kind="state", data_type="string", description="Latest run identifier", source="system", last_value=getattr(state, "run_id", "")),
            EndpointSpec(path="system.last_run_ms", kind="state", data_type="number", description="Latest inspection cycle time", source="system", last_value=getattr(state, "last_run_ms", None)),
            EndpointSpec(path="system.run_inspection", kind="action", callable=True, readable=False, description="Run inspection using latest/captured frame", source="system", example="system.run_inspection()"),
            EndpointSpec(path="system.commit_result", kind="action", callable=True, readable=False, description="Commit OK or NG result", source="system", example="system.commit_result(OK)"),
            EndpointSpec(path="system.clear_working_screen", kind="action", callable=True, readable=False, description="Request Working viewport/result clear", source="system", example="system.clear_working_screen()"),
            EndpointSpec(path="system.run_started", kind="event", description="Inspection cycle started", source="system"),
            EndpointSpec(path="vision.logic_ready", kind="event", description="All Global/ROI Logic services finished; decision automation may run", source="vision"),
            EndpointSpec(path="system.run_finish", kind="event", description="Final result committed and cycle finished", source="system"),
            EndpointSpec(path="system.run_error", kind="event", description="Inspection/automation cycle failed", source="system"),
            EndpointSpec(path="camera", kind="data", data_type="namespace", description="Camera namespace", source="camera"),
            EndpointSpec(path="camera.main", kind="data", data_type="camera", description="Configured program camera", source="camera"),
            EndpointSpec(path="camera.main.capture", kind="action", callable=True, readable=False, description="Capture configured camera into latest frame", source="camera", example="camera.main.capture()"),
            EndpointSpec(path="camera.main.frame_ready", kind="event", description="Camera produced a new frame", source="camera"),
            EndpointSpec(path="camera.main.frame_sequence", kind="state", data_type="integer", description="Increments when a new backend frame is captured", source="camera", last_value=getattr(state, "frame_sequence", 0)),
        ]
        self._declared_iot(program, specs)
        self._declared_vision(program, snapshot, specs)
        specs.extend([
            EndpointSpec(path="event", kind="data", data_type="namespace", description="Current event-service payload", source="event"),
            EndpointSpec(path="event.name", kind="data", data_type="string", description="Current event-service event name", source="event"),
            EndpointSpec(path="event.result", kind="data", data_type="string", description="Current event result when available", source="event"),
            EndpointSpec(path="event.run_id", kind="data", data_type="string", description="Current event run id when available", source="event"),
        ])
        return self._dedupe(specs)

    def as_dict(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None = None, state: Any | None = None) -> list[dict[str, Any]]:
        return [spec.model_dump() if hasattr(spec, "model_dump") else spec.dict() for spec in self.build(program, snapshot, state)]
