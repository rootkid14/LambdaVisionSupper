# Lambda Vision — Full System File Map

> Generated automatically. Re-run the generator after structural code changes.

- Generated: `2026-09-15T22:10:02+07:00`
- Frontend root: `/home/hieu/Desktop/LambdaVisionSuper/LambdaVisionSupper/LambdaVisionSuper`
- Frontend git: `main` @ `2fb5282`
- Backend root: `/home/hieu/Desktop/LambdaVisionSuper/LambdaVisionSupper/LambdaVisionSuperBackEnd`
- Backend git: `main` @ `2fb5282`
- Files indexed: **1230** (FE 147 / BE 1083)

## How to use this file with an LLM

1. Give the LLM this file first when opening a new conversation about the codebase.
2. Identify the module/category relevant to the task.
3. Load only the referenced source files plus the latest matching `docs/llm_context/updates/*.md` note.
4. If the codebase changed structurally, regenerate this map before relying on it.

This inventory intentionally excludes dependency/build/runtime-data directories such as `node_modules`, `.git`, virtual environments, `dist/build`, caches, runtime `storage`, logs, datasets, and updater backups.

## System module summary

| Module / category | Files |
| --- | ---: |
| Backend API | 8 |
| Backend Image LAB Core | 8 |
| Backend Image LAB Operators | 4 |
| Backend Lab Service | 4 |
| Backend Models / Schemas | 1 |
| Backend Project / Config | 975 |
| Backend Python Source | 36 |
| Backend Services | 37 |
| Backend Vision LAB Core | 3 |
| Documentation | 5 |
| Frontend API Clients | 6 |
| Frontend Assets | 18 |
| Frontend Build / Config | 3 |
| Frontend Components | 24 |
| Frontend Pages | 8 |
| Frontend Project / Config | 18 |
| Frontend Source | 41 |
| Frontend State / Hooks | 3 |
| Frontend Vision LAB Components | 9 |
| Tests | 5 |
| Tools / Updaters | 14 |

## Suggested context bundles

### Image Processing LAB frontend

- `FE:src/Pages/ImageProcessingLabPage.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/operatorGuide.ts`
- `FE:src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx`
- `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts`
- `FE:src/api/imageLabApi.ts`

### Image Processing LAB backend

- `BE:app/services/vision_labs/image/`
- `BE:app/api/v1/endpoints/image_lab_api.py`
- `BE:tests/vision_labs/image/`

### Lab Service

- `FE:src/Pages/LabView.tsx`
- `FE:src/api/labServiceApi.ts`
- `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts`
- `BE:app/services/vision_labs/service/`
- `BE:app/api/v1/endpoints/lab_service_api.py`
- `BE:tests/vision_labs/test_lab_service_core.py`

## Full file inventory

