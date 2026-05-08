import os
import base64
import mimetypes
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType

class LoadAsBase64Input(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    image_path : str = Field(default="", title="Image Path", description=UIDataType.STRING.value)

class LoadAsBase64Output(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    ouput_base64 : str = Field(default="", title="Output Base64 Image", description=UIDataType.BASE64.value)

@registry_node  # <-- Bắt buộc phải có để Engine đăng ký khối này
class LoadAsBase64(BaseNode[LoadAsBase64Input, LoadAsBase64Output]):
    INPUT_SCHEMA = LoadAsBase64Input
    OUTPUT_SCHEMA = LoadAsBase64Output
    NODE_TYPE = NodeType.PROGRAM  # <-- Bắt buộc để Frontend vẽ giao diện
    UI_LABEL = "Load Image as Base64"
    UI_DESCRIPTION = "Load Image as Base64"
    REQUIRE_TIMEOUT = False
    UI_COLOR = "#202020"

    async def execute(self):
        path = str(self.local_input.image_path).strip()
        
        # 1. Kiểm tra an toàn: File có tồn tại không?
        if not os.path.exists(path):
            raise RuntimeError(f"Không tìm thấy file ảnh tại đường dẫn: {path}")
            
        # 2. Nhận diện định dạng ảnh (jpeg, png...)
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            mime_type = "image/jpeg" # Fallback an toàn nếu không đoán được
            
        # 3. Đọc file nhị phân và mã hóa Base64
        with open(path, "rb") as image_file:
            encoded_bytes = base64.b64encode(image_file.read())
            encoded_string = encoded_bytes.decode('utf-8')
            
        # 4. Gắn tiền tố (prefix) để Frontend (Debug Panel) có thể render ảnh Preview ngay lập tức
        final_base64 = f"data:{mime_type};base64,{encoded_string}"
        
        # 5. Xuất dữ liệu ra chân Output (Giữ nguyên tên biến ouput_base64 của bạn)
        self.local_output = self.OUTPUT_SCHEMA(
            execute_out="GO",
            ouput_base64=final_base64
        )