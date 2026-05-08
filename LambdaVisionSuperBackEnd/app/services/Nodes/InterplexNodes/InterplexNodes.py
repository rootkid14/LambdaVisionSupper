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

class FindUpperPemLocationInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    image_path: str = Field(title="Image Path", description=UIDataType.STRING.value)
    ai_file_name: str = Field(title="AI Model Name", description=UIDataType.STRING.value)
    min_Confidence: float = Field(default=0.4, title="Min Confidence", description=UIDataType.NUMBER.value)

class FindUpperPemLocationOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    result_xyxy: list = Field(default_factory=list, title="Result Coordinates", description=UIDataType.LIST.value)
    result_count: int = Field(title="Found QTY", description=UIDataType.NUMBER.value)
    result_image: str = Field(None, title="Annotated Image", description=UIDataType.BASE64.value)
    original_image: str = Field(None, title="Original Image", description=UIDataType.BASE64.value)

@registry_node
class FindUpperPemLocation(BaseNode[FindUpperPemLocationInput, FindUpperPemLocationOutput]):
    # SỬA LỖI: Gán đúng Schema cho Input và Output
    INPUT_SCHEMA = FindUpperPemLocationInput
    OUTPUT_SCHEMA = FindUpperPemLocationOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "YOLO PEM Detector"
    UI_DESCRIPTION = "Use OD model to get bounding boxes of the Pems"
    UI_COLOR = "bg-purple-700"

    async def execute(self) -> None:
        # 1. Lấy dữ liệu từ chân Pin đầu vào
        img_path = self.local_input.image_path
        ai_model_name = self.local_input.ai_file_name
        conf_threshold = self.local_input.min_Confidence

        
        # 3. Đọc ảnh
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Không tìm thấy ảnh tại: {img_path}")

        # 4. Chạy AI (YOLO)
        # Lưu ý: Trong thực tế nên dùng một ModelPool để tránh load model liên tục làm chậm hệ thống
        
        model : YOLO = await self.parent._safe_load_file(ai_model_name)
        results = model.predict(img, conf=conf_threshold, iou=0.5, verbose=False)[0]

        # 5. Xử lý kết quả và Vẽ Bounding Box
        coords_list = []
        annotated_img = img.copy()
        
        # Định nghĩa màu: 0: OK (Xanh lá), 1: Missing (Đỏ)
        ma_mau = {0: (0, 255, 0), 1: (0, 0, 255)}

        for box in results.boxes:
            # Lấy tọa độ
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            coords_list.append([x1, y1, x2, y2])

            # Vẽ lên ảnh annotated_img
            color = ma_mau.get(cls_id, (0, 255, 255))
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

            ui_preview_annotated = cv2.resize(annotated_img, (800, 600))
            
            base_64_img = cv2_to_base64(ui_preview_annotated)
            bas64_original_img = cv2_to_base64(img)

        # 6. Đóng gói kết quả trả về cho Frontend
        self.local_output = self.OUTPUT_SCHEMA(
            result_xyxy=coords_list,
            result_count=len(coords_list),
            result_image=base_64_img,
            original_image = bas64_original_img
        )

class ExtractRoiInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image : str = Field(title="Input Image", description=UIDataType.BASE64.value)
    xyxy_list: list = Field(default_factory=list, title="XY List", description=UIDataType.LIST)
    offset_percentage: int = Field(default=10, title="Offset Percent", description=UIDataType.NUMBER)
    # Thêm tham số scale_percentage
    scale_percentage: int = Field(default=0, title="Scale Range (+/- %)", description=UIDataType.NUMBER)
    target_folder_path: str = Field(default="storage/rois", title="Save to", description=UIDataType.STRING)

class ExtractRoiOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    output_images: str = Field(default="", title="Concat Roi Image", description=UIDataType.BASE64)

