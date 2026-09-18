from pathlib import Path
import json
import sys
import types

# Reconstructed updater-test trees may not contain app.core; production trees do.
try:
    import app.core.config  # type: ignore
except ModuleNotFoundError:
    core = types.ModuleType("app.core")
    config = types.ModuleType("app.core.config")
    config.get_base_dir = lambda: Path("/tmp")
    sys.modules.setdefault("app.core", core)
    sys.modules.setdefault("app.core.config", config)

from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.models import (
    CameraDeclaration,
    CameraDeclarationConfig,
    IotDeclarationConfig,
    ModbusDeviceDeclaration,
    ModbusPointDeclaration,
    VisionProgramDefinition,
    WorkspaceDefinition,
)
from app.services.vision_app.repository import VisionProgramRepository, _migrate_payload
from app.services.vision_app.workspace_runtime import projected_program


def _camera(declaration_id: str, alias: str) -> CameraDeclaration:
    return CameraDeclaration(
        declaration_id=declaration_id,
        alias=alias,
        driver="http",
        host="127.0.0.1",
        port=8000,
    )


def _iot(declaration_id: str, alias: str, point_alias: str) -> IotDeclarationConfig:
    return IotDeclarationConfig(
        devices=[
            ModbusDeviceDeclaration(
                declaration_id=declaration_id,
                alias=alias,
                driver="simulated",
                points=[
                    ModbusPointDeclaration(
                        point_id=f"{declaration_id}_x1",
                        alias=point_alias,
                        kind="discrete_input",
                        address=0,
                    )
                ],
            )
        ]
    )


def test_fresh_workspace_has_no_camera_or_iot_inheritance():
    a = WorkspaceDefinition(workspace_id="a", name="A", alias="a")
    b = WorkspaceDefinition(workspace_id="b", name="B", alias="b")
    a.cameras.devices.append(_camera("cam_a", "front"))
    a.iot.devices.extend(_iot("plc_a", "plc_a", "X1").devices)

    assert b.cameras.devices == []
    assert b.iot.devices == []
    assert b.camera_id == ""
    assert b.input_binding == ""


def test_v6_global_resources_migrate_only_into_workspace_1():
    legacy = {
        "version": 6,
        "program_id": "legacy",
        "name": "Legacy",
        "iot": {
            "devices": [
                {
                    "declaration_id": "legacy_plc",
                    "alias": "legacy_plc",
                    "driver": "simulated",
                    "points": [],
                }
            ]
        },
        "cameras": {
            "devices": [
                {
                    "declaration_id": "legacy_cam",
                    "alias": "legacy_cam",
                    "driver": "http",
                    "host": "127.0.0.1",
                    "port": 8000,
                }
            ]
        },
        "workspaces": [
            {
                "workspace_id": "workspace_1",
                "name": "W1",
                "alias": "w1",
                "camera_id": "legacy_cam",
                "input_binding": "camera.legacy_cam.Current_image",
            },
            {
                "workspace_id": "workspace_2",
                "name": "W2",
                "alias": "w2",
                "camera_id": "legacy_cam",
                "input_binding": "camera.legacy_cam.Current_image",
            },
        ],
        "active_workspace_id": "workspace_1",
    }
    migrated = _migrate_payload(json.loads(json.dumps(legacy)))

    assert migrated["version"] >= 7
    assert [x["declaration_id"] for x in migrated["workspaces"][0]["cameras"]["devices"]] == ["legacy_cam"]
    assert [x["declaration_id"] for x in migrated["workspaces"][0]["iot"]["devices"]] == ["legacy_plc"]
    assert migrated["workspaces"][0]["camera_id"] == "legacy_cam"

    assert migrated["workspaces"][1]["cameras"]["devices"] == []
    assert migrated["workspaces"][1]["iot"]["devices"] == []
    assert migrated["workspaces"][1]["camera_id"] == ""
    assert migrated["workspaces"][1]["input_binding"] == ""


def test_repository_preserves_distinct_workspace_resources_and_active_legacy_mirror(tmp_path: Path):
    repo = VisionProgramRepository(tmp_path)
    front = WorkspaceDefinition(
        workspace_id="workspace_1",
        name="Front",
        alias="front_ws",
        cameras=CameraDeclarationConfig(devices=[_camera("cam_front", "front_cam")]),
        iot=_iot("plc_front", "plc_front", "X_FRONT"),
        camera_id="cam_front",
    )
    side = WorkspaceDefinition(
        workspace_id="workspace_2",
        name="Side",
        alias="side_ws",
        cameras=CameraDeclarationConfig(devices=[_camera("cam_side", "side_cam")]),
        iot=_iot("plc_side", "plc_side", "X_SIDE"),
        camera_id="cam_side",
    )
    program = VisionProgramDefinition(
        program_id="p",
        name="P",
        workspaces=[front, side],
        active_workspace_id="workspace_2",
    )

    saved = repo.save(program)
    loaded = repo.get("p")

    assert loaded.workspaces[0].camera_id == "cam_front"
    assert loaded.workspaces[0].input_binding == "camera.front_cam.Current_image"
    assert loaded.workspaces[1].camera_id == "cam_side"
    assert loaded.workspaces[1].input_binding == "camera.side_cam.Current_image"
    assert loaded.workspaces[0].cameras.devices[0].declaration_id == "cam_front"
    assert loaded.workspaces[1].cameras.devices[0].declaration_id == "cam_side"
    assert loaded.workspaces[0].iot.devices[0].declaration_id == "plc_front"
    assert loaded.workspaces[1].iot.devices[0].declaration_id == "plc_side"

    # Root Camera/IOT remain compatibility mirrors only; they follow the saved active Workspace.
    assert saved.cameras.devices[0].declaration_id == "cam_side"
    assert saved.iot.devices[0].declaration_id == "plc_side"


def test_projected_endpoint_registry_exposes_only_selected_workspace_camera_and_iot():
    front = WorkspaceDefinition(
        workspace_id="workspace_1",
        name="Front",
        alias="front_ws",
        cameras=CameraDeclarationConfig(devices=[_camera("cam_front", "front_cam")]),
        iot=_iot("plc_front", "plc_front", "X_FRONT"),
        camera_id="cam_front",
    )
    side = WorkspaceDefinition(
        workspace_id="workspace_2",
        name="Side",
        alias="side_ws",
        cameras=CameraDeclarationConfig(devices=[_camera("cam_side", "side_cam")]),
        iot=_iot("plc_side", "plc_side", "X_SIDE"),
        camera_id="cam_side",
    )
    program = VisionProgramDefinition(program_id="p", name="P", workspaces=[front, side])

    front_paths = {x.path for x in EndpointRegistry().build(projected_program(program, front))}
    side_paths = {x.path for x in EndpointRegistry().build(projected_program(program, side))}

    assert "camera.front_cam.capture" in front_paths
    assert "device.plc_front.X_FRONT" in front_paths
    assert "camera.side_cam.capture" not in front_paths
    assert "device.plc_side.X_SIDE" not in front_paths

    assert "camera.side_cam.capture" in side_paths
    assert "device.plc_side.X_SIDE" in side_paths
    assert "camera.front_cam.capture" not in side_paths
    assert "device.plc_front.X_FRONT" not in side_paths
