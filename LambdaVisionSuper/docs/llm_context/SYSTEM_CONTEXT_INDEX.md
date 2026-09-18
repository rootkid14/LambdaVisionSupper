# Lambda Vision — LLM Context Index

> Start here when opening a new LLM conversation about this codebase.

- Generator: `v2.1`
- Generated: `2026-09-18T23:08:26+07:00`
- Source files indexed: **397** (FE 217 / BE 180)
- Frontend git: `main` @ `83f6c0f` · **DIRTY**
- Backend git: `main` @ `83f6c0f` · **DIRTY**

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
| Computer Vision Program Backend / Control Mapper / Camera / Working Pipeline | 33 |
| Computer Vision Program UI | 18 |
| Contour Extractor LAB Backend | 8 |
| Contour Extractor LAB UI | 6 |
| Database Backend | 2 |
| Database UI | 6 |
| Desktop / Tauri Host | 6 |
| Desktop / Tauri — Unclassified | 1 |
| Fleet / Device / Infrastructure Backend | 12 |
| Fleet / Resource UI | 7 |
| Frontend Application Shell & Routing | 4 |
| Frontend Tools & LLM Context Docs | 66 |
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

- ` D dist/assets/index-CZvA8jJp.css`
- ` D dist/assets/index-cLewrI27.js`
- ` M dist/index.html`
- ` M docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M src/Pages/ComputerVisionPage.tsx`
- ` M src/api/visionAppApi.ts`
- ` M src/components/ComputerVision/ComputerVision.css`
- ` M src/components/ComputerVision/MasterSamplePanel.tsx`
- ` M tools/generate_llm_context_map.py`
- ` M ../LambdaVisionSuperBackEnd/app/api/v1/endpoints/vision_app_api.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/io_runtime.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/models.py`
- ` M ../LambdaVisionSuperBackEnd/app/services/vision_app/repository.py`
- ` M ../LambdaVisionSuperBackEnd/storage/vision_apps/programs/vision-program/program.json`
- ` M ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v0800.py`
- ` M ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v0900.py`
- `?? .lambda_updater_backups/computer_vision_v1100_20260918_175513/`
- `?? .lambda_updater_backups/computer_vision_v1110_20260918_175851/`
- `?? .lambda_updater_backups/computer_vision_v1200_20260918_181839/`
- `?? .lambda_updater_backups/computer_vision_v1300_20260918_213020/`
- `?? .lambda_updater_backups/computer_vision_v1310_20260918_222507/`
- `?? .lambda_updater_backups/computer_vision_v1320_20260918_222828/`
- `?? .lambda_updater_backups/computer_vision_v1330_20260918_223819/`
- `?? .lambda_updater_backups/computer_vision_v1340_20260918_224611/`
- `?? .lambda_updater_backups/computer_vision_v1350_20260918_225224/`
- `?? .lambda_updater_backups/computer_vision_v1360_20260918_230815/`
- `?? dist/assets/index-CDe9ZOYg.js`
- `?? dist/assets/index-CFAK3L4z.css`
- `?? docs/llm_context/updates/v1100_computer_vision_automation_ide.md`
- `?? docs/llm_context/updates/v1110_automation_ide_lucide_build_hotfix.md`
- `?? docs/llm_context/updates/v1200_iot_declaration_dynamic_ide.md`
- `?? docs/llm_context/updates/v1300_multicamera_workspaces_simulator.md`
- `?? docs/llm_context/updates/v1310_workspace_camera_keyboard_cleanup.md`
- `?? docs/llm_context/updates/v1320_context_generator_hotfix.md`
- `?? docs/llm_context/updates/v1330_workspace_activation_sync_hotfix.md`
- `?? docs/llm_context/updates/v1340_workspace_isolation_hotfix.md`
- `?? docs/llm_context/updates/v1350_workspace_transaction_isolation.md`
- `?? docs/llm_context/updates/v1360_workspace_owned_io_camera.md`
- `?? src/components/ComputerVision/AutomationCodeEditor.tsx`
- `?? src/components/ComputerVision/AutomationIdeWorkspace.tsx`
- `?? src/components/ComputerVision/CameraDeclarationWorkspace.tsx`
- `?? src/components/ComputerVision/DeveloperSimulatorWorkspace.tsx`
- `?? src/components/ComputerVision/EndpointObjectTree.tsx`
- `?? src/components/ComputerVision/IotDeclarationWorkspace.tsx`
- `?? src/components/ComputerVision/WorkspaceTabs.tsx`
- `?? update_computer_vision_automation_ide_hotfix_v1110.py`
- `?? update_computer_vision_automation_ide_v1100.py`
- `?? update_computer_vision_context_hotfix_v1320.py`
- `?? update_computer_vision_dynamic_objects_v1200.py`
- `?? update_computer_vision_multicamera_workspaces_v1300.py`
- `?? update_computer_vision_workspace_activation_hotfix_v1330.py`
- `?? update_computer_vision_workspace_camera_keyboard_v1310.py`
- `?? update_computer_vision_workspace_isolation_v1340.py`
- `?? update_computer_vision_workspace_owned_resources_v1360.py`
- `?? update_computer_vision_workspace_transaction_v1350.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/automation_manager.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/automation_models.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/automation_runtime.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/camera_resource_runtime.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/endpoint_registry.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/frame_slot_store.py`
- `?? ../LambdaVisionSuperBackEnd/app/services/vision_app/workspace_runtime.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1100.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1200.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1300.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1310.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1330.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1340.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1350.py`
- `?? ../LambdaVisionSuperBackEnd/tests/vision_app/test_vision_app_v1360.py`

