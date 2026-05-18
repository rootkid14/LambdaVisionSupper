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

class ClassificationInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    coords_list : list = Field(default=[], title="Roi List", description=UIDataType.LIST.value) # Format [x, y, w, h]
    input_image: Any = Field(title="Input Image", description=UIDataType.ANY.value)
    ai_file_name: str = Field(title="AI Model Name", description=UIDataType.STRING.value)
    ok_class_name: str = Field(default="OK", title="OK Class Name", description=UIDataType.STRING.value)
    min_Confidence: float = Field(default=0.85, title="Min Confidence", description=UIDataType.NUMBER.value)

class ClassificationOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # [THÊM MỚI]: Trường chứa ảnh tổng đã được vẽ viền
    annotated_image: str = Field(default="", title="Annotated Image", description=UIDataType.BASE64.value) 
    
    roi_concat_image : str = Field(default="", title="Output Base64", description=UIDataType.BASE64.value)
    overall_result : bool = Field(default=False, title="Final Result", description=UIDataType.BOOLEAN.value)
    qty_ng_found : int = Field(default=0, title="NG QTY Found", description=UIDataType.NUMBER.value)

@registry_node
class YoloClassification(BaseNode[ClassificationInput, ClassificationOutput]):
    INPUT_SCHEMA = ClassificationInput
    OUTPUT_SCHEMA = ClassificationOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "YOLO CLASSIFICATION"
    UI_DESCRIPTION = "Crop ROIs and run YOLO classification"
    UI_COLOR = "bg-purple-700"

    async def execute(self) -> None:
        coords_list = self.local_input.coords_list
        ok_class = self.local_input.ok_class_name
        min_conf = self.local_input.min_Confidence

        # 1. Decode ảnh gốc
        img = extract_cv2_image(self.local_input.input_image)
        img_h, img_w = img.shape[:2]
        
        # [THÊM MỚI]: Tạo bản sao ảnh gốc để vẽ bounding boxes
        annotated_img = img.copy()

        # 2. Load Model YOLO
        model : YOLO = await self.parent._safe_load_file(self.local_input.ai_file_name)

        cropped_rois = []
        qty_ng = 0

        # 3. Lặp qua từng tọa độ để Crop và Classify
        for box in coords_list:
            x, y, w, h = map(int, box)
            
            # Tính toán x1, y1, x2, y2 và Clamp giới hạn trong ảnh
            x1 = max(0, min(x, img_w - 1))
            y1 = max(0, min(y, img_h - 1))
            x2 = max(0, min(x + w, img_w))
            y2 = max(0, min(y + h, img_h))

            if x2 <= x1 or y2 <= y1:
                continue

            # Cắt ROI
            roi = img[y1:y2, x1:x2]

            # Chạy suy luận (Inference)
            results = model.predict(source=roi, verbose=False)
            result = results[0]

            is_ok = False
            pred_class_name = "Unknown"
            annotation_name = "OK"
            conf = 0.0

            # Xử lý kết quả Classification
            if result.probs is not None:
                top_class_idx = result.probs.top1
                conf = float(result.probs.top1conf)
                pred_class_name = result.names[top_class_idx]

                # Kiểm tra điều kiện Pass
                if pred_class_name == ok_class and conf >= min_conf:
                    is_ok = True

            if not is_ok:
                annotation_name = "NG"
                qty_ng += 1

            # ==========================================
            # 4A. VẼ LÊN ẢNH TỔNG (ANNOTATED IMAGE) [THÊM MỚI]
            # ==========================================
            color = (0, 255, 0) if is_ok else (0, 0, 255) # Xanh lá cho OK, Đỏ cho NG

            text = f"{annotation_name} {conf:.2f}"
            
            # Vẽ Box trên ảnh tổng
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 3)
            
            # Vẽ nhãn Text (Có nền để dễ đọc)
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            # Chống tràn chữ lên mép trên màn hình
            text_y = y1 - 5 if y1 > 20 else y1 + th + 5
            cv2.rectangle(annotated_img, (x1, text_y - th - 5), (x1 + tw, text_y + 5), color, -1)
            cv2.putText(annotated_img, text, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


            # ==========================================
            # 4B. VẼ LÊN ROI CẮT RA VÀ THÊM VÀO GRID NHƯ CŨ
            # ==========================================
            roi_resized = cv2.resize(roi, (128, 128))
            
            cv2.rectangle(roi_resized, (0, 0), (127, 127), color, 4)
            cv2.putText(roi_resized, text, (8, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)
            cv2.putText(roi_resized, text, (8, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

            cropped_rois.append(roi_resized)

        # Trả về nếu không có ROI nào hợp lệ
        if not cropped_rois:
            self.local_output = self.OUTPUT_SCHEMA(
                annotated_image=cv2_to_base64(annotated_img), # Trả về ảnh gốc (không có hình vẽ nào do mảng trống)
                roi_concat_image="", 
                overall_result=(qty_ng == 0), 
                qty_ng_found=qty_ng
            )
            return

        # 5. Ghép ảnh (Concat) thành Grid
        cols = 4
        rows = math.ceil(len(cropped_rois) / cols)
        total_cells = cols * rows
        blank_img = np.zeros((128, 128, 3), dtype=np.uint8)
        
        while len(cropped_rois) < total_cells:
            cropped_rois.append(blank_img)
            
        row_images = []
        for r in range(rows):
            row_slice = cropped_rois[r * cols : (r + 1) * cols]
            row_concat = cv2.hconcat(row_slice)
            row_images.append(row_concat)
            
        final_grid = cv2.vconcat(row_images)
        base64_grid = cv2_to_base64(final_grid)

        # 6. Gán output [ĐÃ BỔ SUNG TRƯỜNG MỚI]
        base64_annotated = cv2_to_base64(annotated_img)
        
        self.local_output = self.OUTPUT_SCHEMA(
            annotated_image=base64_annotated,
            roi_concat_image=base64_grid,
            overall_result=(qty_ng == 0), 
            qty_ng_found=qty_ng
        )