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

## Generator v2 handoff workflow

The context compiler now generates four complementary files:

- `SYSTEM_CONTEXT_INDEX.md` — first file to load in a fresh LLM conversation.
- `SYSTEM_ARCHITECTURE.md` — architecture boundaries and execution flows.
- `SYSTEM_CONTEXT_BUNDLES.md` — recommended minimal/deep source bundles.
- `SYSTEM_FILE_MAP.md` — detailed clean source inventory.

Recommended fresh-chat workflow:

1. Load `SYSTEM_CONTEXT_INDEX.md`.
2. Load `SYSTEM_ARCHITECTURE.md`.
3. Load the latest relevant `updates/*.md`.
4. Select a bundle from `SYSTEM_CONTEXT_BUNDLES.md`.
5. Load exact source files only as needed.

The detailed file map should be used for navigation, not automatically dumped into every context window.
