# Lambda Vision — LLM Context Index

> Start here when opening a new LLM conversation about this codebase.

- Generator: `v2.1`
- Generated: `2026-09-16T23:50:37+07:00`
- Source files indexed: **298** (FE 155 / BE 143)
- Frontend git: `main` @ `fb7c839` · **DIRTY**
- Backend git: `main` @ `fb7c839` · **DIRTY**

## Recommended handoff order

For a **new chat**, normally provide:

1. `SYSTEM_CONTEXT_INDEX.md` — this compact index.
2. `SYSTEM_ARCHITECTURE.md` — system boundaries and execution flows.
3. The latest relevant `updates/*.md` note.
4. Only then load the exact source bundle from `SYSTEM_CONTEXT_BUNDLES.md`.
5. Use `SYSTEM_FILE_MAP.md` when the task needs broader source navigation.

Do **not** start by dumping the whole codebase into context.

## Critical architecture boundary

- **Legacy App Builder / Sequencer**: `BaseNode` / `NODE_REGISTRY` → `LogicObject` → `LogicPoolManager`.
- **Vision LAB**: specialized LAB contracts; Image Processing uses `ImageOperator` / operator registry → `ImagePipelineRuntime` / `ImageLabSession`.
- **Lab Service**: versioned callable wrapper around LAB execution; intended future integration boundary for Dataset, Sampling/Geometry, Sequencer and Agentic callers.
- Do not merge the Legacy `BaseNode` hierarchy into the Image LAB operator hierarchy unless an explicit adapter is designed.

## Detected modules

| Module | Files |
| --- | ---: |
| App Builder / Sequencer UI | 30 |
| Backend Application Shell & API Router | 5 |
| Backend Tests | 11 |
| Backend Tools / Updaters | 1 |
| Backend — Unclassified App Source | 2 |
| Backend — Unclassified Project Source | 2 |
| Contour Extractor LAB Backend | 8 |
| Contour Extractor LAB UI | 6 |
| Database Backend | 2 |
| Database UI | 6 |
| Desktop / Tauri Host | 6 |
| Desktop / Tauri — Unclassified | 1 |
| Fleet / Device / Infrastructure Backend | 12 |
| Fleet / Resource UI | 7 |
| Frontend Application Shell & Routing | 4 |
| Frontend Tools & LLM Context Docs | 30 |
| Frontend — Project / Config | 9 |
| Frontend — Unclassified Source | 4 |
| Image Processing LAB Backend | 13 |
| Image Processing LAB UI | 11 |
| Inspection UI Engine | 16 |
| Lab Service Backend | 5 |
| Lab Service Hub UI | 2 |
| Legacy App Builder / Sequencer Runtime | 34 |
| Project Compiler | 1 |
| Research / Experiments / Training | 24 |
| Sampling LAB Backend | 18 |
| Sampling LAB UI | 16 |
| Shared Backend Utilities | 3 |
| Shared Frontend UI & Utilities | 6 |
| Vision LAB Core Contracts | 3 |

## Current working-tree changes

### FE dirty files

