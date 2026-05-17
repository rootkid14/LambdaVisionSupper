from ultralytics import YOLO
import cv2
import numpy as np
import random
import os
import math
import time
from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType
from app.services.utils.image_utils import cv2_to_base64, base64_to_cv2
from typing import Any

def extract_cv2_image(image_input: Any) -> np.ndarray:
    """Helper để tự động nhận diện đầu vào là Numpy hay Base64 string"""
    if isinstance(image_input, np.ndarray):
        return image_input.copy()
    elif isinstance(image_input, str):
        return base64_to_cv2(image_input)
    else:
        raise ValueError("Đầu vào không phải là Numpy Array hoặc Base64 String hợp lệ.")

class FindPositionInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    input_image: Any = Field(title="Input Image", description=UIDataType.ANY.value)
    ai_file_name: str = Field(title="AI Model Name", description=UIDataType.STRING.value)
    min_Confidence: float = Field(default=0.4, title="Min Confidence", description=UIDataType.NUMBER.value)

class FindPositionOuput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    result_xyxy: list = Field(default_factory=list, title="Result Coordinates", description=UIDataType.LIST.value)
    result_count: int = Field(title="Found QTY", description=UIDataType.NUMBER.value)

@registry_node
class FindPosition(BaseNode[FindPositionInput, FindPositionOuput]):
    # SỬA LỖI: Gán đúng Schema cho Input và Output
    INPUT_SCHEMA = FindPositionInput
    OUTPUT_SCHEMA = FindPositionOuput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "YOLO FIND POSITIONS"
    UI_DESCRIPTION = "AUTOMATICALLY FIND THE POSITION WITH YOLO MODEL"
    UI_COLOR = "bg-purple-700"

    async def execute(self) -> None:
        # 1. Lấy dữ liệu từ chân Pin đầu vào
        ai_model_name = self.local_input.ai_file_name
        conf_threshold = self.local_input.min_Confidence

        
        # 3. Đọc ảnh
        img = extract_cv2_image(self.local_input.input_image)

        # 4. Chạy AI (YOLO)
        # Lưu ý: Trong thực tế nên dùng một ModelPool để tránh load model liên tục làm chậm hệ thống
        
        model : YOLO = await self.parent._safe_load_file(ai_model_name)
        results = model.predict(img, conf=conf_threshold, iou=0.5, verbose=False)[0]

        # 5. Xử lý kết quả và Vẽ Bounding Box
        coords_list = []
        
        for box in results.boxes:
            # Lấy tọa độ dạng xyxy
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Tính toán Chiều rộng (w) và Chiều cao (h)
            w = x2 - x1
            h = y2 - y1
            
            # Xuất đúng chuẩn [x_min, y_min, width, height]
            coords_list.append([x1, y1, w, h])

        # 6. Đóng gói kết quả trả về cho Frontend
        self.local_output = self.OUTPUT_SCHEMA(
            result_xyxy=coords_list,
            result_count=len(coords_list),
        )


class CheckTapeInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    input_image: Any = Field(title="Input Image", description=UIDataType.ANY.value)
    ai_file_name: str = Field(title="AI Model Name", description=UIDataType.STRING.value)
    min_Confidence: float = Field(default=0.5, title="Min Confidence", description=UIDataType.NUMBER.value)

# 2. Định nghĩa Output Schema
class CheckTapeOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    annotated_image: str = Field(default="", title="Annotated Image", description=UIDataType.BASE64.value)
    result: bool = Field(default=False, title="Result (OK/NG)", description=UIDataType.BOOLEAN.value)
    found: bool = Field(default=False, title="Found", description=UIDataType.BOOLEAN.value)

# 3. Khởi tạo Node
@registry_node
class CheckTapeNode(BaseNode[CheckTapeInput, CheckTapeOutput]):
    INPUT_SCHEMA = CheckTapeInput
    OUTPUT_SCHEMA = CheckTapeOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Check Tape"
    UI_DESCRIPTION = "Detect tape status. Class 0 -> OK, Class 1 -> NG."
    UI_COLOR = "#f59e0b" # Màu Cam (Amber) để dễ phân biệt trên Graph
    REQUIRE_TIMEOUT = False

    async def execute(self) -> None:
        # 1. Đọc dữ liệu đầu vào
        img = extract_cv2_image(self.local_input.input_image)
        ai_model_name = self.local_input.ai_file_name
        conf_threshold = self.local_input.min_Confidence

        # 2. Load Model và chạy dự đoán
        model: YOLO = await self.parent._safe_load_file(ai_model_name)
        results = model.predict(img, conf=conf_threshold, iou=0.5, verbose=False)[0]

        annotated_img = img.copy()
        
        # Mặc định là False (NG) nếu không tìm thấy cuộn tape nào
        final_result = False 
        found = False
        
        # Quy định màu sắc: Class 0 (OK) -> Xanh lá, Class 1 (NG) -> Đỏ
        colors = {0: (0, 255, 0), 1: (0, 0, 255)}

        # 3. Xử lý kết quả
        if len(results.boxes) > 0:
            # Lấy đối tượng đầu tiên tìm thấy trong danh sách
            found = True
            first_box = results.boxes[0]
            first_cls_id = int(first_box.cls[0])
            conf = float(first_box.conf[0])

            # Kiểm tra Class 0 hay 1 để xuất kết quả logic
            if first_cls_id == 0:
                final_result = True
            elif first_cls_id == 1:
                final_result = False

            # ==========================================
            # CHỈ VẼ ĐỐI TƯỢNG ĐẦU TIÊN (FIRST BOX)
            # ==========================================
            x1, y1, x2, y2 = map(int, first_box.xyxy[0])
            
            color = colors.get(first_cls_id, (0, 255, 255))
            label = f"OK {conf:.2f}" if first_cls_id == 0 else f"NG {conf:.2f}"
            
            # Vẽ khung viền
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 3)
            
            # Vẽ nền chữ và nhãn Text
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            text_y = max(y1 - 5, th + 5)
            cv2.rectangle(annotated_img, (x1, text_y - th - 5), (x1 + tw, text_y + 5), color, -1)
            cv2.putText(annotated_img, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # 4. Chuyển đổi ảnh sang Base64 và trả về
        base64_annotated = cv2_to_base64(annotated_img)

        self.local_output = self.OUTPUT_SCHEMA(
            annotated_image=base64_annotated,
            result=final_result,
            found=found
        )