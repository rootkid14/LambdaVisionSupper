# Lambda Vision — System Architecture

> Project-aware architecture snapshot generated from the current source tree.

## 1. High-level architecture

Lambda Vision contains a legacy automation runtime plus specialized Vision LAB execution domains:

```text
Frontend / Desktop
│
├─ App Builder / Sequencer UI ───────────────┐
│                                             ▼
│                                  Legacy Graph Runtime
│                                  BaseNode / NODE_REGISTRY
│                                  LogicObject / LogicPoolManager
│
├─ Computer Vision Program ──────────────────┐
│    I/O / Master Sample / Stations            ▼
│                                      Vision Program Runtime
│                                      LabServiceRuntime calls
│
├─ Vision LAB Hub
│    ├─ Image Processing LAB ────────────────┐
│    │                                       ▼
│    │                              Image LAB Session/Runtime
│    │                              ImageOperator Registry
│    │
│    ├─ Contour Extractor LAB ──────────────┐
│    │                                       ▼
│    │                              ContourStore / filter funnel
│    │                              meaningful ContourSet
│    │
│    ├─ Sampling LAB ───────────────────────┐
│    │                                       ▼
│    │                              SamplingGeometryRuntime
│    │                              Spatial Units / Spectral
│    │
│    └─ Lab Services ────────────────────────┐
│                                            ▼
│                                   LabServiceRuntime
│                                   versioned LAB snapshots
│
├─ Fleet / Resource UI ───────────── Device/Infrastructure Backend
└─ Database UI ───────────────────── Database Backend
```

## 2. Architectural invariants

1. **General automation and Vision LAB are deliberately separate abstractions.**
   Legacy automation uses `BaseNode`; Image Processing uses `ImageOperator`.
2. **Image Processing LAB is raster-centric.** Operators should not know master/query, inspection spec, station OK/NG, or alignment semantics.
3. **Lab Service is the reusable callable boundary.** A service is a versioned LAB pipeline snapshot with typed inputs and named outputs.
4. **Computer Vision is an orchestration/application layer.** IOT and Camera are shared declared resources; each Workspace is an independent inspection program with its own Master image, ROIs/locator, Working scopes and runtime/debug context. No workspace may inherit another workspace's inspection state. Automation IDE is the glue plane over typed endpoints and must not absorb LAB algorithms.
5. **Interactive LAB sessions and deployed services are different lifecycles.** Interactive sessions optimize editing/tuning; deployed services optimize stable invocation.
6. **Future cross-LAB composition should use explicit typed contracts/adapters**, not implicit imports between specialized internals.

## 3. Execution flows

### Image Processing LAB

```text
ImageProcessingLabPage
  → useImageLabController
  → imageLabApi
  → /api/v1/image-lab
  → ImageLabSessionManager / ImageLabSession
  → ImagePipelineRuntime
  → ImageOperatorRegistry
  → raster operators
```

### Contour Extractor LAB

```text
ContourExtractorLabPage
  → contourExtractorApi
  → /api/v1/contour-extractor
  → candidate generation
  → DEFAULT BASE MEMORY FILTER (reject coordinates before store)
  → ContourStore (single geometry copy + stable contour IDs)
  → registered discovery stages (metric/region/shape/Fourier/master)
  → lazy metrics + selected geometry inspection
  → meaningful ContourSet
```

### Sampling LAB

```text
SamplingGeometryLabPage
  → useSamplingProgramController
  → one inspected image / optional Image Processing Service
  → GLOBAL domain: whole-image Histogram / Statistics / Rays / Cross / Rings
  → LOCAL domain: Patch Grid → same reusable method recipe per patch
  → placement: patch/base center or auto-arranged center grid
  → channels: Gray/RGB/HSV/LAB → measures: profile/histogram/mean/std/min/max/median
  → Output Formulation Workspace: final Vector or 2-D Matrix
  → SamplingProgramRuntime.sample → cached Data Blocks
  → SamplingProgramRuntime.formulate → Vector / 2-D Matrix Lab Service outputs
  → FFT/frequency transforms intentionally out of current editor scope
```

### Computer Vision Program

```text
MainScreen → /computer-vision
  → ComputerVisionPage
  → visionAppApi
  → /api/v1/computer-vision
  → VisionProgramRepository
  → IOT Declaration Engine: declare multiple Modbus TCP devices + aliased points
  → Camera: Manual / Basler pypylon / generic HTTP capture + focus URL
  → Trigger runner: rising edge → capture → inspect → pulse OK/NG
  → Master Sample: one locator family for all ROI/stations + blur preview
  → Global Scope: expandable Filter stack → expandable Logic stack
  → ROI location runs on the globally filtered image (master filtered equivalently)
  → Local station scopes: Filter → Logic; sequential or parallel
  → VisionRunSnapshot freezes Global/ROI Logic outputs for one run
  → Endpoint Registry builds a live object graph from draft declarations: device.<alias>.<point>, vision.roi.<alias>.logic.<alias>, system, camera
  → Declared object roots exist before runtime; VisionRunSnapshot enriches them with actual output leaves/values
  → Camera Declaration Engine: Basler / HTTP cameras expose capture, stream slots and custom APIs
  → Workspaces: multiple independent Master/Working contexts; each workspace binds exactly one declared camera
  → Automation IDE: colored safe-DSL editor + registry-backed dot completion + hierarchical Object/Endpoint Explorer
  → Keyboard object: keyboard.space / enter / escape / arrows / F1-F12 are live ON/OFF endpoints
  → Online/Offline: arm/disarm all Loop/Event automation at program level; simulator drivers remain legacy-hidden
  → Event lifecycle: system.run_started → vision.logic_ready → system.commit_result → system.run_finish
  → Dry Run suppresses physical side effects; Execution Trace records endpoint reads/actions/writes
  → legacy v2 Decision DSL remains runtime-compatible but is not the new decision/glue path
  → unified Debug Stack Workspace: lazy image artifacts + Logic outputs + benchmark trace
```

### Lab Service

```text
LabView / Image LAB deploy UI
  → labServiceApi
  → /api/v1/lab-services
  → LabServiceRepository (versions/snapshots)
  → LabServiceRuntime
  → current LAB adapter (Image Processing today)
  → named service outputs
```

### Legacy App Builder / Sequencer

```text
Programming/Sequencer UI
  → nodeApi / graph API
  → NODE_REGISTRY / BaseNode
  → LogicObject graph
  → LogicPoolManager
  → registered Nodes / devices / actions
```

## 4. Detected modules

### Computer Vision Program Backend / Control Mapper / Camera / Working Pipeline

