# v0.8.0 — Computer Vision Camera + Production Working Pipeline

## Purpose

Extend the v0.7 Computer Vision bootstrap into a production-oriented orchestration frame while keeping the Image Processing, Contour Extractor and Sampling LABs frozen. Computer Vision remains an application/orchestration layer that consumes deployed Lab Services.

## Program lifecycle

- Vision Programs can be created, saved and permanently removed from the Computer Vision page.
- Persisted programs are migrated from the v0.7 contract when loaded.
- `VisionProgramDefinition.version = 2` adds Camera, a program-wide ROI locator and structured Working scopes.

## Camera module

`CameraConfig.driver` supports:

1. `manual` — engineering upload remains available.
2. `basler` — lazy pypylon driver. Device may be selected by GigE IP or serial. Capture follows `InstantCamera -> BGR8 converter -> ExposureTime -> StartGrabbing -> RetrieveResult -> StopGrabbing`.
3. `url` — arbitrary HTTP GET capture URL. Returned bytes are decoded as an image. An independent focus URL template supports `{x}`, `{y}`, `{w}`, `{h}`, `{focal_length}` placeholders, which covers the Raspberry Pi camera API without hard-coding that device.

The automatic trigger runner owns the production chain:

```text
Modbus rising edge
  -> CameraController.capture
  -> VisionProgramRuntime.run_test
  -> overall OK / NG
  -> Modbus OK / NG pulse
```

Runner state is start/stop/status controlled through the Computer Vision API.

## Master Sample / Auto ROI

ROI/stations no longer choose locator algorithms independently. `MasterSampleConfig.locator` applies one family to the complete Master Sample:

- Manual coordinates
- Blur + Template Matching
- Fourier Phase Search (translation-only v1)

Geometry constraints remain additive. Blur Template has an actual Master blur preview endpoint/UI so an engineer can see the entropy/noise reduction caused by the chosen kernel.

## Working execution contract

Each Global or station scope is a `ScopePipelineConfig`:

```text
Filter & Processing
  -> sequential Image Processing Lab Services
Logic Services
  -> independent information-extraction Lab Services
Decision
  -> restricted if/else + mathematical DSL
  -> OK or NG
```

Global Scope always executes first. Its filtered image becomes the test image used for ROI location and local station crops. The same Global filter stack is applied to the Master image before automatic ROI search so locator inputs remain semantically aligned.

ROI stations can execute sequentially or in parallel after Global processing/location.

## Decision DSL

The Decision IDE exposes a `logic` dictionary keyed by each logic binding alias plus `logic_ok` and `filter_ok`.

Numeric/artifact outputs are converted to decision-friendly summaries such as:

- `shape`
- `size`
- `mean`
- `std`
- `min`
- `max`
- small `values` arrays
- contour `count`

Supported syntax intentionally excludes arbitrary Python execution. It supports `if/else`, one assignment target named `result`, boolean operators, arithmetic, comparisons, subscripting, and `abs/min/max/len/round`.

## Debug and benchmark

`VisionDebugStore` keeps bounded in-memory JPEG previews for recent runs. Run results expose named debug images for:

- test input
- Global filter stages/final image
- each station input
- station filter stages

The Working viewport can switch among these artifacts.

`BenchmarkStep` captures timing for filter services, ROI location, logic services, decision scripts and total inspection time. The Working right panel has `Operation` and `Benchmark` tabs.

## UI

- Left and right control panels can collapse so Testing can devote most of the screen to the image viewport.
- `VisionViewport` supports wheel zoom, drag pan and fit/reset.
- Working has a large on-screen OK/NG result box.
- Filter Edit opens a stack editor restricted to Image Processing services and can run a real filter preview against the current test image.
- Logic Edit selects extraction services and gives each binding a stable alias.
- Decision Edit opens an IDE-style script editor with the exposed Logic output contract alongside it.

## Camera source reference

The implementation follows the user-provided Basler pattern (GigE IP/serial discovery, `InstantCamera`, BGR conversion, exposure, latest-image grab) and the existing HTTP-camera pattern (GET image bytes -> OpenCV decode), but moves both behind `CameraController` instead of keeping device-specific code inside orchestration runtime/UI.

## Important boundaries

- Computer Vision does not implement Image Processing/Contour/Sampling algorithms itself.
- Filter phase consumes Image Processing Lab Services.
- Logic phase consumes data-extraction/AI services.
- Decision is currently a small safe built-in DSL. A future Rule/Comparison Service can replace or complement it without changing Global/Station scope structure.
- Camera acquisition and IOT are infrastructure around the inspection runtime, not Lab operators.
