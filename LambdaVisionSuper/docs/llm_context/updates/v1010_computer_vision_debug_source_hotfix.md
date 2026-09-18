# Computer Vision v0.10.1 — Debug Source Hotfix

## Scope-correct Debug input
The Debug Stack Workspace now starts from the actual input of the selected scope. Global scope begins with the full preview image. ROI/station scope first applies the configured Global Filter stack, runs the program-wide ROI locator, crops the located ROI, and stores that crop as `preview_input`. ROI Debug must never present the full Global image as the station input stage.

## Master fallback
Filter-stack Debug no longer requires an explicitly uploaded/captured test image. The `scope-preview` endpoint accepts an empty request body and falls back to the persisted Master Sample as the preview image. The response includes `preview_source = test | master`, and the frontend labels the Debug Workspace title accordingly. For an ROI scope, Master fallback still goes through Global filtering + ROI location + ROI crop before the station Filter stack.

## Failure boundary
If neither an explicit test image nor a persisted Master Sample exists, Debug preview still fails because there is no image source. This is intentional.
