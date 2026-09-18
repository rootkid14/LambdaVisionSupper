# Computer Vision v0.13.5 — Workspace Transaction Isolation

## Why this patch exists

v0.13.4 isolated persisted workspace Master/ROI/Working data, but `+ Workspace` was still implemented as two child callbacks: first mutate the workspace list, then activate the new id. The activation callback executed with the previous React render's `program` closure, so the newly-created workspace was not yet visible and activation could be skipped. This made a new tab appear while the inspection context could remain attached to the previous workspace.

## v0.13.5 contract

- Workspace creation is owned by `ComputerVisionPage`, not `WorkspaceTabs`.
- `freshWorkspace()` always creates a blank inspection definition: no Master shape, no ROIs, empty Global/ROI Filter+Logic stacks, no camera binding.
- Add is atomic from the UI's point of view: append fresh workspace + set active id + reset workspace UI + persist program + activate backend workspace.
- Remove is also parent-owned and persisted.
- `VisionViewport`, `MasterSamplePanel`, and `WorkingModulePanel` are keyed by `workspace_id`, forcing internal React state to remount on every workspace switch.
- Master/test/debug/ROI selection state is cleared immediately before switching/creating/removing workspaces.
- Shared resources remain Camera/IOT declarations only. Inspection definitions remain workspace-local.

Existing workspaces that were intentionally saved with copied data are not silently erased. Delete/recreate such a workspace or edit it explicitly. New workspaces created after v0.13.5 start blank by construction.
