from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

class LabServicePort(BaseModel):
    type: str
    required: bool = True
    label: str | None = None

class LabServiceOutputBinding(BaseModel):
    type: str
    node_id: str
    port: str
    label: str | None = None

class LabServiceDefinition(BaseModel):
    service_id: str
    name: str
    lab_type: str
    workspace_type: str | None = None
    version: int
    status: str = "deployed"
    inputs: dict[str, LabServicePort] = Field(default_factory=dict)
    outputs: dict[str, LabServiceOutputBinding] = Field(default_factory=dict)
    pipeline_snapshot: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    created_at: str
    deployed_at: str

class LabServiceRunManifest(BaseModel):
    run_id: str
    service_id: str
    service_version: int
    lab_type: str
    workspace_type: str | None = None
    outputs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    timings_ms: dict[str, float] = Field(default_factory=dict)
    total_ms: float = 0.0
    started_at: str
