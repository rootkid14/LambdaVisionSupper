# Lambda Vision — LLM Context Bundles

> Use these bundles to load only the source needed for a task.

## Usage

- **Minimal**: start here for design/review/small changes.
- **Deep**: add these when implementing or debugging across boundaries.
- Always add the latest relevant `docs/llm_context/updates/*.md` note.

## Image Processing LAB

Raster-processing editor, operator framework, sessions/runtime, filter playground, and Image LAB API.

### Minimal context

- `FE:src/Pages/ImageProcessingLabPage.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts`
- `FE:src/components/VisionLabs/ImageProcessing/types.ts`
- `FE:src/api/imageLabApi.ts`
- `BE:app/services/vision_labs/image/operator.py`
- `BE:app/services/vision_labs/image/pipeline.py`
- `BE:app/services/vision_labs/image/runtime.py`
- `BE:app/services/vision_labs/image/session.py`
- `BE:app/services/vision_labs/image/types.py`
- `BE:app/api/v1/endpoints/image_lab_api.py`

### Deep context

- `FE:src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/operatorGuide.ts`
- `FE:src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/pipelineUtils.ts`
- `BE:app/services/vision_labs/image/registry.py`
- `BE:app/services/vision_labs/image/operators/builtins.py`
- `BE:app/services/vision_labs/image/operators/basic_families.py`
- `BE:app/services/vision_labs/image/operators/advanced_families.py`
- `BE:tests/vision_labs/image/test_image_lab_core.py`

## Contour Extractor LAB

Memory-efficient contour discovery: candidate generation, early junk rejection, filter funnel, lazy geometry inspection, and deployable ContourSet services.

### Minimal context

- `FE:src/Pages/ContourExtractorLabPage.tsx`
- `FE:src/Pages/ContourStageLibrary.tsx`
- `FE:src/api/contourExtractorApi.ts`
- `BE:app/services/vision_labs/contour_extractor/models.py`
- `BE:app/services/vision_labs/contour_extractor/store.py`
- `BE:app/services/vision_labs/contour_extractor/runtime.py`
- `BE:app/services/vision_labs/contour_extractor/session.py`
- `BE:app/api/v1/endpoints/contour_extractor_api.py`

### Deep context

- `FE:src/Pages/ContourExtractorGuideModal.tsx`
- `FE:src/Pages/ContourStageGuideModal.tsx`
- `FE:src/Pages/ContourFourierInspector.tsx`
- `BE:app/services/vision_labs/contour_extractor/stage_registry.py`
- `BE:app/services/vision_labs/contour_extractor/fourier.py`
- `BE:tests/vision_labs/contour_extractor/test_contour_extractor_v0100.py`
- `BE:tests/vision_labs/contour_extractor/test_contour_extractor_v0200.py`
- `BE:app/services/vision_labs/service/runtime.py`
- `FE:src/components/VisionLabs/SamplingGeometry/SamplingCanvas.tsx`

## Sampling LAB

Hierarchical Global/Local Sampling Program that turns one inspected image into semantic Data Blocks and then formulates them as understandable vectors or 2-D matrices. Formulation is cache-only; tensor depth belongs to Representation LAB and frequency-domain transforms remain outside the current editor.

### Minimal context

