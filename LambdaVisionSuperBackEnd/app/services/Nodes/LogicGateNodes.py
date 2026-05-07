from pydantic import BaseModel, Field, ConfigDict
from typing import Any, List
from app.services.node_registry import BaseNode, registry_node, create_model
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType, TokenStatus


class LogicGateInput(BaseModel):
    val_a: bool = Field(default=False, title="Value A", description=UIDataType.BOOLEAN.value)
    val_b: bool = Field(default=False, title="Value B", description=UIDataType.BOOLEAN.value)

class LogicGateOutput(BaseModel):
    result: bool = Field(..., title="Result", description=UIDataType.BOOLEAN.value)


# ==========================================
# 1. AND GATE NODE
# ==========================================
@registry_node
class LogicAndNode(BaseNode[LogicGateInput, LogicGateOutput]):
    INPUT_SCHEMA = LogicGateInput
    OUTPUT_SCHEMA = LogicGateOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "AND Gate"
    UI_DESCRIPTION = "Trả về True nếu cả A VÀ B đều là True"
    UI_COLOR = "bg-orange-600"

    async def execute(self) -> None:
        a = self.local_input.val_a
        b = self.local_input.val_b
        
        # Phép toán AND
        final_val = a and b
        
        self.local_output = self.OUTPUT_SCHEMA(result=final_val)


# ==========================================
# 2. OR GATE NODE
# ==========================================
@registry_node
class LogicOrNode(BaseNode[LogicGateInput, LogicGateOutput]):
    INPUT_SCHEMA = LogicGateInput
    OUTPUT_SCHEMA = LogicGateOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "OR Gate"
    UI_DESCRIPTION = "Trả về True nếu A HOẶC B là True"
    UI_COLOR = "bg-orange-600"

    async def execute(self) -> None:
        a = self.local_input.val_a
        b = self.local_input.val_b
        
        # Phép toán OR
        final_val = a or b
        
        self.local_output = self.OUTPUT_SCHEMA(result=final_val)


class DynamicSwitchInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    # Chân Any: Chấp nhận mọi loại dữ liệu cắm vào (Number, Boolean, String...)
    match_value: Any = Field(default=None, title="Value to Match", description=UIDataType.ANY.value)

@registry_node
class DynamicUniversalSwitchNode(BaseNode):
    INPUT_SCHEMA = DynamicSwitchInput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Dynamic Switch"
    UI_DESCRIPTION = "Rẽ nhánh động đa kiểu dữ liệu (String, Number, Boolean)"
    UI_COLOR = "bg-red-700"

    # Cấu hình để Frontend hiện Dropdown chọn kiểu so sánh
    CONFIG_FIELDS = [
        UIConfigField(
            id="compare_type",
            label="Kiểu So Sánh",
            type=UIConfigType.SELECT.value,
            options=["String", "Number", "Boolean"],
            default="String"
        )
    ]

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        
        # 1. Đọc cấu hình từ Frontend
        self.compare_type = self.get_config_field_value("compare_type", "String")
        self.cases: List[Any] = self.node_data.get("cases", [])
        
        # 2. TẠO SCHEMA ĐỘNG AN TOÀN
        output_fields = {}
        self.case_pin_mapping = {} # Bản đồ dịch: "Giá trị" -> "Tên Chân cắm"
        
        # Duyệt qua các case người dùng nhập trên giao diện
        for index, case_val in enumerate(self.cases):
            # Dùng index (0, 1, 2...) làm tên biến để tránh lỗi ký tự đặc biệt trong Python
            pin_id = f"out_case_{index}" 
            
            # Lưu vào bản đồ ánh xạ (Ép case_val thành string để làm key của Dictionary)
            self.case_pin_mapping[str(case_val)] = pin_id
            
            # Khởi tạo chân cắm Pydantic
            output_fields[pin_id] = (Any, Field(default=None, title=f"Case: {case_val}", description=UIDataType.EXECUTE.value))
            
        # Luôn luôn phải có một chân Default
        output_fields["out_default"] = (Any, Field(default=None, title="Default", description=UIDataType.EXECUTE.value))

        # 3. Biên dịch Schema
        self.OUTPUT_SCHEMA = create_model(
            f'DynamicSwitchOutput_{self.node_id}',
            __config__=ConfigDict(arbitrary_types_allowed=True),
            **output_fields
        )

    async def execute(self) -> str:
        """Xử lý Data, ép kiểu và trả về chân cắm đích để Engine tự Route Token"""
        raw_val = self.local_input.match_value
        cases = self.node_data.get("cases", [])
        
        # 1. ÉP KIỂU DỮ LIỆU ĐẦU VÀO (MATCH VALUE)
        if self.compare_type == "String":
            compare_val = str(raw_val)
        elif self.compare_type == "Number":
            try: compare_val = float(raw_val)
            except: compare_val = 0.0
        elif self.compare_type == "Boolean":
            if isinstance(raw_val, str):
                compare_val = str(raw_val).lower() in ['true', '1', 'yes']
            else:
                compare_val = bool(raw_val)
        else:
            compare_val = str(raw_val)

        # 2. SO SÁNH VỚI TỪNG CASE TRONG MẢNG
        for index, case_val in enumerate(cases):
            # Ép kiểu cho target_val (giá trị case lấy từ UI)
            if self.compare_type == "String":
                target_val = str(case_val)
            elif self.compare_type == "Number":
                try: target_val = float(case_val)
                except: target_val = 0.0
            elif self.compare_type == "Boolean":
                if isinstance(case_val, str):
                    target_val = str(case_val).lower() in ['true', '1', 'yes']
                else:
                    target_val = bool(case_val)
            else:
                target_val = str(case_val)

            # Nếu khớp hoàn toàn, trả về đúng id của chân cắm đó
            if compare_val == target_val:
                return f"out_case_{index}"

        # Nếu không khớp bất kỳ case nào, rẽ nhánh vào Default
        return "out_default"
        
