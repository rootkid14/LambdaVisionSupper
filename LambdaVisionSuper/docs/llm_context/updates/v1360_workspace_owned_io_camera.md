# Computer Vision v0.13.6 — Workspace-owned Camera / IOT resources

## Problem fixed

v0.13.5 correctly isolated Master, viewport and Working state, but Camera and IOT declarations were still stored at `VisionProgramDefinition.cameras` / `VisionProgramDefinition.iot`. Switching tabs therefore kept showing Workspace 1 hardware declarations.

## v0.13.6 ownership contract

Each `WorkspaceDefinition` now owns all inspection resources required to operate independently:

- `workspace.iot`
- `workspace.cameras`
- `workspace.camera_id` / `workspace.input_binding`
- `workspace.master`
- `workspace.working`
- run/debug/latest-frame context

A newly created Workspace starts with empty `iot.devices` and `cameras.devices`. No Camera or IOT declaration may be inherited from another Workspace implicitly.

## Backward compatibility / migration

Programs saved with v0.13.5 or older may still contain program-global Camera/IOT declarations. During migration those legacy declarations are copied **only into Workspace 1**. Workspace 2+ receive empty declaration lists. Existing Workspace 1 hardware configuration is therefore preserved while the unwanted cross-workspace inheritance is removed.

Root `program.iot` / `program.cameras` remain compatibility mirrors for older integrations. On save they mirror the selected active Workspace; the production UI and current runtime no longer use them as the owner of hardware declarations.

## Runtime projection

Before building Camera/IOT endpoints or executing active-workspace Automation, the backend projects the selected Workspace into the legacy program-root runtime contract. Consequently `camera.*` and `device.*` represent only the active Workspace resources.

The Automation IDE preview performs the same projection for unsaved editor state, so switching Workspace changes IntelliSense/Object Explorer immediately.

## UI isolation

`IotDeclarationWorkspace` and `CameraDeclarationWorkspace` receive `activeWorkspace.iot` / `activeWorkspace.cameras` and are keyed by `workspace_id`. This forces local React state such as selected device/camera, preview and stream state to remount at a Workspace boundary.

## Regression coverage

`test_vision_app_v1360.py` verifies:

1. fresh Workspace Camera/IOT defaults are independent;
2. legacy globals migrate only to Workspace 1;
3. repository round-trip keeps different hardware declarations in different Workspaces;
4. endpoint projection exposes only the selected Workspace Camera/IOT endpoints.
