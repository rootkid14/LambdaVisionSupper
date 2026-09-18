# v0.5.0 — Sampling Program: Global / Local hierarchy

## Why this release exists

Sampling LAB v0.4 still felt like two unrelated editors (Spatial and Spectral) and inherited too much linear-pipeline thinking. v0.5 replaces the new editor/runtime contract with a hierarchical **Sampling Program** while retaining the legacy Sampling/Geometry runtime for already deployed v0.1-v0.4 service snapshots.

Frequency-domain transforms (FFT, Local FFT, Fourier maps) are intentionally removed from the **current Sampling editor scope**. The old code remains only for backward compatibility; frequency analysis may become a dedicated LAB later.

## New mental model

```text
Image
  ↓
Sampling Domain
  ├─ GLOBAL — one whole-image domain
  │    └─ methods[]
  │
  └─ LOCAL — Patch Grid
       ├─ rows × cols
       └─ methods[] repeated identically on every patch

Method
  ↓
placement / sampling geometry
  ↓
channels
  ↓
measures
  ↓
semantic Data Blocks
  ↓
Output Shape Designer
  ↓
vector / patch matrix / spatial tensor
```

## Current method families

- Histogram — whole-domain or per-patch distribution.
- Statistics — mean/std/min/max/median on selected channels.
- Rays — ordered horizontal/vertical profiles.
- Cross Shapes — center-based or auto-grid cross patterns.
- Concentric Rings — center-based or auto-grid ring patterns.

For shape methods, sampling density can be fixed-count, fixed-step, or full-pixel density. The canvas shows approximate **actual sample positions** as yellow points.

## Global and Local UI

The right panel has two root tabs:

- **GLOBAL**: the representative domain is the whole inspected image. Child blocks are global sampling methods.
- **LOCAL**: the root block is a Patch Grid. User configures patch rows/columns; child methods are a recipe repeated on every patch.

The left Method Library is contextual to the selected root. The center canvas visualizes the selected domain/method on the real inspected image.

## Output Shape Designer

Main editor remains compact. Detailed numerical composition is moved into a dedicated Output Shape Designer.

Global example:

```text
[Histogram D] [Gray Rays D] [HSV Statistics D] → Vector [D]
```

Local example:

```text
[Patch 1 D] [Patch 2 D] ... [Patch N D]
```

Clicking a patch reveals its internal method/data-block composition. Local output can be materialized as:

- flattened vector,
- patch matrix,
- spatial tensor.

Axis order can be patch-major or feature-depth-major. A typical local spatial tensor is `[rows, cols, D]`; feature-major becomes `[D, rows, cols]`.

## Image-grounded teaching

Channel help can extract the actual Gray/R/G/B/H/S/V/L*/a*/b* channel from the current inspected image. Mean, STD, histogram, histogram bins, and sampling density include formula/graph explanations inside the app.

## Backend contract

New files:

- `app/services/vision_labs/sampling_geometry/program.py`
- `app/services/vision_labs/sampling_geometry/program_runtime.py`

The public editor model is `SamplingProgramDefinition` (`program_kind = sampling_program_v1`). It owns:

- Source Board config,
- Global methods,
- Local Patch Grid + repeated methods,
- Output shape configuration.

`SamplingProgramRuntime` produces semantic Data Blocks and composed numerical artifacts.

## Lab Service

New Sampling services still use `lab_type = sampling_geometry` for compatibility, but `pipeline_snapshot.program_kind = sampling_program_v1` identifies the new adapter. Public input remains one raw `Image`; pinned Image Processing service configuration is replayed internally.

Available typed outputs:

- `global_data : composed_data`
- `local_data : composed_data`
- `combined_data : composed_data`

`LabServiceRuntime` detects Sampling Program snapshots before falling back to the legacy Sampling pipeline adapter.

## Backward compatibility

Do **not** remove these old modules yet:

- `sampling_geometry/pipeline.py`
- `sampling_geometry/runtime.py`
- `sampling_geometry/operators/spectral.py`
- old Spatial/Spectral React components.

They remain necessary for deployed v0.1-v0.4 snapshots. The v0.5 editor does not expose them.

## Architectural boundaries

Sampling LAB now owns structured numerical observation of raster data. It does not own:

- contour discovery/selection (Contour Extractor LAB),
- FFT/frequency-domain transforms in the current editor,
- OK/NG rules (Comparison / Rule LAB),
- cross-service/model-level normalization and representation engineering,
- AI model training/inference.
