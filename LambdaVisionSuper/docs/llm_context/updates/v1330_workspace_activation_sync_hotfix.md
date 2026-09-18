# Computer Vision v0.13.3 — Workspace Activation Sync Hotfix

Fixes a race where the frontend optimistically selected Workspace 2 but the 700 ms Automation state poll still reported the old backend active workspace and forced the UI back to Workspace 1.

## Synchronization contract

- Clicking a saved workspace calls a backend workspace activation endpoint immediately.
- `AutomationSystemState.workspace_activation_sequence` increments only when the backend active workspace truly changes.
- Frontend polling changes the visible workspace only when this sequence increases.
- `workspace.<alias>.activate()` from Automation IDE therefore still switches the visible UI workspace.
- A newly-created unsaved workspace may remain locally selected even when the backend cannot activate it yet; saving the program makes it available to the runtime.

This prevents stale polling state from overriding normal tab selection while preserving IDE-driven workspace activation.
