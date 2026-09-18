from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ServicePin(BaseModel):
    service_id: str = ""
    version: int | None = None
    output_name: str = ""


class EarlyContourFilter(BaseModel):
    min_area: float = 20.0
    min_perimeter: float = 18.0
    min_bbox_width: int = 3
    min_bbox_height: int = 3
    min_points: int = 4
    max_retained: int = 2000


class ContourSourceConfig(BaseModel):
    image_service: ServicePin = Field(default_factory=ServicePin)
    source_mode: Literal["auto", "canny", "mask_boundary"] = "auto"
    canny_low: float = 80.0
    canny_high: float = 160.0
    blur_kernel: int = 3
    retrieval: Literal["list", "external", "tree"] = "list"
    early_filter: EarlyContourFilter = Field(default_factory=EarlyContourFilter)


class ContourFilterStage(BaseModel):
    id: str
    kind: Literal["metric_filter", "largest_n", "region_filter", "simplify"]
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)


class ContourExtractorDefinition(BaseModel):
    version: int = 1
    source: ContourSourceConfig = Field(default_factory=ContourSourceConfig)
    stages: list[ContourFilterStage] = Field(default_factory=list)
