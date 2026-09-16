# Lambda Vision — Source File Map

> Clean source/config inventory for LLM-assisted development. Runtime data and binary artifacts are excluded by default.

- Generator: `v2.1`
- Generated: `2026-09-15T23:32:30+07:00`
- Frontend root: `/home/hieu/Desktop/LambdaVisionSuper/LambdaVisionSupper/LambdaVisionSuper`
- Frontend git: `main` @ `2fb5282`
- Backend root: `/home/hieu/Desktop/LambdaVisionSuper/LambdaVisionSupper/LambdaVisionSuperBackEnd`
- Backend git: `main` @ `2fb5282`
- Included source/config files: **265**

## Module summary

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

## Exclusion summary

The generator intentionally excludes binary datasets, model weights, images/assets, dependency/build output, runtime storage, caches, lockfiles, generated context dumps and generated schemas.

| Project | Excluded reason | Count |
| --- | --- | ---: |
| FE | `ignored-directory` | 52 |
| FE | `binary/data:.png` | 14 |
| FE | `generated/redundant` | 8 |
| FE | `binary/data:.svg` | 3 |
| FE | `generated/aux-json` | 1 |
| FE | `binary/data:.icns` | 1 |
| FE | `binary/data:.ico` | 1 |
| BE | `binary/data:.npz` | 825 |
| BE | `binary/data:.dll` | 94 |
| BE | `binary/data:.jpg` | 36 |
| BE | `ignored-directory` | 27 |
| BE | `non-source:.cti` | 6 |
| BE | `non-source:.txt` | 3 |
| BE | `non-source:.manifest` | 2 |
| BE | `non-source:.ax` | 2 |
| BE | `generated/redundant` | 2 |
| BE | `generated/aux-json` | 1 |
| BE | `non-source:.spec` | 1 |

### Top excluded extensions

| Project | Extension | Count |
| --- | --- | ---: |
| FE | `.tsx` | 20 |
| FE | `.py` | 14 |
| FE | `.png` | 14 |
| FE | `.ts` | 10 |
| FE | `.json` | 6 |
| FE | `.svg` | 5 |
| FE | `.md` | 3 |
| FE | `.txt` | 2 |
| FE | `.css` | 1 |
| FE | `.js` | 1 |
| FE | `.html` | 1 |
| FE | `.lock` | 1 |
| FE | `.icns` | 1 |
| FE | `.ico` | 1 |
| BE | `.npz` | 825 |
| BE | `.dll` | 94 |
| BE | `.jpg` | 36 |
| BE | `.json` | 23 |
| BE | `.cti` | 6 |
| BE | `.txt` | 5 |
| BE | `.py` | 4 |
| BE | `.manifest` | 2 |
| BE | `.ax` | 2 |
| BE | `.spec` | 1 |
| BE | `.db` | 1 |

## Full source inventory

