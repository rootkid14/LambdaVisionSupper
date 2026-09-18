from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


AutomationMode = Literal["loop", "event", "oneshot"]
AutomationConcurrency = Literal["skip", "queue_latest"]
EndpointKind = Literal["state", "action", "event", "data"]


class AutomationServiceDefinition(BaseModel):
    service_id: str
    name: str
    enabled: bool = True
    mode: AutomationMode = "oneshot"
    interval_ms: int = Field(default=250, ge=25, le=3_600_000)
    event: str = "vision.logic_ready"
    script: str = "# Write automation logic here\n"
    timeout_ms: int = Field(default=1500, ge=50, le=120_000)
    concurrency: AutomationConcurrency = "skip"


class AutomationConfig(BaseModel):
    enabled: bool = True
    services: list[AutomationServiceDefinition] = Field(default_factory=list)


class EndpointSpec(BaseModel):
    path: str
    kind: EndpointKind
    data_type: str = "any"
    readable: bool = True
    writable: bool = False
    callable: bool = False
    description: str = ""
    source: str = "system"
    example: str = ""
    last_value: Any = None
    allowed_values: list[Any] = Field(default_factory=list)
    unit: str = ""
    object_type: str = ""
    parameters: list[dict[str, Any]] = Field(default_factory=list)


class AutomationTraceEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    service_id: str = ""
    service_name: str = ""
    phase: str = "runtime"
    level: Literal["info", "warning", "error"] = "info"
    message: str
    endpoint: str = ""
    value: Any = None
    dry_run: bool = False


class AutomationSystemState(BaseModel):
    program_id: str
    scheduler_running: bool = False
    online: bool = False
    active_workspace: str = "workspace_1"
    last_workspace: str = ""
    workspace_results: dict[str, str] = Field(default_factory=dict)
    run_state: Literal["IDLE", "CAPTURING", "INSPECTING", "DECIDING", "FINISHED", "ERROR"] = "IDLE"
    result: Literal["NONE", "OK", "NG", "ERROR"] = "NONE"
    run_id: str = ""
    last_run_ms: float | None = None
    last_error: str = ""
    frame_sequence: int = 0
    clear_sequence: int = 0
    result_sequence: int = 0
    last_event: str = ""
    keyboard_states: dict[str, bool] = Field(default_factory=dict)


class VisionRunSnapshot(BaseModel):
    program_id: str
    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    global_ok: bool
    overall_ok: bool
    total_ms: float
    global_logic: dict[str, Any] = Field(default_factory=dict)
    roi_logic: dict[str, dict[str, Any]] = Field(default_factory=dict)
    roi_meta: dict[str, Any] = Field(default_factory=dict)
    benchmarks: list[dict[str, Any]] = Field(default_factory=list)


class AutomationValidationIssue(BaseModel):
    line: int = 1
    column: int = 0
    severity: Literal["error", "warning"] = "error"
    message: str


class AutomationExecutionResult(BaseModel):
    ok: bool
    service_id: str
    dry_run: bool = False
    result_value: Any = None
    issues: list[AutomationValidationIssue] = Field(default_factory=list)
    trace: list[AutomationTraceEntry] = Field(default_factory=list)