Persisted Vision Programs, Modbus trigger/result, Basler/URL camera acquisition, automatic trigger runner, program-wide ROI locator, Filter→Logic→Decision scope runtime, debug image store and per-step benchmarks.

- Detected files: **36**
- Boundary: Owns production-program orchestration only. Image Processing services form sequential filter stacks; logic services are independent extractors; a restricted decision DSL produces scope OK/NG. ROI stations may run sequentially or in parallel. Future Rule/AI services can replace/extend the built-in decision frame.
- Key files:
  - `BE:app/services/vision_app/repository.py` — Saved Image LAB pipeline persistence.
  - `BE:app/services/vision_app/runtime.py` — Image LAB artifact cache and pipeline runtime.
  - `BE:app/api/v1/endpoints/vision_app_api.py` — Persisted Vision Programs, Modbus trigger/result, Basler/URL camera acquisition, automatic trigger runner, program-wide ROI locator, Filter→Logic→Decision scope runtime, debug image store and per-step benchmarks.
  - `BE:app/services/vision_app/__init__.py` — Persisted Vision Programs, Modbus trigger/result, Basler/URL camera acquisition, automatic trigger runner, program-wide ROI locator, Filter→Logic→Decision scope runtime, debug image store and per-step benchmarks.
  - `BE:app/services/vision_app/automation_manager.py` — Persisted Vision Programs, Modbus trigger/result, Basler/URL camera acquisition, automatic trigger runner, program-wide ROI locator, Filter→Logic→Decision scope runtime, debug image store and per-step benchmarks.
  - `BE:app/services/vision_app/automation_models.py` — Persisted Vision Programs, Modbus trigger/result, Basler/URL camera acquisition, automatic trigger runner, program-wide ROI locator, Filter→Logic→Decision scope runtime, debug image store and per-step benchmarks.
  - `BE:app/services/vision_app/automation_runtime.py` — Persisted Vision Programs, Modbus trigger/result, Basler/URL camera acquisition, automatic trigger runner, program-wide ROI locator, Filter→Logic→Decision scope runtime, debug image store and per-step benchmarks.
  - `BE:app/services/vision_app/camera_resource_runtime.py` — Persisted Vision Programs, Modbus trigger/result, Basler/URL camera acquisition, automatic trigger runner, program-wide ROI locator, Filter→Logic→Decision scope runtime, debug image store and per-step benchmarks.

### Computer Vision Program UI

Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.

- Detected files: **19**
- Boundary: Computer Vision is the production orchestration layer. v0.14.1 keeps each Workspace fully independent: its own IOT declarations, Camera declarations/binding, Master/ROI, Working scopes and backend stream/Soft Trigger. Basler stream identity is workspace-scoped, browser preview is lazy, and no hardware/runtime resource may fall back to another Workspace.
- Key files:
  - `FE:src/Pages/ComputerVisionPage.tsx` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.
  - `FE:src/api/visionAppApi.ts` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.
  - `FE:src/components/ComputerVision/AutomationCodeEditor.tsx` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.
  - `FE:src/components/ComputerVision/AutomationIdeWorkspace.tsx` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.
  - `FE:src/components/ComputerVision/CameraDeclarationWorkspace.tsx` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.
  - `FE:src/components/ComputerVision/CameraModulePanel.tsx` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.
  - `FE:src/components/ComputerVision/ComputerVision.css` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.
  - `FE:src/components/ComputerVision/DebugWorkspace.tsx` — Production Computer Vision application with v0.14.1 strict Workspace ownership: each Workspace owns IOT declarations, Camera declarations/binding, Master/ROI, Working scopes, Streaming/Soft Trigger and run/debug context; typed dynamic Endpoint Registry and Automation IDE project only the active Workspace resources.

### Contour Extractor LAB Backend

Early-filtered contour candidate runtime with single-copy ContourStore, ID-only stage selections, extensible contour-stage registry, Fourier descriptors/reconstruction, lazy geometry access, sessions, and REST API.

- Detected files: **8**
- Boundary: Contour geometry is stored once; the mandatory memory gate discards junk coordinates before the store, while registered filter/shape stages retain contour IDs rather than cloning geometry.
- Key files:
  - `BE:app/services/vision_labs/contour_extractor/runtime.py` — Image LAB artifact cache and pipeline runtime.
  - `BE:app/api/v1/endpoints/contour_extractor_api.py` — Early-filtered contour candidate runtime with single-copy ContourStore, ID-only stage selections, extensible contour-stage registry, Fourier descriptors/reconstruction, lazy geometry access, sessions, and REST API.
  - `BE:app/services/vision_labs/contour_extractor/__init__.py` — Early-filtered contour candidate runtime with single-copy ContourStore, ID-only stage selections, extensible contour-stage registry, Fourier descriptors/reconstruction, lazy geometry access, sessions, and REST API.
  - `BE:app/services/vision_labs/contour_extractor/fourier.py` — Early-filtered contour candidate runtime with single-copy ContourStore, ID-only stage selections, extensible contour-stage registry, Fourier descriptors/reconstruction, lazy geometry access, sessions, and REST API.
  - `BE:app/services/vision_labs/contour_extractor/models.py` — Lab Service typed deploy/run contracts.
  - `BE:app/services/vision_labs/contour_extractor/session.py` — Interactive Image LAB session, preview, realtime and session management.
  - `BE:app/services/vision_labs/contour_extractor/stage_registry.py` — Early-filtered contour candidate runtime with single-copy ContourStore, ID-only stage selections, extensible contour-stage registry, Fourier descriptors/reconstruction, lazy geometry access, sessions, and REST API.
  - `BE:app/services/vision_labs/contour_extractor/store.py` — Early-filtered contour candidate runtime with single-copy ContourStore, ID-only stage selections, extensible contour-stage registry, Fourier descriptors/reconstruction, lazy geometry access, sessions, and REST API.

### Contour Extractor LAB UI

Contour discovery workbench: mandatory early memory gate, single-copy ContourStore, extensible registered filter/shape stages, lazy geometry inspection, Fourier/master-shape analysis, and Contour Extractor service deployment.

