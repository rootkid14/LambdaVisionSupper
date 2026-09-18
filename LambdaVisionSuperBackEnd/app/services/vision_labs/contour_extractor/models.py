from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ServicePin(BaseModel):
    service_id: str = ""
    version: int | None = None
    output_name: str = ""


class EarlyContourFilter(BaseModel):
    """Mandatory memory gate executed before geometry enters ContourStore.

    This is intentionally conservative but non-zero. It removes the common
    one-pixel/very-short Canny fragments and applies a hard retained-geometry
    cap so a noisy image cannot flood the interactive session.
    """

    min_area: float = 25.0
    min_perimeter: float = 20.0
    min_bbox_width: int = 4
    min_bbox_height: int = 4
    min_points: int = 4
    max_retained: int = 600


class ContourSourceConfig(BaseModel):
    image_service: ServicePin = Field(default_factory=ServicePin)
    source_mode: Literal["auto", "canny", "mask_boundary"] = "auto"
    canny_low: float = 80.0
    canny_high: float = 160.0
    blur_kernel: int = 3
    retrieval: Literal["list", "external", "tree"] = "list"
    early_filter: EarlyContourFilter = Field(default_factory=EarlyContourFilter)


class ContourFilterStage(BaseModel):
    # Deliberately not Literal: stage kinds are plugin-style registry IDs.
    id: str
    kind: str
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)


class ContourExtractorDefinition(BaseModel):
    version: int = 2
    source: ContourSourceConfig = Field(default_factory=ContourSourceConfig)
    stages: list[ContourFilterStage] = Field(default_factory=list)
