# Computer Vision v0.13.2 — Context Generator Hotfix

This narrow hotfix repairs the syntax error introduced in the v0.13.1 LLM context generator.

## Root cause

Five architecture summary lines were accidentally embedded inside a single quoted Python string with raw line breaks, causing:

`SyntaxError: unterminated string literal`

## Fix

The architecture summary is emitted as separate strings and updated to match v0.13.1:

- Basler / HTTP camera declaration engine
- one declared camera per workspace
- colored Automation IDE and object explorer
- live `keyboard.*` endpoints
- Online/Offline runtime
- simulator drivers are legacy-hidden

No Computer Vision runtime, API, workspace, camera, IOT, or Automation behavior is changed by this hotfix.
