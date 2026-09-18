from app.services.vision_app.models import ScopePipelineConfig, VisionProgramDefinition


def test_new_scope_quick_controls_are_enabled_by_default():
    scope = ScopePipelineConfig()
    assert scope.enable_filter is True
    assert scope.enable_logic is True
    assert scope.enable_decision is False


def test_new_program_global_scope_uses_enabled_defaults():
    program = VisionProgramDefinition(program_id="p", name="P")
    assert program.working.global_scope.enable_filter is True
    assert program.working.global_scope.enable_logic is True
