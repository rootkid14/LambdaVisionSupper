from typing import Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node, NodeType, UIDataType

# 1. Định nghĩa Input Schema
class BBoxXYWHtoXYXYInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    # Nhận vào danh sách [[x, y, w, h], ...]
    bboxes_xywh: list = Field(default=[], title="BBoxes (XYWH)", description=UIDataType.LIST.value)

# 2. Định nghĩa Output Schema
class BBoxXYWHtoXYXYOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    # Trả ra danh sách [[x_start, y_start, x_end, y_end], ...]
    bboxes_xyxy: list = Field(default=[], title="BBoxes (XYXY)", description=UIDataType.LIST.value)

# 3. Khởi tạo Node
@registry_node
class BBoxXYWHtoXYXYNode(BaseNode[BBoxXYWHtoXYXYInput, BBoxXYWHtoXYXYOutput]):
    INPUT_SCHEMA = BBoxXYWHtoXYXYInput
    OUTPUT_SCHEMA = BBoxXYWHtoXYXYOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "XYWH to XYXY"
    UI_DESCRIPTION = "Convert bounding boxes from [x, y, width, height] to [x_start, y_start, x_end, y_end]"
    UI_COLOR = "#0ea5e9" # Màu xanh dương nhạt cho các Node tiện ích biến đổi
    REQUIRE_TIMEOUT = False

    async def execute(self) -> None:
        bboxes_in = self.local_input.bboxes_xywh
        bboxes_out = []
        
        # Xử lý tính toán cho từng bounding box
        for box in bboxes_in:
            # Đảm bảo box có ít nhất 4 giá trị
            if len(box) >= 4:
                x, y, w, h = box[:4]
                
                # Tính toán tọa độ kết thúc
                x_start = x
                y_start = y
                x_end = x + w
                y_end = y + h
                
                # Thêm vào mảng kết quả
                bboxes_out.append([x_start, y_start, x_end, y_end])
                
        # Trả kết quả ra cổng output
        self.local_output = self.OUTPUT_SCHEMA(bboxes_xyxy=bboxes_out)