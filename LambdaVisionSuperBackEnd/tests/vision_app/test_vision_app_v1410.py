from __future__ import annotations

import numpy as np

from app.services.vision_app.automation_models import AutomationSystemState
from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.models import (
    CameraDeclaration,
    CameraDeclarationConfig,
    NormalizedRect,
    SoftTriggerConfig,
    VisionProgramDefinition,
    WorkspaceDefinition,
)
from app.services.vision_app.streaming_runtime import SoftTriggerRuntimeState, StreamingServiceManager


def _workspace(alias: str, camera_id: str) -> WorkspaceDefinition:
    return WorkspaceDefinition(
        workspace_id=f"{alias}_ws",
        name=alias,
        alias=alias,
        camera_id=camera_id,
        input_binding=f"camera.main.Current_image",
        cameras=CameraDeclarationConfig(
            devices=[
                CameraDeclaration(
                    declaration_id=camera_id,
                    alias="main",
                    driver="basler",
                    basler_device_id=f"SERIAL-{alias}",
                )
            ]
        ),
        soft_trigger=SoftTriggerConfig(
            enabled=True,
            roi=NormalizedRect(x=0, y=0, w=1, h=1),
            pixel_threshold=100,
            trigger_pixel_count=10,
            reset_pixel_count=0,
            cooldown_ms=0,
        ),
    )


def test_workspace_owned_stream_identity_and_threshold():
    front = _workspace("front", "front_cam")
    side = _workspace("side", "side_cam")
    program = VisionProgramDefinition(
        program_id="p",
        name="P",
        workspaces=[front, side],
        active_workspace_id=front.workspace_id,
    )

    _, front_camera = StreamingServiceManager.workspace_camera(program, "front")
    _, side_camera = StreamingServiceManager.workspace_camera(program, "side")
    assert front_camera.basler_device_id == "SERIAL-front"
    assert side_camera.basler_device_id == "SERIAL-side"

    bright = np.full((8, 8, 3), 255, dtype=np.uint8)
    metrics = StreamingServiceManager.analyze_frame(bright, front.soft_trigger)
    assert metrics["pixel_count"] == 64


def test_full_keyboard_and_soft_trigger_endpoints():
    ws = _workspace("front", "front_cam")
    program = VisionProgramDefinition(
        program_id="p",
        name="P",
        workspaces=[ws],
        active_workspace_id=ws.workspace_id,
    )
    state = AutomationSystemState(
        program_id="p",
        active_workspace="front",
        keyboard_states={"key.A": True},
        stream_states={"front": {"running": True, "fps": 22.5, "sequence": 8}},
        soft_trigger_states={"front": {"armed": True, "pixel_count": 50, "active_ratio": .25, "fires": 2}},
    )
    # v0.13.6 projects active workspace resources before cataloguing; emulate that
    # by mirroring its resources into the compatibility root when necessary.
    program.iot = ws.iot
    program.cameras = ws.cameras
    paths = {e.path: e for e in EndpointRegistry().build(program, state=state)}
    assert paths["keyboard.key.A"].last_value is True
    assert paths["workspace.front.soft_trigger.pixel_count"].last_value == 50
