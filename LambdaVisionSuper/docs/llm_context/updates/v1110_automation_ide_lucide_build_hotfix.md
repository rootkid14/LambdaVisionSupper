# Computer Vision v0.11.1 — Automation IDE Lucide Build Hotfix

## Scope
This hotfix fixes a production frontend build failure introduced in v0.11.0.

`AutomationIdeWorkspace.tsx` imported `Event` from `lucide-react`, but the installed Lucide version in the Lambda Vision frontend does not export that symbol.

## Change
- Remove the unsupported `Event` icon import.
- Reuse the already-supported `CirclePlay` icon for event endpoints.
- No backend, DSL, scheduler, registry, runtime, API, or persisted program behavior changes.

## Compatibility
This patch is intended for the exact Computer Vision v0.11.0 baseline after the Automation IDE updater has been applied.