| Project | Module | File | Size | Purpose | Key symbols |
| --- | --- | --- | ---: | --- | --- |
| BE | Backend API | `BE:app/api/root_api.py` | 6.6 KB | Python module `root_api`. | def check_server_health, def get_fleet_overview_status, def gateway_proxy |
| BE | Backend API | `BE:app/api/v1/api.py` | 756 B | Python module `api`. |  |
| BE | Backend API | `BE:app/api/v1/endpoints/db_api.py` | 6.1 KB | Python module `db_api`. | class QueryCondition, class QueryPayload, def get_database_tables, def get_table_schema, def execute_dynamic_query, def seed_database, def upload_image, def download_image, class ColumnDefinition, class CreateTablePayload |
| BE | Backend API | `BE:app/api/v1/endpoints/graph_api.py` | 5.3 KB | Python module `graph_api`. | def get_node_catalog, class Preflight, def preflight_run, def deploy_graph_to_ram, def undeploy_graph_from_ram, def execute_logic, def get_in_out_schema, def get_logic_id_list, def get_logic_dependencies, class SyncDependenciesRequest |
| BE | Backend API | `BE:app/api/v1/endpoints/image_lab_api.py` | 11.4 KB | REST/WebSocket endpoints for Image Processing LAB sessions. | class SavePipelineRequest, def _http_error, def get_operator_catalog, def validate_pipeline, def list_pipelines, def load_pipeline, def save_pipeline, def create_session, def close_session, def upload_input |
| BE | Backend API | `BE:app/api/v1/endpoints/infra_api.py` | 10.4 KB | Python module `infra_api`. | def get_server_info, def upload_file, def download_file, def get_resource_status, def delete_file, def get_all_local_servers, class ServerInfo, def add_local_server, def remove_local_server, def get_all_local_devices |
| BE | Backend API | `BE:app/api/v1/endpoints/lab_service_api.py` | 7.7 KB | REST endpoints for deployed Lab Services and manual runs. | class DeployOutputRequest, class DeployLabServiceRequest, def _http_error, def _derive_image_contract, def _decode_image, def list_lab_services, def deploy_lab_service, def preview_run_output, def list_lab_service_versions, def get_lab_service |
| BE | Backend API | `BE:app/api/v1/endpoints/utils.py` | 429 B | Python module `utils`. | def perform_health_check |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/__init__.py` | 658 B | Python module `__init__`. |  |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/operator.py` | 1.4 KB | Python module `operator`. | class ImageOperator |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/pipeline.py` | 10.4 KB | Pipeline definition, validation, compilation or graph contracts. | class Endpoint, class PipelineConnection, class OperatorInstance, class ImagePipelineDefinition, def model_to_dict, class PipelineValidationError, class PipelineValidator, class InputBinding, class CompiledNode, class CompiledPipeline |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/registry.py` | 3.5 KB | Operator or service registry and discovery logic. | class OperatorDefinition, class ImageOperatorRegistry, def image_operator |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/repository.py` | 1.3 KB | Persistent repository/storage access and version management. | class ImagePipelineRepository |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/runtime.py` | 9.1 KB | Runtime execution orchestration. | class Artifact, class ArtifactStore, class RuntimeResult, class ImagePipelineRuntime |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/session.py` | 7.2 KB | Python module `session`. | class PreviewEncoder, class ViewSubscription, class RealtimeController, class ImageLabSession, class ImageLabSessionManager |
| BE | Backend Image LAB Core | `BE:app/services/vision_labs/image/types.py` | 4.5 KB | Python module `types`. | class ColorSpace, class ImageFrame, class BinaryMask, class ROI |
| BE | Backend Image LAB Operators | `BE:app/services/vision_labs/image/operators/__init__.py` | 709 B | Python module `__init__`. | def load_builtin_operators |
| BE | Backend Image LAB Operators | `BE:app/services/vision_labs/image/operators/advanced_families.py` | 55.2 KB | Advanced pure-raster Image LAB operator implementations. | def _as_u8, def _to_gray, def _to_bgr, def _restore_from_bgr, def _apply_to_luminance, def _normalize_response, def _gaussian_ksize, def _gaussian_blur_float, def _box_mean, def _frequency_mask |
| BE | Backend Image LAB Operators | `BE:app/services/vision_labs/image/operators/basic_families.py` | 36.4 KB | Basic Image LAB operator family implementations. | def _as_u8, def _to_bgr, def _to_gray, def _to_hsv, def _restore_bgr, def _morph_kernel, class ToHSV, class HSVToBGR, class ExtractChannel, class InvertImage |
| BE | Backend Image LAB Operators | `BE:app/services/vision_labs/image/operators/builtins.py` | 5.7 KB | Core/builtin Image LAB operator implementations. | class Grayscale, class GaussianBlur, class BinaryThreshold, class MorphologyClose, class Resize, class AbsDifference |
| BE | Backend Lab Service | `BE:app/services/vision_labs/service/__init__.py` | 694 B | Python module `__init__`. |  |
| BE | Backend Lab Service | `BE:app/services/vision_labs/service/models.py` | 1.0 KB | Data models and serialized contracts. | class LabServicePort, class LabServiceOutputBinding, class LabServiceDefinition, class LabServiceRunManifest |
| BE | Backend Lab Service | `BE:app/services/vision_labs/service/repository.py` | 5.2 KB | Persistent repository/storage access and version management. | def model_to_dict, def _now_iso, def _slugify, class LabServiceRepository |
| BE | Backend Lab Service | `BE:app/services/vision_labs/service/runtime.py` | 5.5 KB | Runtime execution orchestration. | class LabServiceRun, def _prune_image_pipeline, class LabServiceRuntime, class LabServiceRunStore |
| BE | Backend Models / Schemas | `BE:app/schemas/graph.py` | 879 B | Python module `graph`. | class DeployRequest, class ExecuteRequest, class DebugRunRequest |
| BE | Backend Project / Config | `BE:.gitignore` | 226 B | Project file. |  |
| BE | Backend Project / Config | `BE:.python-version` | 17 B | Project file. |  |
| BE | Backend Project / Config | `BE:.vscode/settings.json` | 65 B | JSON configuration or package metadata. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_001__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_001__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_001__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_001__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_001__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_001__st_0005.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_002__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_002__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_002__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_002__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_002__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_002__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_003__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_003__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_003__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_003__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_003__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_003__st_0005.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_004__st_0000.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_004__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_004__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_004__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_004__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_004__st_0005.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_005__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_005__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_005__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_005__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_005__st_0004.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_006__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_006__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_006__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_006__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_006__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_007__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_007__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_007__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_007__st_0003.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_007__st_0004.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_008__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_008__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_008__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_008__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_008__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_008__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_008__st_0006.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_009__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_009__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_009__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_009__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_009__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_009__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_009__st_0006.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_010__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_010__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_010__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajf3ic9uugtfhuetf98pa4_75b21122__roi_010__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0007.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0008.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0009.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0010.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0011.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_001__st_0012.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_002__st_0000.npz` | 2.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_002__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_002__st_0002.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_002__st_0003.npz` | 2.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_003__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_003__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_003__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_003__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_003__st_0004.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_003__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_003__st_0006.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_004__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_004__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_004__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_004__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_004__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_004__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_004__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_005__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_005__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_005__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_005__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_005__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_005__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_005__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_006__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_006__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_006__st_0002.npz` | 2.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_007__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_007__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_007__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_007__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_007__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_007__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_007__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_008__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_008__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_008__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_008__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_008__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_009__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_009__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_009__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_009__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_009__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsghzmkkwotajfaiutsbq2qkokyedtow2_b1cdf2fd__roi_009__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_001__st_0000.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_001__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_001__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_001__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_001__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_002__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_002__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_002__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_002__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_002__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_002__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_002__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_003__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_003__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_003__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_003__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_004__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_004__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_004__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_004__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_005__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_005__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_005__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_005__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_006__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_006__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_006__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_006__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_006__st_0004.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_007__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_007__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_007__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_007__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_007__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_007__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_007__st_0006.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_008__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_008__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_008__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_008__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_008__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_008__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_008__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_009__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_009__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_009__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_009__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_010__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_010__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_010__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_010__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_010__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_011__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_011__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_011__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_011__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_011__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_011__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_012__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_012__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_012__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_012__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_012__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_012__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsz5cvmkdhyg57fr3jwjv7ylffyfl0by6_3d46fef1__roi_012__st_0006.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_001__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_001__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_001__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_001__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_001__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_002__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_002__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_002__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_002__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_002__st_0004.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_002__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_003__st_0000.npz` | 3.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_003__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_003__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_003__st_0003.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_003__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_003__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_003__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_004__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_004__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_004__st_0002.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_004__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_004__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_004__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_005__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_005__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_005__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_005__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_005__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_005__st_0005.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_006__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_006__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_006__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_006__st_0003.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_006__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_006__st_0005.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_007__st_0000.npz` | 3.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_007__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_007__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_007__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_007__st_0004.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_007__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_007__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_008__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_008__st_0001.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_008__st_0002.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_008__st_0003.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_008__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_008__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_008__st_0006.npz` | 3.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_009__st_0000.npz` | 3.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_009__st_0001.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_009__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_010__st_0000.npz` | 2.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_010__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_010__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_011__st_0000.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_011__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_011__st_0002.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_012__st_0000.npz` | 3.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_012__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_012__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_012__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_012__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_012__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_012__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_013__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_013__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_013__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_013__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_013__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_013__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_014__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_014__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_014__st_0002.npz` | 2.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_015__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_015__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_016__st_0007.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_017__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_017__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_017__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_017__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_017__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_017__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_017__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_018__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_018__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_018__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_018__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_018__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_018__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_018__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_019__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_019__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_019__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_019__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_019__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_019__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qsza4zf5dhj3lnmkjpw0wakrifxwwlze10_6df19a8b__roi_019__st_0006.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0000.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0006.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_001__st_0007.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0005.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0006.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt0icoy5eiebfzqmawucfdmupwc9hdg011_1e8820a6__roi_002__st_0007.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0000.npz` | 4.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_001__st_0007.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_002__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_002__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_002__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_002__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_002__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_002__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_002__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_003__st_0000.npz` | 3.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_003__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_003__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_003__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_003__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_003__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_003__st_0006.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_004__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_004__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_005__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_005__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_005__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_006__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_006__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_006__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_006__st_0003.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_007__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_007__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_007__st_0002.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_007__st_0003.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_007__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_007__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_007__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0001.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0002.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_008__st_0007.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_009__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_009__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_009__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_009__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_009__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_009__st_0005.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_009__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0007.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_010__st_0008.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0000.npz` | 3.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0004.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0005.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0007.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_011__st_0008.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0004.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_012__st_0007.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_013__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_013__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_013__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_013__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_013__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_013__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_013__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_014__st_0007.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_015__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_015__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_015__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_015__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_015__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_015__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_015__st_0006.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_016__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_016__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_016__st_0002.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_016__st_0003.npz` | 2.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_017__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_017__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_017__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_018__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_018__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_018__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_018__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_018__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_018__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_018__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1f079bjhdbvexkzuhaszxonwaipvvy8_f2c4ae67__roi_019__st_0007.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_001__st_0007.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_002__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_002__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_002__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_002__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_002__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_002__st_0005.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_002__st_0006.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_003__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_003__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_003__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_004__st_0000.npz` | 2.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_004__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_004__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_004__st_0003.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_005__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_005__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_005__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_005__st_0003.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0003.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0005.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_006__st_0007.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_007__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_007__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_007__st_0002.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_007__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_007__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_007__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_007__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_008__st_0000.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_008__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_008__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_008__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_008__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_008__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_008__st_0006.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_009__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_009__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_009__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_009__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_009__st_0004.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_009__st_0005.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_010__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_010__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_010__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_010__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_010__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_010__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_010__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0007.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_011__st_0008.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_012__st_0000.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_012__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_012__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_012__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_012__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_012__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_012__st_0006.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_013__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_013__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_013__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_013__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_013__st_0004.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_013__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_013__st_0006.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_014__st_0007.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_015__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_015__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_015__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_015__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_015__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_015__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_015__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_016__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_016__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_017__st_0000.npz` | 3.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_017__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_018__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_018__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_018__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_018__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_018__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_018__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_019__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_019__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_019__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_019__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_019__st_0004.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt1wmu60nrmchj8mcdvy5zr4t5xpio6a9_bf5ce455__roi_019__st_0005.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_001__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_001__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_001__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_001__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_001__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_001__st_0006.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_002__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_002__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_002__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_002__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_002__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_002__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_002__st_0006.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_003__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_003__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_003__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_003__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_003__st_0004.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_004__st_0000.npz` | 2.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_004__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_004__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_004__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_004__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_005__st_0000.npz` | 3.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_005__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_005__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_005__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_006__st_0000.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_006__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_006__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_006__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_007__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_007__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_007__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_007__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_007__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_007__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_007__st_0006.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_008__st_0000.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_008__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_008__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_008__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_008__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_008__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_008__st_0006.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_009__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_009__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_009__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_009__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_009__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_009__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_010__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_010__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_010__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_010__st_0003.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_010__st_0004.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_010__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_010__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_011__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_011__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_011__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_011__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt3re7spvkzsmwtc3tpgjlwfsrhcthka5_9683afdd__roi_011__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0006.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_001__st_0007.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0000.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0006.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_002__st_0007.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_003__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_003__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_004__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_004__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_004__st_0002.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_005__st_0001.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_005__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_005__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0000.npz` | 3.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_006__st_0007.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_007__st_0007.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_008__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_008__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_008__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_008__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_008__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_008__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_008__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_009__st_0000.npz` | 3.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_009__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_009__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_009__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_009__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_009__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_009__st_0006.npz` | 2.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_010__st_0007.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_011__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_011__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_011__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_011__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_011__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_011__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_011__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_012__st_0007.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0006.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_013__st_0007.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_014__st_0000.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_014__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_014__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_014__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_014__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_014__st_0005.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_015__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_015__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_015__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_015__st_0003.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_015__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_015__st_0005.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_016__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_016__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_016__st_0002.npz` | 2.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_017__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_017__st_0001.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_017__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_017__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_017__st_0004.npz` | 2.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_018__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_018__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_018__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_018__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_018__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_018__st_0005.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_018__st_0006.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0000.npz` | 3.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0001.npz` | 3.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0006.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qt46a5sr3rr88gzyxrv36juecnw8vzp67_f4767222__roi_019__st_0007.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_001__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_001__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_001__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_001__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_001__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_001__st_0005.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_002__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_002__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_002__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_002__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_002__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_002__st_0005.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_003__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_003__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_003__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_003__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_003__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_003__st_0005.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_004__st_0000.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_004__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_004__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_004__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_005__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_005__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_005__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_005__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_006__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_006__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_006__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_006__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_007__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_007__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_007__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_007__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_007__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_007__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_007__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0000.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0001.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0004.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_008__st_0007.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_009__st_0000.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_009__st_0001.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_009__st_0002.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_009__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_009__st_0004.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_009__st_0005.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_009__st_0006.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_010__st_0000.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_010__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_010__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_010__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_010__st_0004.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqidcdyifluh8p1x4vsi3_33ee73c7__roi_010__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_001__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_001__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_001__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_001__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_002__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_002__st_0001.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_002__st_0002.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_002__st_0003.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_002__st_0004.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_003__st_0000.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_003__st_0001.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_003__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_003__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_003__st_0004.npz` | 4.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_003__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_004__st_0000.npz` | 3.4 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_004__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_004__st_0002.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_004__st_0003.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_004__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_004__st_0005.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_005__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_005__st_0001.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_005__st_0002.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_005__st_0003.npz` | 3.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_005__st_0004.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0000.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0001.npz` | 4.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0002.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0003.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0004.npz` | 3.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0005.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0006.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0007.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0008.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0009.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0010.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0011.npz` | 3.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0012.npz` | 3.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:_entropy1_train_ca/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1/2aoboqs4qthkmzcbgpzvbqzrnl6nfvdmzditlv6m1_0b9f9507__roi_006__st_0013.npz` | 3.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/CommonTools.dll` | 276.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/CustomCtr.dll` | 1.1 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/DeviceEnumMng.dll` | 378.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/dvp.dll` | 81.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/hAcqMVision.dll` | 345.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/hAcqMVisionxl.dll` | 345.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/libmmd.dll` | 4.0 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/log4qt.dll` | 272.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/log4qtd.dll` | 707.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/msvcm90.dll` | 240.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/msvcp90.dll` | 836.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/msvcr120.dll` | 948.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/msvcr90.dll` | 612.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MVAIndustryControl.dll` | 172.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MVARenderWidget.dll` | 434.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvCameraAcqTool.dll` | 174.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvCameraAcqTool.resources.dll` | 7.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvCameraControl.Net.dll` | 179.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvFGAcqTool.dll` | 90.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvFGAcqTool.resources.dll` | 10.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvFGCtrlC.Net.dll` | 38.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvFrameGrabberControl.dll` | 35.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MVMemAlloc.dll` | 41.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvSerial.dll` | 72.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/MvSerialCtrl.dll` | 37.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/NetworkAdapterCfgLib.dll` | 24.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/NetworkAdapterCfgLib_NIC.dll` | 9.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qgif.dll` | 24.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qico.dll` | 24.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qjpeg.dll` | 237.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qminimal.dll` | 28.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qoffscreen.dll` | 522.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qsvg.dll` | 18.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5Core.dll` | 5.3 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5Gui.dll` | 5.7 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5Network.dll` | 1.0 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5OpenGL.dll` | 267.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5SerialPort.dll` | 58.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5Sql.dll` | 196.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5Svg.dll` | 245.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5Widgets.dll` | 5.3 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/Qt5Xml.dll` | 191.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qtga.dll` | 17.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qtiff.dll` | 306.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qwbmp.dll` | 17.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qwindows.dll` | 988.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/qwt.dll` | 1.1 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/ScreenPoint.dll` | 20.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/dll/UsrAcqDrv.dll` | 146.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/CLAllSerial_MD_VC120_v3_0_MV.dll` | 54.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/CLProtocol_MD_VC120_v3_0_MV.dll` | 142.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/CLSerCOM.dll` | 133.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/CLSerHvc.dll` | 46.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/CommonParameters.ini` | 4.4 KB | Project configuration. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/D3DCompiler_43.dll` | 2.4 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/FormatConversion.dll` | 8.6 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/GCBase_MD_VC120_v3_0_MV.dll` | 111.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/GenApi_MD_VC120_v3_0_MV.dll` | 980.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/libmmd.dll` | 3.1 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/libusb0.dll` | 175.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/log4cpp_MD_VC120_v3_0_MV.dll` | 243.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/Log_MD_VC120_v3_0_MV.dll` | 56.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MathParser_MD_VC120_v3_0_MV.dll` | 51.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MediaProcess.dll` | 5.0 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/Microsoft.VC90.CRT.manifest` | 513 B | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/Microsoft.VC90.DebugCRT.manifest` | 1.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/msvcm90.dll` | 239.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/msvcp120.dll` | 644.2 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/msvcp90.dll` | 831.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/msvcr100.dll` | 811.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/msvcr120.dll` | 940.7 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/msvcr90.dll` | 612.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvCameraControl.dll` | 1.4 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvCameraControlGUI.dll` | 255.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvCameraControlWrapper.dll` | 187.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvCameraPatch.dll` | 90.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvCamLVision.dll` | 223.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvDSS.ax` | 288.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvDSS2.ax` | 297.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MVFGControl.dll` | 1.1 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvFGProducerCML.cti` | 970.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvFGProducerCXP.cti` | 1008.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvFGProducerGEV.cti` | 933.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvFGProducerXoF.cti` | 1.0 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MVGigEVisionSDK.dll` | 750.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvISPControl.dll` | 2.9 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvLCProducer.dll` | 822.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MVMemAlloc.dll` | 54.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvProducerGEV.cti` | 199.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvProducerU3V.cti` | 199.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvProducerVIR.dll` | 1.7 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvRender.dll` | 152.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvSDKVersion.dll` | 147.5 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvSerial.dll` | 97.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvSerialCtrl.dll` | 44.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/MvUsb3vTL.dll` | 376.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/NodeMapData_MD_VC120_v3_0_MV.dll` | 126.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/pthreadGC2.dll` | 181.6 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/pthreadVC2.dll` | 81.0 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/SuperRender.dll` | 13.8 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/svml_dispmd.dll` | 8.7 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/ThirdParty/avutil-60.dll` | 1.1 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/ThirdParty/libwinpthread-1.dll` | 58.9 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/ThirdParty/swscale-9.dll` | 1.7 MB | Project file. |  |
| BE | Backend Project / Config | `BE:app/external_libs/MvImport/Runtime/x64/XmlParser_MD_VC120_v3_0_MV.dll` | 714.1 KB | Project file. |  |
| BE | Backend Project / Config | `BE:app/py_context_for_llm.txt` | 327.8 KB | Project file. |  |
| BE | Backend Project / Config | `BE:chuongtrinhchupanh.spec` | 685 B | Project file. |  |
| BE | Backend Project / Config | `BE:requirements copy.txt` | 1.3 KB | Project file. |  |
| BE | Backend Project / Config | `BE:tesst.txt` | 0 B | Project file. |  |
| BE | Backend Project / Config | `BE:ts_context_for_llm.txt` | 0 B | Project file. |  |
| BE | Backend Project / Config | `BE:tsx_context_for_llm.txt` | 0 B | Project file. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/mylar/crop_1779605008_0.jpg` | 7.8 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/mylar/crop_1779605034_0.jpg` | 8.1 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/mylar/crop_1779605044_0.jpg` | 9.2 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/mylar/crop_1779605051_0.jpg` | 8.8 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_0.jpg` | 2.0 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_1.jpg` | 1.9 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_2.jpg` | 2.2 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_3.jpg` | 1.5 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_4.jpg` | 2.0 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_5.jpg` | 2.1 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_6.jpg` | 1.5 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605008_7.jpg` | 1.6 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_0.jpg` | 2.0 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_1.jpg` | 1.9 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_2.jpg` | 1.9 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_3.jpg` | 1.5 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_4.jpg` | 2.0 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_5.jpg` | 2.1 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_6.jpg` | 1.5 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605034_7.jpg` | 1.6 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_0.jpg` | 2.4 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_1.jpg` | 2.1 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_2.jpg` | 2.1 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_3.jpg` | 1.5 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_4.jpg` | 2.1 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_5.jpg` | 1.9 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_6.jpg` | 1.6 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605044_7.jpg` | 1.4 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_0.jpg` | 2.3 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_1.jpg` | 2.2 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_2.jpg` | 2.0 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_3.jpg` | 1.6 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_4.jpg` | 2.1 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_5.jpg` | 2.0 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_6.jpg` | 1.5 KB | Static visual asset. |  |
| BE | Backend Project / Config | `BE:wrong_alarm_te_black/pem_a/crop_1779605051_7.jpg` | 1.4 KB | Static visual asset. |  |
| BE | Backend Python Source | `BE:app/__init__.py` | 0 B | Python module `__init__`. |  |
| BE | Backend Python Source | `BE:app/core/config.py` | 853 B | Python module `config`. | def get_base_dir, class Settings |
| BE | Backend Python Source | `BE:app/external_libs/camera_core.py` | 15.6 KB | Python module `camera_core`. | class CameraInterface, class HikRobotCamera, class BaslerCamera |
| BE | Backend Python Source | `BE:app/external_libs/MvImport/__init__.py` | 776 B | Python module `__init__`. |  |
| BE | Backend Python Source | `BE:app/external_libs/MvImport/CameraParams_const.py` | 8.8 KB | Python module `CameraParams_const`. |  |
| BE | Backend Python Source | `BE:app/external_libs/MvImport/CameraParams_header.py` | 112.5 KB | Python module `CameraParams_header`. | def check_sys_and_update_PixelType, class _MV_GIGE_DEVICE_INFO_, class _MV_USB3_DEVICE_INFO_, class _MV_CamL_DEV_INFO_, class _MV_CXP_DEVICE_INFO_, class _MV_CML_DEVICE_INFO_, class _MV_XOF_DEVICE_INFO_, class _MV_GENTL_VIR_DEVICE_INFO_, class _MV_CC_DEVICE_INFO_, class N19_MV_CC_DEVICE_INFO_3DOT_0E |
| BE | Backend Python Source | `BE:app/external_libs/MvImport/MvCameraControl_class.py` | 197.9 KB | Python module `MvCameraControl_class`. | def get_platform_functype, def check_sys_and_update_dll, class _MV_PY_OBJECT_, class MvCamera |
| BE | Backend Python Source | `BE:app/external_libs/MvImport/MvErrorDefine_const.py` | 8.7 KB | Python module `MvErrorDefine_const`. |  |
| BE | Backend Python Source | `BE:app/external_libs/MvImport/MvISPErrorDefine_const.py` | 5.8 KB | Python module `MvISPErrorDefine_const`. |  |
| BE | Backend Python Source | `BE:app/external_libs/MvImport/PixelType_header.py` | 11.2 KB | Python module `PixelType_header`. |  |
| BE | Backend Python Source | `BE:app/main.py` | 4.2 KB | Python module `main`. | def load_all_nodes, def lifespan |
| BE | Backend Python Source | `BE:app/mergify_ts.py` | 2.4 KB | Python module `mergify_ts`. | def minify_python_for_llm |
| BE | Backend Python Source | `BE:chuongtrinhchupanh.py` | 8.5 KB | Python module `chuongtrinhchupanh`. | class CameraCaptureApp |
| BE | Backend Python Source | `BE:clean_req.py` | 3.0 KB | Python module `clean_req`. |  |
| BE | Backend Python Source | `BE:concate_image.py` | 1.4 KB | Python module `concate_image`. | def resize_and_concat |
| BE | Backend Python Source | `BE:e1108D_metrics_extractor.py` | 17.8 KB | Python module `e1108D_metrics_extractor`. | class FeatureConfig, def build_feature_names, def _prepare, def _to_lab, def _mean_std, def _percentiles, def _hist, def _bounds, class EdgeMaps, def _edge_maps |
| BE | Backend Python Source | `BE:e1108D_neural_network.py` | 13.6 KB | Python module `e1108D_neural_network`. | class EngineerMLPConfig, class FeatureEncoder, class ResidualMLPBlock, class ResidualFusion, class EngineerMLP, def masked_bce_loss, def masked_dice_loss, def engineer_loss, def count_parameters, def sanity_check |
| BE | Backend Python Source | `BE:e1108D_run.py` | 24.5 KB | Python module `e1108D_run`. | def choose_device, def _config_from_checkpoint, def load_model_and_standardizer, def find_corresponding_mask, def discover_images, def read_station_and_valid, def make_standardized_feature, def prepare_original_64, def highlight_prediction, def make_probability_visualization |
| BE | Backend Python Source | `BE:e1108D_train.py` | 37.1 KB | Python module `e1108D_train`. | def seed_everything, def choose_device, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group, def _cache_path_for, def discover_records, def _read_station_arrays |
| BE | Backend Python Source | `BE:e5204_metrics_extractor.py` | 19.4 KB | Python module `e5204_metrics_extractor`. | class FeatureConfig, def build_feature_names, def _prepare, def _to_lab, def _mean_std, def _percentiles, def _hist, def _bounds, class EdgeMaps, def _edge_maps |
| BE | Backend Python Source | `BE:e5204_neural_network.py` | 15.2 KB | Python module `e5204_neural_network`. | class EngineerMLPConfig, class FeatureEncoder, class ResidualMLPBlock, class ResidualFusion, class EngineerMLP, def masked_bce_loss, def masked_dice_loss, def engineer_loss, def count_parameters, def sanity_check |
| BE | Backend Python Source | `BE:e5204_run.py` | 24.5 KB | Python module `e5204_run`. | def choose_device, def _config_from_checkpoint, def load_model_and_standardizer, def find_corresponding_mask, def discover_images, def read_station_and_valid, def make_standardized_feature, def prepare_original_64, def highlight_prediction, def make_probability_visualization |
| BE | Backend Python Source | `BE:e5204_train.py` | 37.1 KB | Python module `e5204_train`. | def seed_everything, def choose_device, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group, def _cache_path_for, def discover_records, def _read_station_arrays |
| BE | Backend Python Source | `BE:engineer_cnn_u3.py` | 15.4 KB | Python module `engineer_cnn_u3`. | class EngineerCNNU3Config, def make_group_norm, class ConvNormAct, class ResidualBlock, class DownsampleStage, class DecoderStage, class EngineerCNNU3, def _b1hw, def masked_bce_loss, def masked_dice_loss |
| BE | Backend Python Source | `BE:engineer_cnn_u3_run.py` | 23.8 KB | Python module `engineer_cnn_u3_run`. | def choose_device, def safe_torch_load, def config_from_checkpoint, def load_model_and_preprocessing, def find_corresponding_mask, def discover_images, def read_station_and_valid, def prepare_64, def make_cnn_input, def highlight_prediction |
| BE | Backend Python Source | `BE:engineer_cnn_u3_train.py` | 48.6 KB | Python module `engineer_cnn_u3_train`. | def seed_everything, def choose_device, def _autocast_context, def _make_grad_scaler, def _safe_torch_load, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group |
| BE | Backend Python Source | `BE:engineer_master_v1.py` | 29.1 KB | Python module `engineer_master_v1`. | class EngineerMasterV1Config, def make_group_norm, class ConvNormAct, class ResidualConvBlock, class VectorProjector, class MLPWideFlow, class MLPLatentFlow, class CNNBottleneckFlow, class CNND0Flow, class DisagreementFlow |
| BE | Backend Python Source | `BE:engineer_master_v1_train.py` | 53.3 KB | Python module `engineer_master_v1_train`. | def seed_everything, def choose_device, def make_grad_scaler, def safe_torch_load, class StationRecord, def _find_same_relative, def _load_json, def _strip_station_suffix, def _infer_source_group, def discover_records |
| BE | Backend Python Source | `BE:entropy_1_gt_labeller.py` | 29.5 KB | Python module `entropy_1_gt_labeller`. | class Entropy1GTLabeler |
| BE | Backend Python Source | `BE:entropy_1_station_builder.py` | 31.7 KB | Python module `entropy_1_station_builder`. | class StationConfig, def find_matching_file, def read_rgb, def read_mask, def save_rgb, def save_gray, def largest_component, def compute_invalid_fill_rgb, def apply_valid_polygon_to_image, def clip_gt_to_valid |
| BE | Backend Python Source | `BE:get_26D_vectors.py` | 3.2 KB | Python module `get_26D_vectors`. | def local_mean_std, def extract_lab26, def save_features, def save_features_csv, def main |
| BE | Backend Python Source | `BE:kiemtra.py` | 5.3 KB | Python module `kiemtra`. | def init_camera, def capture_and_save, def main |
| BE | Backend Python Source | `BE:kiemtra2.py` | 3.2 KB | Python module `kiemtra2`. | def main |
| BE | Backend Python Source | `BE:kiemtra3.py` | 1.9 KB | Python module `kiemtra3`. | def main |
| BE | Backend Python Source | `BE:modultest.py` | 4.5 KB | Regression or integration tests. | class ESPCameraOutput_test, class VoThaovaChongHieu |
| BE | Backend Python Source | `BE:run_compare_mlp_cnn.py` | 35.1 KB | Python module `run_compare_mlp_cnn`. | def choose_device, def safe_torch_load, def validate_threshold, def mlp_config_from_checkpoint, def load_mlp, def cnn_config_from_checkpoint, def load_cnn, def find_corresponding_mask, def discover_images, def read_station_and_valid |
| BE | Backend Services | `BE:app/services/ConnectionBus.py` | 6.8 KB | Python module `ConnectionBus`. | class APIManualRoutingBus |
| BE | Backend Services | `BE:app/services/DatabaseManager.py` | 10.6 KB | Python module `DatabaseManager`. | class DatabaseManager |
| BE | Backend Services | `BE:app/services/DevicePoolManager.py` | 5.5 KB | Python module `DevicePoolManager`. | class HTTPDevicePoolManager |
| BE | Backend Services | `BE:app/services/LogicObjects.py` | 13.5 KB | Python module `LogicObjects`. | class LogicObject |
| BE | Backend Services | `BE:app/services/LogicPoolManager.py` | 19.0 KB | Python module `LogicPoolManager`. | class LogicPoolManager |
| BE | Backend Services | `BE:app/services/LVSTypes.py` | 3.1 KB | Python module `LVSTypes`. | class UIDataType, class FileType, class NodeType, class TokenStatus, class GraphNodeType, def map_fe_type_to_python, class UIConfigType, class UIConfigField |
| BE | Backend Services | `BE:app/services/node_registry.py` | 18.1 KB | Operator or service registry and discovery logic. | def unregister_node, def registry_node, class BaseNode, class FlowNodeInput, class FlowNodeOutput, class JoinNode, class SplitNode, class TerminalNodeDefaultPin, class SendResponseNode, class ReceivePayloadNode |
| BE | Backend Services | `BE:app/services/Nodes/caliberate_w2_robot_frame.py` | 53.5 KB | Python module `caliberate_w2_robot_frame`. | class CalibrateWorldToRobotFrameInput, class CalibrateWorldToRobotFrameOutput, class CalibrateWorldToRobotFrameNode |
| BE | Backend Services | `BE:app/services/Nodes/CallAPINode.py` | 8.1 KB | Python module `CallAPINode`. | class APIInput, class APIOutput, class APINode, class callLogicObjectInput, class CallLogicObjectNode |
| BE | Backend Services | `BE:app/services/Nodes/charuco_caliberation_update.py` | 90.6 KB | Python module `charuco_caliberation_update`. | class CalibrateCharucoIntrinsicsInput, class CalibrateCharucoIntrinsicsOutput, class CalibrateCharucoIntrinsicsFromDatasetNode |
| BE | Backend Services | `BE:app/services/Nodes/charuco_find_extrinsics_update.py` | 86.5 KB | Python module `charuco_find_extrinsics_update`. | class FindCharucoExtrinsicsInput, class FindCharucoExtrinsicsOutput, class FindCharucoExtrinsicsNode |
| BE | Backend Services | `BE:app/services/Nodes/charuco_generator.py` | 9.5 KB | Python module `charuco_generator`. | class GenerateCharucoBoardInput, class GenerateCharucoBoardOutput, class GenerateCharucoBoardNode |
| BE | Backend Services | `BE:app/services/Nodes/ComparativeNodes.py` | 3.7 KB | Python module `ComparativeNodes`. | class CompareNumberInput, class CompareNumberOutput, class CompareNumbersNode, class CompareStringInput, class CompareStringOuput, class CompareStringNode |
| BE | Backend Services | `BE:app/services/Nodes/createJsonNode.py` | 5.9 KB | Python module `createJsonNode`. | class CreateJSONNode, class ExtractJSONInput, class ExtractJSONNode |
| BE | Backend Services | `BE:app/services/Nodes/ESP32Nodes.py` | 11.7 KB | Python module `ESP32Nodes`. | class ESP32DirectHTTPInput, class ESP32DirectHTTPOutput, class ESP32DirectHTTPOutput, class ESP32CameraInput, class ESP32CameraOutput, class ESP32CameraNode, class ESP32CameraMDNSInput, class ESP32CameraMDNSOutput, class ESP32CameraMDNSNode |
| BE | Backend Services | `BE:app/services/Nodes/ExceptionHandlingNodes.py` | 2.1 KB | Python module `ExceptionHandlingNodes`. | class CheckNoneInput, class CheckNoneOutput, class CheckNoneNode, class RaiseErrorInput, class RaiseErrorNode |
| BE | Backend Services | `BE:app/services/Nodes/FilterNodes/crop_roi.py` | 3.5 KB | Python module `crop_roi`. | class CropAndSaveInput, class CropAndSaveOutput, class CropAndSaveNode |
| BE | Backend Services | `BE:app/services/Nodes/FilterNodes/ImageFiltersNode.py` | 17.5 KB | Python module `ImageFiltersNode`. | def ensure_bgr, def extract_cv2_image, class ImageFilterInput, class ImageFilterOutput, class BrightnessContrastInput, class BrightnessContrastNode, class GaussianBlurInput, class GaussianBlurNode, class AdaptiveThresholdInput, class AdaptiveThresholdNode |
| BE | Backend Services | `BE:app/services/Nodes/GigeCameraNodes.py` | 13.3 KB | Python module `GigeCameraNodes`. | class BaslerCameraManager, class CameraInput, class CameraOutput, class BaslerCameraNode |
| BE | Backend Services | `BE:app/services/Nodes/ImageConversionNodes.py` | 11.3 KB | Python module `ImageConversionNodes`. | class Base64ToCV2Input, class Base64ToCV2Output, class Base64ToCV2ConvertNode, class CV2ToBase64Input, class CV2ToBase64Output, class CV2ToBase64ConvertNode, class ImageResizeInput, class ImageResizeOutput, class ImageResize, class BBoxesWarpAffineInput |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/Classification.py` | 7.7 KB | Python module `Classification`. | def extract_cv2_image, class ClassificationInput, class ClassificationOutput, class YoloClassification |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/ConvertBBoxes.py` | 2.2 KB | Python module `ConvertBBoxes`. | class BBoxXYWHtoXYXYInput, class BBoxXYWHtoXYXYOutput, class BBoxXYWHtoXYXYNode |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/ESP32_serial_rl_control.py` | 6.7 KB | Python module `ESP32_serial_rl_control`. | class ESP32SerialManager, class ESP32SerialInput, class ESP32SerialOutput, class ESP32SerialNode |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/ESP32_Wireless.py` | 2.7 KB | Python module `ESP32_Wireless`. | class ESP32RelayInput, class ESP32RelayOutput, class ESP32RelayNode |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/FindPositions.py` | 7.0 KB | Python module `FindPositions`. | def extract_cv2_image, class FindPositionInput, class FindPositionOuput, class FindPosition, class CheckTapeInput, class CheckTapeOutput, class CheckTapeNode |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/InterplexNodes.py` | 12.0 KB | Python module `InterplexNodes`. | class BBoxesToCentersInput, class BBoxesToCentersOutput, class BBoxesToCentersNode, class FindUpperPemLocationInput, class FindUpperPemLocationOutput, class FindUpperPemLocation, class ExtractRoiInput, class ExtractRoiOutput, class Extract_Roi_W_Offset, class FolderImageScannerInput |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/Sort3Points.py` | 2.8 KB | Python module `Sort3Points`. | class Sort3PointsInput, class Sort3PointsOutput, class Sort3PointsNode |
| BE | Backend Services | `BE:app/services/Nodes/InterplexNodes/yolo_labeling.py` | 5.2 KB | Python module `yolo_labeling`. | class SaveYoloDatasetInput, class SaveYoloDatasetOutput, class SaveYoloDatasetNode |
| BE | Backend Services | `BE:app/services/Nodes/loadImagesNode.py` | 2.4 KB | Python module `loadImagesNode`. | class LoadAsBase64Input, class LoadAsBase64Output, class LoadAsBase64 |
| BE | Backend Services | `BE:app/services/Nodes/LogicGateNodes.py` | 6.1 KB | Python module `LogicGateNodes`. | class LogicGateInput, class LogicGateOutput, class LogicAndNode, class LogicOrNode, class DynamicSwitchInput, class DynamicUniversalSwitchNode |
| BE | Backend Services | `BE:app/services/Nodes/pixel_to_worldframe.py` | 38.4 KB | Python module `pixel_to_worldframe`. | class PixelToWorldFrameInput, class PixelToWorldFrameOutput, class PixelToWorldFrameNode |
| BE | Backend Services | `BE:app/services/Nodes/primitive_nodes.py` | 10.5 KB | Python module `primitive_nodes`. | class PrintInput, class PrintOnput, class PrintNode, class MakeStringOutput, class MakeStringNode, class MakeNumberOutput, class MakeNumberNode, class MakeBooleanOutput, class MakeBooleanNode, class RandomIntInput |
| BE | Backend Services | `BE:app/services/Nodes/TeleportNodes.py` | 4.0 KB | Python module `TeleportNodes`. | class PortalInInput, class PortalInNode, class PortalOutOutput, class PortalOutNode |
| BE | Backend Services | `BE:app/services/Nodes/world_to_robot_matrix_cal.py` | 14.5 KB | Python module `world_to_robot_matrix_cal`. | class WorldPointToRobotFrameInput, class WorldPointToRobotFrameOutput, class WorldPointToRobotFrameNode |
| BE | Backend Services | `BE:app/services/utils/files_loader.py` | 2.3 KB | Python module `files_loader`. | def load_ai_models, def load_image |
| BE | Backend Services | `BE:app/services/utils/image_utils.py` | 2.8 KB | Python module `image_utils`. | def bytes_to_cv2, def cv2_to_base64, def base64_to_cv2, def extract_cv2_image |
| BE | Backend Services | `BE:app/services/utils/ping_measurer.py` | 1.3 KB | Python module `ping_measurer`. | def check_server_status |
| BE | Backend Vision LAB Core | `BE:app/services/vision_labs/__init__.py` | 49 B | Python module `__init__`. |  |
| BE | Backend Vision LAB Core | `BE:app/services/vision_labs/core/__init__.py` | 454 B | Python module `__init__`. |  |
| BE | Backend Vision LAB Core | `BE:app/services/vision_labs/core/specs.py` | 5.9 KB | Python module `specs`. | class DataType, class PortSpec, def ImagePort, def BinaryMaskPort, def ROIPort, class ParameterSpec, def IntParam, def FloatParam, def BoolParam, def EnumParam |
| BE | Tests | `BE:tests/vision_labs/image/test_image_lab_advanced_raster.py` | 4.0 KB | Regression or integration tests. | def _frame, def _mask, def test_advanced_pack_is_registered, def test_comparison_multi_image_operators_hidden_from_image_lab_catalog, def test_sauvola_returns_binary_mask, def test_distance_transform_returns_grayscale_image, def test_zhang_suen_is_binary_and_thinner_than_source, def test_frangi_and_fft_spectrum_smoke |
| BE | Tests | `BE:tests/vision_labs/image/test_image_lab_basic_families.py` | 1.8 KB | Basic Image LAB operator family implementations. | def test_basic_family_registry_has_representative_operators, def test_canny_produces_binary_mask, def test_crop_normalized_changes_shape |
| BE | Tests | `BE:tests/vision_labs/image/test_image_lab_core.py` | 2.6 KB | Regression or integration tests. | def _pipeline, def test_pipeline_and_incremental_cache |
| BE | Tests | `BE:tests/vision_labs/image/test_image_lab_enum_coercion.py` | 1016 B | Regression or integration tests. | def test_numeric_enum_coerces_string_to_declared_choice_type, def test_edge_operator_accepts_numeric_enum_from_html_select, def test_canny_aperture_accepts_numeric_enum_from_html_select |
| BE | Tests | `BE:tests/vision_labs/test_lab_service_core.py` | 3.6 KB | Regression or integration tests. | def _pipeline, def _dump, def _deploy, def test_multiple_services_and_versioned_modify, def test_service_runtime_still_executes_deployed_snapshot |
| BE | Tools / Updaters | `BE:app/services/Nodes/update_file.py` | 23.1 KB | Python module `update_file`. | def replace_once, def replace_between, def remove_config_field, def update_input_schema, def simplify_config_fields, def fix_world_coordinate_definition, def remove_image_size_matching, def make_solver_internal, def update_execute_inputs, def improve_debug_origin_display |
| BE | Tools / Updaters | `BE:update_image_processing_lab_backend_v001.py` | 177.3 KB | Python module `update_image_processing_lab_backend_v001`. | def sha256_text, def find_project_root, def patch_router_text, def status_for_generated, def scan, def backup_file, def apply, def _compile_generated, def _smoke_script, def verify |
| FE | Documentation | `FE:docs/llm_context/README.md` | 1.1 KB | Project documentation / LLM context note. |  |
| FE | Documentation | `FE:docs/llm_context/SYSTEM_FILE_MAP.md` | 241.8 KB | Project documentation / LLM context note. |  |
| FE | Documentation | `FE:docs/llm_context/updates/v0041_lab_service_multi_edit.md` | 7.1 KB | Project documentation / LLM context note. |  |
| FE | Documentation | `FE:docs/llm_context/updates/v0050_filter_guide_system_map.md` | 3.2 KB | Project documentation / LLM context note. |  |
| FE | Documentation | `FE:README.md` | 378 B | Project documentation / LLM context note. |  |
| FE | Frontend API Clients | `FE:src/api/axiosClient.ts` | 1.0 KB | TypeScript module/component `axiosClient`. | api_version, axiosClient |
| FE | Frontend API Clients | `FE:src/api/dbEngineApi.ts` | 4.5 KB | TypeScript module/component `dbEngineApi`. | DBEngineAPI |
| FE | Frontend API Clients | `FE:src/api/fleetApi.ts` | 7.4 KB | TypeScript module/component `fleetApi`. | FleetAPI |
| FE | Frontend API Clients | `FE:src/api/imageLabApi.ts` | 4.6 KB | Frontend client for Image Processing LAB backend APIs. | ImageLabSessionInfo, ImageLabRunResponse, ImageLabAPI |
| FE | Frontend API Clients | `FE:src/api/labServiceApi.ts` | 3.1 KB | Frontend client for versioned Lab Service APIs. | LabServicePort, LabServiceOutputBinding, LabServiceDefinition, LabServiceRunManifest, DeployLabServiceRequest, LabServiceAPI |
| FE | Frontend API Clients | `FE:src/api/nodeApi.ts` | 4.1 KB | TypeScript module/component `nodeApi`. | NodeAPI |
| FE | Frontend Assets | `FE:public/tauri.svg` | 2.5 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:public/vite.svg` | 1.5 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/128x128.png` | 3.4 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/128x128@2x.png` | 6.8 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/32x32.png` | 974 B | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/icon.ico` | 84.6 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/icon.png` | 13.9 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square107x107Logo.png` | 2.8 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square142x142Logo.png` | 3.8 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square150x150Logo.png` | 3.9 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square284x284Logo.png` | 7.6 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square30x30Logo.png` | 903 B | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square310x310Logo.png` | 8.4 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square44x44Logo.png` | 1.3 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square71x71Logo.png` | 2.0 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/Square89x89Logo.png` | 2.4 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src-tauri/icons/StoreLogo.png` | 1.5 KB | Static visual asset. |  |
| FE | Frontend Assets | `FE:src/assets/react.svg` | 4.0 KB | Static visual asset. |  |
| FE | Frontend Build / Config | `FE:package.json` | 1.2 KB | JSON configuration or package metadata. |  |
| FE | Frontend Build / Config | `FE:tsconfig.json` | 605 B | JSON configuration or package metadata. |  |
| FE | Frontend Build / Config | `FE:vite.config.ts` | 878 B | TypeScript module/component `vite.config`. |  |
| FE | Frontend Components | `FE:src/components/DataBaseEngine/DBModals.tsx` | 9.0 KB | TypeScript module/component `DBModals`. | DBErrorModal, DBImageModal, CreateTableModal |
| FE | Frontend Components | `FE:src/components/DataBaseEngine/DBPanels.tsx` | 12.8 KB | TypeScript module/component `DBPanels`. | DBLeftPanel, DBCenterPanel |
| FE | Frontend Components | `FE:src/components/DataBaseEngine/DBResultGrid.tsx` | 3.6 KB | TypeScript module/component `DBResultGrid`. | DBResultGrid |
| FE | Frontend Components | `FE:src/components/Fleet/FleetCards.tsx` | 5.9 KB | TypeScript module/component `FleetCards`. | MasterGatewayCard, WorkerCard, MasterGatewayCardProps, WorkerCardProps |
| FE | Frontend Components | `FE:src/components/Fleet/FleetModals.tsx` | 6.4 KB | TypeScript module/component `FleetModals`. | AddWorkerModal, SwitchMasterModal, ErrorModal |
| FE | Frontend Components | `FE:src/components/Fleet/PoolsDrawer.tsx` | 8.4 KB | TypeScript module/component `PoolsDrawer`. | PoolsDrawer |
| FE | Frontend Components | `FE:src/components/Fleet/PoolsDrawerTabs.tsx` | 18.4 KB | TypeScript module/component `PoolsDrawerTabs`. | ServersTab, DevicesTab, ResourcesTab |
| FE | Frontend Components | `FE:src/components/ProgramMode/BaseNodeShell.tsx` | 2.1 KB | TypeScript module/component `BaseNodeShell`. | BaseNodeShell, n, BaseNodeShellProps |
| FE | Frontend Components | `FE:src/components/ProgramMode/DebugPanel.tsx` | 19.5 KB | TypeScript module/component `DebugPanel`. | DebugPanel |
| FE | Frontend Components | `FE:src/components/ProgramMode/DynamicMemoryNode.tsx` | 4.6 KB | TypeScript module/component `DynamicMemoryNode`. | DynamicMemoryNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/DynamicTerminalNode.tsx` | 4.7 KB | TypeScript module/component `DynamicTerminalNode`. | DynamicTerminalNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/DynamicUniversalSwitchNode.tsx` | 5.5 KB | TypeScript module/component `DynamicUniversalSwitchNode`. | DynamicSwitchNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/FlowControlNode.tsx` | 2.3 KB | TypeScript module/component `FlowControlNode`. | FlowControlNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/InLineNode.tsx` | 2.1 KB | TypeScript module/component `InLineNode`. | InlineNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/JsonBuilderNode.tsx` | 4.1 KB | TypeScript module/component `JsonBuilderNode`. | JsonBuilderNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/JsonExtractorNode.tsx` | 5.0 KB | TypeScript module/component `JsonExtractorNode`. | JsonExtractorNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/MemoryReadNode.tsx` | 3.2 KB | TypeScript module/component `MemoryReadNode`. | MemoryReadNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/NodesMenu.tsx` | 3.3 KB | TypeScript module/component `NodesMenu`. | NodeContextMenu, NodeContextMenuProps |
| FE | Frontend Components | `FE:src/components/ProgramMode/ObjectNodeIUI.tsx` | 5.7 KB | TypeScript module/component `ObjectNodeIUI`. | ObjectNodeUI |
| FE | Frontend Components | `FE:src/components/ProgramMode/PinRow.tsx` | 1.8 KB | TypeScript module/component `PinRow`. | PinRow, PinRowProps |
| FE | Frontend Components | `FE:src/components/ProgramMode/ProgrammingNode.tsx` | 5.2 KB | TypeScript module/component `ProgrammingNode`. | DataType, PinData, ConfigField, UniversalNodeData, UniversalNode |
| FE | Frontend Components | `FE:src/components/ProgramMode/SmartDropdown.tsx` | 2.9 KB | TypeScript module/component `SmartDropdown`. | SmartDropdown, SmartDropdownProps |
| FE | Frontend Components | `FE:src/components/ProgramMode/TeleportNodes.tsx` | 9.9 KB | TypeScript module/component `TeleportNodes`. | TeleportNodeUI |
| FE | Frontend Components | `FE:src/components/ProgramMode/UniversalNode.tsx` | 3.2 KB | TypeScript module/component `UniversalNode`. | UniversalNode |
| FE | Frontend Pages | `FE:src/Pages/DatabasePage.tsx` | 2.4 KB | TypeScript module/component `DatabasePage`. | DatabasePage |
| FE | Frontend Pages | `FE:src/Pages/FleetDashboard.tsx` | 7.8 KB | TypeScript module/component `FleetDashboard`. | FleetDashboard |
| FE | Frontend Pages | `FE:src/Pages/ImageProcessingLabPage.tsx` | 10.2 KB | Top-level Image Processing LAB page and layout. | ImageProcessingLabPage |
| FE | Frontend Pages | `FE:src/Pages/InspectionPage.tsx` | 19.1 KB | TypeScript module/component `InspectionPage`. | NameConfigDropdown, InspectionPage |
| FE | Frontend Pages | `FE:src/Pages/LabView.tsx` | 15.5 KB | Vision LAB launcher and deployed Lab Service hub. | LabView, OutputViewerState |
| FE | Frontend Pages | `FE:src/Pages/MainScreen.tsx` | 6.5 KB | TypeScript module/component `MainScreen`. | MainScreen |
| FE | Frontend Pages | `FE:src/Pages/ProgrammingPage.tsx` | 11.4 KB | TypeScript module/component `ProgrammingPage`. | ProgrammingTab |
| FE | Frontend Pages | `FE:src/Pages/SequencerPage.tsx` | 13.9 KB | TypeScript module/component `SequencerPage`. | SequencerPage |
| FE | Frontend Project / Config | `FE:.gitignore` | 296 B | Project file. |  |
| FE | Frontend Project / Config | `FE:.vscode/extensions.json` | 80 B | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:index.html` | 370 B | Project file. |  |
| FE | Frontend Project / Config | `FE:package-lock.json` | 114.5 KB | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:postcss.config.js` | 90 B | Project file. |  |
| FE | Frontend Project / Config | `FE:src-tauri/.gitignore` | 603 B | Project file. |  |
| FE | Frontend Project / Config | `FE:src-tauri/build.rs` | 39 B | Project file. |  |
| FE | Frontend Project / Config | `FE:src-tauri/capabilities/default.json` | 220 B | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:src-tauri/Cargo.lock` | 119.8 KB | Project file. |  |
| FE | Frontend Project / Config | `FE:src-tauri/Cargo.toml` | 744 B | Project configuration. |  |
| FE | Frontend Project / Config | `FE:src-tauri/gen/schemas/acl-manifests.json` | 67.9 KB | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:src-tauri/gen/schemas/capabilities.json` | 163 B | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:src-tauri/gen/schemas/desktop-schema.json` | 126.1 KB | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:src-tauri/gen/schemas/windows-schema.json` | 126.1 KB | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:src-tauri/icons/icon.icns` | 96.1 KB | Project file. |  |
| FE | Frontend Project / Config | `FE:src-tauri/tauri.conf.json` | 775 B | JSON configuration or package metadata. |  |
| FE | Frontend Project / Config | `FE:tailwind.config.js` | 181 B | Project file. |  |
| FE | Frontend Project / Config | `FE:tsconfig.node.json` | 213 B | JSON configuration or package metadata. |  |
| FE | Frontend Source | `FE:src-tauri/src/lib.rs` | 490 B | Project file. |  |
| FE | Frontend Source | `FE:src-tauri/src/main.rs` | 192 B | Project file. |  |
| FE | Frontend Source | `FE:src/App.css` | 918 B | Project file. |  |
| FE | Frontend Source | `FE:src/App.tsx` | 2.1 KB | TypeScript module/component `App`. |  |
| FE | Frontend Source | `FE:src/Commons/ActionButton.tsx` | 1.2 KB | TypeScript module/component `ActionButton`. | ActionButton, ActionButtonProps |
| FE | Frontend Source | `FE:src/Commons/MiniProgressBar.tsx` | 781 B | TypeScript module/component `MiniProgressBar`. | MiniProgressBar, MiniProgressBarProps |
| FE | Frontend Source | `FE:src/Commons/NeonActionBar.tsx` | 3.4 KB | TypeScript module/component `NeonActionBar`. | ActionItem, NeonActionBar, NeonActionBarProps |
| FE | Frontend Source | `FE:src/Commons/NeonNavBar.tsx` | 2.3 KB | TypeScript module/component `NeonNavBar`. | NavItem, NeonNavbar, NeonNavbarProps |
| FE | Frontend Source | `FE:src/main.tsx` | 248 B | TypeScript module/component `main`. |  |
| FE | Frontend Source | `FE:src/mergify.py` | 2.4 KB | Python module `mergify`. | def minify_python_for_llm |
| FE | Frontend Source | `FE:src/mergify_ts.py` | 2.4 KB | Python module `mergify_ts`. | def minify_python_for_llm |
| FE | Frontend Source | `FE:src/ProjectCompiler/ProjectCompilerCore/ProjectCompilerCore.ts` | 13.8 KB | TypeScript module/component `ProjectCompilerCore`. | Dependencies, WorkerInformation, FleetConfig, UIInformation, SequencerInformation, ProjectBundle, ProjectCompiler |
| FE | Frontend Source | `FE:src/ts_context_for_llm.txt` | 171.9 KB | Project file. |  |
| FE | Frontend Source | `FE:src/tsx_context_for_llm.txt` | 404.2 KB | Project file. |  |
| FE | Frontend Source | `FE:src/UI_Engine/hooks/useKeyboardTrigger.ts` | 2.3 KB | TypeScript module/component `useKeyboardTrigger`. | useKeyboardTrigger |
| FE | Frontend Source | `FE:src/UI_Engine/SequencerComponents/BaseNode.tsx` | 1.9 KB | TypeScript module/component `BaseNode`. | BaseNode, BaseNodeProps |
| FE | Frontend Source | `FE:src/UI_Engine/SequencerComponents/PropertiesSidebar.tsx` | 58.6 KB | TypeScript module/component `PropertiesSidebar`. | PropertiesSidebar |
| FE | Frontend Source | `FE:src/UI_Engine/SequencerComponents/ScriptApiDocs.ts` | 3.2 KB | TypeScript module/component `ScriptApiDocs`. | SCRIPT_API_DOCS_MD |
| FE | Frontend Source | `FE:src/UI_Engine/SequencerComponents/SequencerNodes.tsx` | 28.8 KB | TypeScript module/component `SequencerNodes`. | ProcessNode, SwitchNode, ComputeNode, AndNode, OrNode, DelayNode, TagOverValNode, TagOverTagNode, ExtractJsonNode, BuildJsonNode |
| FE | Frontend Source | `FE:src/UI_Engine/SequencerComponents/TerminalLog.tsx` | 2.5 KB | TypeScript module/component `TerminalLog`. | TerminalLog |
| FE | Frontend Source | `FE:src/UI_Engine/SequencerComponents/TokenBlackboard.tsx` | 8.3 KB | TypeScript module/component `TokenBlackboard`. | TokenBlackboard |
| FE | Frontend Source | `FE:src/UI_Engine/SequencerComponents/TokenLayer.tsx` | 2.2 KB | TypeScript module/component `TokenLayer`. | TokenLayer |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/FileManagerModal.tsx` | 23.3 KB | TypeScript module/component `FileManagerModal`. | FileManagerModal, FileManagerModalProps |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/FloatingPanels.tsx` | 44.8 KB | TypeScript module/component `FloatingPanels`. | UIScriptEditorModal, CreateButtonModal, RenameModal, ActionMenu, UIPropertiesPanel, UIScriptEditorModalProps |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/GlobalTagsTable.tsx` | 17.3 KB | TypeScript module/component `GlobalTagsTable`. | TagManagerTable |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/InspectionCanvas.tsx` | 5.7 KB | TypeScript module/component `InspectionCanvas`. | InspectionCanvas |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/InspectionSidebar.tsx` | 1.6 KB | TypeScript module/component `InspectionSidebar`. | InspectionSidebar |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/InspectionTopbar.tsx` | 11.6 KB | TypeScript module/component `InspectionTopbar`. | InspectionTopbar |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/KonvaNodes.tsx` | 35.3 KB | TypeScript module/component `KonvaNodes`. | SceneNodeRenderer |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineComponents/SettingModal.tsx` | 9.6 KB | TypeScript module/component `SettingModal`. | SettingsModal |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineHelper/useTagHelper.ts` | 285 B | TypeScript module/component `useTagHelper`. | useTagValue, useWriteTag |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineStores/GlobalTagsStore.ts` | 2.3 KB | TypeScript module/component `GlobalTagsStore`. | TagValue, inferTagType, useTagDb, TagDBStore |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineStores/InspectionStore.ts` | 20.9 KB | TypeScript module/component `InspectionStore`. | DrawType, DataBinding, BaseUINode, Screen, Thumbnail, Frame, BoundingBoxNode, TextNode, BoundingCircleNode, LineNode |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineStores/KeyboardTriggerStore.ts` | 2.0 KB | TypeScript module/component `KeyboardTriggerStore`. | TriggerActionType, Shortcut, KeyboardTriggerStore, useKeyboardTriggerStore |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineStores/SequencerEngine.ts` | 51.7 KB | TypeScript module/component `SequencerEngine`. | SequencerEngine, SequencerCompiler, NodeStart, NodeEnd, NodeSplit, NodeJoin, NodeSwitch, NodeCompute, NodeAnd, NodeOR |
| FE | Frontend Source | `FE:src/UI_Engine/UIEngineStores/SequencerStores.ts` | 20.5 KB | TypeScript module/component `SequencerStores`. | OperandType, SequencerNodeType, NodeStartConfig, NodeEndConfig, NodeProcessConfig, NodeSplitConfig, NodeJoinConfig, NodeSwitchConfig, NodeComputeConfig, NodeAndConfig |
| FE | Frontend Source | `FE:src/utils/ColorConst.ts` | 1.0 KB | TypeScript module/component `ColorConst`. | COLOR_PALETTE |
| FE | Frontend Source | `FE:src/utils/FlowCompiler.ts` | 3.1 KB | TypeScript module/component `FlowCompiler`. | FlowCompiler |
| FE | Frontend Source | `FE:src/utils/FlowUtils.ts` | 1.2 KB | TypeScript module/component `FlowUtils`. | getPinColor |
| FE | Frontend Source | `FE:src/utils/imageUtils.ts` | 3.1 KB | TypeScript module/component `imageUtils`. | ImageProcessing |
| FE | Frontend Source | `FE:src/vite-env.d.ts` | 38 B | TypeScript module/component `vite-env.d`. |  |
| FE | Frontend State / Hooks | `FE:src/Stores/DatabaseEngineStore.ts` | 8.1 KB | TypeScript module/component `DatabaseEngineStore`. | DBFilter, ColumnConfig, DBEngineErrorModal, DBImageModal, DatabaseEngineStore, useDBEngineStore |
| FE | Frontend State / Hooks | `FE:src/Stores/FleetDashboardStores.ts` | 24.3 KB | TypeScript module/component `FleetDashboardStores`. | Hardware, DeviceInfo, WorkerInfoCard, LocalServerInfo, FilesState, GraphsState, PluginsState, ActiveLogicsState, ResourceInfo, WorkerDetails |
| FE | Frontend State / Hooks | `FE:src/Stores/FlowStore.tsx` | 19.5 KB | TypeScript module/component `FlowStore`. | NodeKind, DataType, PinManifest, ConfigFieldManifest, BaseManifest, InlineManifest, ObjectManifest, NodeManifest, GraphFile, GraphValidationResult |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx` | 26.4 KB | Standalone filter guide and isolated test playground UI. | FilterGuideModal, Props |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx` | 12.9 KB | Image viewer workbench, upload/run controls and multi-view layout. | ImageWorkbench, Props |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/operatorGuide.ts` | 20.1 KB | Human-readable filter explanations, tuning tips and parameter guidance. | OperatorGuide, buildOperatorGuide |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx` | 7.3 KB | Image Processing LAB operator/filter selector UI. | OperatorLibrary, Props |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/pipelineUtils.ts` | 5.9 KB | Pipeline definition, validation, compilation or graph contracts. | firstEntry, operatorDefaults, isLinearStackOperator, stackCompatibility, validateLinearStack, buildPipelineDefinition, viewerSourcesForStack |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx` | 18.2 KB | TypeScript module/component `ProcessingStack`. | ProcessingStack, Props |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/types.ts` | 1.8 KB | TypeScript module/component `types`. | LabDataType, PortManifest, ParameterManifest, OperatorManifest, StackOperatorInstance, PipelineEndpoint, PipelineConnection, ImagePipelineDefinition, ViewerSource, ViewerPane |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/useImageLabController.ts` | 27.2 KB | Image Processing LAB frontend state/runtime controller. | useImageLabController |
| FE | Frontend Vision LAB Components | `FE:src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx` | 4.2 KB | Reusable zoom/pan raster viewer. | ZoomPanImageView, Props |
| FE | Tools / Updaters | `FE:tools/generate_llm_context_map.py` | 14.9 KB | Generates the full-system LLM context/file inventory. | def git_info, def should_ignore, def collect_files, def classify, def infer_purpose, def python_symbols, def ts_symbols, def symbols_for, def markdown_escape, def human_size |
| FE | Tools / Updaters | `FE:update_image_lab_filter_guide_context_v0050.py` | 120.6 KB | Python module `update_image_lab_filter_guide_context_v0050`. | def resolve_roots, def actual_path, def backup, def replace_state, def create_state, def scan, def preflight, def ensure_readme, def generate_system_map, def apply |
| FE | Tools / Updaters | `FE:update_image_processing_lab_advanced_raster_v0030.py` | 91.8 KB | Python module `update_image_processing_lab_advanced_raster_v0030`. | def resolve_backend, def backup, def patch_registry, def patch_loader, def scan, def apply, def verify, def main |
| FE | Tools / Updaters | `FE:update_image_processing_lab_frontend_v001.py` | 74.1 KB | Python module `update_image_processing_lab_frontend_v001`. | def dedent, def sha256_text, def discover_project, def patch_main_screen, def patch_app, def generated_status, def backup_files, def scan, def apply, def verify |
| FE | Tools / Updaters | `FE:update_image_processing_lab_frontend_v0011_uploadfix.py` | 6.5 KB | Python module `update_image_processing_lab_frontend_v0011_uploadfix`. | def find_root, def api_path, def status, def scan, def apply, def verify, def main |
| FE | Tools / Updaters | `FE:update_image_processing_lab_raw_upload_v0012.py` | 11.0 KB | Python module `update_image_processing_lab_raw_upload_v0012`. | def find_frontend, def find_backend, def replace_exact, def scan, def apply, def verify, def main |
| FE | Tools / Updaters | `FE:update_image_processing_lab_ui_operators_v0020.py` | 80.8 KB | Python module `update_image_processing_lab_ui_operators_v0020`. | def resolve_roots, def patch_operator_loader, def backup, def scan, def apply, def verify, def main |
| FE | Tools / Updaters | `FE:update_image_processing_lab_upload_transport_v0013.py` | 8.7 KB | Python module `update_image_processing_lab_upload_transport_v0013`. | def resolve_roots, def backup, def patch_frontend, def patch_backend, def scan, def apply, def verify, def main |
| FE | Tools / Updaters | `FE:update_image_processing_lab_view_state_v0022.py` | 14.1 KB | Python module `update_image_processing_lab_view_state_v0022`. | def resolve_frontend, def backup, def patch_zoom_view, def patch_workbench, def scan, def apply, def verify, def main |
| FE | Tools / Updaters | `FE:update_image_processing_lab_viewer_ux_v0021.py` | 74.7 KB | Python module `update_image_processing_lab_viewer_ux_v0021`. | def resolve_roots, def backup, def patch_enum_spec, def scan, def apply, def verify, def main |
| FE | Tools / Updaters | `FE:update_lab_service_foundation_v0040.py` | 146.1 KB | Python module `update_lab_service_foundation_v0040`. | def resolve_roots, def patch_router, def preflight_frontend, def backup, def file_status, def scan, def apply, def _backend_smoke, def _typescript_syntax_check, def verify |
| FE | Tools / Updaters | `FE:update_lab_service_multi_edit_v0041.py` | 186.6 KB | Python module `update_lab_service_multi_edit_v0041`. | def resolve_roots, def resolve_path, def backup, def classify_file, def preflight, def scan, def apply, def typescript_syntax_check, def backend_smoke, def verify |

## File-extension summary

| Extension | Files |
| --- | ---: |
| `.ax` | 2 |
| `.css` | 1 |
| `.cti` | 6 |
| `.dll` | 94 |
| `.html` | 1 |
| `.icns` | 1 |
| `.ico` | 1 |
| `.ini` | 1 |
| `.jpg` | 36 |
| `.js` | 2 |
| `.json` | 12 |
| `.lock` | 1 |
| `.manifest` | 2 |
| `.md` | 5 |
| `.npz` | 825 |
| `.png` | 14 |
| `.py` | 122 |
| `.rs` | 3 |
| `.spec` | 1 |
| `.svg` | 3 |
| `.toml` | 1 |
| `.ts` | 27 |
| `.tsx` | 58 |
| `.txt` | 7 |
| `<none>` | 4 |
