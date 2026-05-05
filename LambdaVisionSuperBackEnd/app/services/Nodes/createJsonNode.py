from typing import Dict, Any, List
from pydantic import Field, create_model, BaseModel, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, map_fe_type_to_python, UIConfigField, UIConfigType

@registry_node
class CreateJSONNode(BaseNode):
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Create JSON"
    UI_DESCRIPTION = "Đóng gói các đầu vào thành một đối tượng JSON"
    UI_COLOR = "bg-amber-500"

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)

        # 1. Tạo Dynamic Input Schema dựa trên cấu hình từ FE
        dynamic_inputs = node_data.get("inputs", [])
        input_fields = {}
        for pin in dynamic_inputs:
            pin_id = pin["id"]
            # Sử dụng map_fe_type_to_python đã cập nhật ở trên
            py_type = map_fe_type_to_python(pin.get("dataType"))
            input_fields[pin_id] = (py_type, Field(title=pin.get("label", pin_id)))

        if input_fields:
            self.INPUT_SCHEMA = create_model(
                f'CreateJSONInput_{self.node_id}',
                **input_fields,
                __config__=ConfigDict(arbitrary_types_allowed=True)
            )

        # 2. Định nghĩa Output Schema cố định trả về 1 chân duy nhất
        self.OUTPUT_SCHEMA = create_model(
            f'CreateJSONOutput_{self.node_id}',
            json_data=(Dict[str, Any], Field(title="JSON Output", description="json")),
            __config__=ConfigDict(arbitrary_types_allowed=True)
        )

    async def execute(self) -> None:
        """
        Lấy toàn bộ dữ liệu từ các chân Input đã được Pydantic validate 
        và nén chúng vào một dictionary.
        """
        # local_input chứa dữ liệu đã được resolve_and_execute gom về
        if self.local_input:
            data_dict = self.local_input.model_dump()
        else:
            data_dict = {}

        # Gán vào chân output duy nhất để các node sau có thể sử dụng
        self.local_output = self.OUTPUT_SCHEMA(json_data=data_dict)




# 1. Định nghĩa Input cố định
class ExtractJSONInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    json_data: Dict[str, Any] = Field(..., title="JSON Data", description="json")

@registry_node
class ExtractJSONNode(BaseNode):
    INPUT_SCHEMA = ExtractJSONInput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Extract JSON"
    UI_DESCRIPTION = "Bóc tách dữ liệu từ JSON thông qua đường dẫn (Path)"
    UI_COLOR = "bg-fuchsia-600" # Màu hồng tím để phân biệt với khối Build JSON

    # Thêm cấu hình để xử lý trường hợp tìm không thấy Key
    UI_CONFIG_FIELDS = [
        UIConfigField(
            id="on_missing_key",
            label="Xử lý khi thiếu Key",
            type=UIConfigType.SELECT,
            options=["Bỏ qua (Null)", "Báo lỗi (Crash)"],
            default="Bỏ qua (Null)"
        )
    ]

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        
        self.on_missing_key = self.node_data.get("on_missing_key", "Bỏ qua (Null)")

        # 2. Xây dựng Output Schema động dựa trên các chân FE gửi xuống
        dynamic_outputs = node_data.get("outputs", [])
        output_fields = {}
        
        # Lưu lại danh sách các đường dẫn để lát nữa execute dùng
        self.extraction_paths = {}

        for pin in dynamic_outputs:
            pin_id = pin["id"] # Ví dụ: "data.user.name"
            label = pin.get("label", pin_id)
            py_type = map_fe_type_to_python(pin.get("dataType"))
            
            # Khai báo schema cho Pydantic
            output_fields[pin_id] = (py_type, Field(default=None, title=label))
            self.extraction_paths[pin_id] = pin_id

        if output_fields:
            self.OUTPUT_SCHEMA = create_model(
                f'ExtractJSONOutput_{self.node_id}',
                **output_fields,
                __config__=ConfigDict(arbitrary_types_allowed=True)
            )
        else:
            self.OUTPUT_SCHEMA = None

    async def execute(self) -> None:
        """Thực thi bóc tách dữ liệu"""
        if not self.local_input or not self.local_input.json_data:
            raise ValueError(f"Khối {self.node_id} không nhận được dữ liệu JSON đầu vào.")

        source_json = self.local_input.json_data
        extracted_data = {}

        # Duyệt qua từng chân Output mà user đã định nghĩa
        for output_pin_id, path in self.extraction_paths.items():
            value = self._extract_value_by_path(source_json, path)
            
            if value is None and self.on_missing_key == "Báo lỗi (Crash)":
                raise KeyError(f"Không tìm thấy dữ liệu tại đường dẫn '{path}' trong JSON đầu vào.")
            
            extracted_data[output_pin_id] = value

        # Gán kết quả vào Output Schema
        if self.OUTPUT_SCHEMA:
            self.local_output = self.OUTPUT_SCHEMA(**extracted_data)


    def _extract_value_by_path(self, data: dict, path: str) -> Any:
        """
        Hàm ma thuật để lấy dữ liệu sâu:
        VD: path = 'data.sensor_1.temperature'
        Sẽ tìm: data['data']['sensor_1']['temperature']
        """
        keys = path.split('.')
        current_val = data
        
        for key in keys:
            if isinstance(current_val, dict) and key in current_val:
                current_val = current_val[key]
            # Hỗ trợ luôn cả việc truy cập mảng qua index (VD: data.items.0.name)
            elif isinstance(current_val, list) and key.isdigit() and int(key) < len(current_val):
                current_val = current_val[int(key)]
            else:
                return None # Không tìm thấy
    
        return current_val