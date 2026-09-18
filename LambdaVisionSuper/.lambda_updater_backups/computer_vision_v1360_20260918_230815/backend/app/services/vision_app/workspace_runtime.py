from __future__ import annotations

from typing import Any

from app.services.vision_app.models import VisionProgramDefinition, WorkspaceDefinition
from app.services.vision_app.endpoint_registry import safe_alias


def workspace_by_alias(program: VisionProgramDefinition, alias_or_id: str | None) -> WorkspaceDefinition:
    if not program.workspaces:
        raise RuntimeError('Vision Program has no workspace')
    target = alias_or_id or program.active_workspace_id or program.workspaces[0].workspace_id
    for workspace in program.workspaces:
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        if workspace.workspace_id == target or alias == target:
            return workspace
    return program.workspaces[0]


def projected_program(program: VisionProgramDefinition, workspace: WorkspaceDefinition) -> VisionProgramDefinition:
    payload = program.model_dump() if hasattr(program, 'model_dump') else program.dict()
    payload['master'] = workspace.master.model_dump() if hasattr(workspace.master, 'model_dump') else workspace.master.dict()
    payload['working'] = workspace.working.model_dump() if hasattr(workspace.working, 'model_dump') else workspace.working.dict()
    return VisionProgramDefinition(**payload)
