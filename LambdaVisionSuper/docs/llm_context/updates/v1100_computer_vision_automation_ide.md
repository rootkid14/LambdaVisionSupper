# Computer Vision v0.11.0 — Automation IDE / Control Plane Foundation

## Why this release exists
The Computer Vision application previously had Camera, IOT, Master Sample, Working, Control Mapper and Debug Stack, but no general execution/glue layer. v0.11 freezes the current LAB foundation and introduces the first real Automation IDE architecture underneath `/computer-vision`.

The design goal is not “arbitrary scripting”. The goal is a typed, inspectable and safe industrial control plane that can connect system lifecycle, Modbus I/O, camera actions and Logic-service outputs without embedding hardware/control policy into Vision LABs.

## New architectural layers

### Endpoint Registry
`app/services/vision_app/endpoint_registry.py`

Every IDE-visible primitive is described as one of:
- `state` — readable runtime state
- `action` — callable side effect/action
- `event` — lifecycle event usable by Event services
- `data` — immutable run/Logic output data

Initial namespaces include:

```text
system.run_state
system.result
system.run_id
system.last_run_ms
system.run_inspection()
system.commit_result(OK|NG)
system.clear_working_screen()
system.run_started
system.run_finish
system.run_error

camera.main.capture()
camera.main.frame_ready
camera.main.frame_sequence

device.modbus_1.X1
device.modbus_1.Y1
device.modbus_1.Y1.pulse(seconds)
device.modbus_1.Y2
device.modbus_1.Y2.pulse(seconds)

vision.global_scope.logic.<alias>.outputs...
vision.roi.<roi_alias>.logic.<alias>.outputs...

vision.logic_ready
```

`X1` maps to the configured trigger input. `Y1` maps to the configured OK coil and `Y2` maps to the configured NG coil. This is intentionally an initial alias set; future IOT/device configuration can expose arbitrary named points through the same registry contract.

### VisionRunSnapshot
After Filter/Logic execution, the Automation Manager converts the run into an immutable snapshot containing Global Logic outputs, per-ROI Logic outputs, ROI metadata and benchmark data.

Automation scripts read this snapshot rather than mutable React/UI state. This is the foundation for deterministic decision making and replay/dry-run behavior.

### Automation services
Programs now persist `automation.services[]`.

Supported modes:
- `loop` — scheduler calls the service periodically; user never writes `while True`
- `event` — service is called when a registered event fires
- `oneshot` — manually reusable procedure

Each service has an ID, name, enabled state, mode, interval/event, safe DSL source, timeout and concurrency policy metadata.

### Safe DSL
`automation_runtime.py` parses a small Python-like syntax with Python AST but NEVER uses `exec()`.

Allowed concepts include:
- `if / else`
- boolean logic (`and/or/not`)
- comparisons
- simple arithmetic
- endpoint reads
- writable endpoint assignments
- registered endpoint action calls
- small safe helpers (`abs`, `min`, `max`, `len`, `round`)

Constants:
- `ON`, `OFF`
- `OK`, `NG`, `NONE`

Not allowed:
- import
- arbitrary Python functions/classes
- `while`/user-controlled infinite loops
- filesystem/network/subprocess access
- dunder/private names
- arbitrary object access outside the endpoint resolver

Example Loop service:

```text
if device.modbus_1.X1 == ON:
    system.run_inspection()
```

Example decision Event service (`vision.logic_ready`):

```text
if vision.roi.ROI1.logic.contour.outputs.length > 120:
    system.commit_result(OK)
else:
    system.commit_result(NG)
```

Example result-output Event service (`system.run_finish`):

```text
if event.result == OK:
    device.modbus_1.Y1.pulse(1.0)
else:
    device.modbus_1.Y2.pulse(1.0)
```

### Lifecycle
The intended lifecycle is now explicit:

```text
system.run_started
    ↓
Camera/latest test frame
    ↓
Global Filter/Logic
    ↓
ROI locate
    ↓
ROI Filter/Logic
    ↓
VisionRunSnapshot
    ↓
vision.logic_ready
    ↓
Automation Event services may call system.commit_result(OK/NG)
    ↓
Fallback to Working result only if no automation committed a result
    ↓
system.run_finish
```

This separates “Logic extraction is finished” from “the entire production cycle is finished”.

## Dry Run
Dry Run executes the same parser/runtime but suppresses physical side effects such as Modbus coil writes, camera capture and inspection execution. Trace entries explicitly mark dry-run actions so commissioning engineers can see what WOULD happen.

## Execution Trace
Automation trace is stored per program in a bounded in-memory trace buffer. It records service, phase, message, endpoint, value and dry-run status. The IDE polls this trace while the scheduler is running.

## Automation Manager
`automation_manager.py` owns:
- Automation system state
- latest backend frame
- latest VisionRunSnapshot
- Loop scheduler
- Event dispatch
- One-shot execution
- endpoint read/write/action resolution
- result commit and clear-screen signals
- trace buffer

It receives existing adapters (`VisionProgramRepository`, `VisionProgramRuntime`, `CameraController`, `ModbusIOController`) rather than duplicating them.

## Frontend IDE
New module: `Automation IDE` in the Computer Vision left module rail.

`AutomationIdeWorkspace.tsx` provides:
- service explorer
- Add Loop / Event / One-shot
- service settings
- safe-code editor
- Ctrl+Space registry-backed completion popup
- Endpoint Explorer
- Validate
- Dry Run
- Run Service
- Start/Stop Scheduler
- Problems panel
- Variables panel
- Execution Trace panel

This is intentionally a first editor implementation, not the final Monaco/VS Code implementation. The important contract is that IntelliSense data already comes from the typed Endpoint Registry, so Monaco/LSP can replace the text editor later without changing runtime semantics.

## UI bridge to system endpoints
Automation system state contains sequence counters for:
- captured frame
- clear-working request
- committed result

The Computer Vision page polls this state so backend Automation actions can affect UI without direct React coupling. Manual/test images are also uploaded into the Automation Manager’s latest-frame cache so `system.run_inspection()` can behave like Run Test on the current image.

## Backward compatibility
- Existing v0.7-v0.10 program JSON still loads.
- Existing `control` mappings remain supported.
- Existing legacy v2 Decision DSL remains runtime-compatible.
- Existing Trigger Runner remains present.
- New programs keep program version 3 and add an empty Automation service list; the Automation field is backward-compatible and does not require a program-format version bump.
- Repository migration does NOT force old v2 programs to version 4, preserving the legacy Decision compatibility branch.

## Important future extensions
Do not bypass the Endpoint Registry when adding new IDE capabilities. Add typed endpoints instead.

Likely next areas:
- user-defined Modbus point aliases instead of only X1/Y1/Y2
- Monaco Editor / language server
- endpoint schema/version validation when ROI/service aliases change
- event service replay against historical VisionRunSnapshot
- scheduler concurrency/timeout enforcement
- guided rule builder that emits the same safe DSL
- persistent trace/history database
- richer device endpoints (registers, robots, digital I/O)
- explicit one-shot-to-one-shot calls
- test fixtures/simulation endpoint providers
