# v0.6.0 — LLM Context Generator v2

## Why this update exists

The first full-system map proved useful, but its inventory was polluted by runtime/research data artifacts. In the reviewed map, the backend contained hundreds of `.npz` files under `_entropy1_train_ca`, which inflated the generic `Backend Project / Config` category and obscured the real source architecture.

Generator v2 changes the model from a generic filesystem inventory to a **Lambda Vision project-aware context compiler**.

## Outputs

The generator now produces four documents:

1. `SYSTEM_CONTEXT_INDEX.md`
   - Compact first file for a new LLM conversation.
   - Git revision/dirty state.
   - Critical runtime boundary.
   - Detected module summary.
   - Recommended handoff order.

2. `SYSTEM_ARCHITECTURE.md`
   - High-level architecture.
   - Legacy Sequencer vs Vision LAB boundary.
   - Image LAB / Lab Service / Sequencer execution flows.
   - Project-aware module descriptions.
   - Internal module dependency edges derived from imports.
   - Backend FastAPI routes.
   - Frontend React routes.

3. `SYSTEM_CONTEXT_BUNDLES.md`
   - Minimal and deep context bundles for:
     - Image Processing LAB
     - Lab Service
     - App Builder / Sequencer
     - Inspection UI Engine
     - Fleet / Device
     - Database

4. `SYSTEM_FILE_MAP.md`
   - Clean source/config inventory.
   - Runtime data/binaries excluded by default.
   - Exclusion statistics.
   - Project-aware module classification.
   - Purpose and key symbols per source file.
   - Unclassified-file diagnostics for future generator refinement.

## Important project model encoded in v2

### Legacy App Builder / Sequencer

Backend core:

`BaseNode / NODE_REGISTRY -> LogicObject -> LogicPoolManager`

This is the general automation / future Agentic graph runtime.

### Vision LAB

Image Processing uses its own hierarchy:

`ImageOperator / ImageOperatorRegistry -> ImagePipelineRuntime -> ImageLabSession`

It intentionally does **not** inherit `BaseNode`.

### Lab Service

Lab Service is the versioned/callable wrapper around a LAB pipeline snapshot. It is the intended future integration point for Dataset, Sampling/Geometry, Sequencer and Agentic systems.

## Source-selection policy

By default the generator indexes source/config/documentation only.

It excludes:

- `.npz`, `.npy`, model weights and checkpoints;
- images/video/binary assets;
- datasets and runtime storage;
- logs and caches;
- dependency/build output;
- generated Tauri schemas;
- lock files;
- old concatenated `*_context_for_llm.txt` dumps.

When Git is available, the generator uses tracked + nonignored untracked files as the candidate set before applying the source relevance filter.

## Maintenance rule

After a structural update:

```bash
python tools/generate_llm_context_map.py \
  --frontend /path/to/LambdaVisionSuper \
  --backend /path/to/LambdaVisionSuperBackEnd
```

For a new chat, load `SYSTEM_CONTEXT_INDEX.md` and `SYSTEM_ARCHITECTURE.md` first, then the latest relevant update note, then only the bundle/source files needed for the task.