- ` D dist/assets/index-BdiD-2Zy.js`
- ` D dist/assets/index-DczY4aoc.css`
- ` M dist/index.html`
- ` M docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M src/App.tsx`
- ` M src/Pages/LabView.tsx`
- ` M src/Pages/SamplingGeometryLabPage.tsx`
- ` M src/api/labServiceApi.ts`
- ` M src/api/samplingGeometryApi.ts`
- ` M src/components/VisionLabs/SamplingGeometry/SamplingOperatorLibrary.tsx`
- ` M src/components/VisionLabs/SamplingGeometry/SamplingStack.tsx`
- ` M src/components/VisionLabs/SamplingGeometry/SamplingVisuals.tsx`
- ` M src/components/VisionLabs/SamplingGeometry/SamplingWorkbench.tsx`
- ` M src/components/VisionLabs/SamplingGeometry/types.ts`
- ` M src/components/VisionLabs/SamplingGeometry/useSamplingGeometryController.ts`
- ` M tools/generate_llm_context_map.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/api.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/lab_service_api.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/sampling_geometry_api.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/operator.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/operators/common.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/operators/geometry.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/operators/spatial.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/operators/spectral.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/pipeline.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/preview.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/registry.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/runtime.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/serialization.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/session.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/types.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/service/repository.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/service/runtime.py`
- ` D ../LambdaVisionSuperBackEnd/storage/vision_labs/services/image-processing-service/active.json`
- ` D ../LambdaVisionSuperBackEnd/storage/vision_labs/services/image-processing-service/v0001.json`
- ` D ../LambdaVisionSuperBackEnd/storage/vision_labs/services/image-processing-service/v0002.json`
- `?? .lambda_updater_backups/contour_sampling_v0300_20260916_230514/`
- `?? .lambda_updater_backups/contour_sampling_v0400_20260916_235025/`
- `?? .lambda_updater_backups/sampling_geometry_v0200_20260916_180720/`
- `?? dist/assets/index-B4vbtfiU.js`
- `?? dist/assets/index-CjfZrce7.css`
- `?? docs/llm_context/updates/v0200_sampling_geometry_source_board_inspector.md`
- `?? docs/llm_context/updates/v0300_contour_sampling_split.md`
- `?? docs/llm_context/updates/v0400_contour_sampling_workbench.md`
- `?? src/Pages/ContourExtractorGuideModal.tsx`
- `?? src/Pages/ContourExtractorLabPage.tsx`
- `?? src/Pages/ContourFourierInspector.tsx`
- `?? src/Pages/ContourStageGuideModal.tsx`
- `?? src/Pages/ContourStageLibrary.tsx`
- `?? src/api/contourExtractorApi.ts`
- `?? src/components/VisionLabs/SamplingGeometry/ArtifactInspectorModal.tsx`
- `?? src/components/VisionLabs/SamplingGeometry/DataLayoutComposer.tsx`
- `?? src/components/VisionLabs/SamplingGeometry/SamplingCanvas.tsx`
- `?? src/components/VisionLabs/SamplingGeometry/SamplingParameterHelpModal.tsx`
- `?? src/components/VisionLabs/SamplingGeometry/SamplingUnitLibrary.tsx`
- `?? src/components/VisionLabs/SamplingGeometry/SamplingUnitsPanel.tsx`
- `?? src/components/VisionLabs/SamplingGeometry/SourceBoard.tsx`
- `?? update_contour_sampling_labs_v0300.py`
- `?? update_contour_sampling_labs_v0400.py`
- `?? update_sampling_geometry_lab_v0200.py`
- `?? ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/contour_extractor_api.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_labs/contour_extractor/`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/source_board.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/contour_extractor/`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/sampling_geometry/test_sampling_geometry_lab_v0200.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/sampling_geometry/test_sampling_lab_v0300.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/sampling_geometry/test_sampling_lab_v0400.py`

### BE dirty files

