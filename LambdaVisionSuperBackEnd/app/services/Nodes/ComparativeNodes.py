from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType
from typing import Any


class CompareNumberInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    number_a : float = Field(default=0, title="Number A", description=UIDataType.NUMBER.value)
    number_b : float = Field(default=0, title="Number B", description=UIDataType.NUMBER.value)

class CompareNumberOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_true : Any = Field(default="GO", title="is True", description=UIDataType.EXECUTE.value)
    execute_false: Any = Field(default="GO", title="is False", description=UIDataType.EXECUTE.value)

@registry_node
class CompareNumbersNode(BaseNode[CompareNumberInput, CompareNumberOutput]):
    INPUT_SCHEMA = CompareNumberInput
    OUTPUT_SCHEMA = CompareNumberOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Compare 2 Numbers"
    UI_DESCRIPTION = "Compare 2 numbers"
    UI_COLOR = "#202020"

    CONFIG_FIELDS = [
        UIConfigField(
            id="operator",
            label="Operator",
            default="==",
            options=["==", ">=", "<=", "<", ">", "!="],
            type = UIConfigType.SELECT
        )
    ]

    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)
        self.operator = self.get_config_field_value("operator")

    async def execute(self):
        number_a = self.local_input.number_a
        number_b = self.local_input.number_b
        result : bool = False
        match self.operator:
            case "==":
                result = (number_a == number_b)
            case ">=":
                result = (number_a >= number_b)
            case "<=":
                result = (number_a <= number_b)
            case "<":
                result = (number_a < number_b)
            case ">":
                result = (number_a > number_b)
            case "!=":
                result = (number_a != number_b)
        
        if result:
            return "execute_true"
        else:
            return "execute_false"


class CompareStringInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    string_a : str = Field(default="", title="", description=UIDataType.STRING.value)
    string_b : str = Field(default="", title="", description=UIDataType.STRING.value)

class CompareStringOuput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_true : Any = Field(default="GO", title="is True", description=UIDataType.EXECUTE.value)
    execute_false: Any = Field(default="GO", title="is False", description=UIDataType.EXECUTE.value)

@registry_node
class CompareStringNode(BaseNode[CompareStringInput, CompareStringOuput]):
    INPUT_SCHEMA = CompareStringInput
    OUTPUT_SCHEMA = CompareStringOuput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Compare 2 Strings"
    UI_DESCRIPTION = "Compare 2 Strings"
    UI_COLOR = "bg-amber-500"


    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)
        self.operator = self.get_config_field_value("operator")

    async def execute(self):
        string_a = self.local_input.string_a
        string_b = self.local_input.string_b
        result : bool = (string_a == string_b)
        
        if result:
            return "execute_true"
        else:
            return "execute_false"

