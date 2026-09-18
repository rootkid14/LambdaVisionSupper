from pathlib import Path
import sys
import types

import cv2
import numpy as np
import pytest

# The reconstructed updater test tree does not contain app.core; real codebases do.
try:
    import app.core.config  # type: ignore
except ModuleNotFoundError:
    core = types.ModuleType("app.core")
    config = types.ModuleType("app.core.config")
    config.get_base_dir = lambda: Path("/tmp")
    sys.modules.setdefault("app.core", core)
    sys.modules.setdefault("app.core.config", config)

from app.services.vision_app.automation_models import AutomationSystemState
from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.models import (
    MasterRoi, NormalizedRect, VisionProgramDefinition, WorkspaceDefinition, WorkingServiceBinding,
)
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.workspace_runtime import projected_program


def _workspace(workspace_id: str, alias: str) -> WorkspaceDefinition:
    return WorkspaceDefinition(workspace_id=workspace_id, name=alias, alias=alias, camera_id="", input_binding="")


def test_workspace_master_does_not_fallback_to_workspace_1(tmp_path: Path):
    repo = VisionProgramRepository(tmp_path)
    program = VisionProgramDefinition(program_id="p", name="P", workspaces=[_workspace("workspace_1", "front"), _workspace("workspace_2", "side")])
    repo.save(program)
    image = np.full((20, 30, 3), 123, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    repo.save_master_bytes("p", encoded.tobytes(), "workspace_1")
    assert int(repo.load_master("p", "workspace_1").mean()) > 100
    with pytest.raises(FileNotFoundError):
        repo.load_master("p", "workspace_2")


def test_workspace_roi_and_working_configs_are_independent(tmp_path: Path):
    repo = VisionProgramRepository(tmp_path)
    front = _workspace("workspace_1", "front")
    side = _workspace("workspace_2", "side")
    front.master.rois.append(MasterRoi(roi_id="front_roi", name="Front ROI", alias="front_roi", rect=NormalizedRect(x=0.1, y=0.1, w=0.2, h=0.2)))
    front.working.global_scope.logic_services.append(WorkingServiceBinding(binding_id="front_logic", service_id="sampling", alias="front_logic"))
    repo.save(VisionProgramDefinition(program_id="p", name="P", workspaces=[front, side]))
    loaded = repo.get("p")
    assert [r.roi_id for r in loaded.workspaces[0].master.rois] == ["front_roi"]
    assert loaded.workspaces[1].master.rois == []
    assert len(loaded.workspaces[0].working.global_scope.logic_services) == 1
    assert loaded.workspaces[1].working.global_scope.logic_services == []
    projected = projected_program(loaded, loaded.workspaces[1])
    assert projected.master.rois == []
    assert projected.working.global_scope.logic_services == []


def test_legacy_vision_namespace_tracks_active_workspace_not_workspace1_mirror():
    front = _workspace("workspace_1", "front")
    side = _workspace("workspace_2", "side")
    front.master.rois.append(MasterRoi(roi_id="front_roi", name="Front ROI", alias="front_roi", rect=NormalizedRect(x=0.1, y=0.1, w=0.2, h=0.2)))
    side.master.rois.append(MasterRoi(roi_id="side_roi", name="Side ROI", alias="side_roi", rect=NormalizedRect(x=0.2, y=0.2, w=0.2, h=0.2)))
    program = VisionProgramDefinition(program_id="p", name="P", workspaces=[front, side])
    program.master = front.master
    program.working = front.working
    state = AutomationSystemState(program_id="p", active_workspace="side")
    paths = {item.path for item in EndpointRegistry().build(program, state=state)}
    assert "vision.roi.side_roi" in paths
    assert "vision.roi.front_roi" not in paths
    assert "workspace.front.vision.roi.front_roi" in paths
    assert "workspace.side.vision.roi.side_roi" in paths