- Detected files: **6**
- Boundary: Owns contour discovery/selection. Cheap memory gates run before retained geometry; advanced registered stages (including Fourier/master-shape primitives) operate on stable contour IDs and produce meaningful ContourSets rather than arbitrary measurements.
- Key files:
  - `FE:src/Pages/ContourExtractorGuideModal.tsx` — Contour discovery workbench: mandatory early memory gate, single-copy ContourStore, extensible registered filter/shape stages, lazy geometry inspection, Fourier/master-shape analysis, and Contour Extractor service deployment.
  - `FE:src/Pages/ContourExtractorLabPage.tsx` — Contour discovery workbench: mandatory early memory gate, single-copy ContourStore, extensible registered filter/shape stages, lazy geometry inspection, Fourier/master-shape analysis, and Contour Extractor service deployment.
  - `FE:src/Pages/ContourFourierInspector.tsx` — Contour discovery workbench: mandatory early memory gate, single-copy ContourStore, extensible registered filter/shape stages, lazy geometry inspection, Fourier/master-shape analysis, and Contour Extractor service deployment.
  - `FE:src/Pages/ContourStageGuideModal.tsx` — Contour discovery workbench: mandatory early memory gate, single-copy ContourStore, extensible registered filter/shape stages, lazy geometry inspection, Fourier/master-shape analysis, and Contour Extractor service deployment.
  - `FE:src/Pages/ContourStageLibrary.tsx` — Contour discovery workbench: mandatory early memory gate, single-copy ContourStore, extensible registered filter/shape stages, lazy geometry inspection, Fourier/master-shape analysis, and Contour Extractor service deployment.
  - `FE:src/api/contourExtractorApi.ts` — Contour discovery workbench: mandatory early memory gate, single-copy ContourStore, extensible registered filter/shape stages, lazy geometry inspection, Fourier/master-shape analysis, and Contour Extractor service deployment.

### Image Processing LAB Backend

ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API.

- Detected files: **13**
- Boundary: Pure raster processing. Registration/comparison/inspection semantics belong in other LABs.
- Key files:
  - `BE:app/services/vision_labs/image/pipeline.py` — Image LAB pipeline schema, validation, compilation, and graph contracts.
  - `BE:app/services/vision_labs/image/repository.py` — Saved Image LAB pipeline persistence.
  - `BE:app/services/vision_labs/image/runtime.py` — Image LAB artifact cache and pipeline runtime.
  - `BE:app/api/v1/endpoints/image_lab_api.py` — Image LAB session/pipeline/operator REST and WebSocket API.
  - `BE:app/services/vision_labs/image/__init__.py` — ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API.
  - `BE:app/services/vision_labs/image/operator.py` — ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API.
  - `BE:app/services/vision_labs/image/operators/__init__.py` — ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API.
  - `BE:app/services/vision_labs/image/operators/advanced_families.py` — ImageFrame/BinaryMask types, ImageOperator registry, pipeline validation/compiler, runtime artifact cache, sessions, operators, repository, and Image LAB REST/WebSocket API.

### Sampling LAB Backend

SamplingProgram v2 runtime with explicit Sample → cached Data Blocks → Formulate separation. Global whole-image and Local patch-grid methods produce semantic blocks; formulation rearranges cached blocks into a Vector or 2-D Matrix without re-sampling. Representation LAB owns future tensor-depth/channel stacking. Legacy v0.1-v0.5 runtimes remain for deployed snapshots.

- Detected files: **20**
- Boundary: Feature-extraction backbone. The new domain model is Image → Global/Local domain → placement/sampling shape → channels → measures → composed numerical shape. It does not own contour selection, frequency-domain transforms, OK/NG, or model training semantics.
- Key files:
  - `BE:app/services/vision_labs/sampling_geometry/pipeline.py` — Image LAB pipeline schema, validation, compilation, and graph contracts.
  - `BE:app/services/vision_labs/sampling_geometry/repository.py` — Saved Image LAB pipeline persistence.
  - `BE:app/services/vision_labs/sampling_geometry/runtime.py` — Image LAB artifact cache and pipeline runtime.
  - `BE:app/api/v1/endpoints/sampling_geometry_api.py` — SamplingProgram v2 runtime with explicit Sample → cached Data Blocks → Formulate separation. Global whole-image and Local patch-grid methods produce semantic blocks; formulation rearranges cached blocks into a Vector or 2-D Matrix without re-sampling. Representation LAB owns future tensor-depth/channel stacking. Legacy v0.1-v0.5 runtimes remain for deployed snapshots.
  - `BE:app/services/vision_labs/sampling_geometry/__init__.py` — SamplingProgram v2 runtime with explicit Sample → cached Data Blocks → Formulate separation. Global whole-image and Local patch-grid methods produce semantic blocks; formulation rearranges cached blocks into a Vector or 2-D Matrix without re-sampling. Representation LAB owns future tensor-depth/channel stacking. Legacy v0.1-v0.5 runtimes remain for deployed snapshots.
  - `BE:app/services/vision_labs/sampling_geometry/operator.py` — SamplingProgram v2 runtime with explicit Sample → cached Data Blocks → Formulate separation. Global whole-image and Local patch-grid methods produce semantic blocks; formulation rearranges cached blocks into a Vector or 2-D Matrix without re-sampling. Representation LAB owns future tensor-depth/channel stacking. Legacy v0.1-v0.5 runtimes remain for deployed snapshots.
  - `BE:app/services/vision_labs/sampling_geometry/operators/__init__.py` — SamplingProgram v2 runtime with explicit Sample → cached Data Blocks → Formulate separation. Global whole-image and Local patch-grid methods produce semantic blocks; formulation rearranges cached blocks into a Vector or 2-D Matrix without re-sampling. Representation LAB owns future tensor-depth/channel stacking. Legacy v0.1-v0.5 runtimes remain for deployed snapshots.
  - `BE:app/services/vision_labs/sampling_geometry/operators/common.py` — SamplingProgram v2 runtime with explicit Sample → cached Data Blocks → Formulate separation. Global whole-image and Local patch-grid methods produce semantic blocks; formulation rearranges cached blocks into a Vector or 2-D Matrix without re-sampling. Representation LAB owns future tensor-depth/channel stacking. Legacy v0.1-v0.5 runtimes remain for deployed snapshots.

### Image Processing LAB UI

Interactive raster-processing editor: operator library, stack, viewers, Live/Manual execution, filter playground, and Image LAB API client.

- Detected files: **11**
- Boundary: Edits ImagePipelineDefinition and talks to Image LAB sessions. It must not inherit or depend on legacy BaseNode/Sequencer semantics.
- Key files:
  - `FE:src/Pages/ImageProcessingLabPage.tsx` — Top-level Image Processing LAB page/layout.
  - `FE:src/api/imageLabApi.ts` — Frontend Image LAB REST/WebSocket API client.
  - `FE:src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx` — Standalone filter documentation and isolated test playground.
  - `FE:src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx` — Image LAB upload/run/viewer workbench.
  - `FE:src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx` — Image LAB operator selector and per-filter guide launcher.
  - `FE:src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx` — Image LAB stack editor, ordering, parameters, and exposed service outputs.
  - `FE:src/components/VisionLabs/ImageProcessing/ZoomPanImageView.tsx` — Reusable zoom/pan/fullscreen raster viewer.
  - `FE:src/components/VisionLabs/ImageProcessing/operatorGuide.ts` — Filter explanations, tuning guidance, and parameter help.