@registry_node
class Extract_Roi_W_Offset(BaseNode[ExtractRoiInput, ExtractRoiOutput]):
    INPUT_SCHEMA = ExtractRoiInput
    OUTPUT_SCHEMA = ExtractRoiOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Extract ROI (Offset & Scale)"
    UI_COLOR = "bg-orange-600"

    async def execute(self) -> None:
        img = self.local_input.image
        xyxy_list = self.local_input.xyxy_list
        offset_pct = self.local_input.offset_percentage
        scale_pct = self.local_input.scale_percentage
        raw_folder_path = self.local_input.target_folder_path
        
        img = base64_to_cv2(img)
        if not xyxy_list:
            self.local_output = self.OUTPUT_SCHEMA(output_images="")
            return

        save_folder = raw_folder_path.strip().strip("'").strip('"')
        if save_folder.startswith('r'):
            save_folder = save_folder[1:].strip("'").strip('"')
        os.makedirs(save_folder, exist_ok=True)
        
        img_h, img_w = img.shape[:2]
        cropped_rois = []
        session_id = str(int(time.time()))

        for idx, box in enumerate(xyxy_list):
            x1, y1, x2, y2 = map(int, box)
            w, h = x2 - x1, y2 - y1
            if w <= 0 or h <= 0:
                continue

            # 1. Tính toán Scale (Zoom in / Zoom out)
            scale_factor = 0.0
            if scale_pct > 0:
                # Random từ âm scale_pct đến dương scale_pct
                scale_factor = random.uniform(-scale_pct, scale_pct) / 100.0 
            
            dw = w * scale_factor
            dh = h * scale_factor
            
            new_w = w + dw
            new_h = h + dh
            cx, cy = x1 + w/2, y1 + h/2

            # 2. Tính toán Offset ngẫu nhiên
            max_ox = int(new_w * (offset_pct / 100.0))
            max_oy = int(new_h * (offset_pct / 100.0))
            
            direction = random.choice(['N', 'S', 'E', 'W', 'C']) # Thêm 'C' (Center) để có tỷ lệ không bị lệch
            dx, dy = 0, 0
            if direction == 'N':
                dy = -random.randint(0, max_oy)
            elif direction == 'S':
                dy = random.randint(0, max_oy)
            elif direction == 'E':
                dx = random.randint(0, max_ox)
            elif direction == 'W':
                dx = -random.randint(0, max_ox)

            # 3. Tính toán lại tọa độ Bounding Box mới
            nx1 = int(cx - new_w/2 + dx)
            ny1 = int(cy - new_h/2 + dy)
            nx2 = int(cx + new_w/2 + dx)
            ny2 = int(cy + new_h/2 + dy)

            # 4. Clamp (Giới hạn trong khung ảnh)
            nx1 = max(0, min(nx1, img_w - 1))
            ny1 = max(0, min(ny1, img_h - 1))
            nx2 = max(0, min(nx2, img_w))
            ny2 = max(0, min(ny2, img_h))

            if nx2 <= nx1 or ny2 <= ny1:
                continue

            roi_img = img[ny1:ny2, nx1:nx2]
            file_name = f"roi_{session_id}_{idx}_{direction}.jpg"
            cv2.imwrite(os.path.join(save_folder, file_name), roi_img)
            
            roi_resized = cv2.resize(roi_img, (128, 128))
            cropped_rois.append(roi_resized)

        if not cropped_rois:
            self.local_output = self.OUTPUT_SCHEMA(output_images="")
            return

        cols = 8
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
        self.local_output = self.OUTPUT_SCHEMA(output_images=base64_grid)

class FolderImageScannerInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    folder_path: str = Field(default="storage/dataset", title="Target Folder", description=UIDataType.STRING.value)

class FolderImageScannerOutput(BaseModel):
    # Trả về nguyên 1 List đường dẫn ảnh
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    image_list: list = Field(default_factory=list, title="Image List", description=UIDataType.LIST.value)

@registry_node
class FolderImageScanner(BaseNode[FolderImageScannerInput, FolderImageScannerOutput]):
    INPUT_SCHEMA = FolderImageScannerInput
    OUTPUT_SCHEMA = FolderImageScannerOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Folder Image Scanner"
    UI_COLOR = "bg-purple-500" 

    async def execute(self) -> None:
        folder_path = self.local_input.folder_path
        
        # 1. Làm sạch đường dẫn
        folder_path = folder_path.strip().strip("'").strip('"')
        if folder_path.startswith('r'):
            folder_path = folder_path[1:].strip("'").strip('"')

        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Thư mục không tồn tại: {folder_path}")
            
        valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        
        # 2. Quét và trả về toàn bộ mảng (Không lưu state)
        full_list = [
            os.path.join(folder_path, f) 
            for f in os.listdir(folder_path) 
            if f.lower().endswith(valid_exts)
        ]

        self.local_output = self.OUTPUT_SCHEMA(
            image_list=full_list
        )