# Computer Vision v0.9.0 — Control Mapping + Workspace Cleanup

## Frozen LAB boundary
Image Processing, Contour Extractor and Sampling LAB remain service producers. Computer Vision is the production orchestration layer.

## Module-specific center workspaces
- Camera: camera-only capture/live-preview viewport. Captured frames may also become the Working test image, but Camera does not automatically navigate to Working.
- Master Sample: Master/Blur tabs with explicit Original Master restore.
- Working: inspection viewport and OK/NG overlay. Result overlay exists only here.
- IOT: center viewport is reserved for the future Control IDE / sandbox instead of showing an image.

## Control Mapper
Program v3 owns a ControlMapperConfig. Primitive actions are `trigger_camera`, `run_inspection`, `out_ok`, `out_ng`, and `clear_working_screen`. Current sources are keyboard and the Modbus trigger. The future IDE/sandbox should emit the same primitives rather than directly coupling to camera or Modbus implementations.

## Working UI
Operation panel selects one scope from a combobox: Global or one ROI station. The selected scope receives a larger explanatory editor for Filter & Processing and Logic Services. Decision Edit is removed. New v3 programs treat final decision/glue as future IDE ownership; legacy v2 programs keep their saved Decision DSL compatibility.

## Debug
Debug images are no longer rendered as a tab strip over the main viewport. Debug Workspace is a separate full-screen environment and image bytes are fetched lazily only when a debug artifact is selected.

## Pipeline
Global Filter -> Global Logic -> ROI locator -> station Filter/Logic. Station scopes can execute sequentially or in parallel. Until IDE decision exists, v3 temporary scope OK means enabled Filter and Logic stages completed successfully.
