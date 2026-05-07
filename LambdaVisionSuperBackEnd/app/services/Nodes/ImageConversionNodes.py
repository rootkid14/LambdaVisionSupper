from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType
from app.services.utils.image_utils import base64_to_cv2, cv2_to_base64
from typing import Any
import numpy as np


# ==========================================
# 1. NODE: BASE64 -> CV2
# ==========================================
class Base64ToCV2Input(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute In
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    base64_image : Any = Field(default=None, title="Base64 Image", description=UIDataType.BASE64.value)

class Base64ToCV2Output(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute Out
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    cv2_image : np.ndarray = Field(default=None, title="CV2 Image", description=UIDataType.NUMPY_ARRAY.value)

@registry_node
class Base64ToCV2ConvertNode(BaseNode[Base64ToCV2Input, Base64ToCV2Output]):
    INPUT_SCHEMA = Base64ToCV2Input
    OUTPUT_SCHEMA = Base64ToCV2Output
    NODE_TYPE = NodeType.PROGRAM  # <--- THÊM NODE_TYPE (Type 1)
    UI_LABEL = "Base64 -> CV2"
    UI_DESCRIPTION = "Convert Base 64 Image to CV2 Image"
    UI_COLOR = "#1A5300"

    async def execute(self):
        result = base64_to_cv2(self.local_input.base64_image)
        # Bổ sung truyền giá trị cho execute_out
        self.local_output = self.OUTPUT_SCHEMA(execute_out="GO", cv2_image=result)


# ==========================================
# 2. NODE: CV2 -> BASE64
# ==========================================
class CV2ToBase64Input(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute In
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    cv2_image : np.ndarray = Field(default=None, title="CV2 Image", description=UIDataType.NUMPY_ARRAY.value)
    
class CV2ToBase64Output(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute Out
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    base64_image : Any = Field(default=None, title="Base64 Image", description=UIDataType.BASE64.value)
    
@registry_node
class CV2ToBase64ConvertNode(BaseNode[CV2ToBase64Input, CV2ToBase64Output]):
    INPUT_SCHEMA = CV2ToBase64Input
    OUTPUT_SCHEMA = CV2ToBase64Output
    NODE_TYPE = NodeType.PROGRAM  # <--- THÊM NODE_TYPE (Type 1)
    UI_LABEL = "CV2 --> Base64"
    UI_DESCRIPTION = "Convert CV2 to Base64 Image"
    UI_COLOR = "#9E5400"

    async def execute(self):
        result = cv2_to_base64(self.local_input.cv2_image)
        # Bổ sung truyền giá trị cho execute_out
        self.local_output = self.OUTPUT_SCHEMA(execute_out="GO", base64_image=result)