# Lambda Vision — LLM Context Index

> Start here when opening a new LLM conversation about this codebase.

- Generator: `v2.1`
- Generated: `2026-09-19T11:36:02+07:00`
- Source files indexed: **412** (FE 227 / BE 185)
- Frontend git: `main` @ `b65c420` · **DIRTY**
- Backend git: `main` @ `b65c420` · **DIRTY**

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
| Computer Vision Program Backend / Control Mapper / Camera / Working Pipeline | 38 |
| Computer Vision Program UI | 20 |
| Contour Extractor LAB Backend | 8 |
| Contour Extractor LAB UI | 6 |
| Database Backend | 2 |
| Database UI | 6 |
| Desktop / Tauri Host | 6 |
| Desktop / Tauri — Unclassified | 1 |
| Fleet / Device / Infrastructure Backend | 12 |
| Fleet / Resource UI | 7 |
| Frontend Application Shell & Routing | 4 |
| Frontend Tools & LLM Context Docs | 74 |
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

- ` D dist/assets/index-CDe9ZOYg.js`
- ` D dist/assets/index-CFAK3L4z.css`
- ` M dist/index.html`
- ` M docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M src/Pages/ComputerVisionPage.tsx`
- ` M src/api/visionAppApi.ts`
- ` M src/components/ComputerVision/AutomationCodeEditor.tsx`
- ` M tools/generate_llm_context_map.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/vision_app_api.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/automation_manager.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/automation_models.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/camera_resource_runtime.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/endpoint_registry.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/models.py`
- ` M ../LambdaVisionSuperBackEnd/e1108D_neural_network.py`
- `?? .lambda_updater_backups/computer_vision_v1410_20260919_101836/`
- `?? .lambda_updater_backups/computer_vision_v1420_20260919_104004/`
- `?? .lambda_updater_backups/computer_vision_v1500_20260919_113551/`
- `?? dist/assets/index-C9Flhv1M.css`
- `?? dist/assets/index-Cy-GqG9G.js`
- `?? docs/llm_context/updates/1.zip`
- `?? docs/llm_context/updates/v1410_workspace_owned_streaming.md`
- `?? docs/llm_context/updates/v1420_soft_trigger_tuning_backpressure.md`
- `?? docs/llm_context/updates/v1500_utilities_data_gathering.md`
- `?? src/components/ComputerVision/StreamingWorkspace.tsx`
- `?? src/components/ComputerVision/UtilitiesWorkspace.tsx`
- `?? update_computer_vision_softtrigger_tuning_backpressure_v1420.py`
- `?? update_computer_vision_streaming_softtrigger_v1400.py`
- `?? update_computer_vision_streaming_softtrigger_v1400_rebase.py`
- `?? update_computer_vision_streaming_softtrigger_v1410_workspace_owned.py`
- `?? update_computer_vision_utilities_data_gathering_v1500.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/streaming_runtime.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/utilities_runtime.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/vision_app.zip`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_labs/image/folder_vision_labs_image.zip`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1410.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1420.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1500.py`

### BE dirty files

- ` D ../LambdaVisionSuper/dist/assets/index-CDe9ZOYg.js`
- ` D ../LambdaVisionSuper/dist/assets/index-CFAK3L4z.css`
- ` M ../LambdaVisionSuper/dist/index.html`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M ../LambdaVisionSuper/src/Pages/ComputerVisionPage.tsx`
- ` M ../LambdaVisionSuper/src/api/visionAppApi.ts`
- ` M ../LambdaVisionSuper/src/components/ComputerVision/AutomationCodeEditor.tsx`
- ` M ../LambdaVisionSuper/tools/generate_llm_context_map.py`
- ` M app/api/v1/endpoints/vision_app_api.py`
- ` M app/services/vision_app/automation_manager.py`
- ` M app/services/vision_app/automation_models.py`
- ` M app/services/vision_app/camera_resource_runtime.py`
- ` M app/services/vision_app/endpoint_registry.py`
- ` M app/services/vision_app/models.py`
- ` M e1108D_neural_network.py`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1410_20260919_101836/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1420_20260919_104004/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1500_20260919_113551/`
- `?? ../LambdaVisionSuper/dist/assets/index-C9Flhv1M.css`
- `?? ../LambdaVisionSuper/dist/assets/index-Cy-GqG9G.js`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/1.zip`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1410_workspace_owned_streaming.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1420_soft_trigger_tuning_backpressure.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1500_utilities_data_gathering.md`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/StreamingWorkspace.tsx`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/UtilitiesWorkspace.tsx`
- `?? ../LambdaVisionSuper/update_computer_vision_softtrigger_tuning_backpressure_v1420.py`
- `?? ../LambdaVisionSuper/update_computer_vision_streaming_softtrigger_v1400.py`
- `?? ../LambdaVisionSuper/update_computer_vision_streaming_softtrigger_v1400_rebase.py`
- `?? ../LambdaVisionSuper/update_computer_vision_streaming_softtrigger_v1410_workspace_owned.py`
- `?? ../LambdaVisionSuper/update_computer_vision_utilities_data_gathering_v1500.py`
- `?? app/services/vision_app/streaming_runtime.py`
- `?? app/services/vision_app/utilities_runtime.py`
- `?? app/services/vision_app/vision_app.zip`
- `?? app/services/vision_labs/image/folder_vision_labs_image.zip`
- `?? tests/vision_app/test_vision_app_v1410.py`
- `?? tests/vision_app/test_vision_app_v1420.py`
- `?? tests/vision_app/test_vision_app_v1500.py`

## Generated context documents

- `SYSTEM_ARCHITECTURE.md` — architectural modules, boundaries, routes and dependency edges.
- `SYSTEM_CONTEXT_BUNDLES.md` — minimal/deep file bundles for common tasks.
- `SYSTEM_FILE_MAP.md` — cleaned source/config inventory.
- `updates/*.md` — change-specific architectural notes.
