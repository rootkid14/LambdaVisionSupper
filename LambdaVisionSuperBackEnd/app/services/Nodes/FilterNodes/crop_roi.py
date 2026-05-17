from typing import Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node, NodeType, UIDataType

# 1. Định nghĩa Input Schema
class FilterSecondRowBBoxesInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    bboxes: list = Field(default=[], title="BBoxes Input", description=UIDataType.LIST.value)
    
    # Chân Pin lựa chọn: "Left", "Right", hoặc "Both"
    keep_option: str = Field(default="Both", title="Keep Option (Left/Right/Both)", description=UIDataType.STRING.value)
    
    # Dung sai Y (pixel) để gom nhóm các box đứng gần nhau thành 1 hàng
    y_tolerance: int = Field(default=20, title="Y Tolerance (px)", description=UIDataType.NUMBER.value)

# 2. Định nghĩa Output Schema
class FilterSecondRowBBoxesOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    filtered_bboxes: list = Field(default=[], title="Filtered BBoxes", description=UIDataType.LIST.value)

# 3. Khởi tạo Node
@registry_node
class FilterSecondRowBBoxesNode(BaseNode[FilterSecondRowBBoxesInput, FilterSecondRowBBoxesOutput]):
    INPUT_SCHEMA = FilterSecondRowBBoxesInput
    OUTPUT_SCHEMA = FilterSecondRowBBoxesOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Filter 2nd Row BBoxes"
    UI_DESCRIPTION = "Giữ lại BBox trái/phải ngoài cùng của hàng có tọa độ Y lớn thứ 2"
    UI_COLOR = "#ec4899" # Màu hồng (Pink) để dễ nhận diện trên Graph
    REQUIRE_TIMEOUT = False

    async def execute(self) -> None:
        bboxes = self.local_input.bboxes
        # Xóa khoảng trắng và in hoa để tránh lỗi gõ sai từ Frontend
        keep_option = str(self.local_input.keep_option).strip().upper() 
        tol = self.local_input.y_tolerance

        # Trả về rỗng nếu AI không tìm thấy Box nào
        if not bboxes or len(bboxes) == 0:
            self.local_output = self.OUTPUT_SCHEMA(filtered_bboxes=[])
            return

        # ==============================================================
        # BƯỚC 1: Sắp xếp theo trục Y giảm dần (Tìm hàng dưới cùng trước)
        # ==============================================================
        sorted_by_y = sorted(bboxes, key=lambda b: b[1], reverse=True)
        
        # ==============================================================
        # BƯỚC 2: Gom nhóm các BBoxes thành từng hàng (Rows)
        # ==============================================================
        rows = []
        current_row = [sorted_by_y[0]]
        
        for box in sorted_by_y[1:]:
            # Nếu chênh lệch Y <= dung sai (y_tolerance) -> Coi như cùng một hàng ngang
            if abs(box[1] - current_row[0][1]) <= tol:
                current_row.append(box)
            else:
                rows.append(current_row)
                current_row = [box]
        if current_row:
            rows.append(current_row)
            
        # ==============================================================
        # BƯỚC 3: Chọn hàng có Y lớn thứ 2
        # ==============================================================
        # rows[0] là hàng dưới cùng (Y lớn nhất). rows[1] là hàng áp chót (Y lớn thứ 2).
        if len(rows) < 2:
            # Nếu tổng cộng chỉ có 1 hàng, coi như không thỏa mãn điều kiện
            self.local_output = self.OUTPUT_SCHEMA(filtered_bboxes=[])
            return
            
        second_row = rows[1]
        
        # ==============================================================
        # BƯỚC 4: Tìm trái nhất và phải nhất trong hàng đó (Trục X)
        # ==============================================================
        # Sắp xếp hàng thứ 2 theo tọa độ X tăng dần (từ trái qua phải)
        second_row_sorted_x = sorted(second_row, key=lambda b: b[0])
        
        leftmost_box = second_row_sorted_x[0]
        rightmost_box = second_row_sorted_x[-1]
        
        # ==============================================================
        # BƯỚC 5: Xuất kết quả theo lựa chọn của người dùng
        # ==============================================================
        result = []
        if keep_option == "LEFT":
            result.append(leftmost_box)
        elif keep_option == "RIGHT":
            result.append(rightmost_box)
        else: # Mặc định là BOTH
            result.append(leftmost_box)
            # Đảm bảo không add trùng 2 lần nếu hàng đó chỉ có đúng 1 đối tượng
            if leftmost_box != rightmost_box:
                result.append(rightmost_box)
                
        self.local_output = self.OUTPUT_SCHEMA(filtered_bboxes=result)