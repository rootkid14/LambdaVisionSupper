# v0.2.0 — Sampling / Geometry Source Board + Universal Artifact Inspector

## Why this update exists

The first Sampling / Geometry LAB proved the three-workspace concept but treated each tab too much like an independent mini application. v0.2 makes the page one coherent feature-extraction environment built around a shared inspected source.

## Shared Source Board

One raw input image is loaded once for the whole page.

The Source Board can pin two optional upstream Image Processing Lab Services:

1. **Image Processing Service** — must expose an `Image`; its selected output becomes `inspected_image` for Spatial/Spectral workspaces. When blank, raw input is used.
2. **Contour Source Service** — may expose `Image` or `BinaryMask`; Canny runs on this raster and produces the Geometry master contour map. When blank, Canny runs on the raw input image.

The board exposes typed internal sources:

- `raw_image : Image`
- `inspected_image : Image`
- `geometry_raster : Image | BinaryMask`
- `edge_map : BinaryMask`
- `contour_image : Image`
- `master_contours : ContourSet`

Switching tabs no longer discards the input or the per-tab stacks.

## Deployed Sampling service behavior

The Source Board configuration is stored in `SamplingPipelineDefinition.source_board`.

A deployed Sampling / Geometry Lab Service has a public input contract of one raw `Image`. `LabServiceRuntime` reconstructs the Source Board internally, directly invokes pinned upstream Image Processing services, resolves typed source bindings, then executes the deployed workspace pipeline.

No localhost HTTP call is used for internal service composition.

## Universal Artifact Inspector

`View/Inspect` and `Expose` now have separate semantics:

- **Inspect**: development/debug UI only.
- **Expose**: adds a typed output to the public Lab Service contract.

Each output port on each stack operator has an Inspect button. Multiple-output operators can expose or inspect ports independently.

Typed inspector behaviors include:

- `ContourSet`: count, contour metrics, linked row/image selection, kept-vs-master overlay.
- `Polyline`: point count, arc length, metadata, spatial overlay.
- `SamplingHousing`: element list plus housing overlay.
- `ProfileSet`: graph.
- `FeatureVector`: dimension, named feature schema and values.
- `FeatureMatrix`: matrix/heatmap representation.
- `Spectrum2D`: Fourier energy map plus radial/angular diagnostic graphs.
- generic fallback for future artifact types.

This is the extensibility rule for new algorithms: operators emit typed artifacts; inspectors belong to artifact types, not individual algorithms whenever possible.

## Geometry workspace mission

Geometry is now primarily a contour-discovery funnel:

`Master Contour Map -> filter -> rank -> spatial filter -> cleanup -> meaningful shape set`

New visible operators:

- Contour Filter
- Keep Largest N
- Contour Region Filter
- Simplify Contours

Legacy explicit Extract Contours is hidden from the catalog because Source Board owns initial contour extraction. Legacy operators remain registered so saved v0.1 pipelines can still load.

`ContourSet` preserves stable contour IDs through filters so the UI can highlight the same candidate across pipeline stages.

## Spatial Sampling mission

Spatial sampling separates two questions:

- **WHERE**: Sampling Housing
- **HOW**: Data Extractor

Visible housings:

- Axis Ray Housing
- Cross Housing
- Concentric Ring Housing
- Patch Grid Housing

`Data Extractor` accepts a `SamplingHousing` plus a Source Board `Image` reference and lets the user choose:

- Gray / RGB / HSV / LAB channels;
- full-resolution, pixel-step or fixed-count sampling;
- mean / standard deviation / min-max;
- normalized histogram bins;
- fixed-length raw profiles for visual debugging.

It returns three independently inspectable outputs:

- `FeatureVector`
- `FeatureMatrix`
- `ProfileSet`

Feature names encode housing element + channel + statistic so Representation LAB never has to guess vector composition.

## Spectral / Statistics mission

FFT visualization is strengthened. `Spectrum2D` now carries diagnostic metadata:

- 32-bin normalized radial energy profile;
- 36-sector normalized angular energy profile;
- dominant radial band;
- dominant orientation;
- total spectral energy.

The workbench can show source image, Fourier energy map, radial graph and angular graph together.

`contour_image` is a first-class Source Board image, so FFT can be run directly on contour/edge structure for future shape-frequency comparison work.

## Viewport

The spatial workbench uses a zoom/pan canvas:

- mouse wheel zoom;
- drag pan;
- double-click reset/fit;
- overlays transform with the image;
- contour hit-testing is available through SVG geometry.

## Important files

Frontend:

- `src/Pages/SamplingGeometryLabPage.tsx`
- `src/components/VisionLabs/SamplingGeometry/SourceBoard.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingCanvas.tsx`
- `src/components/VisionLabs/SamplingGeometry/ArtifactInspectorModal.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingStack.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingWorkbench.tsx`
- `src/components/VisionLabs/SamplingGeometry/useSamplingGeometryController.ts`
- `src/api/samplingGeometryApi.ts`

Backend:

- `app/services/vision_labs/sampling_geometry/source_board.py`
- `app/services/vision_labs/sampling_geometry/types.py`
- `app/services/vision_labs/sampling_geometry/serialization.py`
- `app/services/vision_labs/sampling_geometry/operators/geometry.py`
- `app/services/vision_labs/sampling_geometry/operators/spatial.py`
- `app/services/vision_labs/sampling_geometry/operators/spectral.py`
- `app/api/v1/endpoints/sampling_geometry_api.py`
- `app/services/vision_labs/service/runtime.py`
- `app/api/v1/endpoints/lab_service_api.py`
