# Computer Vision v0.14.2 - Soft Trigger Tuning & Backpressure

Backend-rendered Raw/Gray/Threshold/Overlay tuning views use the same threshold rule as runtime. Soft Trigger inspection is serialized at Program scope with per-Workspace skip/latest/FIFO backpressure policies and queue/drop/wait telemetry.
