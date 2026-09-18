# Lambda Vision — LLM Context Index

> Start here when opening a new LLM conversation about this codebase.

- Generator: `v2.1`
- Generated: `2026-09-18T16:25:13+07:00`
- Source files indexed: **355** (FE 190 / BE 165)
- Frontend git: `main` @ `fa07cac` · **DIRTY**
- Backend git: `main` @ `fa07cac` · **DIRTY**

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
| Backend Tests | 13 |
| Backend Tools / Updaters | 1 |
| Backend — Unclassified App Source | 2 |
| Backend — Unclassified Project Source | 2 |
| Computer Vision Program Backend / Control Mapper / Camera / Working Pipeline | 18 |
| Computer Vision Program UI | 11 |
| Contour Extractor LAB Backend | 8 |
| Contour Extractor LAB UI | 6 |
| Database Backend | 2 |
| Database UI | 6 |
| Desktop / Tauri Host | 6 |
| Desktop / Tauri — Unclassified | 1 |
| Fleet / Device / Infrastructure Backend | 12 |
| Fleet / Resource UI | 7 |
| Frontend Application Shell & Routing | 4 |
| Frontend Tools & LLM Context Docs | 46 |
| Frontend — Project / Config | 9 |
| Frontend — Unclassified Source | 12 |
| Image Processing LAB Backend | 13 |
| Image Processing LAB UI | 11 |
| Inspection UI Engine | 16 |
| Lab Service Backend | 5 |
| Lab Service Hub UI | 2 |
| Legacy App Builder / Sequencer Runtime | 34 |
| Project Compiler | 1 |
| Research / Experiments / Training | 24 |
| Sampling LAB Backend | 20 |
| Sampling LAB UI | 16 |
| Shared Backend Utilities | 3 |
| Shared Frontend UI & Utilities | 6 |
| Vision LAB Core Contracts | 3 |

## Current working-tree changes

### FE dirty files

