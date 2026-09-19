# Computer Vision v0.15.0 — Utilities / Data Gathering

## Purpose

Add the first **Utilities** tool to the Computer Vision application: a manual, controllable image-harvesting workspace for collecting full camera frames and ROI crops without running inspection or introducing Dataset/Training/AI infrastructure.

## Architectural boundary

Utilities is a **tooling plane** owned by the current Vision Workspace context, but it is not part of the production `Working` inspection pipeline.

```text
Vision Workspace
├─ Camera declarations / assigned camera
├─ Master Sample / ROIs
├─ Working                  # production inspection
└─ Utilities
   └─ Data Gathering        # image/ROI harvesting only
```

Utilities must not infer OK/NG semantics, model classes, training splits, augmentation, model registry, or deployment behavior. Users route each visual output to filesystem folders of their choice.

## v0.15.0 workflow

### Camera Collection

1. Use the camera assigned to the active Workspace.
2. Configure a base output folder and one destination for each output.
3. Outputs are:
   - full captured frame;
   - every Master ROI currently selected for extraction;
   - optional manual utility ROIs drawn in the Utilities viewport.
4. `Capture + Save` captures once and writes every enabled route from that same frozen frame.
5. Repeat capture without reconfiguring routes.

This supports operator flows such as configuring an `ALL_OK` directory layout, capturing tens of products, changing routes for an NG condition, then continuing collection.

### Offline Folder

1. Point Utilities at an existing server/local image folder.
2. Preview images by index.
3. Reuse Workspace Master ROIs and/or draw temporary utility ROIs on the preview.
4. Configure output routing once.
5. Run the whole folder through the same extraction engine.

This allows raw full-frame images collected at the factory to be taken elsewhere and converted into ROI samples later without requiring camera access.

## Extraction semantics

- v0.15.0 uses **fixed normalized rectangles** from the current Master ROI definitions plus optional manual utility ROIs.
- Full-frame and ROI outputs from one source image share the same source stem/token so they can be correlated by filename.
- Relative destination paths resolve under the configured base folder; absolute destination folders are also allowed.
- Existing files are never overwritten. A numeric suffix is added on collision.
- Image writing is filesystem-only and does not mutate Vision Program inspection state.
- Camera capture reuses the Workspace-owned camera declaration and writes the frame into that Workspace's latest-frame context for preview.
- Offline folder enumeration is non-recursive in v0.15.0.

Locator-aware extraction can be added later, but must reuse the existing Workspace locator contract rather than creating a second ROI-location algorithm inside Utilities.

## Backend files

- `app/services/vision_app/models.py`
  - Adds non-persistent Utilities request contracts: `UtilityGatherRoi`, `UtilityGatherRoute`, `UtilityGatherPlan`, `UtilityBatchRequest`.
- `app/services/vision_app/utilities_runtime.py`
  - New filesystem-oriented extraction engine.
  - Folder discovery/preview.
  - Normalized ROI cropping.
  - Collision-safe JPEG/PNG writes.
  - Full-folder batch extraction.
- `app/api/v1/endpoints/vision_app_api.py`
  - Adds Workspace-scoped Utilities routes for folder info/preview, camera capture+save, and offline batch extraction.
- `tests/vision_app/test_vision_app_v1500.py`
  - Regression coverage for full-frame + ROI extraction and offline batch reuse of one extraction plan.

## Frontend files

- `src/components/ComputerVision/UtilitiesWorkspace.tsx`
  - New Utilities/Data Gathering UI.
  - Camera Collection and Offline Folder modes.
  - Base-folder + per-output routing.
  - Master ROI reuse and temporary manual ROI drawing.
- `src/api/visionAppApi.ts`
  - Utilities contracts and API helpers.
- `src/Pages/ComputerVisionPage.tsx`
  - Adds the Utilities top-level module for the active Workspace.
  - Version footer becomes v0.15.0.

## API routes

```text
GET  /programs/<id>/workspaces/<workspace>/utilities/gather/folder-info
GET  /programs/<id>/workspaces/<workspace>/utilities/gather/folder-preview
POST /programs/<id>/workspaces/<workspace>/utilities/gather/capture
POST /programs/<id>/workspaces/<workspace>/utilities/gather/batch
```

## Invariants

1. Utilities never falls back to another Workspace's camera or ROI state.
2. Camera acquisition uses the camera assigned to the route Workspace.
3. Utilities does not execute Working Filter/Logic/Decision in v0.15.0.
4. Utilities does not create AI/Dataset/Training abstractions.
5. Master ROI definitions remain owned by Master; temporary utility ROIs are session-local frontend state.
6. Offline and camera modes share the same extraction/routing contract.
7. No output file is overwritten by a gathering operation.

## Recommended minimal context for future Utilities work

- `FE:src/Pages/ComputerVisionPage.tsx`
- `FE:src/components/ComputerVision/UtilitiesWorkspace.tsx`
- `FE:src/components/ComputerVision/VisionViewport.tsx`
- `FE:src/api/visionAppApi.ts`
- `BE:app/services/vision_app/models.py`
- `BE:app/services/vision_app/utilities_runtime.py`
- `BE:app/services/vision_app/camera_resource_runtime.py`
- `BE:app/services/vision_app/workspace_runtime.py`
- `BE:app/api/v1/endpoints/vision_app_api.py`
- `BE:tests/vision_app/test_vision_app_v1500.py`
