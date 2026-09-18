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
    """Project one independent Workspace into legacy program-root runtime contracts."""
    payload = program.model_dump() if hasattr(program, 'model_dump') else program.dict()
    dump = lambda value: value.model_dump() if hasattr(value, 'model_dump') else value.dict()
    payload['master'] = dump(workspace.master)
    payload['working'] = dump(workspace.working)
    payload['iot'] = dump(workspace.iot)
    payload['cameras'] = dump(workspace.cameras)
    payload['active_workspace_id'] = workspace.workspace_id
    return VisionProgramDefinition(**payload)