| Project | Module | File | Size | Purpose | Key symbols |
| --- | --- | --- | ---: | --- | --- |
| BE | Backend Application Shell & API Router | `BE:app/api/root_api.py` | 6.6 KB | FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition. | def check_server_health, def get_fleet_overview_status, def gateway_proxy |
| BE | Backend Application Shell & API Router | `BE:app/api/v1/api.py` | 930 B | FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition. |  |
| BE | Backend Application Shell & API Router | `BE:app/api/v1/endpoints/utils.py` | 429 B | FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition. | def perform_health_check |
| BE | Backend Application Shell & API Router | `BE:app/core/config.py` | 853 B | FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition. | def get_base_dir, class Settings |
| BE | Backend Application Shell & API Router | `BE:app/main.py` | 4.2 KB | FastAPI backend bootstrap/entry point. | def load_all_nodes, def lifespan |
| BE | Backend Tests | `BE:tests/vision_labs/image/test_image_lab_advanced_raster.py` | 4.0 KB | Regression and integration tests. | def _frame, def _mask, def test_advanced_pack_is_registered, def test_comparison_multi_image_operators_hidden_from_image_lab_catalog, def test_sauvola_returns_binary_mask, def test_distance_transform_returns_grayscale_image, def test_zhang_suen_is_binary_and_thinner_than_source, def test_frangi_and_fft_spectrum_smoke |
| BE | Backend Tests | `BE:tests/vision_labs/image/test_image_lab_basic_families.py` | 1.8 KB | Regression and integration tests. | def test_basic_family_registry_has_representative_operators, def test_canny_produces_binary_mask, def test_crop_normalized_changes_shape |
| BE | Backend Tests | `BE:tests/vision_labs/image/test_image_lab_core.py` | 2.6 KB | Regression and integration tests. | def _pipeline, def test_pipeline_and_incremental_cache |
| BE | Backend Tests | `BE:tests/vision_labs/image/test_image_lab_enum_coercion.py` | 1016 B | Regression and integration tests. | def test_numeric_enum_coerces_string_to_declared_choice_type, def test_edge_operator_accepts_numeric_enum_from_html_select, def test_canny_aperture_accepts_numeric_enum_from_html_select |
| BE | Backend Tests | `BE:tests/vision_labs/sampling_geometry/test_sampling_geometry_lab_v0100.py` | 5.3 KB | Regression and integration tests. | def _image, def test_operator_catalog_has_three_workspaces, def test_geometry_pipeline_produces_curvature_profile, def test_spatial_ray_profiles_and_patch_features, def test_spectral_fft_to_radial_service |
| BE | Backend Tests | `BE:tests/vision_labs/test_lab_service_core.py` | 3.6 KB | Regression and integration tests. | def _pipeline, def _dump, def _deploy, def test_multiple_services_and_versioned_modify, def test_service_runtime_still_executes_deployed_snapshot |
| BE | Backend Tools / Updaters | `BE:update_image_processing_lab_backend_v001.py` | 177.3 KB | Backend-side updater and maintenance scripts. | def sha256_text, def find_project_root, def patch_router_text, def status_for_generated, def scan, def backup_file, def apply, def _compile_generated, def _smoke_script, def verify, def main |
| BE | Backend — Unclassified App Source | `BE:app/__init__.py` | 0 B | Python source module `__init__`. |  |
| BE | Backend — Unclassified App Source | `BE:app/mergify_ts.py` | 2.4 KB | Python source module `mergify_ts`. | def minify_python_for_llm |
| BE | Backend — Unclassified Project Source | `BE:.gitignore` | 226 B | Project source/configuration file. |  |
| BE | Backend — Unclassified Project Source | `BE:.python-version` | 17 B | Project source/configuration file. |  |
| BE | Database Backend | `BE:app/api/v1/endpoints/db_api.py` | 6.1 KB | Database CRUD/query API and database manager. | class QueryCondition, class QueryPayload, def get_database_tables, def get_table_schema, def execute_dynamic_query, def seed_database, def upload_image, def download_image, class ColumnDefinition, class CreateTablePayload, class InsertPayload, def create_new_table |
| BE | Database Backend | `BE:app/services/DatabaseManager.py` | 10.6 KB | Database access and dynamic table management. | class DatabaseManager |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/api/v1/endpoints/infra_api.py` | 10.4 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. | def get_server_info, def upload_file, def download_file, def get_resource_status, def delete_file, def get_all_local_servers, class ServerInfo, def add_local_server, def remove_local_server, def get_all_local_devices, class DeviceInfo, def add_local_device |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/camera_core.py` | 15.6 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. | class CameraInterface, class HikRobotCamera, class BaslerCamera |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/__init__.py` | 776 B | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. |  |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/CameraParams_const.py` | 8.8 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. |  |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/CameraParams_header.py` | 112.5 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. | def check_sys_and_update_PixelType, class _MV_GIGE_DEVICE_INFO_, class _MV_USB3_DEVICE_INFO_, class _MV_CamL_DEV_INFO_, class _MV_CXP_DEVICE_INFO_, class _MV_CML_DEVICE_INFO_, class _MV_XOF_DEVICE_INFO_, class _MV_GENTL_VIR_DEVICE_INFO_, class _MV_CC_DEVICE_INFO_, class N19_MV_CC_DEVICE_INFO_3DOT_0E, class _MV_CC_DEVICE_INFO_LIST_, class _MV_INTERFACE_INFO_ |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/MvCameraControl_class.py` | 197.9 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. | def get_platform_functype, def check_sys_and_update_dll, class _MV_PY_OBJECT_, class MvCamera |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/MvErrorDefine_const.py` | 8.7 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. |  |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/MvISPErrorDefine_const.py` | 5.8 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. |  |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/PixelType_header.py` | 11.2 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. |  |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/external_libs/MvImport/Runtime/x64/CommonParameters.ini` | 4.4 KB | Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings. |  |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/services/ConnectionBus.py` | 6.8 KB | Backend resource/device connection bus. | class APIManualRoutingBus |
| BE | Fleet / Device / Infrastructure Backend | `BE:app/services/DevicePoolManager.py` | 5.5 KB | Backend device/resource pool lifecycle. | class HTTPDevicePoolManager |
| BE | Image Processing LAB Backend | `BE:app/api/v1/endpoints/image_lab_api.py` | 11.4 KB | Image LAB session/pipeline/operator REST and WebSocket API. | class SavePipelineRequest, def _http_error, def get_operator_catalog, def validate_pipeline, def list_pipelines, def load_pipeline, def save_pipeline, def create_session, def close_session, def upload_input, def set_session_pipeline, def run_session |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/__init__.py` | 658 B | ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API. |  |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/operator.py` | 1.4 KB | ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API. | class ImageOperator |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/operators/__init__.py` | 709 B | ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API. | def load_builtin_operators |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/operators/advanced_families.py` | 55.2 KB | ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API. | def _as_u8, def _to_gray, def _to_bgr, def _restore_from_bgr, def _apply_to_luminance, def _normalize_response, def _gaussian_ksize, def _gaussian_blur_float, def _box_mean, def _frequency_mask, def _fft_filter_plane, def _frequency_filter_image |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/operators/basic_families.py` | 36.4 KB | ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API. | def _as_u8, def _to_bgr, def _to_gray, def _to_hsv, def _restore_bgr, def _morph_kernel, class ToHSV, class HSVToBGR, class ExtractChannel, class InvertImage, class BrightnessContrast, class GammaCorrection |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/operators/builtins.py` | 5.7 KB | ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API. | class Grayscale, class GaussianBlur, class BinaryThreshold, class MorphologyClose, class Resize, class AbsDifference |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/pipeline.py` | 10.4 KB | Image LAB pipeline schema, validation, compilation, and graph contracts. | class Endpoint, class PipelineConnection, class OperatorInstance, class ImagePipelineDefinition, def model_to_dict, class PipelineValidationError, class PipelineValidator, class InputBinding, class CompiledNode, class CompiledPipeline, class PipelineCompiler |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/registry.py` | 3.5 KB | Image LAB operator registry/catalog and stable operator IDs. | class OperatorDefinition, class ImageOperatorRegistry, def image_operator |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/repository.py` | 1.3 KB | Saved Image LAB pipeline persistence. | class ImagePipelineRepository |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/runtime.py` | 9.1 KB | Image LAB artifact cache and pipeline runtime. | class Artifact, class ArtifactStore, class RuntimeResult, class ImagePipelineRuntime |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/session.py` | 7.2 KB | Interactive Image LAB session, preview, realtime and session management. | class PreviewEncoder, class ViewSubscription, class RealtimeController, class ImageLabSession, class ImageLabSessionManager |
| BE | Image Processing LAB Backend | `BE:app/services/vision_labs/image/types.py` | 4.5 KB | ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API. | class ColorSpace, class ImageFrame, class BinaryMask, class ROI |
| BE | Lab Service Backend | `BE:app/api/v1/endpoints/lab_service_api.py` | 8.0 KB | Versioned Lab Service deploy/run/preview REST API. | class DeployOutputRequest, class DeployLabServiceRequest, def _http_error, def _derive_contract, def _decode_image, def _decode_mask, def list_lab_services, def deploy_lab_service, def preview_run_output, def list_lab_service_versions, def get_lab_service, def run_lab_service |
| BE | Lab Service Backend | `BE:app/services/vision_labs/service/__init__.py` | 694 B | Versioned deployable LAB snapshots, repository, generic runtime facade, run store, pruning, and Lab Service REST API. |  |
| BE | Lab Service Backend | `BE:app/services/vision_labs/service/models.py` | 1.1 KB | Lab Service typed deploy/run contracts. | class LabServicePort, class LabServiceOutputBinding, class LabServiceDefinition, class LabServiceRunManifest |
| BE | Lab Service Backend | `BE:app/services/vision_labs/service/repository.py` | 5.3 KB | Versioned Lab Service persistence. | def model_to_dict, def _now_iso, def _slugify, class LabServiceRepository |
| BE | Lab Service Backend | `BE:app/services/vision_labs/service/runtime.py` | 6.7 KB | Lab Service runtime/pruning/run store. | class LabServiceRun, def _required_nodes, def _prune_image_pipeline, def _prune_sampling_pipeline, class LabServiceRuntime, class LabServiceRunStore |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/api/v1/endpoints/graph_api.py` | 5.3 KB | Legacy App Builder/Sequencer graph deployment and execution API. | def get_node_catalog, class Preflight, def preflight_run, def deploy_graph_to_ram, def undeploy_graph_from_ram, def execute_logic, def get_in_out_schema, def get_logic_id_list, def get_logic_dependencies, class SyncDependenciesRequest, def sync_logic_dependencies |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/schemas/graph.py` | 879 B | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class DeployRequest, class ExecuteRequest, class DebugRunRequest |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/LogicObjects.py` | 13.5 KB | Legacy compiled graph execution object. | class LogicObject |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/LogicPoolManager.py` | 19.0 KB | Legacy deployed graph/LogicObject pool and execution lifecycle. | class LogicPoolManager |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/LVSTypes.py` | 3.1 KB | Legacy sequencer/node UI/runtime type definitions. | class UIDataType, class FileType, class NodeType, class TokenStatus, class GraphNodeType, def map_fe_type_to_python, class UIConfigType, class UIConfigField |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/node_registry.py` | 18.1 KB | Legacy BaseNode/NODE_REGISTRY contract and node registration. | def unregister_node, def registry_node, class BaseNode, class FlowNodeInput, class FlowNodeOutput, class JoinNode, class SplitNode, class TerminalNodeDefaultPin, class SendResponseNode, class ReceivePayloadNode, class ObjectNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/caliberate_w2_robot_frame.py` | 53.5 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class CalibrateWorldToRobotFrameInput, class CalibrateWorldToRobotFrameOutput, class CalibrateWorldToRobotFrameNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/CallAPINode.py` | 8.1 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class APIInput, class APIOutput, class APINode, class callLogicObjectInput, class CallLogicObjectNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/charuco_caliberation_update.py` | 90.6 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class CalibrateCharucoIntrinsicsInput, class CalibrateCharucoIntrinsicsOutput, class CalibrateCharucoIntrinsicsFromDatasetNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/charuco_find_extrinsics_update.py` | 86.5 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class FindCharucoExtrinsicsInput, class FindCharucoExtrinsicsOutput, class FindCharucoExtrinsicsNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/charuco_generator.py` | 9.5 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class GenerateCharucoBoardInput, class GenerateCharucoBoardOutput, class GenerateCharucoBoardNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/ComparativeNodes.py` | 3.7 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class CompareNumberInput, class CompareNumberOutput, class CompareNumbersNode, class CompareStringInput, class CompareStringOuput, class CompareStringNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/createJsonNode.py` | 5.9 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class CreateJSONNode, class ExtractJSONInput, class ExtractJSONNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/ESP32Nodes.py` | 11.7 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class ESP32DirectHTTPInput, class ESP32DirectHTTPOutput, class ESP32DirectHTTPOutput, class ESP32CameraInput, class ESP32CameraOutput, class ESP32CameraNode, class ESP32CameraMDNSInput, class ESP32CameraMDNSOutput, class ESP32CameraMDNSNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/ExceptionHandlingNodes.py` | 2.1 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class CheckNoneInput, class CheckNoneOutput, class CheckNoneNode, class RaiseErrorInput, class RaiseErrorNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/FilterNodes/crop_roi.py` | 3.5 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class CropAndSaveInput, class CropAndSaveOutput, class CropAndSaveNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/FilterNodes/ImageFiltersNode.py` | 17.5 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | def ensure_bgr, def extract_cv2_image, class ImageFilterInput, class ImageFilterOutput, class BrightnessContrastInput, class BrightnessContrastNode, class GaussianBlurInput, class GaussianBlurNode, class AdaptiveThresholdInput, class AdaptiveThresholdNode, class MorphologyInput, class MorphologyNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/GigeCameraNodes.py` | 13.3 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class BaslerCameraManager, class CameraInput, class CameraOutput, class BaslerCameraNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/ImageConversionNodes.py` | 11.3 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class Base64ToCV2Input, class Base64ToCV2Output, class Base64ToCV2ConvertNode, class CV2ToBase64Input, class CV2ToBase64Output, class CV2ToBase64ConvertNode, class ImageResizeInput, class ImageResizeOutput, class ImageResize, class BBoxesWarpAffineInput, class BBoxesWarpAffineOutput, class BBoxesWarpAffine |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/Classification.py` | 7.7 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | def extract_cv2_image, class ClassificationInput, class ClassificationOutput, class YoloClassification |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/ConvertBBoxes.py` | 2.2 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class BBoxXYWHtoXYXYInput, class BBoxXYWHtoXYXYOutput, class BBoxXYWHtoXYXYNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/ESP32_serial_rl_control.py` | 6.7 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class ESP32SerialManager, class ESP32SerialInput, class ESP32SerialOutput, class ESP32SerialNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/ESP32_Wireless.py` | 2.7 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class ESP32RelayInput, class ESP32RelayOutput, class ESP32RelayNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/FindPositions.py` | 7.0 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | def extract_cv2_image, class FindPositionInput, class FindPositionOuput, class FindPosition, class CheckTapeInput, class CheckTapeOutput, class CheckTapeNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/InterplexNodes.py` | 12.0 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class BBoxesToCentersInput, class BBoxesToCentersOutput, class BBoxesToCentersNode, class FindUpperPemLocationInput, class FindUpperPemLocationOutput, class FindUpperPemLocation, class ExtractRoiInput, class ExtractRoiOutput, class Extract_Roi_W_Offset, class FolderImageScannerInput, class FolderImageScannerOutput, class FolderImageScanner |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/Sort3Points.py` | 2.8 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class Sort3PointsInput, class Sort3PointsOutput, class Sort3PointsNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/InterplexNodes/yolo_labeling.py` | 5.2 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class SaveYoloDatasetInput, class SaveYoloDatasetOutput, class SaveYoloDatasetNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/loadImagesNode.py` | 2.4 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class LoadAsBase64Input, class LoadAsBase64Output, class LoadAsBase64 |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/LogicGateNodes.py` | 6.1 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class LogicGateInput, class LogicGateOutput, class LogicAndNode, class LogicOrNode, class DynamicSwitchInput, class DynamicUniversalSwitchNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/pixel_to_worldframe.py` | 38.4 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class PixelToWorldFrameInput, class PixelToWorldFrameOutput, class PixelToWorldFrameNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/primitive_nodes.py` | 10.5 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class PrintInput, class PrintOnput, class PrintNode, class MakeStringOutput, class MakeStringNode, class MakeNumberOutput, class MakeNumberNode, class MakeBooleanOutput, class MakeBooleanNode, class RandomIntInput, class RandomNumberOutput, class RandomIntNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/TeleportNodes.py` | 4.0 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class PortalInInput, class PortalInNode, class PortalOutOutput, class PortalOutNode |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/update_file.py` | 23.1 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | def replace_once, def replace_between, def remove_config_field, def update_input_schema, def simplify_config_fields, def fix_world_coordinate_definition, def remove_image_size_matching, def make_solver_internal, def update_execute_inputs, def improve_debug_origin_display, def update_documentation, def validate_result |
| BE | Legacy App Builder / Sequencer Runtime | `BE:app/services/Nodes/world_to_robot_matrix_cal.py` | 14.5 KB | General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes. | class WorldPointToRobotFrameInput, class WorldPointToRobotFrameOutput, class WorldPointToRobotFrameNode |
| BE | Research / Experiments / Training | `BE:chuongtrinhchupanh.py` | 8.5 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class CameraCaptureApp |
| BE | Research / Experiments / Training | `BE:clean_req.py` | 3.0 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. |  |
| BE | Research / Experiments / Training | `BE:concate_image.py` | 1.4 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def resize_and_concat |
| BE | Research / Experiments / Training | `BE:e1108D_metrics_extractor.py` | 17.8 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class FeatureConfig, def build_feature_names, def _prepare, def _to_lab, def _mean_std, def _percentiles, def _hist, def _bounds, class EdgeMaps, def _edge_maps, def _global, def _grid |
| BE | Research / Experiments / Training | `BE:e1108D_neural_network.py` | 13.6 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class EngineerMLPConfig, class FeatureEncoder, class ResidualMLPBlock, class ResidualFusion, class EngineerMLP, def masked_bce_loss, def masked_dice_loss, def engineer_loss, def count_parameters, def sanity_check |
| BE | Research / Experiments / Training | `BE:e1108D_run.py` | 24.5 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def choose_device, def _config_from_checkpoint, def load_model_and_standardizer, def find_corresponding_mask, def discover_images, def read_station_and_valid, def make_standardized_feature, def prepare_original_64, def highlight_prediction, def make_probability_visualization, def resize_for_output, def save_outputs |
| BE | Research / Experiments / Training | `BE:e1108D_train.py` | 37.1 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def seed_everything, def choose_device, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group, def _cache_path_for, def discover_records, def _read_station_arrays, def build_or_validate_feature_cache, def split_records_by_group |
| BE | Research / Experiments / Training | `BE:e5204_metrics_extractor.py` | 19.4 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class FeatureConfig, def build_feature_names, def _prepare, def _to_lab, def _mean_std, def _percentiles, def _hist, def _bounds, class EdgeMaps, def _edge_maps, def _global, def _grid |
| BE | Research / Experiments / Training | `BE:e5204_neural_network.py` | 15.2 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class EngineerMLPConfig, class FeatureEncoder, class ResidualMLPBlock, class ResidualFusion, class EngineerMLP, def masked_bce_loss, def masked_dice_loss, def engineer_loss, def count_parameters, def sanity_check |
| BE | Research / Experiments / Training | `BE:e5204_run.py` | 24.5 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def choose_device, def _config_from_checkpoint, def load_model_and_standardizer, def find_corresponding_mask, def discover_images, def read_station_and_valid, def make_standardized_feature, def prepare_original_64, def highlight_prediction, def make_probability_visualization, def resize_for_output, def save_outputs |
| BE | Research / Experiments / Training | `BE:e5204_train.py` | 37.1 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def seed_everything, def choose_device, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group, def _cache_path_for, def discover_records, def _read_station_arrays, def build_or_validate_feature_cache, def split_records_by_group |
| BE | Research / Experiments / Training | `BE:engineer_cnn_u3.py` | 15.4 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class EngineerCNNU3Config, def make_group_norm, class ConvNormAct, class ResidualBlock, class DownsampleStage, class DecoderStage, class EngineerCNNU3, def _b1hw, def masked_bce_loss, def masked_dice_loss, def engineer_cnn_u3_loss, def count_parameters |
| BE | Research / Experiments / Training | `BE:engineer_cnn_u3_run.py` | 23.8 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def choose_device, def safe_torch_load, def config_from_checkpoint, def load_model_and_preprocessing, def find_corresponding_mask, def discover_images, def read_station_and_valid, def prepare_64, def make_cnn_input, def highlight_prediction, def make_probability_visualization, def resize_for_output |
| BE | Research / Experiments / Training | `BE:engineer_cnn_u3_train.py` | 48.6 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def seed_everything, def choose_device, def _autocast_context, def _make_grad_scaler, def _safe_torch_load, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group, def discover_records, def read_station_arrays |
| BE | Research / Experiments / Training | `BE:engineer_master_v1.py` | 29.1 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class EngineerMasterV1Config, def make_group_norm, class ConvNormAct, class ResidualConvBlock, class VectorProjector, class MLPWideFlow, class MLPLatentFlow, class CNNBottleneckFlow, class CNND0Flow, class DisagreementFlow, class EngineerMasterV1, def _b1hw |
| BE | Research / Experiments / Training | `BE:engineer_master_v1_train.py` | 53.3 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def seed_everything, def choose_device, def make_grad_scaler, def safe_torch_load, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group, def discover_records, def split_records_by_group, def split_records_from_reference_manifest |
| BE | Research / Experiments / Training | `BE:entropy_1_gt_labeller.py` | 29.5 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class Entropy1GTLabeler |
| BE | Research / Experiments / Training | `BE:entropy_1_station_builder.py` | 31.7 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class StationConfig, def find_matching_file, def read_rgb, def read_mask, def save_rgb, def save_gray, def largest_component, def compute_invalid_fill_rgb, def apply_valid_polygon_to_image, def clip_gt_to_valid, def zhang_suen_thinning, def skeletonize |
| BE | Research / Experiments / Training | `BE:get_26D_vectors.py` | 3.2 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def local_mean_std, def extract_lab26, def save_features, def save_features_csv, def main |
| BE | Research / Experiments / Training | `BE:kiemtra.py` | 5.3 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def init_camera, def capture_and_save, def main |
| BE | Research / Experiments / Training | `BE:kiemtra2.py` | 3.2 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def main |
| BE | Research / Experiments / Training | `BE:kiemtra3.py` | 1.9 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def main |
| BE | Research / Experiments / Training | `BE:modultest.py` | 4.5 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | class ESPCameraOutput_test, class VoThaovaChongHieu |
| BE | Research / Experiments / Training | `BE:run_compare_mlp_cnn.py` | 35.1 KB | Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package. | def choose_device, def safe_torch_load, def validate_threshold, def mlp_config_from_checkpoint, def load_mlp, def cnn_config_from_checkpoint, def load_cnn, def find_corresponding_mask, def discover_images, def read_station_and_valid, def prepare_64, def make_mlp_feature |
| BE | Sampling / Geometry LAB Backend | `BE:app/api/v1/endpoints/sampling_geometry_api.py` | 11.0 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | class SavePipelineRequest, def _http_error, def _decode_image, def _decode_mask, def _source_manifest, def get_operator_catalog, def validate_pipeline, def list_pipelines, def load_pipeline, def save_pipeline, def create_session, def close_session |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/__init__.py` | 978 B | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. |  |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/operator.py` | 1.5 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | class SamplingGeometryOperator |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/operators/__init__.py` | 306 B | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | def load_sampling_geometry_operators |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/operators/common.py` | 2.4 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | def image_to_bgr, def image_channel, def sample_line, def normalized_entropy |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/operators/geometry.py` | 11.9 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | class ExtractContours, class LargestContour, class ResampleCurve, class CurvatureProfile, class ContourMeasurements |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/operators/spatial.py` | 13.9 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | class AxisRays, class CrossSampler, class ConcentricRings, class PatchGridStatistics |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/operators/spectral.py` | 12.5 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | def _window_2d, class FFT2D, class RadialFrequencyBands, class AngularFrequencyBands, class Histogram, class BasicStatistics |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/pipeline.py` | 9.9 KB | Image LAB pipeline schema, validation, compilation, and graph contracts. | def model_to_dict, class Endpoint, class PipelineConnection, class OperatorInstance, class SamplingPipelineDefinition, class CompiledNode, class CompiledPipeline, class SamplingPipelineValidator, class SamplingPipelineCompiler |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/preview.py` | 7.9 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | def _canvas, def _normalize_u8, def _plot_series, def _render_vector, def _render_matrix, def _render_geometry, def _render_table, class SamplingPreviewEncoder |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/registry.py` | 3.9 KB | Image LAB operator registry/catalog and stable operator IDs. | class SamplingOperatorDefinition, class SamplingOperatorRegistry, def sampling_operator |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/repository.py` | 1.5 KB | Saved Image LAB pipeline persistence. | class SamplingPipelineRepository |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/runtime.py` | 5.2 KB | Image LAB artifact cache and pipeline runtime. | class SamplingArtifact, class SamplingRuntimeResult, def artifact_shape, def artifact_type_name, def artifact_manifest, class SamplingGeometryRuntime |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/serialization.py` | 3.6 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | def _float_list, def artifact_to_json |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/session.py` | 3.2 KB | Interactive Image LAB session, preview, realtime and session management. | class SamplingGeometrySession, class SamplingGeometrySessionManager |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/specs.py` | 644 B | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | class SamplingPortSpec, def SamplingPort |
| BE | Sampling / Geometry LAB Backend | `BE:app/services/vision_labs/sampling_geometry/types.py` | 2.2 KB | Typed geometry/signal/feature artifacts, three-workspace operator registry, pipeline/runtime/session, visualization serialization, and Sampling / Geometry REST API. | class ContourSet, class Polyline, class ProfileSet, class Histogram1D, class FeatureVector, class FeatureMatrix, class Spectrum2D, class MeasurementTable |
| BE | Shared Backend Utilities | `BE:app/services/utils/files_loader.py` | 2.3 KB | Generic file/image/network helpers shared by backend domains. | def load_ai_models, def load_image |
| BE | Shared Backend Utilities | `BE:app/services/utils/image_utils.py` | 2.8 KB | Generic file/image/network helpers shared by backend domains. | def bytes_to_cv2, def cv2_to_base64, def base64_to_cv2, def extract_cv2_image |
| BE | Shared Backend Utilities | `BE:app/services/utils/ping_measurer.py` | 1.3 KB | Generic file/image/network helpers shared by backend domains. | def check_server_status |
| BE | Vision LAB Core Contracts | `BE:app/services/vision_labs/__init__.py` | 49 B | LAB-level shared port/parameter specifications and common Vision LAB package contracts. |  |
| BE | Vision LAB Core Contracts | `BE:app/services/vision_labs/core/__init__.py` | 454 B | LAB-level shared port/parameter specifications and common Vision LAB package contracts. |  |
| BE | Vision LAB Core Contracts | `BE:app/services/vision_labs/core/specs.py` | 5.9 KB | LAB-level shared port/parameter specifications and common Vision LAB package contracts. | class DataType, class PortSpec, def ImagePort, def BinaryMaskPort, def ROIPort, class ParameterSpec, def IntParam, def FloatParam, def BoolParam, def EnumParam, class ExecutionMode, class ExecutionContext |
| FE | App Builder / Sequencer UI | `FE:src/api/nodeApi.ts` | 4.1 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | NodeAPI |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/BaseNodeShell.tsx` | 2.1 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | BaseNodeShell |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/DebugPanel.tsx` | 19.5 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | DebugPanel |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/DynamicMemoryNode.tsx` | 4.6 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | DynamicMemoryNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/DynamicTerminalNode.tsx` | 4.7 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | DynamicTerminalNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/DynamicUniversalSwitchNode.tsx` | 5.5 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | DynamicSwitchNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/FlowControlNode.tsx` | 2.3 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | FlowControlNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/InLineNode.tsx` | 2.1 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | InlineNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/JsonBuilderNode.tsx` | 4.1 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | JsonBuilderNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/JsonExtractorNode.tsx` | 5.0 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | JsonExtractorNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/MemoryReadNode.tsx` | 3.2 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | MemoryReadNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/NodesMenu.tsx` | 3.3 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | NodeContextMenu |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/ObjectNodeIUI.tsx` | 5.7 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | ObjectNodeUI |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/PinRow.tsx` | 1.8 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | PinRow |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/ProgrammingNode.tsx` | 5.2 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | DataType, PinData, ConfigField, UniversalNodeData, UniversalNode |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/SmartDropdown.tsx` | 2.9 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | SmartDropdown |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/TeleportNodes.tsx` | 9.9 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | TeleportNodeUI |
| FE | App Builder / Sequencer UI | `FE:src/components/ProgramMode/UniversalNode.tsx` | 3.2 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | UniversalNode |
| FE | App Builder / Sequencer UI | `FE:src/Pages/ProgrammingPage.tsx` | 11.4 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | ProgrammingTab |
| FE | App Builder / Sequencer UI | `FE:src/Pages/SequencerPage.tsx` | 13.9 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | SequencerPage |
| FE | App Builder / Sequencer UI | `FE:src/Stores/FlowStore.tsx` | 19.5 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | NodeKind, DataType, PinManifest, ConfigFieldManifest, BaseManifest, InlineManifest, ObjectManifest, NodeManifest, GraphFile, GraphValidationResult, PreflightData, useFlowStore |
| FE | App Builder / Sequencer UI | `FE:src/UI_Engine/SequencerComponents/BaseNode.tsx` | 1.9 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | BaseNode |
| FE | App Builder / Sequencer UI | `FE:src/UI_Engine/SequencerComponents/PropertiesSidebar.tsx` | 58.6 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | PropertiesSidebar |
| FE | App Builder / Sequencer UI | `FE:src/UI_Engine/SequencerComponents/ScriptApiDocs.ts` | 3.2 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | SCRIPT_API_DOCS_MD |
| FE | App Builder / Sequencer UI | `FE:src/UI_Engine/SequencerComponents/SequencerNodes.tsx` | 28.8 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | ProcessNode, SwitchNode, ComputeNode, AndNode, OrNode, DelayNode, TagOverValNode, TagOverTagNode, ExtractJsonNode, BuildJsonNode, StartNode, EndNode |
| FE | App Builder / Sequencer UI | `FE:src/UI_Engine/SequencerComponents/TerminalLog.tsx` | 2.5 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | TerminalLog |
| FE | App Builder / Sequencer UI | `FE:src/UI_Engine/SequencerComponents/TokenBlackboard.tsx` | 8.3 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | TokenBlackboard |
| FE | App Builder / Sequencer UI | `FE:src/UI_Engine/SequencerComponents/TokenLayer.tsx` | 2.2 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | TokenLayer |
| FE | App Builder / Sequencer UI | `FE:src/utils/FlowCompiler.ts` | 3.1 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | FlowCompiler |
| FE | App Builder / Sequencer UI | `FE:src/utils/FlowUtils.ts` | 1.2 KB | Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client. | getPinColor |
| FE | Database UI | `FE:src/api/dbEngineApi.ts` | 4.5 KB | Database page, table/query panels and grids, database store, and database API client. | DBEngineAPI |
| FE | Database UI | `FE:src/components/DataBaseEngine/DBModals.tsx` | 9.0 KB | Database page, table/query panels and grids, database store, and database API client. | DBErrorModal, DBImageModal, CreateTableModal |
| FE | Database UI | `FE:src/components/DataBaseEngine/DBPanels.tsx` | 12.8 KB | Database page, table/query panels and grids, database store, and database API client. | DBLeftPanel, DBCenterPanel |
| FE | Database UI | `FE:src/components/DataBaseEngine/DBResultGrid.tsx` | 3.6 KB | Database page, table/query panels and grids, database store, and database API client. | DBResultGrid |
| FE | Database UI | `FE:src/Pages/DatabasePage.tsx` | 2.4 KB | Database page, table/query panels and grids, database store, and database API client. | DatabasePage |
| FE | Database UI | `FE:src/Stores/DatabaseEngineStore.ts` | 8.1 KB | Database page, table/query panels and grids, database store, and database API client. | DBFilter, ColumnConfig, DBEngineErrorModal, DBImageModal, DatabaseEngineStore, useDBEngineStore |
| FE | Desktop / Tauri Host | `FE:src-tauri/build.rs` | 39 B | Rust/Tauri desktop shell and its hand-authored configuration. |  |
| FE | Desktop / Tauri Host | `FE:src-tauri/capabilities/default.json` | 220 B | Rust/Tauri desktop shell and its hand-authored configuration. |  |
| FE | Desktop / Tauri Host | `FE:src-tauri/Cargo.toml` | 744 B | Rust/Tauri desktop shell and its hand-authored configuration. |  |
| FE | Desktop / Tauri Host | `FE:src-tauri/src/lib.rs` | 490 B | Rust/Tauri desktop shell and its hand-authored configuration. |  |
| FE | Desktop / Tauri Host | `FE:src-tauri/src/main.rs` | 192 B | Frontend bootstrap entry point. |  |
| FE | Desktop / Tauri Host | `FE:src-tauri/tauri.conf.json` | 775 B | Rust/Tauri desktop shell and its hand-authored configuration. |  |
| FE | Desktop / Tauri — Unclassified | `FE:src-tauri/.gitignore` | 603 B | Project source/configuration file. |  |
| FE | Fleet / Resource UI | `FE:src/api/fleetApi.ts` | 7.4 KB | Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client. | FleetAPI |
| FE | Fleet / Resource UI | `FE:src/components/Fleet/FleetCards.tsx` | 5.9 KB | Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client. | MasterGatewayCard, WorkerCard |
| FE | Fleet / Resource UI | `FE:src/components/Fleet/FleetModals.tsx` | 6.4 KB | Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client. | AddWorkerModal, SwitchMasterModal, ErrorModal |
| FE | Fleet / Resource UI | `FE:src/components/Fleet/PoolsDrawer.tsx` | 8.4 KB | Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client. | PoolsDrawer |
| FE | Fleet / Resource UI | `FE:src/components/Fleet/PoolsDrawerTabs.tsx` | 18.4 KB | Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client. | ServersTab, DevicesTab, ResourcesTab |
| FE | Fleet / Resource UI | `FE:src/Pages/FleetDashboard.tsx` | 7.8 KB | Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client. | FleetDashboard |
| FE | Fleet / Resource UI | `FE:src/Stores/FleetDashboardStores.ts` | 24.3 KB | Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client. | Hardware, DeviceInfo, WorkerInfoCard, LocalServerInfo, FilesState, GraphsState, PluginsState, ActiveLogicsState, ResourceInfo, WorkerDetails, AddServerInfo, AddHttpDeviceInfo |
| FE | Frontend Application Shell & Routing | `FE:src/App.css` | 918 B | Frontend route composition / application shell. |  |
| FE | Frontend Application Shell & Routing | `FE:src/App.tsx` | 2.3 KB | Frontend route composition / application shell. |  |
| FE | Frontend Application Shell & Routing | `FE:src/main.tsx` | 248 B | Frontend bootstrap entry point. |  |
| FE | Frontend Application Shell & Routing | `FE:src/Pages/MainScreen.tsx` | 6.5 KB | React/Vite application entry points, global routes, and the main navigation/home surface. | MainScreen |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/README.md` | 1.8 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/SYSTEM_ARCHITECTURE.md` | 33.5 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md` | 7.7 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/SYSTEM_CONTEXT_INDEX.md` | 7.6 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/SYSTEM_FILE_MAP.md` | 66.0 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/updates/v0041_lab_service_multi_edit.md` | 7.1 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/updates/v0050_filter_guide_system_map.md` | 3.2 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/updates/v0060_context_generator_v2.md` | 3.0 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:docs/llm_context/updates/v0100_sampling_geometry_lab.md` | 4.3 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:tools/generate_llm_context_map.py` | 58.9 KB | Project-aware LLM context compiler. | class ModuleProfile, def _profiles, def run_git, def git_metadata, def git_candidate_paths, def walk_candidate_paths, def all_candidate_paths, def ignored_by_directory, def generated_or_redundant, def source_relevance, def pattern_match, def module_for |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_lab_filter_guide_context_v0050.py` | 120.6 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_roots, def actual_path, def backup, def replace_state, def create_state, def scan, def preflight, def ensure_readme, def generate_system_map, def apply, def typescript_check, def verify |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_advanced_raster_v0030.py` | 91.8 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_backend, def backup, def patch_registry, def patch_loader, def scan, def apply, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_frontend_v001.py` | 74.1 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def dedent, def sha256_text, def discover_project, def patch_main_screen, def patch_app, def generated_status, def backup_files, def scan, def apply, def verify, def build_parser, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_frontend_v0011_uploadfix.py` | 6.5 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def find_root, def api_path, def status, def scan, def apply, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_raw_upload_v0012.py` | 11.0 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def find_frontend, def find_backend, def replace_exact, def scan, def apply, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_ui_operators_v0020.py` | 80.8 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_roots, def patch_operator_loader, def backup, def scan, def apply, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_upload_transport_v0013.py` | 8.7 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_roots, def backup, def patch_frontend, def patch_backend, def scan, def apply, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_view_state_v0022.py` | 14.1 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_frontend, def backup, def patch_zoom_view, def patch_workbench, def scan, def apply, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_image_processing_lab_viewer_ux_v0021.py` | 74.7 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_roots, def backup, def patch_enum_spec, def scan, def apply, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_lab_service_foundation_v0040.py` | 146.1 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_roots, def patch_router, def preflight_frontend, def backup, def file_status, def scan, def apply, def _backend_smoke, def _typescript_syntax_check, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_lab_service_multi_edit_v0041.py` | 186.6 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_roots, def resolve_path, def backup, def classify_file, def preflight, def scan, def apply, def typescript_syntax_check, def backend_smoke, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_llm_context_generator_v0060.py` | 117.6 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. | def resolve_roots, def generator_state, def backup, def ensure_readme, def run_generator, def scan, def apply, def _create_mock_tree, def verify, def main |
| FE | Frontend Tools & LLM Context Docs | `FE:update_sampling_geometry_lab_v0100.py` | 492.8 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend Tools & LLM Context Docs | `FE:update_sampling_geometry_lab_v0101_mergefix.py` | 492.5 KB | Updater scripts, context generators, architectural snapshots, and LLM handoff documentation. |  |
| FE | Frontend — Project / Config | `FE:.gitignore` | 296 B | Project source/configuration file. |  |
| FE | Frontend — Project / Config | `FE:index.html` | 370 B | Project source/configuration file. |  |
| FE | Frontend — Project / Config | `FE:package.json` | 1.2 KB | Project source/configuration file. |  |
| FE | Frontend — Project / Config | `FE:postcss.config.js` | 90 B | TypeScript/JavaScript source `postcss.config`. |  |
| FE | Frontend — Project / Config | `FE:README.md` | 378 B | Project documentation. |  |
| FE | Frontend — Project / Config | `FE:tailwind.config.js` | 181 B | TypeScript/JavaScript source `tailwind.config`. |  |
| FE | Frontend — Project / Config | `FE:tsconfig.json` | 605 B | Project source/configuration file. |  |
| FE | Frontend — Project / Config | `FE:tsconfig.node.json` | 213 B | Project source/configuration file. |  |
| FE | Frontend — Project / Config | `FE:vite.config.ts` | 878 B | TypeScript/JavaScript source `vite.config`. |  |
| FE | Frontend — Unclassified Source | `FE:src/api/axiosClient.ts` | 1.0 KB | TypeScript/JavaScript source `axiosClient`. | api_version, axiosClient |
| FE | Frontend — Unclassified Source | `FE:src/mergify.py` | 2.4 KB | Python source module `mergify`. | def minify_python_for_llm |
| FE | Frontend — Unclassified Source | `FE:src/mergify_ts.py` | 2.4 KB | Python source module `mergify_ts`. | def minify_python_for_llm |
| FE | Frontend — Unclassified Source | `FE:src/vite-env.d.ts` | 38 B | TypeScript/JavaScript source `vite-env.d`. |  |
| FE | Image Processing LAB UI | `FE:src/api/imageLabApi.ts` | 4.6 KB | Frontend Image LAB REST/WebSocket API client. | ImageLabSessionInfo, ImageLabRunResponse, ImageLabAPI |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx` | 26.4 KB | Standalone filter documentation and isolated test playground. | FilterGuideModal |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx` | 12.9 KB | Image LAB upload/run/viewer workbench. | ImageWorkbench |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/operatorGuide.ts` | 20.1 KB | Filter explanations, tuning guidance, and parameter help. | OperatorGuide, buildOperatorGuide |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx` | 7.3 KB | Image LAB operator selector and per-filter guide launcher. | OperatorLibrary |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/pipelineUtils.ts` | 5.9 KB | Interactive raster-processing editor: operator library, stack, viewers, Live/Manual execution, filter playground, and Image LAB API client. | firstEntry, operatorDefaults, isLinearStackOperator, stackCompatibility, validateLinearStack, buildPipelineDefinition, viewerSourcesForStack |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx` | 18.2 KB | Image LAB stack editor, ordering, parameters, and exposed service outputs. | ProcessingStack |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/types.ts` | 1.8 KB | Interactive raster-processing editor: operator library, stack, viewers, Live/Manual execution, filter playground, and Image LAB API client. | LabDataType, PortManifest, ParameterManifest, OperatorManifest, StackOperatorInstance, PipelineEndpoint, PipelineConnection, ImagePipelineDefinition, ViewerSource, ViewerPane, ImageLabExecutionMode, LabServiceOutputSelection |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts` | 27.2 KB | Image LAB frontend controller for sessions, Live/Manual execution, viewers, and service editing. | useImageLabController |
| FE | Image Processing LAB UI | `FE:src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx` | 4.2 KB | Reusable zoom/pan/fullscreen raster viewer. | ZoomPanImageView |
| FE | Image Processing LAB UI | `FE:src/Pages/ImageProcessingLabPage.tsx` | 10.2 KB | Top-level Image Processing LAB page/layout. | ImageProcessingLabPage |
| FE | Inspection UI Engine | `FE:src/Pages/InspectionPage.tsx` | 19.1 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | NameConfigDropdown, InspectionPage |
| FE | Inspection UI Engine | `FE:src/UI_Engine/hooks/useKeyboardTrigger.ts` | 2.3 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | useKeyboardTrigger |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/FileManagerModal.tsx` | 23.3 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | FileManagerModal |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/FloatingPanels.tsx` | 44.8 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | UIScriptEditorModal, CreateButtonModal, RenameModal, ActionMenu, UIPropertiesPanel |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/GlobalTagsTable.tsx` | 17.3 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | TagManagerTable |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/InspectionCanvas.tsx` | 5.7 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | InspectionCanvas |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/InspectionSidebar.tsx` | 1.6 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | InspectionSidebar |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/InspectionTopbar.tsx` | 11.6 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | InspectionTopbar |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/KonvaNodes.tsx` | 35.3 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | SceneNodeRenderer |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineComponents/SettingModal.tsx` | 9.6 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | SettingsModal |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineHelper/useTagHelper.ts` | 285 B | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | useTagValue, useWriteTag |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineStores/GlobalTagsStore.ts` | 2.3 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | TagValue, inferTagType, useTagDb |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineStores/InspectionStore.ts` | 20.9 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | DrawType, DataBinding, BaseUINode, Screen, Thumbnail, Frame, BoundingBoxNode, TextNode, BoundingCircleNode, LineNode, ActionMenuContext, PropertiesPanelContext |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineStores/KeyboardTriggerStore.ts` | 2.0 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | TriggerActionType, Shortcut, KeyboardTriggerStore, useKeyboardTriggerStore |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineStores/SequencerEngine.ts` | 51.7 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | SequencerEngine, SequencerCompiler |
| FE | Inspection UI Engine | `FE:src/UI_Engine/UIEngineStores/SequencerStores.ts` | 20.5 KB | Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI. | OperandType, SequencerNodeType, NodeStartConfig, NodeEndConfig, NodeProcessConfig, NodeSplitConfig, NodeJoinConfig, NodeSwitchConfig, NodeComputeConfig, NodeAndConfig, NodeOrConfig, NodeDelayConfig |
| FE | Lab Service Hub UI | `FE:src/api/labServiceApi.ts` | 3.1 KB | Frontend Lab Service API client. | LabServicePort, LabServiceOutputBinding, LabServiceDefinition, LabServiceRunManifest, DeployLabServiceRequest, LabServiceAPI |
| FE | Lab Service Hub UI | `FE:src/Pages/LabView.tsx` | 15.8 KB | Vision LAB launcher and deployed Lab Service hub/manual runner. | LabView |
| FE | Project Compiler | `FE:src/ProjectCompiler/ProjectCompilerCore/ProjectCompilerCore.ts` | 13.8 KB | Frontend project/compiler utilities used to transform or package project definitions. | Dependencies, WorkerInformation, FleetConfig, UIInformation, SequencerInformation, ProjectBundle, ProjectCompiler |
| FE | Sampling / Geometry LAB UI | `FE:src/api/samplingGeometryApi.ts` | 3.9 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | SamplingGeometryAPI |
| FE | Sampling / Geometry LAB UI | `FE:src/components/VisionLabs/SamplingGeometry/SamplingGuideModal.tsx` | 6.9 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | SamplingGuideModal |
| FE | Sampling / Geometry LAB UI | `FE:src/components/VisionLabs/SamplingGeometry/SamplingOperatorLibrary.tsx` | 3.1 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | SamplingOperatorLibrary |
| FE | Sampling / Geometry LAB UI | `FE:src/components/VisionLabs/SamplingGeometry/SamplingStack.tsx` | 5.5 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | SamplingStack |
| FE | Sampling / Geometry LAB UI | `FE:src/components/VisionLabs/SamplingGeometry/SamplingVisuals.tsx` | 10.5 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | LineChart, FeatureBars, FeatureMatrixView, MeasurementTableView, SyntheticGuideVisual, ArtifactDataView |
| FE | Sampling / Geometry LAB UI | `FE:src/components/VisionLabs/SamplingGeometry/SamplingWorkbench.tsx` | 5.1 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | SamplingWorkbench |
| FE | Sampling / Geometry LAB UI | `FE:src/components/VisionLabs/SamplingGeometry/types.ts` | 3.1 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | SamplingWorkspace, ExecutionMode, SamplingPortManifest, SamplingParameterManifest, SamplingGuideManifest, SamplingOperatorManifest, SamplingEndpoint, SamplingPipelineDefinition, SamplingStackItem, SamplingArtifact, SamplingRunResponse, InputBindingState |
| FE | Sampling / Geometry LAB UI | `FE:src/components/VisionLabs/SamplingGeometry/useSamplingGeometryController.ts` | 14.5 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | buildSamplingPipeline, useSamplingGeometryController |
| FE | Sampling / Geometry LAB UI | `FE:src/Pages/SamplingGeometryLabPage.tsx` | 8.6 KB | Three specialized workspaces for geometry, spatial sampling, and spectral/statistical feature extraction. | SamplingGeometryLabPage |
| FE | Shared Frontend UI & Utilities | `FE:src/Commons/ActionButton.tsx` | 1.2 KB | Reusable navigation/action UI and generic frontend utilities shared by feature modules. | ActionButton |
| FE | Shared Frontend UI & Utilities | `FE:src/Commons/MiniProgressBar.tsx` | 781 B | Reusable navigation/action UI and generic frontend utilities shared by feature modules. | MiniProgressBar |
| FE | Shared Frontend UI & Utilities | `FE:src/Commons/NeonActionBar.tsx` | 3.4 KB | Reusable navigation/action UI and generic frontend utilities shared by feature modules. | ActionItem, NeonActionBar |
| FE | Shared Frontend UI & Utilities | `FE:src/Commons/NeonNavBar.tsx` | 2.3 KB | Reusable navigation/action UI and generic frontend utilities shared by feature modules. | NavItem, NeonNavbar |
| FE | Shared Frontend UI & Utilities | `FE:src/utils/ColorConst.ts` | 1.0 KB | Reusable navigation/action UI and generic frontend utilities shared by feature modules. | COLOR_PALETTE |
| FE | Shared Frontend UI & Utilities | `FE:src/utils/imageUtils.ts` | 3.1 KB | Reusable navigation/action UI and generic frontend utilities shared by feature modules. | ImageProcessing |

## Generator coverage diagnostics

- Unclassified source/config files: **18**
- These files should be reviewed when improving the generator:
  - `FE:src-tauri/.gitignore`
  - `FE:.gitignore`
  - `FE:index.html`
  - `FE:package.json`
  - `FE:postcss.config.js`
  - `FE:README.md`
  - `FE:tailwind.config.js`
  - `FE:tsconfig.json`
  - `FE:tsconfig.node.json`
  - `FE:vite.config.ts`
  - `FE:src/api/axiosClient.ts`
  - `FE:src/mergify.py`
  - `FE:src/mergify_ts.py`
  - `FE:src/vite-env.d.ts`
  - `BE:app/__init__.py`
  - `BE:app/mergify_ts.py`
  - `BE:.gitignore`
  - `BE:.python-version`
