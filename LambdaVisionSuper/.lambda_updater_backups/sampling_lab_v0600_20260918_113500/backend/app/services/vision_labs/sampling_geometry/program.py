from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SamplingMethodKind = Literal["histogram", "statistics", "rays", "cross", "rings"]
SamplingPlacementMode = Literal["domain", "center", "auto_grid"]
SamplingMode = Literal["count", "step", "full"]


class SamplingPlacement(BaseModel):
    mode: SamplingPlacementMode = "domain"
    center_x: float = Field(default=0.5, ge=0.0, le=1.0)
    center_y: float = Field(default=0.5, ge=0.0, le=1.0)
    rows: int = Field(default=2, ge=1, le=32)
    cols: int = Field(default=2, ge=1, le=32)


class SamplingMethodDefinition(BaseModel):
    id: str
    kind: SamplingMethodKind
    label: str | None = None
    enabled: bool = True
    channels: list[str] = Field(default_factory=lambda: ["gray"])
    measures: list[str] = Field(default_factory=lambda: ["profile"])
    placement: SamplingPlacement = Field(default_factory=SamplingPlacement)
    sampling_mode: SamplingMode = "count"
    sample_count: int = Field(default=64, ge=2, le=4096)
    sample_step: float = Field(default=4.0, gt=0.0, le=4096.0)
    histogram_bins: int = Field(default=16, ge=2, le=256)
    parameters: dict[str, Any] = Field(default_factory=dict)


class SamplingDomainDefinition(BaseModel):
    methods: list[SamplingMethodDefinition] = Field(default_factory=list)


class LocalGridDefinition(BaseModel):
    rows: int = Field(default=4, ge=1, le=64)
    cols: int = Field(default=6, ge=1, le=64)
    gap_px: int = Field(default=0, ge=0, le=128)


class LocalSamplingDomainDefinition(BaseModel):
    grid: LocalGridDefinition = Field(default_factory=LocalGridDefinition)
    methods: list[SamplingMethodDefinition] = Field(default_factory=list)


class OutputShapeDefinition(BaseModel):
    global_layout: Literal["vector"] = "vector"
    local_layout: Literal["flatten", "patch_matrix", "spatial_tensor"] = "spatial_tensor"
    local_order: Literal["patch_major", "feature_major"] = "patch_major"
    include_global: bool = True
    include_local: bool = True
    include_combined: bool = False


class SamplingProgramDefinition(BaseModel):
    version: int = 5
    program_kind: Literal["sampling_program_v1"] = "sampling_program_v1"
    source_board: dict[str, Any] = Field(default_factory=dict)
    input_source: str = "inspected_image"
    global_domain: SamplingDomainDefinition = Field(default_factory=SamplingDomainDefinition)
    local_domain: LocalSamplingDomainDefinition = Field(default_factory=LocalSamplingDomainDefinition)
    output_shape: OutputShapeDefinition = Field(default_factory=OutputShapeDefinition)


def sampling_program_catalog() -> list[dict[str, Any]]:
    """Stable editor-facing method catalog for Sampling Program v1.

    The catalog intentionally excludes FFT/frequency transforms. Frequency-domain
    analysis can become a dedicated LAB later without coupling the sampling DSL.
    """
    return [
        {
            "kind": "histogram",
            "label": "Histogram",
            "family": "Statistics",
            "description": "Represent a domain/channel as a distribution of values.",
            "supports_placement": False,
            "default_measures": ["histogram"],
            "guide": {
                "concept": "Count how many sampled values fall inside each value interval (bin).",
                "formula": "hist[k] = count(x in bin k) / N",
                "visual": "histogram",
            },
        },
        {
            "kind": "statistics",
            "label": "Statistics",
            "family": "Statistics",
            "description": "Compact summary such as mean, standard deviation, min/max and median.",
            "supports_placement": False,
            "default_measures": ["mean", "std", "min", "max"],
            "guide": {
                "concept": "Summarize a large set of pixel values with a few interpretable numbers.",
                "formula": "mean = Σx/N ; std = sqrt(Σ(x-mean)^2/N)",
                "visual": "distribution",
            },
        },
        {
            "kind": "rays",
            "label": "Rays",
            "family": "Spatial Shape",
            "description": "Sample ordered one-dimensional profiles along horizontal/vertical rays.",
            "supports_placement": False,
            "default_measures": ["profile"],
            "guide": {
                "concept": "A ray converts spatial pixels along a line into an ordered numerical signal.",
                "formula": "profile[i] = channel(x_i, y_i)",
                "visual": "rays",
            },
        },
        {
            "kind": "cross",
            "label": "Cross Shapes",
            "family": "Spatial Shape",
            "description": "Horizontal + vertical profiles around one center or an automatically arranged center grid.",
            "supports_placement": True,
            "default_measures": ["profile"],
            "guide": {
                "concept": "Each center creates two orthogonal rays; Auto Grid repeats the same cross throughout the domain.",
                "formula": "cross = horizontal profile ⊕ vertical profile",
                "visual": "cross",
            },
        },
        {
            "kind": "rings",
            "label": "Concentric Rings",
            "family": "Spatial Shape",
            "description": "Circular profiles around one center or an automatically arranged center grid.",
            "supports_placement": True,
            "default_measures": ["profile"],
            "guide": {
                "concept": "Rings sample how channel values change around and away from one or more centers.",
                "formula": "ring[i] = channel(cx+r cos θ_i, cy+r sin θ_i)",
                "visual": "rings",
            },
        },
    ]