### Lab Service Backend

Versioned deployable LAB snapshots, repository, generic runtime facade, run store, pruning, and Lab Service REST API.

- Detected files: **5**
- Boundary: LabServiceRuntime is the future callable boundary for Dataset/Sampling/Sequencer/Agentic integrations; callers should not duplicate LAB execution logic.
- Key files:
  - `BE:app/services/vision_labs/service/repository.py` — Versioned Lab Service persistence.
  - `BE:app/services/vision_labs/service/runtime.py` — Lab Service runtime/pruning/run store.
  - `BE:app/api/v1/endpoints/lab_service_api.py` — Versioned Lab Service deploy/run/preview REST API.
  - `BE:app/services/vision_labs/service/__init__.py` — Versioned deployable LAB snapshots, repository, generic runtime facade, run store, pruning, and Lab Service REST API.
  - `BE:app/services/vision_labs/service/models.py` — Lab Service typed deploy/run contracts.

### Sampling LAB UI

Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.

- Detected files: **16**
- Boundary: Consumes one inspected raster source directly or through Image Processing Lab Services. SamplingProgram v2 semantics are Global/Local sampling → semantic Data Blocks → cached formulation as Vector or 2-D Matrix; FFT/frequency transforms and tensor-depth semantics are intentionally out of editor scope. Legacy v0.1-v0.5 snapshots remain runtime-compatible.
- Key files:
  - `FE:src/Pages/SamplingGeometryLabPage.tsx` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.
  - `FE:src/api/samplingGeometryApi.ts` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.
  - `FE:src/components/VisionLabs/SamplingGeometry/ArtifactInspectorModal.tsx` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.
  - `FE:src/components/VisionLabs/SamplingGeometry/DataLayoutComposer.tsx` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.
  - `FE:src/components/VisionLabs/SamplingGeometry/SamplingCanvas.tsx` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.
  - `FE:src/components/VisionLabs/SamplingGeometry/SamplingGuideModal.tsx` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.
  - `FE:src/components/VisionLabs/SamplingGeometry/SamplingOperatorLibrary.tsx` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.
  - `FE:src/components/VisionLabs/SamplingGeometry/SamplingParameterHelpModal.tsx` — Hierarchical Global/Local Sampling Program editor: whole-image measurements, patch-grid local recipes, spatial sampling shapes, channel/measure configuration, image-grounded teaching, and cached Output Formulation Workspace for final vectors or 2-D matrices. Tensor depth/channel stacking is delegated to Representation LAB.

### Vision LAB Core Contracts

LAB-level shared port/parameter specifications and common Vision LAB package contracts.

- Detected files: **3**
- Boundary: Common LAB vocabulary only; specialized LABs keep specialized domain models.
- Key files:
  - `BE:app/services/vision_labs/__init__.py` — LAB-level shared port/parameter specifications and common Vision LAB package contracts.
  - `BE:app/services/vision_labs/core/__init__.py` — LAB-level shared port/parameter specifications and common Vision LAB package contracts.
  - `BE:app/services/vision_labs/core/specs.py` — LAB-level shared port/parameter specifications and common Vision LAB package contracts.

### Lab Service Hub UI

Deployed/versioned Lab Service cards, manual runner, edit navigation, and Lab Service API client.

- Detected files: **2**
- Boundary: Consumes the generic Lab Service contract; currently Image Processing is the first runtime adapter.
- Key files:
  - `FE:src/Pages/LabView.tsx` — Vision LAB launcher and deployed Lab Service hub/manual runner.
  - `FE:src/api/labServiceApi.ts` — Frontend Lab Service API client.

### App Builder / Sequencer UI

Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.

- Detected files: **30**
- Boundary: This is the general automation/agentic graph system. Keep its node model separate from Vision LAB ImageOperator.
- Key files:
  - `FE:src/Pages/ProgrammingPage.tsx` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.
  - `FE:src/Pages/SequencerPage.tsx` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.
  - `FE:src/Stores/FlowStore.tsx` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.
  - `FE:src/UI_Engine/SequencerComponents/BaseNode.tsx` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.
  - `FE:src/UI_Engine/SequencerComponents/PropertiesSidebar.tsx` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.
  - `FE:src/UI_Engine/SequencerComponents/ScriptApiDocs.ts` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.
  - `FE:src/UI_Engine/SequencerComponents/SequencerNodes.tsx` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.
  - `FE:src/UI_Engine/SequencerComponents/TerminalLog.tsx` — Legacy/general automation graph editor, programming nodes, sequencer compiler/runtime UI, flow state, and node API client.

### Legacy App Builder / Sequencer Runtime

General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes.

- Detected files: **34**
- Boundary: Do not make Vision LAB ImageOperator inherit BaseNode. Integration should occur through explicit adapters/services.
- Key files:
  - `BE:app/services/LogicObjects.py` — Legacy compiled graph execution object.
  - `BE:app/services/LogicPoolManager.py` — Legacy deployed graph/LogicObject pool and execution lifecycle.
  - `BE:app/services/node_registry.py` — Legacy BaseNode/NODE_REGISTRY contract and node registration.
  - `BE:app/api/v1/endpoints/graph_api.py` — Legacy App Builder/Sequencer graph deployment and execution API.
  - `BE:app/schemas/graph.py` — General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes.
  - `BE:app/services/LVSTypes.py` — Legacy sequencer/node UI/runtime type definitions.
  - `BE:app/services/Nodes/CallAPINode.py` — General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes.
  - `BE:app/services/Nodes/ComparativeNodes.py` — General automation graph runtime built around BaseNode/NODE_REGISTRY, LogicObject, LogicPoolManager, graph API, and registered Nodes.

### Backend Application Shell & API Router

FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition.

- Detected files: **5**
- Boundary: Composes feature routers; feature execution belongs to domain services.
- Key files:
  - `BE:app/main.py` — FastAPI backend bootstrap/entry point.
  - `BE:app/api/root_api.py` — FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition.
  - `BE:app/api/v1/api.py` — FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition.
  - `BE:app/api/v1/endpoints/utils.py` — FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition.
  - `BE:app/core/config.py` — FastAPI application/bootstrap, shared configuration, root health/proxy endpoints, and v1 router composition.

### Frontend Application Shell & Routing

React/Vite application entry points, global routes, and the main navigation/home surface.

