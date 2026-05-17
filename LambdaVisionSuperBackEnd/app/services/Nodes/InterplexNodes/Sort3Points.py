from typing import Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.services.LVSTypes import UIDataType, NodeType
from app.services.node_registry import BaseNode, registry_node

# 1. Định nghĩa Input Schema
class Sort3PointsInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    points: list = Field(default=[], title="Input Points", description=UIDataType.LIST.value) # Nhận vào [[x, y], [x, y], [x, y]]

# 2. Định nghĩa Output Schema
class Sort3PointsOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    sorted_points: list = Field(default=[], title="Sorted Points", description=UIDataType.LIST.value)

# 3. Khởi tạo Node logic
@registry_node
class Sort3PointsNode(BaseNode[Sort3PointsInput, Sort3PointsOutput]):
    INPUT_SCHEMA = Sort3PointsInput
    OUTPUT_SCHEMA = Sort3PointsOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Sort 3 Points"
    UI_DESCRIPTION = "Sorts exactly 3 points: P1(Max Y), P2(Low Y, Min X), P3(Low Y, Max X)"
    UI_COLOR = "#10b981" # Màu xanh ngọc (Emerald) để dễ nhận diện
    REQUIRE_TIMEOUT = False

    async def execute(self) -> None:
        pts = self.local_input.points
        
        # Kiểm tra tính hợp lệ của đầu vào
        if not isinstance(pts, list) or len(pts) != 3:
            raise ValueError(f"Node 'Sort 3 Points' yêu cầu chính xác 3 điểm đầu vào. Hiện tại nhận được: {len(pts)} điểm.")
        
        for p in pts:
            if len(p) < 2:
                raise ValueError("Mỗi điểm đầu vào phải có ít nhất 2 giá trị [x, y].")

        # 1. Lọc Điểm 1: Giá trị Y lớn nhất
        # Sắp xếp danh sách điểm theo tọa độ Y (index 1) giảm dần (reverse=True)
        pts_sorted_by_y = sorted(pts, key=lambda p: p[1], reverse=True)
        
        # Lấy điểm có Y lớn nhất
        point_1 = pts_sorted_by_y[0]
        
        # 2 điểm còn lại có Y nhỏ hơn
        remaining_points = pts_sorted_by_y[1:]
        
        # 2. Lọc Điểm 2 và 3: Dựa trên giá trị X
        # Sắp xếp 2 điểm còn lại theo tọa độ X (index 0) tăng dần
        rem_sorted_by_x = sorted(remaining_points, key=lambda p: p[0])
        
        # Điểm 2: X nhỏ hơn
        point_2 = rem_sorted_by_x[0]
        # Điểm 3: X lớn hơn
        point_3 = rem_sorted_by_x[1]
        
        # 3. Gộp lại theo đúng thứ tự luật đề ra
        result_sorted = [point_1, point_2, point_3]
        
        # Trả kết quả ra Output
        self.local_output = self.OUTPUT_SCHEMA(sorted_points=result_sorted)