- `FE:src/Pages/SamplingGeometryLabPage.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/useSamplingProgramController.ts`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingMethodLibrary.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingStructurePanel.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingProgramCanvas.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingOutputShapeDesigner.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingConceptHelpModal.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/types.ts`
- `FE:src/api/samplingGeometryApi.ts`
- `BE:app/services/vision_labs/sampling_geometry/program.py`
- `BE:app/services/vision_labs/sampling_geometry/program_runtime.py`
- `BE:app/api/v1/endpoints/sampling_geometry_api.py`
- `BE:app/services/vision_labs/service/runtime.py`

### Deep context

- `FE:src/components/VisionLabs/SamplingProgram/SamplingConceptHelpModal.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingMethodEditor.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingMethodLibrary.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingOutputShapeDesigner.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingProgramCanvas.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/SamplingStructurePanel.tsx`
- `FE:src/components/VisionLabs/SamplingProgram/types.ts`
- `FE:src/components/VisionLabs/SamplingProgram/useSamplingProgramController.ts`
- `FE:src/components/VisionLabs/SamplingGeometry/SourceBoard.tsx`
- `BE:app/services/vision_labs/sampling_geometry/types.py`
- `BE:app/services/vision_labs/sampling_geometry/serialization.py`
- `BE:tests/vision_labs/sampling_geometry/test_sampling_geometry_lab_v0100.py`
- `BE:tests/vision_labs/sampling_geometry/test_sampling_geometry_lab_v0200.py`
- `BE:tests/vision_labs/sampling_geometry/test_sampling_lab_v0300.py`
- `BE:tests/vision_labs/sampling_geometry/test_sampling_lab_v0400.py`
- `BE:tests/vision_labs/sampling_geometry/test_sampling_program_v0500.py`
- `BE:tests/vision_labs/sampling_geometry/test_sampling_program_v0600.py`
- `BE:app/api/v1/endpoints/lab_service_api.py`
- `BE:app/services/vision_labs/sampling_geometry/pipeline.py`
- `BE:app/services/vision_labs/sampling_geometry/runtime.py`

## Computer Vision Program

Production Computer Vision application with v0.13.6 Workspace-owned resources: per-Workspace IOT + Camera declarations/binding, Master/ROI/Working state, active-Workspace Endpoint Registry/Automation IDE projection, Online/Offline scheduler, VisionRunSnapshot, Filter→Logic execution and lazy Debug Stack.

### Minimal context

- `FE:src/Pages/ComputerVisionPage.tsx`
- `FE:src/components/ComputerVision/VisionViewport.tsx`
- `FE:src/components/ComputerVision/IotDeclarationWorkspace.tsx`
- `FE:src/components/ComputerVision/AutomationCodeEditor.tsx`
- `FE:src/components/ComputerVision/EndpointObjectTree.tsx`
- `FE:src/components/ComputerVision/CameraModulePanel.tsx`
- `FE:src/components/ComputerVision/MasterSamplePanel.tsx`
- `FE:src/components/ComputerVision/WorkingModulePanel.tsx`
- `FE:src/components/ComputerVision/ScopeEditorModal.tsx`
- `FE:src/components/ComputerVision/DebugWorkspace.tsx`
- `FE:src/components/ComputerVision/AutomationIdeWorkspace.tsx`
- `FE:src/api/visionAppApi.ts`
- `BE:app/services/vision_app/models.py`
- `BE:app/services/vision_app/repository.py`
- `BE:app/services/vision_app/roi_search.py`
- `BE:app/services/vision_app/runtime.py`
- `BE:app/services/vision_app/io_runtime.py`
- `BE:app/services/vision_app/camera_runtime.py`
- `BE:app/services/vision_app/decision_runtime.py`
- `BE:app/services/vision_app/debug_store.py`
- `BE:app/services/vision_app/runner.py`
- `BE:app/services/vision_app/automation_models.py`
- `BE:app/services/vision_app/endpoint_registry.py`
- `BE:app/services/vision_app/automation_runtime.py`
- `BE:app/services/vision_app/automation_manager.py`
- `BE:app/api/v1/endpoints/vision_app_api.py`

### Deep context

- `BE:tests/vision_app/test_vision_app_frame_v0100.py`
- `BE:tests/vision_app/test_vision_app_v0800.py`
- `BE:tests/vision_app/test_vision_app_v0801.py`
- `BE:tests/vision_app/test_vision_app_v0900.py`
- `BE:tests/vision_app/test_vision_app_v1000.py`
- `BE:tests/vision_app/test_vision_app_v1010.py`
- `BE:tests/vision_app/test_vision_app_v1100.py`
- `BE:tests/vision_app/test_vision_app_v1200.py`
- `BE:tests/vision_app/test_vision_app_v1300.py`
- `BE:tests/vision_app/test_vision_app_v1310.py`
- `BE:tests/vision_app/test_vision_app_v1330.py`
- `BE:tests/vision_app/test_vision_app_v1340.py`
- `BE:tests/vision_app/test_vision_app_v1350.py`
- `BE:tests/vision_app/test_vision_app_v1360.py`
- `BE:tests/vision_app/test_vision_app_v1410.py`
- `BE:tests/vision_app/test_vision_app_v1420.py`
- `BE:app/services/vision_labs/service/runtime.py`
- `BE:app/services/vision_labs/service/repository.py`
- `FE:src/Pages/LabView.tsx`
- `FE:src/api/labServiceApi.ts`
- `FE:docs/llm_context/updates/v0800_computer_vision_production_pipeline.md`
- `FE:docs/llm_context/updates/v0900_computer_vision_control_workspace.md`
- `FE:docs/llm_context/updates/v1000_computer_vision_scope_debug_stack.md`
- `FE:docs/llm_context/updates/v1100_computer_vision_automation_ide.md`

## Lab Service

Versioned deployable LAB snapshots and the callable/manual-run service boundary.

### Minimal context

- `FE:src/Pages/LabView.tsx`
- `FE:src/api/labServiceApi.ts`
- `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts`
- `BE:app/services/vision_labs/service/models.py`
- `BE:app/services/vision_labs/service/repository.py`
- `BE:app/services/vision_labs/service/runtime.py`
- `BE:app/api/v1/endpoints/lab_service_api.py`

### Deep context

- `BE:tests/vision_labs/test_lab_service_core.py`
- `BE:app/services/vision_labs/image/pipeline.py`
- `BE:app/services/vision_labs/image/runtime.py`

## App Builder / Sequencer

General automation graph editor/runtime based on BaseNode, LogicObject and LogicPoolManager.

### Minimal context

- `FE:src/Pages/ProgrammingPage.tsx`
- `FE:src/Pages/SequencerPage.tsx`
- `FE:src/Stores/FlowStore.tsx`
- `FE:src/utils/FlowCompiler.ts`
- `FE:src/api/nodeApi.ts`
- `BE:app/services/node_registry.py`
- `BE:app/services/LogicObjects.py`
- `BE:app/services/LogicPoolManager.py`
- `BE:app/services/LVSTypes.py`
- `BE:app/api/v1/endpoints/graph_api.py`

### Deep context

- `FE:src/components/ProgramMode/BaseNodeShell.tsx`
- `FE:src/components/ProgramMode/DebugPanel.tsx`
- `FE:src/components/ProgramMode/DynamicMemoryNode.tsx`
- `FE:src/components/ProgramMode/DynamicTerminalNode.tsx`
- `FE:src/components/ProgramMode/DynamicUniversalSwitchNode.tsx`
- `FE:src/components/ProgramMode/FlowControlNode.tsx`
- `FE:src/components/ProgramMode/InLineNode.tsx`
- `FE:src/components/ProgramMode/JsonBuilderNode.tsx`
- `FE:src/components/ProgramMode/JsonExtractorNode.tsx`
- `FE:src/components/ProgramMode/MemoryReadNode.tsx`
- `FE:src/components/ProgramMode/NodesMenu.tsx`
- `FE:src/components/ProgramMode/ObjectNodeIUI.tsx`
- `FE:src/components/ProgramMode/PinRow.tsx`
- `FE:src/components/ProgramMode/ProgrammingNode.tsx`
- `FE:src/components/ProgramMode/SmartDropdown.tsx`
- `FE:src/components/ProgramMode/TeleportNodes.tsx`
- `FE:src/components/ProgramMode/UniversalNode.tsx`
- `FE:src/UI_Engine/SequencerComponents/BaseNode.tsx`
- `FE:src/UI_Engine/SequencerComponents/PropertiesSidebar.tsx`
- `FE:src/UI_Engine/SequencerComponents/ScriptApiDocs.ts`
- `FE:src/UI_Engine/SequencerComponents/SequencerNodes.tsx`
- `FE:src/UI_Engine/SequencerComponents/TerminalLog.tsx`
- `FE:src/UI_Engine/SequencerComponents/TokenBlackboard.tsx`
- `FE:src/UI_Engine/SequencerComponents/TokenLayer.tsx`
- `BE:app/services/Nodes/caliberate_w2_robot_frame.py`
- `BE:app/services/Nodes/CallAPINode.py`
- `BE:app/services/Nodes/charuco_caliberation_update.py`
- `BE:app/services/Nodes/charuco_find_extrinsics_update.py`
- `BE:app/services/Nodes/charuco_generator.py`
- `BE:app/services/Nodes/ComparativeNodes.py`
- `BE:app/services/Nodes/createJsonNode.py`
- `BE:app/services/Nodes/ESP32Nodes.py`
- `BE:app/services/Nodes/ExceptionHandlingNodes.py`
- `BE:app/services/Nodes/FilterNodes/crop_roi.py`
- `BE:app/services/Nodes/FilterNodes/ImageFiltersNode.py`
- `BE:app/services/Nodes/GigeCameraNodes.py`
- `BE:app/services/Nodes/ImageConversionNodes.py`
- `BE:app/services/Nodes/InterplexNodes/Classification.py`
- `BE:app/services/Nodes/InterplexNodes/ConvertBBoxes.py`
- `BE:app/services/Nodes/InterplexNodes/ESP32_serial_rl_control.py`
- `BE:app/services/Nodes/InterplexNodes/ESP32_Wireless.py`
- `BE:app/services/Nodes/InterplexNodes/FindPositions.py`
- `BE:app/services/Nodes/InterplexNodes/InterplexNodes.py`
- `BE:app/services/Nodes/InterplexNodes/Sort3Points.py`
- `BE:app/services/Nodes/InterplexNodes/yolo_labeling.py`
- `BE:app/services/Nodes/loadImagesNode.py`
- `BE:app/services/Nodes/LogicGateNodes.py`
- `BE:app/services/Nodes/pixel_to_worldframe.py`
- `BE:app/services/Nodes/primitive_nodes.py`
- `BE:app/services/Nodes/TeleportNodes.py`
- `BE:app/services/Nodes/update_file.py`
- `BE:app/services/Nodes/world_to_robot_matrix_cal.py`
- `BE:app/schemas/graph.py`

## Inspection UI Engine

Inspection canvas/UI-engine state, tags, panels, keyboard triggers and Konva nodes.

### Minimal context

- `FE:src/Pages/InspectionPage.tsx`
- `FE:src/UI_Engine/UIEngineStores/InspectionStore.ts`
- `FE:src/UI_Engine/UIEngineComponents/InspectionCanvas.tsx`
- `FE:src/UI_Engine/UIEngineComponents/InspectionSidebar.tsx`
- `FE:src/UI_Engine/UIEngineComponents/InspectionTopbar.tsx`

### Deep context

- `FE:src/UI_Engine/UIEngineComponents/FileManagerModal.tsx`
- `FE:src/UI_Engine/UIEngineComponents/FloatingPanels.tsx`
- `FE:src/UI_Engine/UIEngineComponents/GlobalTagsTable.tsx`
- `FE:src/UI_Engine/UIEngineComponents/InspectionCanvas.tsx`
- `FE:src/UI_Engine/UIEngineComponents/InspectionSidebar.tsx`
- `FE:src/UI_Engine/UIEngineComponents/InspectionTopbar.tsx`
- `FE:src/UI_Engine/UIEngineComponents/KonvaNodes.tsx`
- `FE:src/UI_Engine/UIEngineComponents/SettingModal.tsx`
- `FE:src/UI_Engine/UIEngineStores/GlobalTagsStore.ts`
- `FE:src/UI_Engine/UIEngineStores/InspectionStore.ts`
- `FE:src/UI_Engine/UIEngineStores/KeyboardTriggerStore.ts`
- `FE:src/UI_Engine/UIEngineStores/SequencerEngine.ts`
- `FE:src/UI_Engine/UIEngineStores/SequencerStores.ts`
- `FE:src/UI_Engine/UIEngineHelper/useTagHelper.ts`

## Fleet / Device

Resource/device discovery, pools, connections and camera/device infrastructure.

### Minimal context

- `FE:src/Pages/FleetDashboard.tsx`
- `FE:src/api/fleetApi.ts`
- `BE:app/api/v1/endpoints/infra_api.py`
- `BE:app/services/ConnectionBus.py`
- `BE:app/services/DevicePoolManager.py`

### Deep context

- `FE:src/components/Fleet/FleetCards.tsx`
- `FE:src/components/Fleet/FleetModals.tsx`
- `FE:src/components/Fleet/PoolsDrawer.tsx`
- `FE:src/components/Fleet/PoolsDrawerTabs.tsx`
- `FE:src/Stores/FleetDashboardStores.ts`
- `BE:app/external_libs/camera_core.py`

## Database

Database UI, dynamic table/query API, and database manager.

### Minimal context

- `FE:src/Pages/DatabasePage.tsx`
- `FE:src/api/dbEngineApi.ts`
- `FE:src/Stores/DatabaseEngineStore.ts`
- `BE:app/api/v1/endpoints/db_api.py`
- `BE:app/services/DatabaseManager.py`

### Deep context

- `FE:src/components/DataBaseEngine/DBModals.tsx`
- `FE:src/components/DataBaseEngine/DBPanels.tsx`
- `FE:src/components/DataBaseEngine/DBResultGrid.tsx`
