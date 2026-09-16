# Lambda Vision — LLM Context Index

> Start here when opening a new LLM conversation about this codebase.

- Generator: `v2.1`
- Generated: `2026-09-15T23:32:30+07:00`
- Source files indexed: **265** (FE 136 / BE 129)
- Frontend git: `main` @ `2fb5282` · **DIRTY**
- Backend git: `main` @ `2fb5282` · **DIRTY**

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
| Backend Tests | 6 |
| Backend Tools / Updaters | 1 |
| Backend — Unclassified App Source | 2 |
| Backend — Unclassified Project Source | 2 |
| Database Backend | 2 |
| Database UI | 6 |
| Desktop / Tauri Host | 6 |
| Desktop / Tauri — Unclassified | 1 |
| Fleet / Device / Infrastructure Backend | 12 |
| Fleet / Resource UI | 7 |
| Frontend Application Shell & Routing | 4 |
| Frontend Tools & LLM Context Docs | 24 |
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
| Sampling / Geometry LAB Backend | 17 |
| Sampling / Geometry LAB UI | 9 |
| Shared Backend Utilities | 3 |
| Shared Frontend UI & Utilities | 6 |
| Vision LAB Core Contracts | 3 |

## Current working-tree changes

### FE dirty files

- ` D dist/assets/index-DJtsUeVF.js`
- ` D dist/assets/index-_lqLas_X.css`
- ` M dist/index.html`
- ` M src/App.tsx`
- ` M src/Pages/ImageProcessingLabPage.tsx`
- ` M src/Pages/LabView.tsx`
- ` M src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx`
- ` M src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx`
- ` M src/components/VisionLabs/ImageProcessing/types.ts`
- ` M src/components/VisionLabs/ImageProcessing/useImageLabController.ts`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/api.py`
- `?? .lambda_updater_backups/filter_guide_system_map_v0050_20260915_220956/`
- `?? .lambda_updater_backups/lab_service_foundation_v0040_20260915_211749/`
- `?? .lambda_updater_backups/lab_service_multi_edit_v0041_20260915_214518/`
- `?? .lambda_updater_backups/llm_context_generator_v0060_20260915_222730/`
- `?? .lambda_updater_backups/sampling_geometry_lab_v0100_20260915_233229/`
- `?? dist/assets/index-Cd__1al-.css`
- `?? dist/assets/index-DKYFaJAT.js`
- `?? docs/`
- `?? src/Pages/SamplingGeometryLabPage.tsx`
- `?? src/api/labServiceApi.ts`
- `?? src/api/samplingGeometryApi.ts`
- `?? src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx`
- `?? src/components/VisionLabs/ImageProcessing/operatorGuide.ts`
- `?? src/components/VisionLabs/SamplingGeometry/`
- `?? tools/`
- `?? update_image_lab_filter_guide_context_v0050.py`
- `?? update_lab_service_foundation_v0040.py`
- `?? update_lab_service_multi_edit_v0041.py`
- `?? update_llm_context_generator_v0060.py`
- `?? update_sampling_geometry_lab_v0100.py`
- `?? update_sampling_geometry_lab_v0101_mergefix.py`
- `?? ../LambdaVisionSuperBackEnd/_entropy1_train_ca/`
- `?? ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/lab_service_api.py`
- `?? ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/sampling_geometry_api.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_labs/service/`
- `?? ../LambdaVisionSuperBackEnd/e1108D_metrics_extractor.py`
- `?? ../LambdaVisionSuperBackEnd/e1108D_neural_network.py`
- `?? ../LambdaVisionSuperBackEnd/e1108D_run.py`
- `?? ../LambdaVisionSuperBackEnd/e1108D_train.py`
- `?? ../LambdaVisionSuperBackEnd/e5204_metrics_extractor.py`
- `?? ../LambdaVisionSuperBackEnd/e5204_neural_network.py`
- `?? ../LambdaVisionSuperBackEnd/e5204_run.py`
- `?? ../LambdaVisionSuperBackEnd/e5204_train.py`
- `?? ../LambdaVisionSuperBackEnd/engineer_cnn_u3.py`
- `?? ../LambdaVisionSuperBackEnd/engineer_cnn_u3_run.py`
- `?? ../LambdaVisionSuperBackEnd/engineer_cnn_u3_train.py`
- `?? ../LambdaVisionSuperBackEnd/engineer_master_v1.py`
- `?? ../LambdaVisionSuperBackEnd/engineer_master_v1_train.py`
- `?? ../LambdaVisionSuperBackEnd/entropy_1_gt_labeller.py`
- `?? ../LambdaVisionSuperBackEnd/entropy_1_station_builder.py`
- `?? ../LambdaVisionSuperBackEnd/get_26D_vectors.py`
- `?? ../LambdaVisionSuperBackEnd/run_compare_mlp_cnn.py`
- `?? ../LambdaVisionSuperBackEnd/storage/vision_labs/`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/sampling_geometry/`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/test_lab_service_core.py`

### BE dirty files

- ` D ../LambdaVisionSuper/dist/assets/index-DJtsUeVF.js`
- ` D ../LambdaVisionSuper/dist/assets/index-_lqLas_X.css`
- ` M ../LambdaVisionSuper/dist/index.html`
- ` M ../LambdaVisionSuper/src/App.tsx`
- ` M ../LambdaVisionSuper/src/Pages/ImageProcessingLabPage.tsx`
- ` M ../LambdaVisionSuper/src/Pages/LabView.tsx`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/ImageProcessing/types.ts`
- ` M ../LambdaVisionSuper/src/components/VisionLabs/ImageProcessing/useImageLabController.ts`
- ` M app/api/v1/api.py`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/filter_guide_system_map_v0050_20260915_220956/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/lab_service_foundation_v0040_20260915_211749/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/lab_service_multi_edit_v0041_20260915_214518/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/llm_context_generator_v0060_20260915_222730/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/sampling_geometry_lab_v0100_20260915_233229/`
- `?? ../LambdaVisionSuper/dist/assets/index-Cd__1al-.css`
- `?? ../LambdaVisionSuper/dist/assets/index-DKYFaJAT.js`
- `?? ../LambdaVisionSuper/docs/`
- `?? ../LambdaVisionSuper/src/Pages/SamplingGeometryLabPage.tsx`
- `?? ../LambdaVisionSuper/src/api/labServiceApi.ts`
- `?? ../LambdaVisionSuper/src/api/samplingGeometryApi.ts`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/ImageProcessing/operatorGuide.ts`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingGeometry/`
- `?? ../LambdaVisionSuper/tools/`
- `?? ../LambdaVisionSuper/update_image_lab_filter_guide_context_v0050.py`
- `?? ../LambdaVisionSuper/update_lab_service_foundation_v0040.py`
- `?? ../LambdaVisionSuper/update_lab_service_multi_edit_v0041.py`
- `?? ../LambdaVisionSuper/update_llm_context_generator_v0060.py`
- `?? ../LambdaVisionSuper/update_sampling_geometry_lab_v0100.py`
- `?? ../LambdaVisionSuper/update_sampling_geometry_lab_v0101_mergefix.py`
- `?? _entropy1_train_ca/`
- `?? app/api/v1/endpoints/lab_service_api.py`
- `?? app/api/v1/endpoints/sampling_geometry_api.py`
- `?? app/services/vision_labs/sampling_geometry/`
- `?? app/services/vision_labs/service/`
- `?? e1108D_metrics_extractor.py`
- `?? e1108D_neural_network.py`
- `?? e1108D_run.py`
- `?? e1108D_train.py`
- `?? e5204_metrics_extractor.py`
- `?? e5204_neural_network.py`
- `?? e5204_run.py`
- `?? e5204_train.py`
- `?? engineer_cnn_u3.py`
- `?? engineer_cnn_u3_run.py`
- `?? engineer_cnn_u3_train.py`
- `?? engineer_master_v1.py`
- `?? engineer_master_v1_train.py`
- `?? entropy_1_gt_labeller.py`
- `?? entropy_1_station_builder.py`
- `?? get_26D_vectors.py`
- `?? run_compare_mlp_cnn.py`
- `?? storage/vision_labs/`
- `?? tests/vision_labs/sampling_geometry/`
- `?? tests/vision_labs/test_lab_service_core.py`

## Generated context documents

- `SYSTEM_ARCHITECTURE.md` — architectural modules, boundaries, routes and dependency edges.
- `SYSTEM_CONTEXT_BUNDLES.md` — minimal/deep file bundles for common tasks.
- `SYSTEM_FILE_MAP.md` — cleaned source/config inventory.
- `updates/*.md` — change-specific architectural notes.
