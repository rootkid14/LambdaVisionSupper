from __future__ import annotations

from hashlib import sha256
import json
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


# ---------------------------------------------------------------------------
# Legacy v0.5 model. It remains parseable so deployed Sampling Program v1
# snapshots continue to run unchanged.
# ---------------------------------------------------------------------------
class LegacyOutputShapeDefinition(BaseModel):
    global_layout: Literal["vector"] = "vector"
    local_layout: Literal["flatten", "patch_matrix", "spatial_tensor"] = "spatial_tensor"
    local_order: Literal["patch_major", "feature_major"] = "patch_major"
    include_global: bool = True
    include_local: bool = True
    include_combined: bool = False


class LegacySamplingProgramDefinition(BaseModel):
    version: int = 5
    program_kind: Literal["sampling_program_v1"] = "sampling_program_v1"
    source_board: dict[str, Any] = Field(default_factory=dict)
    input_source: str = "inspected_image"
    global_domain: SamplingDomainDefinition = Field(default_factory=SamplingDomainDefinition)
    local_domain: LocalSamplingDomainDefinition = Field(default_factory=LocalSamplingDomainDefinition)
    output_shape: LegacyOutputShapeDefinition = Field(default_factory=LegacyOutputShapeDefinition)


# ---------------------------------------------------------------------------
# Sampling Program v2 / LAB v0.6.
# Sampling intentionally stops at a numeric Vector or 2-D Matrix.
# Tensor depth/channel stacking belongs to the future Representation LAB.
# ---------------------------------------------------------------------------
class OutputShapeDefinition(BaseModel):
    global_layout: Literal["vector"] = "vector"
    local_layout: Literal["vector", "matrix"] = "matrix"
    local_vector_order: Literal["patch_major", "feature_major"] = "patch_major"
    local_matrix_axis: Literal["patch_rows", "patch_columns"] = "patch_rows"
    include_global: bool = True
    include_local: bool = True
    include_combined: bool = False


class SamplingProgramDefinition(BaseModel):
    version: int = 6
    program_kind: Literal["sampling_program_v2"] = "sampling_program_v2"
    source_board: dict[str, Any] = Field(default_factory=dict)
    input_source: str = "inspected_image"
    global_domain: SamplingDomainDefinition = Field(default_factory=SamplingDomainDefinition)
    local_domain: LocalSamplingDomainDefinition = Field(default_factory=LocalSamplingDomainDefinition)
    output_shape: OutputShapeDefinition = Field(default_factory=OutputShapeDefinition)


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def sampling_program_sample_signature(program: SamplingProgramDefinition) -> str:
    """Hash only the sampling definition, never the formulation.

    Changing Vector/Matrix formulation must be able to reuse sampled Data Blocks.
    Any change to source binding, Global/Local methods, channels, measures, placement
    or patch grid invalidates this signature and therefore requires Run Program.
    """
    payload = model_to_dict(program)
    payload.pop("output_shape", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


def migrate_v1_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert an editable v0.5 Sampling Program snapshot to v0.6 semantics.

    Old spatial tensors are intentionally flattened into a 2-D patch matrix because
    Sampling LAB v0.6 no longer owns tensor-depth semantics.
    """
    if payload.get("program_kind") != "sampling_program_v1":
        return payload
    old = dict(payload.get("output_shape") or {})
    old_layout = str(old.get("local_layout") or "spatial_tensor")
    old_order = str(old.get("local_order") or "patch_major")
    if old_layout == "flatten":
        local_layout = "vector"
    else:
        local_layout = "matrix"
    converted = dict(payload)
    converted["version"] = 6
    converted["program_kind"] = "sampling_program_v2"
    converted["output_shape"] = {
        "global_layout": "vector",
        "local_layout": local_layout,
        "local_vector_order": old_order if old_order in {"patch_major", "feature_major"} else "patch_major",
        "local_matrix_axis": "patch_columns" if old_order == "feature_major" else "patch_rows",
        "include_global": bool(old.get("include_global", True)),
        "include_local": bool(old.get("include_local", True)),
        "include_combined": bool(old.get("include_combined", False)),
    }
    return converted


def sampling_program_catalog() -> list[dict[str, Any]]:
    """Stable editor-facing method catalog for Sampling Program v2.

    Frequency-domain transforms remain deliberately outside the Sampling LAB editor.
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
