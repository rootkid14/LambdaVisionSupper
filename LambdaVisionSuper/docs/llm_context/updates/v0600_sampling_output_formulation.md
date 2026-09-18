# v0.6.0 — Sampling Output Formulation Workspace

## Why this update exists

Sampling LAB v0.5 correctly moved to a Global/Local hierarchical sampling model, but its Output Shape Designer still mixed Sampling with tensor-depth semantics and required a full Program Run after every output-layout change. v0.6 establishes a cleaner boundary:

- Sampling LAB samples image domains and produces semantic Data Blocks.
- Sampling LAB formulates those blocks only as a **Vector** or **2-D Matrix**.
- Future Representation LAB owns cross-service channel/depth stacking, normalization, model tensor assembly, and representation-level composition.

## Runtime split

The new runtime is explicitly two-stage:

```text
Image
  ↓
SamplingProgramRuntime.sample(...)
  ↓
Cached semantic Data Blocks
  ↓
SamplingProgramRuntime.formulate(...)
  ↓
Vector [N] OR Matrix [R × C]
```

Changing sampling methods, channels, measures, placements, or Local patch grid invalidates the sampling cache and requires **Run Program**.

Changing only output formulation does not touch the image. The editor calls:

```text
POST /api/v1/sampling-geometry/sessions/{session_id}/program/formulate
```

which reformulates the cached Data Blocks.

## Sampling Program v2

New snapshots use:

```text
version = 6
program_kind = sampling_program_v2
```

Output formulation:

```text
Global: Vector only

Local:
  Vector
    - patch_major
    - feature_major

  Matrix
    - patch_rows     => [patches × features]
    - patch_columns  => [features × patches]
```

No 3-D tensor representation exists in the v0.6 editor/runtime.

Legacy `sampling_program_v1` snapshots remain runnable. The v0.6 editor can migrate v1 Program snapshots to v2 semantics; an old `spatial_tensor` editor choice becomes a 2-D patch matrix when edited under v0.6.

## Output Formulation Workspace

`SamplingOutputShapeDesigner.tsx` is now a dedicated formulation environment rather than an options dialog.

It visualizes the actual logical shape:

- Global vector as proportionally segmented feature ranges.
- Local vector as Patch-major or Feature-major segments.
- Local matrix as a real 2-D semantic plane:
  - Patch rows × feature columns, or
  - Feature rows × patch columns.
- Selecting a patch reveals the internal method/channel/measure groups that form that patch vector.

The workspace includes a **Formulate** button. It is enabled when only formulation has changed and a valid Sampling cache exists.

## Semantic metadata

Formulated outputs now describe their axes and groups rather than exposing only a numeric shape.

Examples:

```text
representation = matrix
rows_semantic = patches
columns_semantic = features
features_per_patch = 296
patch_labels = [...]
feature_groups = [...]
```

For vectors, metadata records patch/feature ordering and group ranges.

This is intended to let future Representation LAB understand what each axis and feature interval means without reverse engineering Sampling implementation details.

## Representation LAB boundary

Sampling produces one numerical representation plane per service:

```text
Sampling Gray service → Matrix [24 × 128]
Sampling R service    → Matrix [24 × 128]
Sampling G service    → Matrix [24 × 128]
```

Representation LAB may later choose to stack these into depth, concatenate them, normalize them, select features, or reshape them for a model. Sampling LAB deliberately does not make that decision.

## Key files

Frontend:

- `src/Pages/SamplingGeometryLabPage.tsx`
- `src/components/VisionLabs/SamplingProgram/SamplingOutputShapeDesigner.tsx`
- `src/components/VisionLabs/SamplingProgram/useSamplingProgramController.ts`
- `src/components/VisionLabs/SamplingProgram/types.ts`
- `src/api/samplingGeometryApi.ts`

Backend:

- `app/services/vision_labs/sampling_geometry/program.py`
- `app/services/vision_labs/sampling_geometry/program_runtime.py`
- `app/services/vision_labs/sampling_geometry/session.py`
- `app/api/v1/endpoints/sampling_geometry_api.py`
- `app/services/vision_labs/service/runtime.py`

Regression:

- `tests/vision_labs/sampling_geometry/test_sampling_program_v0500.py`
- `tests/vision_labs/sampling_geometry/test_sampling_program_v0600.py`
