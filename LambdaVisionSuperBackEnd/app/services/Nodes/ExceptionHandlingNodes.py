from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType
from typing import Any


class CheckNoneInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_int : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    check_value : Any = Field(default=None, title="Value to check", description=UIDataType.ANY.value)

class CheckNoneOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    is_not_none: Any = Field(default="GO", title="Is Valid", description=UIDataType.EXECUTE.value)
    is_none: Any = Field(default="GO", title="Is None", description=UIDataType.EXECUTE.value)


@registry_node
class CheckNoneNode(BaseNode[CheckNoneInput, CheckNoneOutput]):
    INPUT_SCHEMA = CheckNoneInput
    OUTPUT_SCHEMA = CheckNoneOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Is Valid?"
    UI_DESCRIPTION = "Check if the value is None"
    UI_COLOR = "#A70000"

    async def execute(self):
        is_none = self.local_input.check_value is None
        if self.local_input.check_value is None:
            return "is_none"
        else: 
            return "is_not_none"


class RaiseErrorInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)

@registry_node
class RaiseErrorNode(BaseNode[RaiseErrorInput, None]):
    INPUT_SCHEMA = RaiseErrorInput
    OUTPUT_SCHEMA = None
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "RAISE ERROR"
    UI_DESCRIPTION = "Raise an exception with custom message"
    UI_COLOR = "#FF0000"

    CONFIG_FIELDS = [
        UIConfigField(
            id= "error_message",
            label="Error Message",
            type=UIConfigType.TEXT.value,
            default="SYSTEM ERROR"
        )
    ]

    async def execute(self) -> None:
        msg = self.get_config_field_value("error_message", "SYSTEM ERROR")

        raise Exception(f"[USER ASSERT]: {msg}")