- ` D ../LambdaVisionSuper/dist/assets/index-BdiD-2Zy.js`
- ` D ../LambdaVisionSuper/dist/assets/index-DczY4aoc.css`
- ` M ../LambdaVisionSuper/dist/index.html`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M ../LambdaVisionSuper/src/App.tsx`
- ` M ../LambdaVisionSuper/src/Pages/LabView.tsx`
- ` M ../LambdaVisionSuper/src/Pages/SamplingGeometryLabPage.tsx`
- ` M ../LambdaVisionSuper/src/api/labServiceApi.ts`
- ` M ../LambdaVisionSuper/src/api/samplingGeometryApi.ts`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingOperatorLibrary.tsx`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingStack.tsx`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingVisuals.tsx`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingWorkbench.tsx`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/types.ts`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/useSamplingGeometryController.ts`
- ` M ../LambdaVisionSuper/tools/generate_llm_context_map.py`
- ` M app/api/v1/api.py`
- ` M app/api/v1/endpoints/lab_service_api.py`
- ` M app/api/v1/endpoints/sampling_geometry_api.py`
- ` M app/services/vision_labs/sampling_geometry/operator.py`
- ` M app/services/vision_labs/sampling_geometry/operators/common.py`
- ` M app/services/vision_labs/sampling_geometry/operators/geometry.py`
- ` M app/services/vision_labs/sampling_geometry/operators/spatial.py`
- ` M app/services/vision_labs/sampling_geometry/operators/spectral.py`
- ` M app/services/vision_labs/sampling_geometry/pipeline.py`
- ` M app/services/vision_labs/sampling_geometry/preview.py`
- ` M app/services/vision_labs/sampling_geometry/registry.py`
- ` M app/services/vision_labs/sampling_geometry/runtime.py`
- ` M app/services/vision_labs/sampling_geometry/serialization.py`
- ` M app/services/vision_labs/sampling_geometry/session.py`
- ` M app/services/vision_labs/sampling_geometry/types.py`
- ` M app/services/vision_labs/service/repository.py`
- ` M app/services/vision_labs/service/runtime.py`
- ` D storage/vision_labs/services/image-processing-service/active.json`
- ` D storage/vision_labs/services/image-processing-service/v0001.json`
- ` D storage/vision_labs/services/image-processing-service/v0002.json`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/contour_sampling_v0300_20260916_230514/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/contour_sampling_v0400_20260916_235025/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/sampling_geometry_v0200_20260916_180720/`
- `?? ../LambdaVisionSuper/dist/assets/index-B4vbtfiU.js`
- `?? ../LambdaVisionSuper/dist/assets/index-CjfZrce7.css`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0200_sampling_geometry_source_board_inspector.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0300_contour_sampling_split.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0400_contour_sampling_workbench.md`
- `?? ../LambdaVisionSuper/src/Pages/ContourExtractorGuideModal.tsx`
- `?? ../LambdaVisionSuper/src/Pages/ContourExtractorLabPage.tsx`
- `?? ../LambdaVisionSuper/src/Pages/ContourFourierInspector.tsx`
- `?? ../LambdaVisionSuper/src/Pages/ContourStageGuideModal.tsx`
- `?? ../LambdaVisionSuper/src/Pages/ContourStageLibrary.tsx`
- `?? ../LambdaVisionSuper/src/api/contourExtractorApi.ts`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/ArtifactInspectorModal.tsx`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/DataLayoutComposer.tsx`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingCanvas.tsx`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingParameterHelpModal.tsx`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingUnitLibrary.tsx`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SamplingUnitsPanel.tsx`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/SourceBoard.tsx`
- `?? ../LambdaVisionSuper/update_contour_sampling_labs_v0300.py`
- `?? ../LambdaVisionSuper/update_contour_sampling_labs_v0400.py`
- `?? ../LambdaVisionSuper/update_sampling_geometry_lab_v0200.py`
- `?? app/api/v1/endpoints/contour_extractor_api.py`
- `?? app/services/vision_labs/contour_extractor/`
- `?? app/services/vision_labs/sampling_geometry/source_board.py`
- `?? tests/vision_labs/contour_extractor/`
- `?? tests/vision_labs/sampling_geometry/test_sampling_geometry_lab_v0200.py`
- `?? tests/vision_labs/sampling_geometry/test_sampling_lab_v0300.py`
- `?? tests/vision_labs/sampling_geometry/test_sampling_lab_v0400.py`

## Generated context documents

- `SYSTEM_ARCHITECTURE.md` — architectural modules, boundaries, routes and dependency edges.
- `SYSTEM_CONTEXT_BUNDLES.md` — minimal/deep file bundles for common tasks.
- `SYSTEM_FILE_MAP.md` — cleaned source/config inventory.
- `updates/*.md` — change-specific architectural notes.
