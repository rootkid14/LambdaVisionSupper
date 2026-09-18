# v0.7.0 — Computer Vision Program Frame

## Purpose

Freeze the current Image Processing, Contour Extractor and Sampling LABs and introduce the first orchestration-level **Computer Vision** application surface. Computer Vision consumes deployed Lab Services; it does not duplicate their internal algorithms.

## Navigation

- Main Screen gets a new **Computer Vision** action.
- Frontend route: `/computer-vision`.
- Backend route: `/api/v1/computer-vision`.

## Program model

A `VisionProgramDefinition` owns three modules:

1. **IOT** — Modbus TCP trigger/result contract.
2. **Master Sample** — one stored master image, many ROI/stations, and ROI search method/configuration.
3. **Working** — Global whole-image service bindings and Local per-station service bindings with simple decision rules.

Programs persist under `storage/vision_apps/programs/<program_id>/` with `program.json` and `master.png`.

## IOT v1

`ModbusIOController` uses the same pymodbus semantics as the existing device prototype: connect to host/port, read one coil/discrete input as trigger, write an OK or NG coil, wait the configured pulse duration, then clear it. The v1 UI supports one-shot trigger reads and OK/NG output tests. A future production runner may own persistent polling/connection lifecycle without changing the program contract.

## Master Sample / stations

ROIs use normalized coordinates. Every ROI is also a station. Search methods in v1:

- `manual`: identical normalized coordinates on the test image.
- `blur_template`: blur master/test and run locally constrained template matching.
- `fourier`: translation-only phase correlation inside geometry-constrained context windows.

Geometry constraints (`search_margin_px`, `max_shift_px`) reduce search entropy and leave room for future multi-ROI relation graphs, scale/rotation search and stronger master-based localization.

## Working module

- **Global** bindings receive the whole test image.
- **Local** bindings receive the located/cropped ROI image for that station.
- Bindings call `LabServiceRuntime` directly through `LabServiceRepository`; they never call localhost REST internally.
- v1 station decisions support service-success and simple scalar threshold comparisons. This is intentionally a frame until Comparison / Rule LAB and AI contracts mature.

## Frame test flow

```text
Modbus trigger (future persistent runner)
          ↓
      test image
          ↓
Master ROI locator
          ↓
┌──────────────────┬───────────────────────────────┐
│ Global Working   │ Local Working                │
│ full image       │ ROI = station               │
│ Lab Services     │ per-station Lab Services    │
└──────────────────┴───────────────────────────────┘
          ↓
     OK / NG result
          ↓
Modbus OK or NG coil pulse
```

## New source bundle

Frontend:
- `src/Pages/ComputerVisionPage.tsx`
- `src/components/ComputerVision/`
- `src/api/visionAppApi.ts`

Backend:
- `app/services/vision_app/`
- `app/api/v1/endpoints/vision_app_api.py`
- `tests/vision_app/test_vision_app_frame_v0100.py`
