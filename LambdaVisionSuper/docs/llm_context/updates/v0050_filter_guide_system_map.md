# v0.5.0 — Filter Guide Playground + Full System Context Map

## Scope

This update improves Image Processing LAB operator discoverability and introduces a codebase-wide LLM context inventory.

## Frontend files

### `src/components/VisionLabs/ImageProcessing/OperatorLibrary.tsx`

- Adds an `(i)` / guide button to every operator row.
- Opens `FilterGuideModal` without adding the operator to the active processing stack.
- Keeps the existing add/compatibility behavior unchanged.

### `src/components/VisionLabs/ImageProcessing/FilterGuideModal.tsx`

- Three-column standalone playground:
  - left: explanation, algorithm behavior, tuning tips, notes and I/O contract;
  - center: independent input/result preview with zoom/pan;
  - right: isolated parameter controls.
- Creates its own temporary Image LAB session.
- Does not mutate the current editor stack/session.
- Parameter changes are manual: they run only when `Run Test` is pressed.
- Supports one-input operators whose input type is `image` or `binary_mask`.
- For `binary_mask` inputs, a clearly disclosed playground-only adapter converts the uploaded image using:
  - Grayscale
  - Binary Threshold
- Multi-input/unsupported operators still show documentation but standalone execution is disabled rather than inventing semantic inputs.

### `src/components/VisionLabs/ImageProcessing/operatorGuide.ts`

- Category-level explanations for current Image Processing LAB families.
- Specific guidance for important operators such as Bradley Threshold, Zhang-Suen, Frangi and Notch Reject.
- Parameter-name heuristics provide automatic tuning hints for future operators.
- The guide therefore degrades gracefully when new filters are added without dedicated documentation.

## LLM context infrastructure

### `tools/generate_llm_context_map.py`

Scans both Lambda Vision frontend and backend source trees and generates:

`docs/llm_context/SYSTEM_FILE_MAP.md`

The generated snapshot includes:

- FE/BE project roots and git branch/commit;
- module/category summary;
- recommended LLM context bundles;
- full source-oriented file inventory;
- inferred purpose per file;
- top-level Python/TypeScript symbols where practical;
- size and extension summaries.

Heavy/generated/runtime directories are excluded, including dependencies, git data, virtual environments, build outputs, caches, storage, logs, datasets and updater backups.

## Documentation model going forward

Use two documentation layers:

1. `docs/llm_context/SYSTEM_FILE_MAP.md`
   - Current whole-system structural snapshot.
   - Regenerate after structural updates.
   - Best first file to provide to a fresh LLM conversation.

2. `docs/llm_context/updates/*.md`
   - Human-authored update notes for a specific architectural/code change.
   - Use with the system map to decide which exact source files to load next.

## Runtime invariants

- Filter Guide playground must remain independent from the current editor pipeline.
- It reuses the existing Image LAB backend/session runtime; do not create a parallel image-processing engine.
- Guide parameter dropdowns preserve typed enum choices (numeric enum choices must stay numeric).
- BinaryMask playground conversion is an explicit test adapter, not part of the operator itself.
