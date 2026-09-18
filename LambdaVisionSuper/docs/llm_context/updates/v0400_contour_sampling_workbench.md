# v0.4.0 — Contour Discovery + Sampling Data Exploration Workbench

## Why this release exists

v0.3 correctly separated Contour Extractor LAB from Sampling LAB, but real use exposed two runtime bugs and several UX/architecture weaknesses:

- `edge_map` preview returned HTTP 400 because a boolean BinaryMask reached OpenCV JPEG/PNG encoding.
- Spectral blocks tried to inspect `node.spectrum` immediately when merely selecting/adding a node, before any runtime artifact existed.
- Contour LAB had the right memory concept but the UI still looked like a small filter control panel, leaving no credible path toward master-shape/Fourier/pattern discovery.
- Spatial Sampling still did not communicate sampling density well and its Cross/Ring patterns were single-center only.
- Data Layout blocks cluttered the editor instead of behaving like a real composition workspace.
- Teaching/help surfaces were generic instead of grounded in the actual inspected image/data.
- Spectral/Statistics inspectors overused source-image previews instead of making numerical/statistical representations primary.

v0.4 keeps the v0.3 architectural split but redesigns both workbenches around **data inspection, explanation and extensibility**.

## Contour Extractor LAB

### Memory model

Candidate geometry follows this lifecycle:

```text
source raster / mask
  -> candidate extraction
  -> mandatory Base Memory Filter
       rejected candidate coordinates are discarded here
  -> retained ContourStore
       geometry stored exactly once
  -> registered stages
       selections contain only stable contour IDs
  -> final ContourSet
```

The default retained cap is intentionally conservative (`max_retained=600`). The user can change it, but large retained sets should normally trigger source/filter tuning rather than browser-side brute force.

The frontend receives summary/metrics first. Geometry is fetched lazily for selected contours instead of serializing every retained coordinate array after every run.

### Preview fix

`BinaryMask` previews are normalized to uint8 (`0/255`) before `PreviewEncoder` so `edge_map` and other masks can be encoded safely. `edge_map` and `contour_image` are real backend artifacts; they are not aliases for the raw image.

### Contour Stage Registry

Contour discovery is now explicitly extensible through a stage registry. A stage manifest defines:

- stable `kind`;
- category/label/description;
- parameter manifest;
- execution implementation;
- ID-in / ID-out behavior.

Existing stage families include metric filtering, largest-N, region filtering and simplification.

### Fourier/master-shape foundation

`fourier_shape_filter` is the first advanced shape-pattern stage.

An ordered contour is arc-length resampled and represented as a complex signal:

```text
z(s) = x(s) + i y(s)
```

FFT coefficients provide a compact contour descriptor. Translation and scale are normalized before comparison. A selected contour can act as the current master/reference shape.

The UI provides original-vs-low-harmonic reconstruction so users can see that lower harmonics describe broad shape while higher harmonics restore finer detail.

This is intentionally a foundation for future:

- master contour libraries;
- topology stages;
- curvature signatures;
- convex/part decomposition;
- graph-based shape structure;
- learned contour embeddings;
- hybrid rule + descriptor stages.

New contour algorithms should register a stage, avoid geometry cloning, provide before/after diagnostics and reuse the standard contour inspector.

## Sampling LAB

Sampling remains split from contour discovery and contains only Spatial Sampling and Spectral / Statistics.

### Spatial Sampling Unit

A unit owns both halves of sampling:

```text
Housing = WHERE
Data Extractor = WHAT / HOW
```

The Housing is inspectable and visualizable but is not itself a service output. The extracted/composed numerical data is the useful output.

The left panel is now an actual Sampling Unit Library rather than a workflow explanation panel.

### Grid-centred Cross and Ring patterns

Cross and Concentric Ring housings support a grid of center points:

```text
center_rows x center_cols
```

Each grid point owns its own cross or ring family, allowing the pattern to cover the inspected image at selectable density.

### Sampling density visualization

The spatial canvas overlays yellow sample points using the current mode:

- full resolution;
- fixed step;
- fixed sample count.

This makes `sampling step` visible instead of remaining a hidden numeric parameter.

### Image-grounded parameter teaching

Channel help uses the current inspected image and asks the backend for a real channel preview (Gray/R/G/B/H/S/V/L*/a*/b*).

Math/statistics help uses graphs plus formulas, for example:

