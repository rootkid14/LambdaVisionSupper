# Computer Vision v0.13.1 — Workspace / Camera / Keyboard cleanup

- Fix `+ Workspace` stale-state bug.
- One Workspace binds to exactly one declared Camera (`camera_id`); `input_binding` remains derived runtime compatibility data.
- Remove Developer Simulator from active UI and hide simulated drivers. Legacy simulator data/runtime remains readable only for backward compatibility.
- HTTP Camera Custom API now supports named DSL arguments and explicit `{placeholder}` substitution. Example: `camera.pi.focus(x=0.5, y=0.5, w=1.0, h=1.0)`.
- Add live `keyboard.*` Automation endpoints such as `keyboard.space`, arrows and F1-F12.
- ONLINE/OFFLINE top-level control uses high-contrast green/red states.
