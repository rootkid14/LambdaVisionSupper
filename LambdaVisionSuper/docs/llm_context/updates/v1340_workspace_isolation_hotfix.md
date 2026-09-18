# Computer Vision v0.13.4 — Strict Workspace Isolation

## Contract

Each Workspace is an independent inspection program inside one Vision Program. Shared resources are Camera/IOT declarations; inspection state is workspace-owned.

Workspace-owned state includes:
- Master image file
- ROI definitions and locator configuration
- Working Global/ROI Filter and Logic scopes
- test/run/debug viewport context
- latest workspace inspection result
- one declared camera binding

## Fixes

- Removed the repository fallback that returned Workspace 1 `master.png` when another workspace had no master.
- Frontend clears Master/test/debug state immediately on workspace changes and guards against stale asynchronous Master responses.
- Legacy `vision.*` compatibility endpoints now project the active/latest workspace rather than the Workspace 1 mirror fields.
- `program.master` / `program.working` remain Workspace 1 mirrors only for old integrations; new APIs/runtimes must use the selected Workspace or a projected program.

A new workspace therefore starts with no Master image, no ROI definitions, and default empty Working scopes.
