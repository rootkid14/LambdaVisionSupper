from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from app.services.vision_app.automation_models import AutomationConfig


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
    alias: str = ""
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




class ModbusPointDeclaration(BaseModel):
    point_id: str
    alias: str
    enabled: bool = True
    kind: Literal["coil", "discrete_input", "holding_register", "input_register"] = "coil"
    address: int = Field(default=0, ge=0)
    description: str = ""
    pulse_seconds: float = Field(default=1.0, gt=0.0, le=60.0)

    @property
    def writable(self) -> bool:
        return self.kind in {"coil", "holding_register"}

    @property
    def data_type(self) -> str:
        return "bool" if self.kind in {"coil", "discrete_input"} else "number"


class ModbusDeviceDeclaration(BaseModel):
    declaration_id: str
    alias: str = "modbus_1"
    enabled: bool = True
    driver: Literal["modbus_tcp", "simulated"] = "modbus_tcp"
    host: str = "192.168.1.177"
    port: int = Field(default=502, ge=1, le=65535)
    unit_id: int = Field(default=1, ge=0, le=247)
    points: list[ModbusPointDeclaration] = Field(default_factory=list)


def default_iot_declarations() -> list[ModbusDeviceDeclaration]:
    return [
        ModbusDeviceDeclaration(
            declaration_id="modbus_1",
            alias="modbus_1",
            points=[
                ModbusPointDeclaration(point_id="x1", alias="X1", kind="discrete_input", address=0, description="Trigger input"),
                ModbusPointDeclaration(point_id="y1", alias="Y1", kind="coil", address=0, description="OK output"),
                ModbusPointDeclaration(point_id="y2", alias="Y2", kind="coil", address=1, description="NG output"),
            ],
        )
    ]


class IotDeclarationConfig(BaseModel):
    devices: list[ModbusDeviceDeclaration] = Field(default_factory=default_iot_declarations)


class CameraApiParameter(BaseModel):
    name: str
    data_type: Literal["number", "integer", "bool", "string"] = "number"
    default: Any = None
    description: str = ""


class CameraCustomApi(BaseModel):
    api_id: str
    alias: str
    enabled: bool = True
    method: Literal["GET", "POST"] = "GET"
    path_template: str = "/"
    description: str = ""
    parameters: list[CameraApiParameter] = Field(default_factory=list)


class CameraDeclaration(BaseModel):
    declaration_id: str
    alias: str = "camera_1"
    enabled: bool = True
    driver: Literal["basler", "http", "simulated"] = "simulated"
    # Basler resource
    basler_device_id: str = ""
    exposure_us: float = Field(default=5000.0, gt=0.0, le=10_000_000.0)
    grab_timeout_ms: int = Field(default=5000, ge=100, le=120000)
    # Generic HTTP resource
    host: str = "pi3b.local"
    port: int = Field(default=8000, ge=1, le=65535)
    capture_path: str = "/capture"
    stream_path: str = ""
    http_timeout_s: float = Field(default=8.0, gt=0.1, le=120.0)
    # Named slots are part of the public object contract.
    image_slot: str = "Current_image"
    stream_slot: str = "Streaming_frame"
    custom_apis: list[CameraCustomApi] = Field(default_factory=list)


def default_camera_declarations() -> list[CameraDeclaration]:
    return [CameraDeclaration(declaration_id="camera_main", alias="main", driver="simulated")]


class CameraDeclarationConfig(BaseModel):
    devices: list[CameraDeclaration] = Field(default_factory=default_camera_declarations)


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


ControlPrimitiveAction = Literal[
    "trigger_camera",
    "run_inspection",
    "out_ok",
    "out_ng",
    "clear_working_screen",
]


class ControlBinding(BaseModel):
    binding_id: str
    enabled: bool = True
    source: Literal["keyboard", "modbus_trigger"] = "keyboard"
    key: str = "F8"
    action: ControlPrimitiveAction = "run_inspection"


class ControlMapperConfig(BaseModel):
    """Maps primitive control events to Vision App actions.

    The future IDE/sandbox can become another action source without changing camera/IOT/runtime contracts.
    """

    bindings: list[ControlBinding] = Field(default_factory=lambda: [
        ControlBinding(binding_id="keyboard_run", source="keyboard", key="F8", action="run_inspection"),
        ControlBinding(binding_id="keyboard_camera", source="keyboard", key="F7", action="trigger_camera"),
        ControlBinding(binding_id="keyboard_ok", source="keyboard", key="F9", action="out_ok"),
        ControlBinding(binding_id="keyboard_ng", source="keyboard", key="F10", action="out_ng"),
        ControlBinding(binding_id="keyboard_clear", source="keyboard", key="Escape", action="clear_working_screen"),
        ControlBinding(binding_id="modbus_run", source="modbus_trigger", key="", action="run_inspection"),
    ])


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
    enable_filter: bool = True
    filter_services: list[WorkingServiceBinding] = Field(default_factory=list)
    enable_logic: bool = True
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


class WorkspaceDefinition(BaseModel):
    workspace_id: str
    name: str = "Workspace 1"
    alias: str = "workspace_1"
    enabled: bool = True
    # Example: camera.main.Current_image. Empty means manual/latest frame for this workspace.
    input_binding: str = "camera.main.Current_image"
    master: MasterSampleConfig = Field(default_factory=MasterSampleConfig)
    working: WorkingConfig = Field(default_factory=WorkingConfig)


def default_workspaces() -> list[WorkspaceDefinition]:
    return [WorkspaceDefinition(workspace_id="workspace_1", name="Workspace 1", alias="workspace_1")]


class SimulatorConfig(BaseModel):
    enabled: bool = False
    # UI-only defaults; runtime simulated resources keep volatile values in memory.
    camera_sequence_mode: Literal["fixed", "next", "loop"] = "fixed"
    stream_fps: float = Field(default=4.0, ge=0.2, le=30.0)


class VisionProgramDefinition(BaseModel):
    version: int = 5
    program_id: str
    name: str
    description: str = ""
    # Legacy contracts remain for old runner/program JSON. New UI uses iot/cameras/workspaces.
    io: ModbusIOConfig = Field(default_factory=ModbusIOConfig)
    iot: IotDeclarationConfig = Field(default_factory=IotDeclarationConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    cameras: CameraDeclarationConfig = Field(default_factory=CameraDeclarationConfig)
    control: ControlMapperConfig = Field(default_factory=ControlMapperConfig)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)
    master: MasterSampleConfig = Field(default_factory=MasterSampleConfig)
    working: WorkingConfig = Field(default_factory=WorkingConfig)
    workspaces: list[WorkspaceDefinition] = Field(default_factory=default_workspaces)
    active_workspace_id: str = "workspace_1"
    simulator: SimulatorConfig = Field(default_factory=SimulatorConfig)


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
