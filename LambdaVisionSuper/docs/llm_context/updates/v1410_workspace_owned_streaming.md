# Computer Vision v0.14.1 — Workspace-owned Streaming / Soft Trigger

This release rebases the v0.14 streaming plane onto the actual v0.13.6 architecture where IOT and Camera declarations belong to each Workspace.

## Key rule

A stream is identified by `(program, workspace)`, not by camera alias globally. Two independent Workspaces may both declare `camera.main` without sharing stream frames or runtime state.

## Implemented

- Persistent native Basler backend streaming.
- Lazy browser JPEG preview only while the Streaming workspace preview is open.
- Per-Workspace Soft Trigger ROI, threshold, active-pixel count, hysteresis/re-arm, frame stride and cooldown.
- Soft Trigger can run that Workspace inspection directly from the in-memory stream frame.
- ONLINE arms enabled Soft Triggers for all enabled Workspaces.
- Full `keyboard.key.*` namespace.
- HTTP/Raspberry Pi streaming remains transport scaffolding only.

## Workspace ownership

Each Workspace retains its own IOT declarations, Camera declarations/binding, Master/ROI, Working pipeline and Soft Trigger. No stream lookup falls back to another Workspace.
