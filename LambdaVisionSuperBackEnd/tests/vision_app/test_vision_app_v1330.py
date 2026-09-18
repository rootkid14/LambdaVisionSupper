from app.services.vision_app.automation_manager import AutomationManager
from app.services.vision_app.models import VisionProgramDefinition, WorkspaceDefinition


class Repo:
    def __init__(self, program):
        self.program = program
    def get(self, _):
        return self.program


def test_workspace_activation_sequence_changes_only_on_real_change():
    program = VisionProgramDefinition(
        program_id="p",
        name="P",
        workspaces=[
            WorkspaceDefinition(workspace_id="workspace_1", name="One", alias="one"),
            WorkspaceDefinition(workspace_id="workspace_2", name="Two", alias="two"),
        ],
        active_workspace_id="workspace_1",
    )
    manager = AutomationManager(repository=Repo(program))
    state = manager.state("p")
    assert state.workspace_activation_sequence == 0

    manager.activate_workspace("p", "two")
    assert state.active_workspace == "two"
    assert state.workspace_activation_sequence == 1

    manager.activate_workspace("p", "two")
    assert state.workspace_activation_sequence == 1

    manager.activate_workspace("p", "one")
    assert state.active_workspace == "one"
    assert state.workspace_activation_sequence == 2
