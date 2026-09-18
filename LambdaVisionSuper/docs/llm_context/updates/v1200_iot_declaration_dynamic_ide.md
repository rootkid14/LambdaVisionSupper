# Computer Vision v0.12 — IOT Declaration Engine + Dynamic Automation Objects

## Scope

v0.12 replaces the old single-purpose IOT configuration surface with an IOT Declaration Engine. The Automation control plane is now declaration-driven rather than hard-coded around `device.modbus_1.X1/Y1/Y2`.

## IOT declaration model

A Vision Program now persists `iot.devices[]`. Each Modbus TCP device has a stable declaration id, human/API alias, host, port, unit id and declared points. Points have aliases, Modbus kind (`coil`, `discrete_input`, `holding_register`, `input_register`), address, description and pulse defaults.

Legacy `io` remains in the program for v0.8-v0.11 trigger-runner compatibility. Repository migration seeds a new `modbus_1` declaration from old trigger/OK/NG settings.

## Dynamic object graph

The Endpoint Registry now derives object roots directly from the current draft program:

- `device.<device_alias>`
- `device.<device_alias>.<point_alias>`
- writable coils/registers preserve write metadata
- coil points expose `.pulse(seconds)` actions
- `vision.roi.<roi_alias>` exists as soon as the ROI is declared
- configured Logic aliases exist under `.logic.<alias>.outputs` before any inspection is run
- runtime `VisionRunSnapshot` enriches those objects with concrete leaf outputs and values

The frontend uses a draft endpoint-preview API so unsaved alias/configuration edits appear in IntelliSense immediately.

## IDE UX

Automation IDE v0.12 adds:

- colored safe-DSL syntax (keywords, constants, strings, comments, numbers and namespaces)
- dot-triggered and Ctrl+Space completion backed by the live registry
- source-colored suggestions (`device`, `vision.roi`, `system`, `camera`)
- hierarchical Object / Endpoint Explorer rather than a flat static list
- colored Loop/Event/One-shot service cards

The DSL runtime remains restricted AST execution; there is still no arbitrary Python `exec`, import, filesystem, subprocess or while loop.

## Compatibility

Legacy Control Mapper, trigger runner and `program.io` remain installed. New Automation scripts should prefer declared `program.iot` objects. Program contract version advances to v4.
