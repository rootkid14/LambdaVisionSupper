from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class ServicePin(BaseModel):
    service_id: str = ""
    version: int | None = None
    output_name: str = ""


class NormalizedRect(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(gt=0.0, le=1.0)
    h: float = Field(gt=0.0, le=1.0)


class GeometryConstraint(BaseModel):
    enabled: bool = True
    search_margin_px: int = Field(default=80, ge=0, le=4096)
    max_shift_px: int = Field(default=120, ge=0, le=4096)


class RoiSearchConfig(BaseModel):
    """Legacy per-ROI locator contract retained so v0.7 JSON keeps loading."""

    method: Literal["manual", "blur_template", "fourier"] = "manual"
    blur_kernel: int = Field(default=9, ge=1, le=99)
    template_threshold: float = Field(default=0.65, ge=-1.0, le=1.0)
    geometry: GeometryConstraint = Field(default_factory=GeometryConstraint)


class RoiLocatorConfig(BaseModel):
    """One locator family/config applies to every ROI in a Master Sample."""

    method: Literal["manual", "blur_template", "fourier"] = "manual"
    blur_kernel: int = Field(default=9, ge=1, le=99)
    template_threshold: float = Field(default=0.65, ge=-1.0, le=1.0)
    geometry: GeometryConstraint = Field(default_factory=GeometryConstraint)


class MasterRoi(BaseModel):
    roi_id: str
    name: str
    rect: NormalizedRect
    enabled: bool = True
    # Legacy only. New runtime reads MasterSampleConfig.locator.
    search: RoiSearchConfig | None = None


class MasterSampleConfig(BaseModel):
    rois: list[MasterRoi] = Field(default_factory=list)
    master_shape: list[int] = Field(default_factory=list)
    locator: RoiLocatorConfig = Field(default_factory=RoiLocatorConfig)


class ModbusIOConfig(BaseModel):
    enabled: bool = False
    host: str = "192.168.1.177"
    port: int = Field(default=502, ge=1, le=65535)
    device_id: int = Field(default=1, ge=0, le=247)
    trigger_kind: Literal["discrete_input", "coil"] = "discrete_input"
    trigger_address: int = Field(default=0, ge=0)
    trigger_active_high: bool = True
    ok_coil: int = Field(default=0, ge=0)
    ng_coil: int = Field(default=1, ge=0)
    pulse_seconds: float = Field(default=1.0, gt=0.0, le=60.0)
    poll_interval_ms: int = Field(default=50, ge=10, le=5000)


class CameraConfig(BaseModel):
    enabled: bool = False
    driver: Literal["manual", "basler", "url"] = "manual"
    # Basler can be addressed by GigE IP or serial number.
    basler_device_id: str = ""
    exposure_us: float = Field(default=5000.0, gt=0.0, le=10_000_000.0)
    grab_timeout_ms: int = Field(default=5000, ge=100, le=120000)
    # Generic HTTP camera contract. Raspberry Pi is simply one implementation.
    capture_url: str = "http://pi3b.local:8000/capture"
    focus_url_template: str = "http://pi3b.local:8000/focus?x={x}&y={y}&w={w}&h={h}"
    http_timeout_s: float = Field(default=8.0, gt=0.1, le=120.0)


class DecisionRule(BaseModel):
    """Legacy v0.7 rule retained for program migration."""

    mode: Literal[
        "service_success",
        "scalar_gt",
        "scalar_gte",
        "scalar_lt",
        "scalar_lte",
        "scalar_eq",
    ] = "service_success"
    output_name: str = ""
    value_path: str = ""
    threshold: float = 0.0


class WorkingServiceBinding(BaseModel):
    binding_id: str
    service_id: str
    version: int | None = None
    enabled: bool = True
    label: str = ""
    alias: str = ""
    # Legacy v0.7 per-binding decision. New programs use ScopeDecisionConfig.
    decision: DecisionRule | None = None


class ScopeDecisionConfig(BaseModel):
    script: str = (
        "if logic_ok:\n"
        "    result = 'OK'\n"
        "else:\n"
        "    result = 'NG'\n"
    )


class ScopePipelineConfig(BaseModel):
    enable_filter: bool = False
    filter_services: list[WorkingServiceBinding] = Field(default_factory=list)
    enable_logic: bool = False
    logic_services: list[WorkingServiceBinding] = Field(default_factory=list)
    enable_decision: bool = False
    decision: ScopeDecisionConfig = Field(default_factory=ScopeDecisionConfig)


class WorkingConfig(BaseModel):
    global_scope: ScopePipelineConfig = Field(default_factory=ScopePipelineConfig)
    station_scopes: dict[str, ScopePipelineConfig] = Field(default_factory=dict)
    station_execution: Literal["sequential", "parallel"] = "sequential"
    # Legacy fields preserved for repository migration/backward JSON parsing.
    global_services: list[WorkingServiceBinding] = Field(default_factory=list)
    station_services: dict[str, list[WorkingServiceBinding]] = Field(default_factory=dict)


class VisionProgramDefinition(BaseModel):
    version: int = 2
    program_id: str
    name: str
    description: str = ""
    io: ModbusIOConfig = Field(default_factory=ModbusIOConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    master: MasterSampleConfig = Field(default_factory=MasterSampleConfig)
    working: WorkingConfig = Field(default_factory=WorkingConfig)


class LocatedRoi(BaseModel):
    roi_id: str
    name: str
    rect: NormalizedRect
    score: float = 1.0
    method: str
    found: bool = True
    message: str = ""


class ServiceExecutionResult(BaseModel):
    binding_id: str
    service_id: str
    alias: str = ""
    ok: bool
    outputs: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    elapsed_ms: float = 0.0


class DecisionExecutionResult(BaseModel):
    enabled: bool = False
    ok: bool = True
    result: str = "OK"
    message: str = ""
    elapsed_ms: float = 0.0


class DebugImageRef(BaseModel):
    key: str
    label: str
    scope: str
    phase: str


class BenchmarkStep(BaseModel):
    scope: str
    phase: str
    name: str
    elapsed_ms: float
    detail: str = ""


class ScopeRunResult(BaseModel):
    scope_id: str
    scope_name: str
    ok: bool
    filter_services: list[ServiceExecutionResult] = Field(default_factory=list)
    logic_services: list[ServiceExecutionResult] = Field(default_factory=list)
    decision: DecisionExecutionResult = Field(default_factory=DecisionExecutionResult)
    elapsed_ms: float = 0.0


class StationRunResult(BaseModel):
    station_id: str
    station_name: str
    rect: NormalizedRect
    located: bool
    search_score: float
    ok: bool
    scope: ScopeRunResult | None = None


class VisionProgramRunResult(BaseModel):
    program_id: str
    run_id: str
    global_ok: bool
    overall_ok: bool
    located_rois: list[LocatedRoi] = Field(default_factory=list)
    global_scope: ScopeRunResult | None = None
    stations: list[StationRunResult] = Field(default_factory=list)
    debug_images: list[DebugImageRef] = Field(default_factory=list)
    benchmarks: list[BenchmarkStep] = Field(default_factory=list)
    total_ms: float = 0.0


class TriggerRunnerStatus(BaseModel):
    program_id: str
    armed: bool = False
    running_cycle: bool = False
    last_triggered: bool = False
    last_result: str | None = None
    last_error: str = ""
    last_cycle_ms: float | None = None
    cycles: int = 0