### BE dirty files

- ` D ../LambdaVisionSuper/dist/assets/index-CZvA8jJp.css`
- ` D ../LambdaVisionSuper/dist/assets/index-cLewrI27.js`
- ` M ../LambdaVisionSuper/dist/index.html`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_ARCHITECTURE.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_CONTEXT_INDEX.md`
- ` M ../LambdaVisionSuper/docs/llm_context/SYSTEM_FILE_MAP.md`
- ` M ../LambdaVisionSuper/src/Pages/ComputerVisionPage.tsx`
- ` M ../LambdaVisionSuper/src/api/visionAppApi.ts`
- ` M ../LambdaVisionSuper/src/components/ComputerVision/ComputerVision.css`
- ` M ../LambdaVisionSuper/src/components/ComputerVision/MasterSamplePanel.tsx`
- ` M ../LambdaVisionSuper/tools/generate_llm_context_map.py`
- ` M app/api/v1/endpoints/vision_app_api.py`
- ` M app/services/vision_app/io_runtime.py`
- ` M app/services/vision_app/models.py`
- ` M app/services/vision_app/repository.py`
- ` M storage/vision_apps/programs/vision-program/program.json`
- ` M tests/vision_app/test_vision_app_v0800.py`
- ` M tests/vision_app/test_vision_app_v0900.py`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1100_20260918_175513/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1110_20260918_175851/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1200_20260918_181839/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1300_20260918_213020/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1310_20260918_222507/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1320_20260918_222828/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1330_20260918_223819/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1340_20260918_224611/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1350_20260918_225224/`
- `?? ../LambdaVisionSuper/.lambda_updater_backups/computer_vision_v1360_20260918_230815/`
- `?? ../LambdaVisionSuper/dist/assets/index-CDe9ZOYg.js`
- `?? ../LambdaVisionSuper/dist/assets/index-CFAK3L4z.css`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1100_computer_vision_automation_ide.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1110_automation_ide_lucide_build_hotfix.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1200_iot_declaration_dynamic_ide.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1300_multicamera_workspaces_simulator.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1310_workspace_camera_keyboard_cleanup.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1320_context_generator_hotfix.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1330_workspace_activation_sync_hotfix.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1340_workspace_isolation_hotfix.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1350_workspace_transaction_isolation.md`
- `?? ../LambdaVisionSuper/docs/llm_context/updates/v1360_workspace_owned_io_camera.md`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/AutomationCodeEditor.tsx`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/AutomationIdeWorkspace.tsx`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/CameraDeclarationWorkspace.tsx`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/DeveloperSimulatorWorkspace.tsx`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/EndpointObjectTree.tsx`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/IotDeclarationWorkspace.tsx`
- `?? ../LambdaVisionSuper/src/components/ComputerVision/WorkspaceTabs.tsx`
- `?? ../LambdaVisionSuper/update_computer_vision_automation_ide_hotfix_v1110.py`
- `?? ../LambdaVisionSuper/update_computer_vision_automation_ide_v1100.py`
- `?? ../LambdaVisionSuper/update_computer_vision_context_hotfix_v1320.py`
- `?? ../LambdaVisionSuper/update_computer_vision_dynamic_objects_v1200.py`
- `?? ../LambdaVisionSuper/update_computer_vision_multicamera_workspaces_v1300.py`
- `?? ../LambdaVisionSuper/update_computer_vision_workspace_activation_hotfix_v1330.py`
- `?? ../LambdaVisionSuper/update_computer_vision_workspace_camera_keyboard_v1310.py`
- `?? ../LambdaVisionSuper/update_computer_vision_workspace_isolation_v1340.py`
- `?? ../LambdaVisionSuper/update_computer_vision_workspace_owned_resources_v1360.py`
- `?? ../LambdaVisionSuper/update_computer_vision_workspace_transaction_v1350.py`
- `?? app/services/vision_app/automation_manager.py`
- `?? app/services/vision_app/automation_models.py`
- `?? app/services/vision_app/automation_runtime.py`
- `?? app/services/vision_app/camera_resource_runtime.py`
- `?? app/services/vision_app/endpoint_registry.py`
- `?? app/services/vision_app/frame_slot_store.py`
- `?? app/services/vision_app/workspace_runtime.py`
- `?? tests/vision_app/test_vision_app_v1100.py`
- `?? tests/vision_app/test_vision_app_v1200.py`
- `?? tests/vision_app/test_vision_app_v1300.py`
- `?? tests/vision_app/test_vision_app_v1310.py`
- `?? tests/vision_app/test_vision_app_v1330.py`
- `?? tests/vision_app/test_vision_app_v1340.py`
- `?? tests/vision_app/test_vision_app_v1350.py`
- `?? tests/vision_app/test_vision_app_v1360.py`

## Generated context documents

- `SYSTEM_ARCHITECTURE.md` — architectural modules, boundaries, routes and dependency edges.
- `SYSTEM_CONTEXT_BUNDLES.md` — minimal/deep file bundles for common tasks.
- `SYSTEM_FILE_MAP.md` — cleaned source/config inventory.
- `updates/*.md` — change-specific architectural notes.
