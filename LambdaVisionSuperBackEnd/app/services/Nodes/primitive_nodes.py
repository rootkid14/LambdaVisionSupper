from pydantic import BaseModel, Field
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType

# ==========================================
# 1. NODE TẠO CHUỖI (MAKE STRING)
# ==========================================
class MakeStringOutput(BaseModel):
    # Field description sẽ đóng vai trò là DataType gửi cho Frontend
    value: str = Field(title="String", description=UIDataType.STRING.value)

@registry_node
class MakeStringNode(BaseNode[None, MakeStringOutput]):
    INPUT_SCHEMA = None  # Không có đầu vào
    OUTPUT_SCHEMA = MakeStringOutput
    
    NODE_TYPE = NodeType.IN_LINE
    INLINE_TYPE = "text" # Báo cho FE hiện ô nhập Text
    
    UI_LABEL = "Make String"
    UI_DESCRIPTION = "Khởi tạo một hằng số chuỗi (Text)"
    UI_COLOR = "bg-yellow-600"

    async def execute(self) -> None:
        # Xử lý giá trị Inline
        val = str(self.inline_val) if self.inline_val is not None else ""
        
        # Gán trực tiếp vào Output
        self.local_output = self.OUTPUT_SCHEMA(value=val)


# ==========================================
# 2. NODE TẠO SỐ (MAKE NUMBER)
# ==========================================
class MakeNumberOutput(BaseModel):
    value: float = Field(title="Number", description=UIDataType.NUMBER.value)

@registry_node
class MakeNumberNode(BaseNode[None, MakeNumberOutput]):
    INPUT_SCHEMA = None
    OUTPUT_SCHEMA = MakeNumberOutput
    
    NODE_TYPE = NodeType.IN_LINE
    INLINE_TYPE = "number" # Báo cho FE hiện ô nhập Số
    
    UI_LABEL = "Make Number"
    UI_DESCRIPTION = "Khởi tạo một hằng số học (Int/Float)"
    UI_COLOR = "bg-emerald-600"

    async def execute(self) -> None:
        try:
            val = float(self.inline_val) if self.inline_val is not None else 0.0
        except ValueError:
            raise ValueError(f"Giá trị '{self.inline_val}' không phải là một số hợp lệ.")
            
        self.local_output = self.OUTPUT_SCHEMA(value=val)


# ==========================================
# 3. NODE TẠO LOGIC (MAKE BOOLEAN)
# ==========================================
class MakeBooleanOutput(BaseModel):
    value: bool = Field(title="Boolean", description=UIDataType.BOOLEAN.value)

@registry_node
class MakeBooleanNode(BaseNode[None, MakeBooleanOutput]):
    INPUT_SCHEMA = None
    OUTPUT_SCHEMA = MakeBooleanOutput
    
    NODE_TYPE = NodeType.IN_LINE
    # Mở rộng cho Frontend: Nếu là boolean, FE có thể render cái Switch/Checkbox thay vì ô input
    INLINE_TYPE = "checkbox" 
    
    UI_LABEL = "Make Boolean"
    UI_DESCRIPTION = "Khởi tạo giá trị Đúng/Sai (True/False)"
    UI_COLOR = "bg-red-600"

    async def execute(self) -> None:
        # Nếu inline_val là chuỗi "true", "false" thì ép kiểu, nếu không thì dùng bool()
        if isinstance(self.inline_val, str):
            val = self.inline_val.lower() == 'true'
        else:
            val = bool(self.inline_val)
            
        self.local_output = self.OUTPUT_SCHEMA(value=val)


