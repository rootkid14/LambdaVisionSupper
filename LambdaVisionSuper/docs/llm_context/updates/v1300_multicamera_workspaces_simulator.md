# Computer Vision v0.13 — Multi-Camera / Multi-Workspace / Simulator

## Architectural boundary

- **Camera is a declared resource**, not an inspection pipeline. Camera drivers expose typed actions/properties and named image/stream slots.
- **Workspace is an inspection context**. Every workspace owns its Master Sample, ROI definitions and Working Filter/Logic configuration, and binds its input to an image slot such as `camera.front.Current_image`.
- **Automation IDE is the glue/control plane**. Program automation can orchestrate any camera, workspace or IOT object. `system.run_inspection()` means the active workspace; `workspace.<alias>.run_inspection()` is explicit.
- **Program result and workspace result are different concepts**. Workspace runs produce `workspace.<alias>.result`; multi-workspace product judgment should be composed by Automation and committed to `system.result`.

## New resource declarations

### Camera Declaration Engine

Supported first-version drivers:

- `basler`: IP/serial, capture, engineering stream polling, writable `exposure_us`.
- `http`: host/port/capture path plus user-declared custom HTTP APIs.
- `simulated`: image upload/replay through the same frame-slot contract.

Each camera declares an `image_slot` (default `Current_image`) and `stream_slot` (default `Streaming_frame`). The runtime stores volatile frames outside `program.json`.

### Workspaces

Program v5 persists `workspaces[]` with:

- `workspace_id`, `name`, `alias`, `enabled`
- `input_binding`
- workspace-owned `master`
- workspace-owned `working`

Legacy top-level `master/working/camera/io` fields remain for old program compatibility.

## Endpoint Registry additions

Examples:

```text
camera.front.capture()
camera.front.Current_image
camera.front.Streaming_frame
camera.front.exposure_us
workspace.front.activate()
workspace.front.run_inspection()
workspace.front.result
workspace.front.vision.roi.upper_bearing.logic.contour.outputs...
```

Typed endpoint metadata now also carries `allowed_values`, `unit` and `object_type` so IntelliSense can recommend `ON/OFF` versus `OK/NG/NONE` rather than requiring users to guess.

## Online / Offline

Top-level Online starts the Automation scheduler for all enabled Loop services and represents the production-armed program state. The IDE-local scheduler controls remain for individual debugging.

## Developer Simulator

The first simulator is intentionally small:

- Modbus declaration driver `simulated` stores point values in memory while preserving the exact `device.<alias>.<point>` API.
- Camera declaration driver `simulated` accepts uploaded frames into the same image/stream slots as real cameras.

Automation scripts therefore do not need to change when a declaration is switched from simulated to real hardware.

## Streaming scope

v0.13 engineering streaming is **polling preview**, not a high-FPS push transport. This is deliberate so future Soft Trigger / stream-analysis architecture can be designed separately without coupling it to the inspection runtime.
