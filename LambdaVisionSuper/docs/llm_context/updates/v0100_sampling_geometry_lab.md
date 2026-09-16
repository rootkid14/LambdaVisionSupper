# v0.1.0 — Sampling / Geometry LAB foundation

## Purpose

Introduces the second Vision LAB as a reusable typed feature-extraction environment rather than a contour-only toolbox.

The page is split into three specialized workspaces:

1. **Geometry** — blob boundaries, ordered curves and measurements.
2. **Spatial Sampling** — rays, crosses, concentric rings, patch grids and signal profiles.
3. **Spectral / Statistics** — histograms, 2D Fourier spectrum and structured frequency/statistical descriptors.

## Architectural boundary

Sampling / Geometry LAB does not inherit legacy `BaseNode` and does not inherit Image LAB `ImageOperator`.

It owns a specialized `SamplingGeometryOperator` hierarchy and `SamplingGeometryRuntime`, while still following the common LAB protocol of typed ports, parameter manifests, pipeline snapshots and Lab Service deployment.

## Input source abstraction

The LAB supports two v1 raster source modes:

- **Upload** — direct `Image` or `BinaryMask` source.
- **Lab Service** — select an active `image_processing` Lab Service and one of its `Image` / `BinaryMask` outputs; the Sampling backend invokes `LAB_SERVICE_RUNTIME.run()` directly, not a localhost HTTP loop.

This establishes the future pipeline path:

`Image Processing Service -> Sampling / Geometry pipeline -> downstream Lab Service consumers`.

## Lab Service deployment

Sampling pipelines deploy using:

- `lab_type = sampling_geometry`
- `workspace_type = geometry | spatial | spectral`

Exposed stack checkpoints become stable named service outputs. `LabServiceRuntime` now has a `sampling_geometry` adapter in addition to `image_processing`.

## Backend files

- `app/services/vision_labs/sampling_geometry/types.py` — typed geometry/signal/feature artifacts.
- `specs.py` — specialized typed port spec.
- `operator.py` — `SamplingGeometryOperator` contract.
- `registry.py` — operator catalog split by workspace.
- `pipeline.py` — typed pipeline schema, validation and compiler.
- `runtime.py` — execution runtime and artifact store.
- `session.py` — interactive session lifecycle.
- `serialization.py` — JSON serialization for workbench visualization.
- `preview.py` — PNG previews for spectral maps, vectors, matrices, profiles and geometry.
- `repository.py` — saved pipeline persistence.
- `operators/geometry.py` — contour/curve/measurement operators.
- `operators/spatial.py` — ray/cross/ring/patch sampling.
- `operators/spectral.py` — FFT, histogram, statistics and frequency descriptors.
- `app/api/v1/endpoints/sampling_geometry_api.py` — REST control/preview API and upstream Lab Service source binding.

## Frontend files

- `src/Pages/SamplingGeometryLabPage.tsx` — shared shell + three workspace tabs + input/service/deploy controls.
- `src/api/samplingGeometryApi.ts` — Sampling/Geometry API client.
- `src/components/VisionLabs/SamplingGeometry/types.ts` — frontend contracts.
- `SamplingOperatorLibrary.tsx` — workspace-specific operator browser with `(i)` guide.
- `SamplingGuideModal.tsx` — text guidance + interactive/synthetic visualization + parameter exploration.
- `SamplingWorkbench.tsx` — real source overlay/data workbench.
- `SamplingVisuals.tsx` — charts, feature views and synthetic guide models.
- `SamplingStack.tsx` — typed linear stack, parameters and service-output exposure.
- `useSamplingGeometryController.ts` — session/source/live-manual/deploy/edit orchestration.

## v1 operators

### Geometry

- Extract Contours
- Select Largest Contour
- Arc-Length Resample
- Curvature Profile
- Contour Measurements

### Spatial Sampling

- Axis Rays
- Cross Sampler
- Concentric Rings
- Patch Grid Statistics

### Spectral / Statistics

- 2D Fourier Spectrum
- Radial Frequency Bands
- Angular Frequency Bands
- Intensity Histogram
- Basic Statistics

## UI/UX invariants

- `(i)` guide exists for every operator.
- Guide visualization is interactive/synthetic when an image representation is not the clearest teaching surface.
- Main workbench visualizes sampling patterns/geometry over the actual loaded source whenever spatially meaningful.
- Fourier map is a real artifact preview, not a decorative simulation.
- Profile/vector/matrix/table artifacts have dedicated data views.
- Live mode re-runs after debounced edits; Manual mode waits for Run.
- v1 UI is intentionally linear-stack-first, while backend contracts remain typed and graph-capable.