```text
mean: μ = (1/N) Σ xᵢ
std : σ = sqrt((1/N) Σ(xᵢ-μ)²)
```

Histogram help explains bins visually; sample-step help visualizes selected points.

### Data Blocks and dedicated Layout Composer

The inline unit editor no longer renders a long field of blocks. It displays a compact block count/output-shape summary and opens a dedicated Data Layout Workspace.

The workspace exposes:

- semantic Data Blocks;
- block metadata/source/channel/shape;
- custom reordering;
- element-major/channel-major ordering;
- concatenate vector;
- stack rows;
- stack columns;
- predicted composed output shape.

This keeps local feature construction inside Sampling LAB while leaving future cross-service/global normalization/PCA/model-input work to a possible Representation LAB.

## Spectral / Statistics

### Artifact lifecycle fix

Selecting or adding a spectral node no longer fetches an artifact. Selection only updates editor state. Artifact retrieval occurs after execution or explicit `Inspect`, preventing `Artifact not available: <node>.spectrum` errors caused by eager inspection.

### Graph-first inspectors

Numerical operators are represented by their meaningful data first:

- Histogram -> histogram graph;
- Basic Statistics -> feature/statistic display + source distribution graph + formulas;
- Radial/Angular frequency vectors -> frequency/angle graphs;
- FeatureMatrix -> heatmap;
- Spectrum2D -> Fourier magnitude map + frequency diagnostics.

The source image is context, not a fake substitute for the artifact.

### FFT reconstruction

For a global FFT, a frequency coefficient does not belong to one local image region; it represents a sinusoidal component spanning the image. v0.4 therefore visualizes frequency contribution correctly by masking selected frequencies and running inverse FFT.

Supported interactive reconstruction concepts:

- radial band;
- angular sector;
- conjugate single-frequency pair.

This answers: **what visual structure does this frequency/band contribute?**

### Local FFT Band Energy

Global FFT answers primarily **WHAT frequencies exist**. To begin answering **WHERE they occur**, v0.4 adds Local FFT Band Energy Map:

```text
image -> spatial grid -> FFT per patch -> selected radial-band energy -> FeatureMatrix heatmap
```

This is the extensible path toward future STFT, Gabor and wavelet analysis for Global Vision / Auto ROI / texture inspection.

## Compatibility

- Existing v0.2/v0.3 Sampling Geometry backend types/operators remain available for deployed legacy snapshots.
- New Sampling editor remains Spatial + Spectral only.
- Contour Extractor remains its own LAB and service type.
- Lab Service Remove/Delete behavior from v0.3 is preserved.

## Important source files

### Contour frontend

- `src/Pages/ContourExtractorLabPage.tsx`
- `src/Pages/ContourExtractorGuideModal.tsx`
- `src/Pages/ContourStageLibrary.tsx`
- `src/Pages/ContourStageGuideModal.tsx`
- `src/Pages/ContourFourierInspector.tsx`
- `src/api/contourExtractorApi.ts`

### Contour backend

- `app/services/vision_labs/contour_extractor/runtime.py`
- `app/services/vision_labs/contour_extractor/store.py`
- `app/services/vision_labs/contour_extractor/stage_registry.py`
- `app/services/vision_labs/contour_extractor/fourier.py`
- `app/api/v1/endpoints/contour_extractor_api.py`

### Sampling frontend

- `src/Pages/SamplingGeometryLabPage.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingUnitLibrary.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingUnitsPanel.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingCanvas.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingParameterHelpModal.tsx`
- `src/components/VisionLabs/SamplingGeometry/DataLayoutComposer.tsx`
- `src/components/VisionLabs/SamplingGeometry/SamplingWorkbench.tsx`
- `src/components/VisionLabs/SamplingGeometry/ArtifactInspectorModal.tsx`

### Sampling backend

- `app/services/vision_labs/sampling_geometry/operators/spatial.py`
- `app/services/vision_labs/sampling_geometry/operators/spectral.py`
- `app/api/v1/endpoints/sampling_geometry_api.py`

## Next likely expansion points

1. Master contour library and multiple-reference shape matching.
2. Topology/graph contour stages.
3. Local curvature / multiscale descriptors.
4. STFT/Gabor/Wavelet spatial-frequency operators.
5. Richer Data Layout composition and reusable named feature schemas.
6. Cross-service representation/model-input composition when Sampling-local composition is no longer sufficient.
