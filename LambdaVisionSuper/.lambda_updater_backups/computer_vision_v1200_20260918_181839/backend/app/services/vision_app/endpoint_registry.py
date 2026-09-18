from __future__ import annotations

from typing import Any

from app.services.vision_app.automation_models import EndpointSpec, VisionRunSnapshot
from app.services.vision_app.models import VisionProgramDefinition


def _flatten(prefix: str, value: Any, *, source: str, out: list[EndpointSpec]) -> None:
    if isinstance(value, dict):
        if not value:
            out.append(EndpointSpec(path=prefix, kind="data", data_type="object", description="Structured output", source=source, last_value=value))
            return
        for key, child in value.items():
            safe = str(key).replace(" ", "_")
            _flatten(f"{prefix}.{safe}", child, source=source, out=out)
        return
    if isinstance(value, list):
        out.append(EndpointSpec(path=prefix, kind="data", data_type="array", description=f"Array output ({len(value)} item(s))", source=source, last_value=value))
        return
    dtype = "bool" if isinstance(value, bool) else "number" if isinstance(value, (int, float)) else "string" if isinstance(value, str) else "any"
    out.append(EndpointSpec(path=prefix, kind="data", data_type=dtype, description="Logic-service exposed output", source=source, last_value=value))


class EndpointRegistry:
    """Builds the typed namespace exposed to the Automation IDE.

    The registry is metadata only. Runtime reads/writes are resolved by AutomationExecutionContext.
    """

    def build(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None = None, state: Any | None = None) -> list[EndpointSpec]:
        specs: list[EndpointSpec] = [
            EndpointSpec(path="system.run_state", kind="state", data_type="enum", description="Current Vision execution state", source="system", last_value=getattr(state, "run_state", "IDLE")),
            EndpointSpec(path="system.result", kind="state", data_type="enum", description="Current committed result: NONE/OK/NG/ERROR", source="system", last_value=getattr(state, "result", "NONE")),
            EndpointSpec(path="system.run_id", kind="state", data_type="string", description="Latest run identifier", source="system", last_value=getattr(state, "run_id", "")),
            EndpointSpec(path="system.last_run_ms", kind="state", data_type="number", description="Latest inspection cycle time", source="system", last_value=getattr(state, "last_run_ms", None)),
            EndpointSpec(path="system.run_inspection", kind="action", callable=True, description="Run inspection using latest/captured frame", source="system", example="system.run_inspection()"),
            EndpointSpec(path="system.commit_result", kind="action", callable=True, description="Commit OK or NG result", source="system", example="system.commit_result(OK)"),
            EndpointSpec(path="system.clear_working_screen", kind="action", callable=True, description="Request Working viewport/result clear", source="system", example="system.clear_working_screen()"),
            EndpointSpec(path="system.run_started", kind="event", description="Inspection cycle started", source="system"),
            EndpointSpec(path="vision.logic_ready", kind="event", description="All Global/ROI Logic services finished; decision automation may run", source="vision"),
            EndpointSpec(path="system.run_finish", kind="event", description="Final result committed and cycle finished", source="system"),
            EndpointSpec(path="system.run_error", kind="event", description="Inspection/automation cycle failed", source="system"),
            EndpointSpec(path="camera.main.capture", kind="action", callable=True, description="Capture configured camera into latest frame", source="camera", example="camera.main.capture()"),
            EndpointSpec(path="camera.main.frame_ready", kind="event", description="Camera produced a new frame", source="camera"),
            EndpointSpec(path="camera.main.frame_sequence", kind="state", data_type="integer", description="Increments when a new backend frame is captured", source="camera", last_value=getattr(state, "frame_sequence", 0)),
        ]

        io = program.io
        specs.extend([
            EndpointSpec(path="device.modbus_1.X1", kind="state", data_type="bool", readable=True, writable=False, description=f"Configured trigger input ({io.trigger_kind} {io.trigger_address})", source="modbus", example="if device.modbus_1.X1 == ON:"),
            EndpointSpec(path="device.modbus_1.Y1", kind="state", data_type="bool", readable=True, writable=True, description=f"OK output coil {io.ok_coil}", source="modbus", example="device.modbus_1.Y1 = ON"),
            EndpointSpec(path="device.modbus_1.Y1.pulse", kind="action", callable=True, description="Pulse OK output", source="modbus", example="device.modbus_1.Y1.pulse(1.0)"),
            EndpointSpec(path="device.modbus_1.Y2", kind="state", data_type="bool", readable=True, writable=True, description=f"NG output coil {io.ng_coil}", source="modbus", example="device.modbus_1.Y2 = ON"),
            EndpointSpec(path="device.modbus_1.Y2.pulse", kind="action", callable=True, description="Pulse NG output", source="modbus", example="device.modbus_1.Y2.pulse(1.0)"),
        ])

        if snapshot is not None:
            for alias, outputs in snapshot.global_logic.items():
                _flatten(f"vision.global_scope.logic.{alias}.outputs", outputs, source="vision.global", out=specs)
            for roi_alias, logic_map in snapshot.roi_logic.items():
                for logic_alias, outputs in logic_map.items():
                    _flatten(f"vision.roi.{roi_alias}.logic.{logic_alias}.outputs", outputs, source=f"vision.roi.{roi_alias}", out=specs)

        specs.append(EndpointSpec(path="event.name", kind="data", data_type="string", description="Current event-service event name", source="event"))
        specs.append(EndpointSpec(path="event.result", kind="data", data_type="string", description="Current event result when available", source="event"))
        specs.append(EndpointSpec(path="event.run_id", kind="data", data_type="string", description="Current event run id when available", source="event"))
        return specs

    def as_dict(self, program: VisionProgramDefinition, snapshot: VisionRunSnapshot | None = None, state: Any | None = None) -> list[dict[str, Any]]:
        return [spec.model_dump() if hasattr(spec, "model_dump") else spec.dict() for spec in self.build(program, snapshot, state)]