- Detected files: **4**
- Boundary: Owns navigation/composition only; domain logic should remain in the feature modules.
- Key files:
  - `FE:src/App.tsx` — Frontend route composition / application shell.
  - `FE:src/App.css` — Frontend route composition / application shell.
  - `FE:src/Pages/MainScreen.tsx` — React/Vite application entry points, global routes, and the main navigation/home surface.
  - `FE:src/main.tsx` — Frontend bootstrap entry point.

### Inspection UI Engine

Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.

- Detected files: **16**
- Boundary: UI-engine state/canvas layer; treat separately from the Vision LAB editor unless an explicit adapter is introduced.
- Key files:
  - `FE:src/Pages/InspectionPage.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.
  - `FE:src/UI_Engine/UIEngineComponents/FileManagerModal.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.
  - `FE:src/UI_Engine/UIEngineComponents/FloatingPanels.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.
  - `FE:src/UI_Engine/UIEngineComponents/GlobalTagsTable.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.
  - `FE:src/UI_Engine/UIEngineComponents/InspectionCanvas.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.
  - `FE:src/UI_Engine/UIEngineComponents/InspectionSidebar.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.
  - `FE:src/UI_Engine/UIEngineComponents/InspectionTopbar.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.
  - `FE:src/UI_Engine/UIEngineComponents/KonvaNodes.tsx` — Inspection canvas, floating panels, tags, UI-engine stores, keyboard triggers, and inspection-oriented Konva UI.

### Database Backend

Database CRUD/query API and database manager.

- Detected files: **2**
- Key files:
  - `BE:app/api/v1/endpoints/db_api.py` — Database CRUD/query API and database manager.
  - `BE:app/services/DatabaseManager.py` — Database access and dynamic table management.

### Database UI

Database page, table/query panels and grids, database store, and database API client.

- Detected files: **6**
- Key files:
  - `FE:src/Pages/DatabasePage.tsx` — Database page, table/query panels and grids, database store, and database API client.
  - `FE:src/Stores/DatabaseEngineStore.ts` — Database page, table/query panels and grids, database store, and database API client.
  - `FE:src/api/dbEngineApi.ts` — Database page, table/query panels and grids, database store, and database API client.
  - `FE:src/components/DataBaseEngine/DBModals.tsx` — Database page, table/query panels and grids, database store, and database API client.
  - `FE:src/components/DataBaseEngine/DBPanels.tsx` — Database page, table/query panels and grids, database store, and database API client.
  - `FE:src/components/DataBaseEngine/DBResultGrid.tsx` — Database page, table/query panels and grids, database store, and database API client.

### Fleet / Device / Infrastructure Backend

Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.

- Detected files: **12**
- Key files:
  - `BE:app/api/v1/endpoints/infra_api.py` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.
  - `BE:app/external_libs/MvImport/CameraParams_const.py` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.
  - `BE:app/external_libs/MvImport/CameraParams_header.py` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.
  - `BE:app/external_libs/MvImport/MvCameraControl_class.py` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.
  - `BE:app/external_libs/MvImport/MvErrorDefine_const.py` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.
  - `BE:app/external_libs/MvImport/MvISPErrorDefine_const.py` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.
  - `BE:app/external_libs/MvImport/PixelType_header.py` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.
  - `BE:app/external_libs/MvImport/Runtime/x64/CommonParameters.ini` — Infrastructure APIs, device/resource pools, connection bus, camera integration, and vendor camera SDK bindings.

### Fleet / Resource UI

Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.

- Detected files: **7**
- Key files:
  - `FE:src/Pages/FleetDashboard.tsx` — Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.
  - `FE:src/Stores/FleetDashboardStores.ts` — Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.
  - `FE:src/api/fleetApi.ts` — Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.
  - `FE:src/components/Fleet/FleetCards.tsx` — Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.
  - `FE:src/components/Fleet/FleetModals.tsx` — Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.
  - `FE:src/components/Fleet/PoolsDrawer.tsx` — Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.
  - `FE:src/components/Fleet/PoolsDrawerTabs.tsx` — Resource/device dashboard, fleet cards/modals, resource pools, frontend fleet store, and fleet API client.

### Project Compiler

Frontend project/compiler utilities used to transform or package project definitions.

- Detected files: **1**
- Key files:
  - `FE:src/ProjectCompiler/ProjectCompilerCore/ProjectCompilerCore.ts` — Frontend project/compiler utilities used to transform or package project definitions.

### Shared Backend Utilities

Generic file/image/network helpers shared by backend domains.

- Detected files: **3**
- Key files:
  - `BE:app/services/utils/files_loader.py` — Generic file/image/network helpers shared by backend domains.
  - `BE:app/services/utils/image_utils.py` — Generic file/image/network helpers shared by backend domains.
  - `BE:app/services/utils/ping_measurer.py` — Generic file/image/network helpers shared by backend domains.

### Shared Frontend UI & Utilities

Reusable navigation/action UI and generic frontend utilities shared by feature modules.

- Detected files: **6**
- Key files:
  - `FE:src/Commons/ActionButton.tsx` — Reusable navigation/action UI and generic frontend utilities shared by feature modules.
  - `FE:src/Commons/MiniProgressBar.tsx` — Reusable navigation/action UI and generic frontend utilities shared by feature modules.
  - `FE:src/Commons/NeonActionBar.tsx` — Reusable navigation/action UI and generic frontend utilities shared by feature modules.
  - `FE:src/Commons/NeonNavBar.tsx` — Reusable navigation/action UI and generic frontend utilities shared by feature modules.
  - `FE:src/utils/ColorConst.ts` — Reusable navigation/action UI and generic frontend utilities shared by feature modules.
  - `FE:src/utils/imageUtils.ts` — Reusable navigation/action UI and generic frontend utilities shared by feature modules.

### Desktop / Tauri Host

Rust/Tauri desktop shell and its hand-authored configuration.

- Detected files: **6**
- Key files:
  - `FE:src-tauri/Cargo.toml` — Rust/Tauri desktop shell and its hand-authored configuration.
  - `FE:src-tauri/build.rs` — Rust/Tauri desktop shell and its hand-authored configuration.
  - `FE:src-tauri/capabilities/default.json` — Rust/Tauri desktop shell and its hand-authored configuration.
  - `FE:src-tauri/src/lib.rs` — Rust/Tauri desktop shell and its hand-authored configuration.
  - `FE:src-tauri/src/main.rs` — Frontend bootstrap entry point.
  - `FE:src-tauri/tauri.conf.json` — Rust/Tauri desktop shell and its hand-authored configuration.

### Backend Tests

Regression and integration tests.

- Detected files: **13**
- Key files:
  - `BE:tests/vision_labs/contour_extractor/test_contour_extractor_v0100.py` — Regression and integration tests.
  - `BE:tests/vision_labs/contour_extractor/test_contour_extractor_v0200.py` — Regression and integration tests.
  - `BE:tests/vision_labs/image/test_image_lab_advanced_raster.py` — Regression and integration tests.
  - `BE:tests/vision_labs/image/test_image_lab_basic_families.py` — Regression and integration tests.
  - `BE:tests/vision_labs/image/test_image_lab_core.py` — Regression and integration tests.
  - `BE:tests/vision_labs/image/test_image_lab_enum_coercion.py` — Regression and integration tests.
  - `BE:tests/vision_labs/sampling_geometry/test_sampling_geometry_lab_v0100.py` — Regression and integration tests.
  - `BE:tests/vision_labs/sampling_geometry/test_sampling_geometry_lab_v0200.py` — Regression and integration tests.

### Backend Tools / Updaters

Backend-side updater and maintenance scripts.

- Detected files: **1**
- Key files:
  - `BE:update_image_processing_lab_backend_v001.py` — Backend-side updater and maintenance scripts.

### Frontend Tools & LLM Context Docs

Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.

- Detected files: **72**
- Key files:
  - `FE:docs/llm_context/README.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.
  - `FE:docs/llm_context/SYSTEM_ARCHITECTURE.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.
  - `FE:docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.
  - `FE:docs/llm_context/SYSTEM_CONTEXT_INDEX.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.
  - `FE:docs/llm_context/SYSTEM_FILE_MAP.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.
  - `FE:docs/llm_context/updates/v0041_lab_service_multi_edit.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.
  - `FE:docs/llm_context/updates/v0050_filter_guide_system_map.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.
  - `FE:docs/llm_context/updates/v0060_context_generator_v2.md` — Updater scripts, context generators, architectural snapshots, and LLM handoff documentation.

