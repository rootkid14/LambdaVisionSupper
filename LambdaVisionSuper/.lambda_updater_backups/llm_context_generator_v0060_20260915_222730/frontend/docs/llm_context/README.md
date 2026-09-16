# LLM Context Maps

This directory contains compact architecture/file maps intended for future LLM-assisted code changes.

## Convention

Every updater that materially changes a module should create or update a Markdown context note under:

`docs/llm_context/updates/`

Each note should include:

- update/version name;
- files touched or closely related;
- one-line purpose of each file;
- important contracts and invariants;
- recommended minimal file set for a future LLM context window.

These notes are documentation aids only. Runtime code must never depend on them.

## Full-system context map

The current structural snapshot is generated at:

`docs/llm_context/SYSTEM_FILE_MAP.md`

Regenerate it with:

```bash
python tools/generate_llm_context_map.py \
  --frontend /path/to/LambdaVisionSuper \
  --backend /path/to/LambdaVisionSuperBackEnd
```

Recommended workflow for a fresh LLM conversation:

1. Provide `SYSTEM_FILE_MAP.md`.
2. Provide the latest relevant file from `docs/llm_context/updates/`.
3. Use those maps to select only the exact source files needed for the requested module.
