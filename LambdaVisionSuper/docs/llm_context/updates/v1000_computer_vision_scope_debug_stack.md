# Computer Vision v0.10.0 — Scope Quick Controls + Debug Stack Workspace

## Scope Operation UX
The Working Operation panel still selects one scope at a time (Global or one ROI station), but Filter & Processing and Logic Services are now expandable quick-control accordions instead of shallow Edit launchers. New scopes default to Filter enabled and Logic enabled. Each accordion exposes the active service stack, per-service enable, quick reorder/remove, Logic alias editing, quick service add, and an optional full Stack Workspace for deeper editing.

Decision / Glue is removed completely from the scope UI. Program v3+ still reserves decision/glue ownership for the future IDE/sandbox. Legacy v2 saved Decision scripts remain runtime-compatible only for old programs.

## Unified Debug Stack Workspace
There is one debug experience. The old embedded Filter Debug View inside the Filter editor is removed. Both full inspection runs and Filter-stack previews open the same full-screen Debug Stack Workspace.

The Debug Stack Workspace is intentionally modeled after the Image Processing LAB pipeline feeling:
- left: grouped stage stack by scope, ordered Input -> Filter stages -> final filtered image -> Logic stages;
- center: large zoom/pan image viewport for image stages, or structured Logic output inspector for Logic stages;
- right: stage metadata + benchmark trace;
- Prev/Next walks the pipeline stage-by-stage;
- image bytes are lazy-loaded only when a stage is selected and cached only for the current workspace session.

Filter-stack preview API now returns benchmark timing together with debug image references, so the same workspace can debug a scope without requiring a complete production inspection cycle.

## Defaults and Compatibility
`ScopePipelineConfig.enable_filter` and `enable_logic` default to true for newly created scopes/programs. Repository migration keeps explicit legacy settings, so existing saved programs are not silently changed. `enable_decision` stays false by default.

## Architecture boundary
Computer Vision Working remains orchestration only: Global/ROI Filter services transform images, Logic services extract information, and the future IDE owns cross-scope decision/glue/actions. The Debug Stack observes this orchestration; it does not become another processing runtime.