### Research / Experiments / Training

Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.

- Detected files: **24**
- Boundary: Treat as research tooling unless a production module imports it explicitly.
- Key files:
  - `BE:chuongtrinhchupanh.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.
  - `BE:clean_req.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.
  - `BE:concate_image.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.
  - `BE:e1108D_metrics_extractor.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.
  - `BE:e1108D_neural_network.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.
  - `BE:e1108D_run.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.
  - `BE:e1108D_train.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.
  - `BE:e5204_metrics_extractor.py` — Standalone training, metrics, labeling, comparison, and experimental scripts outside the production app package.

## 5. Internal module dependency edges

Derived from Python/TypeScript imports. Counts are import edges between source files.

| Source module | Depends on | Edges |
| --- | --- | ---: |
| Backend Tests | Image Processing LAB Backend | 24 |
| Backend Tests | Sampling LAB Backend | 21 |
| Legacy App Builder / Sequencer Runtime | Shared Backend Utilities | 12 |
| App Builder / Sequencer UI | Inspection UI Engine | 11 |
| Sampling LAB Backend | Image Processing LAB Backend | 11 |
| Lab Service Backend | Sampling LAB Backend | 10 |
| Sampling LAB UI | Frontend — Unclassified Source | 8 |
| Image Processing LAB Backend | Vision LAB Core Contracts | 7 |
| Sampling LAB Backend | Vision LAB Core Contracts | 7 |
| App Builder / Sequencer UI | Fleet / Resource UI | 6 |
| Lab Service Backend | Image Processing LAB Backend | 6 |
| Inspection UI Engine | App Builder / Sequencer UI | 5 |
| Backend Tests | Lab Service Backend | 5 |
| Backend Application Shell & API Router | Fleet / Device / Infrastructure Backend | 4 |
| Backend Tests | Contour Extractor LAB Backend | 4 |
| Contour Extractor LAB Backend | Image Processing LAB Backend | 4 |
| Computer Vision Program UI | Lab Service Hub UI | 3 |
| Frontend — Unclassified Source | Sampling LAB UI | 3 |
| Inspection UI Engine | Fleet / Resource UI | 3 |
| Project Compiler | Inspection UI Engine | 3 |
| Backend Tests | Vision LAB Core Contracts | 3 |
| Computer Vision Program Backend / Control Mapper / Camera / Working Pipeline | Backend Application Shell & API Router | 3 |
| Lab Service Backend | Contour Extractor LAB Backend | 3 |
| Fleet / Resource UI | Frontend — Unclassified Source | 2 |
| Fleet / Resource UI | Shared Frontend UI & Utilities | 2 |
| Fleet / Resource UI | App Builder / Sequencer UI | 2 |
| Frontend Application Shell & Routing | App Builder / Sequencer UI | 2 |
| Inspection UI Engine | Shared Frontend UI & Utilities | 2 |
| Project Compiler | Fleet / Resource UI | 2 |
| Sampling LAB UI | Lab Service Hub UI | 2 |
| Backend Application Shell & API Router | Legacy App Builder / Sequencer Runtime | 2 |
| Computer Vision Program Backend / Control Mapper / Camera / Working Pipeline | Image Processing LAB Backend | 2 |
| Computer Vision Program Backend / Control Mapper / Camera / Working Pipeline | Lab Service Backend | 2 |
| Database Backend | Backend Application Shell & API Router | 2 |
| Fleet / Device / Infrastructure Backend | Legacy App Builder / Sequencer Runtime | 2 |
| Fleet / Device / Infrastructure Backend | Shared Backend Utilities | 2 |
| Legacy App Builder / Sequencer Runtime | Backend Application Shell & API Router | 2 |
| Legacy App Builder / Sequencer Runtime | Fleet / Device / Infrastructure Backend | 2 |
| Research / Experiments / Training | Legacy App Builder / Sequencer Runtime | 2 |
| App Builder / Sequencer UI | Frontend — Unclassified Source | 1 |
| App Builder / Sequencer UI | Shared Frontend UI & Utilities | 1 |
| App Builder / Sequencer UI | Project Compiler | 1 |
| App Builder / Sequencer UI | Database UI | 1 |
| Computer Vision Program UI | Frontend — Unclassified Source | 1 |
| Contour Extractor LAB UI | Frontend — Unclassified Source | 1 |
| Contour Extractor LAB UI | Lab Service Hub UI | 1 |
| Contour Extractor LAB UI | Sampling LAB UI | 1 |
| Database UI | Frontend — Unclassified Source | 1 |
| Database UI | Fleet / Resource UI | 1 |
| Frontend Application Shell & Routing | Computer Vision Program UI | 1 |
| Frontend Application Shell & Routing | Contour Extractor LAB UI | 1 |
| Frontend Application Shell & Routing | Database UI | 1 |
| Frontend Application Shell & Routing | Fleet / Resource UI | 1 |
| Frontend Application Shell & Routing | Image Processing LAB UI | 1 |
| Frontend Application Shell & Routing | Inspection UI Engine | 1 |
| Frontend Application Shell & Routing | Lab Service Hub UI | 1 |
| Frontend Application Shell & Routing | Sampling LAB UI | 1 |
| Frontend Application Shell & Routing | Shared Frontend UI & Utilities | 1 |
| Frontend — Unclassified Source | Lab Service Hub UI | 1 |
| Image Processing LAB UI | Frontend — Unclassified Source | 1 |

## 6. Backend API routes

| File | Method | Path | Handler |
| --- | --- | --- | --- |
| `BE:app/api/root_api.py` | `GET` | `/fleetstatus` | `get_fleet_overview_status` |
| `BE:app/api/root_api.py` | `GET` | `/status` | `check_server_health` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `DELETE` | `/sessions/{session_id}` | `close_session` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `GET` | `/sessions/{session_id}/contours` | `list_contours` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `GET` | `/sessions/{session_id}/contours/geometry` | `contour_geometry` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `GET` | `/sessions/{session_id}/contours/{contour_id}/fourier` | `contour_fourier_analysis` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `GET` | `/sessions/{session_id}/preview/{source_name}` | `source_preview` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `GET` | `/stages` | `list_stage_catalog` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `POST` | `/sessions` | `create_session` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `POST` | `/sessions/{session_id}/run` | `run_session` |
| `BE:app/api/v1/endpoints/contour_extractor_api.py` | `PUT` | `/sessions/{session_id}/definition` | `set_definition` |
| `BE:app/api/v1/endpoints/db_api.py` | `GET` | `/images/{filename}/download` | `download_image` |
| `BE:app/api/v1/endpoints/db_api.py` | `GET` | `/schema/{table_name}` | `get_table_schema` |
| `BE:app/api/v1/endpoints/db_api.py` | `GET` | `/tables` | `get_database_tables` |
| `BE:app/api/v1/endpoints/db_api.py` | `POST` | `/images/upload` | `upload_image` |
| `BE:app/api/v1/endpoints/db_api.py` | `POST` | `/insert` | `insert_data` |
| `BE:app/api/v1/endpoints/db_api.py` | `POST` | `/query` | `execute_dynamic_query` |
| `BE:app/api/v1/endpoints/db_api.py` | `POST` | `/seed` | `seed_database` |
| `BE:app/api/v1/endpoints/db_api.py` | `POST` | `/tables/create` | `create_new_table` |
| `BE:app/api/v1/endpoints/db_api.py` | `POST` | `/tables/drop` | `drop_table` |
| `BE:app/api/v1/endpoints/graph_api.py` | `DELETE` | `/undeploygraph/{logic_object_id}` | `undeploy_graph_from_ram` |
| `BE:app/api/v1/endpoints/graph_api.py` | `GET` | `/catalog` | `get_node_catalog` |
| `BE:app/api/v1/endpoints/graph_api.py` | `GET` | `/dependencies` | `get_logic_dependencies` |
| `BE:app/api/v1/endpoints/graph_api.py` | `GET` | `/getLogicIDs` | `get_logic_id_list` |
| `BE:app/api/v1/endpoints/graph_api.py` | `GET` | `/getinoutschema/{logic_object_id}` | `get_in_out_schema` |
| `BE:app/api/v1/endpoints/graph_api.py` | `POST` | `/deploygraph/{graph_file_name}` | `deploy_graph_to_ram` |
| `BE:app/api/v1/endpoints/graph_api.py` | `POST` | `/executelogic/{logic_object_id}` | `execute_logic` |
| `BE:app/api/v1/endpoints/graph_api.py` | `POST` | `/preflight` | `preflight_run` |
| `BE:app/api/v1/endpoints/graph_api.py` | `POST` | `/sync-dependencies` | `sync_logic_dependencies` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `DELETE` | `/sessions/{session_id}` | `close_session` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `GET` | `/operators` | `get_operator_catalog` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `GET` | `/pipelines` | `list_pipelines` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `GET` | `/pipelines/{name}` | `load_pipeline` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `GET` | `/sessions/{session_id}/preview/node/{node_id}/{port}` | `preview_node` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `GET` | `/sessions/{session_id}/preview/source/{source_name}` | `preview_source` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `POST` | `/pipelines/save` | `save_pipeline` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `POST` | `/pipelines/validate` | `validate_pipeline` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `POST` | `/sessions` | `create_session` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `POST` | `/sessions/{session_id}/input/{source_name}` | `upload_input` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `POST` | `/sessions/{session_id}/run` | `run_session` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `PUT` | `/sessions/{session_id}/pipeline` | `set_session_pipeline` |
| `BE:app/api/v1/endpoints/image_lab_api.py` | `WEBSOCKET` | `/sessions/{session_id}/live` | `image_lab_live` |
| `BE:app/api/v1/endpoints/infra_api.py` | `DELETE` | `/devices/delete/{device_id}` | `remove_local_device` |
| `BE:app/api/v1/endpoints/infra_api.py` | `DELETE` | `/resources/delete/{file_type}/{file_name}` | `delete_file` |
| `BE:app/api/v1/endpoints/infra_api.py` | `DELETE` | `/servers/delete/{server_id}` | `remove_local_server` |
| `BE:app/api/v1/endpoints/infra_api.py` | `GET` | `/devices` | `get_all_local_devices` |
| `BE:app/api/v1/endpoints/infra_api.py` | `GET` | `/resources/files/{filetype}/{filename}/content` | `get_file_content` |
| `BE:app/api/v1/endpoints/infra_api.py` | `GET` | `/resources/files/{filetype}/{filename}/download` | `download_file` |
| `BE:app/api/v1/endpoints/infra_api.py` | `GET` | `/resources/status` | `get_resource_status` |
| `BE:app/api/v1/endpoints/infra_api.py` | `GET` | `/servers` | `get_all_local_servers` |
| `BE:app/api/v1/endpoints/infra_api.py` | `GET` | `/servers/{server_id}` | `get_server_info` |
| `BE:app/api/v1/endpoints/infra_api.py` | `POST` | `/devices/add` | `add_local_device` |
| `BE:app/api/v1/endpoints/infra_api.py` | `POST` | `/devices/heartbeat/{new_interval}` | `change_server_bus_heartbeat` |
| `BE:app/api/v1/endpoints/infra_api.py` | `POST` | `/resources/files/load-to-ram/{filename}` | `load_file_to_memory` |
| `BE:app/api/v1/endpoints/infra_api.py` | `POST` | `/resources/files/unload-from-ram/{filename}` | `unload_file_from_memory` |
| `BE:app/api/v1/endpoints/infra_api.py` | `POST` | `/resources/files/{filetype}/upload` | `upload_file` |
| `BE:app/api/v1/endpoints/infra_api.py` | `POST` | `/servers/add` | `add_local_server` |
| `BE:app/api/v1/endpoints/infra_api.py` | `POST` | `/servers/heartbeat/{new_interval}` | `change_server_bus_heartbeat` |
| `BE:app/api/v1/endpoints/lab_service_api.py` | `DELETE` | `/{service_id}` | `delete_lab_service` |
| `BE:app/api/v1/endpoints/lab_service_api.py` | `GET` | `` | `list_lab_services` |
| `BE:app/api/v1/endpoints/lab_service_api.py` | `GET` | `/runs/{run_id}/outputs/{output_name}` | `preview_run_output` |
| `BE:app/api/v1/endpoints/lab_service_api.py` | `GET` | `/{service_id}` | `get_lab_service` |
| `BE:app/api/v1/endpoints/lab_service_api.py` | `GET` | `/{service_id}/versions` | `list_lab_service_versions` |
| `BE:app/api/v1/endpoints/lab_service_api.py` | `POST` | `/deploy` | `deploy_lab_service` |
| `BE:app/api/v1/endpoints/lab_service_api.py` | `POST` | `/{service_id}/run` | `run_lab_service` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `DELETE` | `/sessions/{session_id}` | `close_session` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/operators` | `get_operator_catalog` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/pipelines` | `list_pipelines` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/pipelines/{name}` | `load_pipeline` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/program/methods` | `list_sampling_program_methods` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/sessions/{session_id}/artifact/{node_id}/{port}` | `get_artifact_json` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/sessions/{session_id}/fft-reconstruction/{node_id}` | `fft_reconstruction` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/sessions/{session_id}/preview/node/{node_id}/{port}` | `preview_artifact` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/sessions/{session_id}/preview/source/{source_name}` | `preview_source` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/sessions/{session_id}/source-board` | `get_source_board` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/sessions/{session_id}/source-board/{source_name}/artifact` | `get_source_board_artifact` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `GET` | `/sessions/{session_id}/source-board/{source_name}/channel-preview` | `channel_preview` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/pipelines/save` | `save_pipeline` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/pipelines/validate` | `validate_pipeline` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/sessions` | `create_session` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/sessions/{session_id}/input/{source_name}` | `upload_input` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/sessions/{session_id}/input/{source_name}/from-lab-service` | `bind_input_from_lab_service` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/sessions/{session_id}/program/formulate` | `formulate_sampling_program` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/sessions/{session_id}/program/run` | `run_sampling_program` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/sessions/{session_id}/run` | `run_session` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `POST` | `/sessions/{session_id}/source-board` | `build_source_board` |
| `BE:app/api/v1/endpoints/sampling_geometry_api.py` | `PUT` | `/sessions/{session_id}/pipeline` | `set_session_pipeline` |
| `BE:app/api/v1/endpoints/utils.py` | `GET` | `/health-check` | `perform_health_check` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `DELETE` | `/programs/{program_id}` | `delete_program` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `DELETE` | `/programs/{program_id}/automation/trace` | `automation_clear_trace` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `DELETE` | `/programs/{program_id}/workspaces/{workspace_alias}/stream/stop` | `workspace_stream_stop` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/cameras/basler/scan` | `basler_scan` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/debug/{run_id}/{key}` | `debug_image` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs` | `list_programs` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}` | `get_program` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/automation/endpoints` | `automation_endpoints` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/automation/latest-frame` | `automation_latest_frame` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/automation/state` | `automation_state` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/automation/trace` | `automation_trace` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/cameras/{camera_alias}/stream-frame` | `declared_camera_stream_frame` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/iot/trigger` | `read_trigger` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/master` | `master_preview` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/master/blur-preview` | `master_blur_preview` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/runner/status` | `runner_status` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/workspaces/{workspace_alias}/stream/frame` | `workspace_stream_frame` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `GET` | `/programs/{program_id}/workspaces/{workspace_alias}/stream/status` | `workspace_stream_status` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/new` | `create_program` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/automation/endpoints/preview` | `automation_endpoints_preview` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/automation/keyboard` | `automation_keyboard` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/automation/latest-frame` | `automation_set_latest_frame` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/automation/services/{service_id}/run` | `automation_run_service` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/automation/start` | `automation_start` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/automation/stop` | `automation_stop` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/automation/validate` | `automation_validate` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/camera/capture` | `camera_capture` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/camera/focus` | `camera_focus` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/cameras/{camera_alias}/capture` | `declared_camera_capture` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/cameras/{camera_alias}/sim-frame` | `simulated_camera_frame` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/iot/pulse` | `pulse_output` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/locate-rois` | `locate_rois` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/master` | `upload_master` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/offline` | `program_offline` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/online` | `program_online` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/runner/start` | `runner_start` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/runner/stop` | `runner_stop` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/scope-preview/{scope_id}` | `scope_preview` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/simulator/iot/{device_alias}/{point_alias}` | `simulator_iot` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/test-run` | `test_run` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/workspaces/{workspace_alias}/activate` | `workspace_activate` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/workspaces/{workspace_alias}/run` | `workspace_run` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/workspaces/{workspace_alias}/soft-trigger/analyze` | `workspace_soft_trigger_analyze` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/workspaces/{workspace_alias}/soft-trigger/preview` | `workspace_soft_trigger_preview` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `POST` | `/programs/{program_id}/workspaces/{workspace_alias}/stream/start` | `workspace_stream_start` |
| `BE:app/api/v1/endpoints/vision_app_api.py` | `PUT` | `/programs/{program_id}` | `save_program` |

## 7. Frontend routes

| File | Route |
| --- | --- |
| `FE:src/App.tsx` | `*` |
| `FE:src/App.tsx` | `/` |
| `FE:src/App.tsx` | `/computer-vision` |
| `FE:src/App.tsx` | `/data` |
| `FE:src/App.tsx` | `/fleet` |
| `FE:src/App.tsx` | `/fleet/:worker_id/devices` |
| `FE:src/App.tsx` | `/fleet/:worker_id/logic` |
| `FE:src/App.tsx` | `/inspection` |
| `FE:src/App.tsx` | `/labs` |
| `FE:src/App.tsx` | `/labs/contour-extractor` |
| `FE:src/App.tsx` | `/labs/image-processing` |
| `FE:src/App.tsx` | `/labs/sampling-geometry` |
| `FE:src/App.tsx` | `/sequencer` |
