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
    method: Literal["manual", "blur_template", "fourier"] = "manual"
    blur_kernel: int = Field(default=9, ge=1, le=99)
    template_threshold: float = Field(default=0.65, ge=-1.0, le=1.0)
    geometry: GeometryConstraint = Field(default_factory=GeometryConstraint)


class MasterRoi(BaseModel):
    roi_id: str
    name: str
    rect: NormalizedRect
    search: RoiSearchConfig = Field(default_factory=RoiSearchConfig)
    enabled: bool = True


class MasterSampleConfig(BaseModel):
    rois: list[MasterRoi] = Field(default_factory=list)
    master_shape: list[int] = Field(default_factory=list)


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


class DecisionRule(BaseModel):
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
    decision: DecisionRule = Field(default_factory=DecisionRule)


class WorkingConfig(BaseModel):
    global_services: list[WorkingServiceBinding] = Field(default_factory=list)
    station_services: dict[str, list[WorkingServiceBinding]] = Field(default_factory=dict)


class VisionProgramDefinition(BaseModel):
    version: int = 1
    program_id: str
    name: str
    description: str = ""
    io: ModbusIOConfig = Field(default_factory=ModbusIOConfig)
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
    ok: bool
    output_name: str = ""
    scalar_value: float | None = None
    message: str = ""
    shape: list[int] | None = None


class StationRunResult(BaseModel):
    station_id: str
    station_name: str
    rect: NormalizedRect
    located: bool
    search_score: float
    ok: bool
    services: list[ServiceExecutionResult] = Field(default_factory=list)


class VisionProgramRunResult(BaseModel):
    program_id: str
    global_ok: bool
    overall_ok: bool
    located_rois: list[LocatedRoi] = Field(default_factory=list)
    global_services: list[ServiceExecutionResult] = Field(default_factory=list)
    stations: list[StationRunResult] = Field(default_factory=list)
    total_ms: float = 0.0
