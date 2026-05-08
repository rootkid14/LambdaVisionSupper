from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node, create_model
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType, map_fe_type_to_python
import random
from typing import Any

class PrintInput(BaseModel):
    # Field description sẽ đóng vai trò là DataType gửi cho Frontend
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    value: str = Field(title="String", description=UIDataType.STRING.value)

class PrintOnput(BaseModel):
    # Field description sẽ đóng vai trò là DataType gửi cho Frontend
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)

@registry_node
class PrintNode(BaseNode[PrintInput, PrintOnput]):
    INPUT_SCHEMA = PrintInput  # Không có đầu vào
    OUTPUT_SCHEMA = PrintOnput
    
    NODE_TYPE = NodeType.PROGRAM
    INLINE_TYPE = "text" # Báo cho FE hiện ô nhập Text
    
    UI_LABEL = "Print"
    UI_DESCRIPTION = "Print TO BE Terminal"
    UI_COLOR = "bg-yellow-600"

    async def execute(self) -> None:
        # Xử lý giá trị Inline
        print(self.local_input.value)

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


class RandomIntInput(BaseModel):
    min_val: int = Field(default=0, title="Min Value", description=UIDataType.NUMBER.value)
    max_val: int = Field(default=100, title="Max Value", description=UIDataType.NUMBER.value)

class RandomNumberOutput(BaseModel):
    result: float = Field(..., title="Result", description=UIDataType.NUMBER.value)

@registry_node
class RandomIntNode(BaseNode[RandomIntInput, RandomNumberOutput]):
    INPUT_SCHEMA = RandomIntInput
    OUTPUT_SCHEMA = RandomNumberOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Random Int"
    UI_DESCRIPTION = "Sinh số nguyên ngẫu nhiên trong khoảng [Min, Max]"
    UI_COLOR = "bg-green-700"
    REQUIRE_TIMEOUT = False

    async def execute(self) -> None:
        min_v = int(self.local_input.min_val)
        max_v = int(self.local_input.max_val)
        
        # Đảm bảo min không lớn hơn max
        if min_v > max_v:
            min_v, max_v = max_v, min_v
            
        val = random.randint(min_v, max_v)
        self.local_output = self.OUTPUT_SCHEMA(result=float(val))

# --- RANDOM FLOAT ---
class RandomFloatInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # Bổ sung chân Execute In để nhận luồng chạy
    min_val: float = Field(default=0.0, title="Min Value", description=UIDataType.NUMBER.value)
    max_val: float = Field(default=1.0, title="Max Value", description=UIDataType.NUMBER.value)

@registry_node
class RandomFloatNode(BaseNode[RandomFloatInput, RandomNumberOutput]):
    INPUT_SCHEMA = RandomFloatInput
    OUTPUT_SCHEMA = RandomNumberOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Random Float"
    UI_DESCRIPTION = "Sinh số thực ngẫu nhiên trong khoảng [Min, Max]"
    UI_COLOR = "bg-green-600"
    REQUIRE_TIMEOUT = False

    # 1. Khai báo trường cấu hình để Frontend tự động vẽ ô nhập liệu
    CONFIG_FIELDS = [
        UIConfigField(
            id="decimal_places", 
            label="Decimal Places", 
            type=UIConfigType.NUMBER.value, 
            default=2  # Mặc định lấy 2 chữ số thập phân
        )
    ]

    async def execute(self) -> None:
        min_v = float(self.local_input.min_val)
        max_v = float(self.local_input.max_val)
        
        if min_v > max_v:
            min_v, max_v = max_v, min_v
            
        # 2. Đọc giá trị cấu hình từ giao diện (Fallback về 2 nếu có lỗi)
        decimals = int(self.get_config_field_value("decimal_places", 2))
        
        # 3. Sinh số ngẫu nhiên và làm tròn theo hệ số thập phân đã cấu hình
        raw_val = random.uniform(min_v, max_v)
        final_val = round(raw_val, decimals)
        
        self.local_output = self.OUTPUT_SCHEMA(
            execute_out="GO",
            result=final_val
        )


class InternalMemoryWriteInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)

class InternalMemoryWriteOutput(BaseModel):
    execute: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)

@registry_node
class InternalMemoryWrite(BaseNode[InternalMemoryWriteInput, InternalMemoryWriteOutput]):
    INPUT_SCHEMA = InternalMemoryWriteInput
    OUTPUT_SCHEMA = InternalMemoryWriteOutput
    NODE_TYPE = NodeType.MEMORY
    UI_LABEL = "Memory Table Write"
    UI_DESCRIPTION = "Write multiple values into system Memory"
    UI_COLOR = "bg-red-600"

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        
        dynamic_inputs = node_data.get("inputs", [])
        fields = {}

        for pin in dynamic_inputs:
            pin_id = pin["id"]
            data_type_str = pin.get("dataType")
            
            # Bỏ qua chân execute
            if data_type_str == UIDataType.EXECUTE.value:
                continue
                
            py_type = map_fe_type_to_python(data_type_str)
            mem_key = pin.get("label", pin_id)
            
            fields[pin_id] = (py_type, Field(default=None, title=mem_key))

        if fields:
            self.INPUT_SCHEMA = create_model(f'DynamicMemWrite_{self.node_id}', __config__=ConfigDict(arbitrary_types_allowed=True), **fields)
        else:
            self.INPUT_SCHEMA = None

    async def execute(self) -> None:
        if self.local_input:
            input_dict = self.local_input.model_dump()
            
            for pin_id, val in input_dict.items():
                # Lấy đúng tên label mà FE gửi xuống (chính là tên biến người dùng gõ)
                mem_key = next((p.get("label", pin_id) for p in self.node_data.get("inputs", []) if p["id"] == pin_id), pin_id)
                
                # Ghi vào extra_memory
                self.parent.extra_memory[mem_key] = val
                


# 1. Định nghĩa Schema Output Tĩnh (có sẵn chân tên là "value")
class InternalMemoryReadOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    value: Any = Field(default=None, title="Value", description=UIDataType.ANY.value)

# 2. Khai báo Node
@registry_node
class InternalMemoryRead(BaseNode[None, InternalMemoryReadOutput]):
    INPUT_SCHEMA = None
    OUTPUT_SCHEMA = InternalMemoryReadOutput
    NODE_TYPE = NodeType.MEMORY_READ # <--- Đổi thành TYPE mới
    UI_LABEL = "Memory Table Read"
    UI_DESCRIPTION = "Read a selected variable from Memory"
    UI_COLOR = "bg-purple-600"

    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)
        # Lấy tên biến đã được user chọn từ Dropdown FE gửi xuống
        self.selected_var = node_data.get("selectedVar", "")

    async def execute(self):
        # Lấy giá trị biến từ Memory Pool
        val = self.parent.extra_memory.get(self.selected_var)
        
        # Đẩy ra chân "value" để các Node khác lấy xài
        self.local_output = self.OUTPUT_SCHEMA(value=val)