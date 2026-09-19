from __future__ import annotations

import numpy as np

from app.services.vision_app.automation_manager import AutomationManager
from app.services.vision_app.models import SoftTriggerConfig, VisionProgramDefinition, WorkspaceDefinition
from app.services.vision_app.streaming_runtime import StreamingServiceManager


def test_threshold_preview_matches_trigger_mask():
    config = SoftTriggerConfig(
        roi={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        threshold_mode="bright",
        pixel_threshold=100,
        trigger_pixel_count=2,
        reset_pixel_count=0,
    )
    image = np.zeros((4, 4, 3), dtype=np.uint8)
    image[0, 0] = 255
    image[1, 1] = 200
    metrics = StreamingServiceManager.analyze_frame(image, config)
    preview = StreamingServiceManager.render_threshold_preview(image, config, "mask")
    assert metrics["pixel_count"] == 2
    assert preview.shape == image.shape
    assert int(preview[0, 0, 0]) == 255


class _Repo:
    def __init__(self, program):
        self.program = program
    def get(self, _program_id):
        return self.program


def _program(policy: str):
    ws = WorkspaceDefinition(
        workspace_id="front_ws",
        name="Front",
        alias="front",
        soft_trigger=SoftTriggerConfig(
            enabled=True,
            roi={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
            backpressure_policy=policy,
            queue_capacity=2,
            overflow_policy="drop_oldest",
        ),
    )
    return VisionProgramDefinition(program_id="p", name="P", workspaces=[ws], active_workspace_id=ws.workspace_id)


def test_skip_policy_counts_busy_trigger_without_starting_second_inspection():
    program = _program("skip")
    manager = AutomationManager(repository=_Repo(program))
    manager._soft_dispatch_busy.add("p")
    manager._on_soft_trigger("p", "front", "main", np.zeros((4, 4, 3), dtype=np.uint8), 1)
    metrics = manager._soft_delivery[("p", "front")]
    assert metrics["triggered_total"] == 1
    assert metrics["skipped_busy"] == 1
    assert metrics["queue_depth"] == 0


def test_latest_policy_keeps_one_waiting_frame():
    program = _program("latest")
    manager = AutomationManager(repository=_Repo(program))
    manager._soft_dispatch_busy.add("p")
    manager._on_soft_trigger("p", "front", "main", np.zeros((4, 4, 3), dtype=np.uint8), 1)
    manager._on_soft_trigger("p", "front", "main", np.ones((4, 4, 3), dtype=np.uint8), 2)
    metrics = manager._soft_delivery[("p", "front")]
    assert metrics["queue_depth"] == 1
    assert metrics["replaced_latest"] == 1
    assert len(manager._soft_dispatch_queue["p"]) == 1
    assert manager._soft_dispatch_queue["p"][0]["sequence"] == 2