- ` D dist/assets/index-B4vbtfiU.js`
- ` D dist/assets/index-CjfZrce7.css`
- ` M dist/index.html`
- ` M docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M src/App.tsx`
- ` M src/Pages/MainScreen.tsx`
- ` M src/Pages/SamplingGeometryLabPage.tsx`
- ` M src/api/samplingGeometryApi.ts`
- ` M tools/generate_llm_context_map.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/api.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/lab_service_api.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/sampling_geometry_api.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/session.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_labs/service/runtime.py`
- `?? .lambda_updater_backups/computer_vision_v0700_20260918_121654/`
- `?? .lambda_updater_backups/computer_vision_v0800_20260918_134404/`
- `?? .lambda_updater_backups/computer_vision_v0801_20260918_134934/`
- `?? .lambda_updater_backups/computer_vision_v0900_20260918_145405/`
- `?? .lambda_updater_backups/computer_vision_v1000_20260918_153222/`
- `?? .lambda_updater_backups/computer_vision_v1010_20260918_162456/`
- `?? .lambda_updater_backups/sampling_lab_v0500_20260918_110013/`
- `?? .lambda_updater_backups/sampling_lab_v0600_20260918_113500/`
- `?? dist/assets/index-CZvA8jJp.css`
- `?? dist/assets/index-cLewrI27.js`
- `?? docs/llm_context/updates/v0500_sampling_program_global_local.md`
- `?? docs/llm_context/updates/v0600_sampling_output_formulation.md`
- `?? docs/llm_context/updates/v0700_computer_vision_frame.md`
- `?? docs/llm_context/updates/v0800_computer_vision_production_pipeline.md`
- `?? docs/llm_context/updates/v0801_blur_template_refinement.md`
- `?? docs/llm_context/updates/v0900_computer_vision_control_workspace.md`
- `?? docs/llm_context/updates/v1000_computer_vision_scope_debug_stack.md`
- `?? docs/llm_context/updates/v1010_computer_vision_debug_source_hotfix.md`
- `?? src/Pages/ComputerVisionPage.tsx`
- `?? src/api/visionAppApi.ts`
- `?? src/components/ComputerVision/`
- `?? src/components/VisionLabs/SamplingProgram/`
- `?? update_computer_vision_blur_template_hotfix_v0801.py`
- `?? update_computer_vision_control_workspace_v0900.py`
- `?? update_computer_vision_debug_source_hotfix_v1010.py`
- `?? update_computer_vision_frame_v0700.py`
- `?? update_computer_vision_production_v0800.py`
- `?? update_computer_vision_scope_debug_v1000.py`
- `?? update_sampling_lab_global_local_v0500.py`
- `?? update_sampling_output_formulation_v0600.py`
- `?? ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/vision_app_api.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/program.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_labs/sampling_geometry/program_runtime.py`
- `?? ../LambdaVisionSuperBackEnd/storage/vision_apps/`
- `?? ../LambdaVisionSuperBackEnd/storage/vision_labs/services/canny-edge/`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/sampling_geometry/test_sampling_program_v0500.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_labs/sampling_geometry/test_sampling_program_v0600.py`

### BE dirty files

- ` D ../LambdaVisionSuper/dist/assets/index-B4vbtfiU.js`
- ` D ../LambdaVisionSuper/dist/assets/index-CjfZrce7.css`
- ` M ../LambdaVisionSuper/dist/index.html`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M ../LambdaVisionSuper/src/App.tsx`
- ` M ../LambdaVisionSuper/src/Pages/MainScreen.tsx`
- ` M ../LambdaVisionSuper/src/Pages/SamplingGeometryLabPage.tsx`
- ` M ../LambdaVisionSuper/src/api/samplingGeometryApi.ts`
- ` M ../LambdaVisionSuper/tools/generate_llm_context_map.py`
- ` M app/api/v1/api.py`
- ` M app/api/v1/endpoints/lab_service_api.py`
- ` M app/api/v1/endpoints/sampling_geometry_api.py`
- ` M app/services/vision_labs/sampling_geometry/session.py`
- ` M app/services/vision_labs/service/runtime.py`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v0700_20260918_121654/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v0800_20260918_134404/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v0801_20260918_134934/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v0900_20260918_145405/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1000_20260918_153222/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1010_20260918_162456/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/sampling_lab_v0500_20260918_110013/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/sampling_lab_v0600_20260918_113500/`
- `?? ../LambdaVisionSuper/dist/assets/index-CZvA8jJp.css`
- `?? ../LambdaVisionSuper/dist/assets/index-cLewrI27.js`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0500_sampling_program_global_local.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0600_sampling_output_formulation.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0700_computer_vision_frame.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0800_computer_vision_production_pipeline.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0801_blur_template_refinement.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v0900_computer_vision_control_workspace.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1000_computer_vision_scope_debug_stack.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1010_computer_vision_debug_source_hotfix.md`
- `?? ../LambdaVisionSuper/src/Pages/ComputerVisionPage.tsx`
- `?? ../LambdaVisionSuper/src/api/visionAppApi.ts`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/`
- `?? ../LambdaVisionSuper/src/components/VisionLabs/SamplingProgram/`
- `?? ../LambdaVisionSuper/update_computer_vision_blur_template_hotfix_v0801.py`
- `?? ../LambdaVisionSuper/update_computer_vision_control_workspace_v0900.py`
- `?? ../LambdaVisionSuper/update_computer_vision_debug_source_hotfix_v1010.py`
- `?? ../LambdaVisionSuper/update_computer_vision_frame_v0700.py`
- `?? ../LambdaVisionSuper/update_computer_vision_production_v0800.py`
- `?? ../LambdaVisionSuper/update_computer_vision_scope_debug_v1000.py`
- `?? ../LambdaVisionSuper/update_sampling_lab_global_local_v0500.py`
- `?? ../LambdaVisionSuper/update_sampling_output_formulation_v0600.py`
- `?? app/api/v1/endpoints/vision_app_api.py`
- `?? app/services/vision_app/`
- `?? app/services/vision_labs/sampling_geometry/program.py`
- `?? app/services/vision_labs/sampling_geometry/program_runtime.py`
- `?? storage/vision_apps/`
- `?? storage/vision_labs/services/canny-edge/`
- `?? tests/vision_app/`
- `?? tests/vision_labs/sampling_geometry/test_sampling_program_v0500.py`
- `?? tests/vision_labs/sampling_geometry/test_sampling_program_v0600.py`

## Generated context documents

- `SYSTEM_ARCHITECTURE.md` — architectural modules, boundaries, routes and dependency edges.
- `SYSTEM_CONTEXT_BUNDLES.md` — minimal/deep file bundles for common tasks.
- `SYSTEM_FILE_MAP.md` — cleaned source/config inventory.
- `updates/*.md` — change-specific architectural notes.
