# Computer Vision v0.15.1 — Utilities Active / Burst / ROI Sampling

## Purpose

Extend the v0.15.0 Data Gathering utility from an operator-only tool into a Workspace-owned harvesting capability that can participate in production cycles without becoming part of Working inspection logic.

## Files touched / closely related

- `BE:app/services/vision_app/models.py` — persistent Workspace Utilities config, burst and ROI-sampling contracts.
- `BE:app/services/vision_app/utilities_runtime.py` — filesystem harvesting plus deterministic shift/scale ROI sampling augmentation.
- `BE:app/services/vision_app/automation_manager.py` — production Workspace cycle router and same-frame Working/Utilities fan-out.
- `BE:app/services/vision_app/endpoint_registry.py` — Utilities state plus cycle/working actions in Automation IDE.
- `BE:app/api/v1/endpoints/vision_app_api.py` — burst and explicit Workspace-cycle routes.
- `FE:src/api/visionAppApi.ts` — Utilities v0.15.1 contracts.
- `FE:src/components/ComputerVision/UtilitiesWorkspace.tsx` — routing brush, Active modes, burst and ROI sampling controls.
- `FE:src/Pages/ComputerVisionPage.tsx` — Workspace persistence wiring and v0.15.1 baseline.
- `BE:tests/vision_app/test_vision_app_v1510.py` — regression contracts.

## Architectural invariants

1. Utilities remains a tooling/data-harvesting plane. It does not own Dataset, Training, AI model or inspection-decision semantics.
2. Utilities configuration is Workspace-owned. No Workspace may inherit another Workspace's gather plan or destinations.
3. `Working` remains inspection-only. Engineering `test-run` and the existing `/workspaces/<alias>/run` route continue to call Working directly.
4. Production Automation actions (`system.run_inspection`, `workspace.<alias>.run_inspection`) and Soft Trigger dispatch use the production Workspace-cycle router. With Utilities Active OFF this is behavior-compatible with v0.15.0.
5. `UTILITIES_ONLY` gathers data and intentionally skips Working. It does not fabricate OK/NG or `logic_ready` results.
6. `BOTH` gathers the primary frame and then runs Working exactly once on that same primary frame. Extra burst frames are Utilities-only.
7. Burst gathering finishes before Working emits `run_finish`; this prevents a downstream automation step from removing the product before all requested temporal samples are collected.
8. Basler burst capture reuses `CameraResourceController.capture()`. If native streaming owns the device, capture snapshots the latest `Streaming_frame` rather than opening a second camera handle.
9. ROI sampling augmentation changes crop geometry only. It does not mutate image pixels. Variants are deterministic, clamped to image bounds, and rejected below the configured minimum IoU with the original ROI.
10. The legacy `VisionTriggerRunnerManager` remains a compatibility runtime and is not migrated into the Workspace Utilities cycle in this version.

## Utilities Active modes

- `off` — production cycle runs Working only.
- `utilities_only` — production cycle gathers configured samples and skips Working.
- `both` — production cycle gathers first, then Working inspects the exact primary gathered frame once.

## New Automation actions / state

- `system.run_inspection()` — production cycle honoring Utilities Active.
- `system.run_working()` — explicit Working-only bypass.
- `workspace.<alias>.run_inspection()` — production cycle honoring Utilities Active.
- `workspace.<alias>.run_cycle()` — explicit cycle alias.
- `workspace.<alias>.run_working()` — explicit Working-only bypass.
- `workspace.<alias>.utilities.active_mode`
- `workspace.<alias>.utilities.samples_per_cycle`

Events added:

- `workspace.<alias>.utilities_gathered`
- `workspace.<alias>.cycle_finish`
- `workspace.<alias>.cycle_error`

## UI behavior

- Route brush/pipette: choose one destination from any output row, then click other output rows or ROI boxes to apply that destination quickly. Escape or Stop Brush exits paint mode.
- Manual burst: configure temporal sample count and interval; each frame is gathered independently.
- Utilities Active config persists with the Workspace and can run while the Utilities UI is not open.
- ROI Sampling Augmentation supports original inclusion, deterministic extra variants, X/Y shift bounds, context scale range and minimum IoU.

## Recommended context for future changes

Minimal:

- `FE:src/Pages/ComputerVisionPage.tsx`
- `FE:src/components/ComputerVision/UtilitiesWorkspace.tsx`
- `FE:src/api/visionAppApi.ts`
- `BE:app/services/vision_app/models.py`
- `BE:app/services/vision_app/utilities_runtime.py`
- `BE:app/services/vision_app/automation_manager.py`
- `BE:app/services/vision_app/endpoint_registry.py`
- `BE:app/api/v1/endpoints/vision_app_api.py`
- `BE:tests/vision_app/test_vision_app_v1510.py`

Add `camera_resource_runtime.py` and `streaming_runtime.py` when changing burst acquisition or Soft Trigger/stream ownership.
