from app.services.vision_app.control_runtime import ControlMapperRuntime
from app.services.vision_app.models import ScopePipelineConfig, VisionProgramDefinition


def test_default_control_mapper_supports_keyboard_and_modbus():
    program = VisionProgramDefinition(program_id="p", name="P")
    assert "run_inspection" in ControlMapperRuntime.actions_for_keyboard(program.control, "F8")
    assert "clear_working_screen" in ControlMapperRuntime.actions_for_keyboard(program.control, "Escape")
    assert "run_inspection" in ControlMapperRuntime.actions_for_modbus_trigger(program.control)


def test_new_program_version_reserves_decision_for_ide():
    program = VisionProgramDefinition(program_id="p", name="P")
    assert program.version >= 4
    assert hasattr(program, "control")
    scope = ScopePipelineConfig()
    assert scope.enable_decision is False
