import cv2
import os
import time
from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType
from typing import Any
from app.services.utils.image_utils import extract_cv2_image

class CropAndSaveInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    input_image: Any = Field(title="Input Image", description=UIDataType.ANY.value)
    bboxes_list: list = Field(default=[], title="BBoxes List", description=UIDataType.LIST.value) # Format: [x, y, w, h]
    target_folder: str = Field(default="storage/cropped_rois", title="Save Folder", description=UIDataType.STRING.value)

class CropAndSaveOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    saved_count: int = Field(default=0, title="Saved Count", description=UIDataType.NUMBER.value)

@registry_node
class CropAndSaveNode(BaseNode[CropAndSaveInput, CropAndSaveOutput]):
    INPUT_SCHEMA = CropAndSaveInput
    OUTPUT_SCHEMA = CropAndSaveOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "CROP & SAVE ROIS"
    UI_DESCRIPTION = "Crop bounding boxes [x,y,w,h] and save to disk"
    UI_COLOR = "bg-teal-600" # Đổi màu cho dễ nhận diện trên UI

    async def execute(self) -> None:
        bboxes = self.local_input.bboxes_list
        folder_path = self.local_input.target_folder
        
        # 1. Decode ảnh đầu vào
        try:
            img = extract_cv2_image(self.local_input.input_image)
        except Exception:
            self.local_output = self.OUTPUT_SCHEMA(saved_count=0)
            return

        if not bboxes or img is None:
            self.local_output = self.OUTPUT_SCHEMA(saved_count=0)
            return

        img_h, img_w = img.shape[:2]

        # 2. Làm sạch đường dẫn và tự động tạo thư mục nếu chưa có
        save_folder = folder_path.strip().strip("'").strip('"')
        if save_folder.startswith('r'):
            save_folder = save_folder[1:].strip("'").strip('"')
        os.makedirs(save_folder, exist_ok=True)

        saved_qty = 0
        session_id = str(int(time.time())) # Dùng thời gian làm ID để tránh trùng tên file

        # 3. Duyệt qua mảng bboxes để cắt và lưu
        for idx, box in enumerate(bboxes):
            # Ép kiểu int đề phòng đầu vào là float
            x, y, w, h = map(int, box)
            
            # Tính toán x1, y1, x2, y2 và Clamp giới hạn trong ảnh để không bị crash
            x1 = max(0, min(x, img_w - 1))
            y1 = max(0, min(y, img_h - 1))
            x2 = max(0, min(x + w, img_w))
            y2 = max(0, min(y + h, img_h))

            # Bỏ qua nếu khung cắt không hợp lệ (chiều rộng/cao <= 0)
            if x2 <= x1 or y2 <= y1:
                continue

            # Cắt ảnh (Crop ROI)
            roi = img[y1:y2, x1:x2]

            # 4. Lưu ảnh xuống ổ cứng
            file_name = f"crop_{session_id}_{idx}.jpg"
            save_path = os.path.join(save_folder, file_name)
            
            # cv2.imwrite yêu cầu string chuẩn, nếu thư mục có dấu tiếng Việt thì cần cẩn thận
            success = cv2.imwrite(save_path, roi)
            if success:
                saved_qty += 1

        # 5. Gán kết quả đầu ra
        self.local_output = self.OUTPUT_SCHEMA(saved_count=saved_qty)