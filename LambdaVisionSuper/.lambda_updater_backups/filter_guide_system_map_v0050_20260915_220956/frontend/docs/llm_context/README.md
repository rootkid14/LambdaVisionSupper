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
