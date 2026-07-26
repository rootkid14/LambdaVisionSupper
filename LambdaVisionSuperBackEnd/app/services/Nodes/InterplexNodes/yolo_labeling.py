import cv2
import os
import time
from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType
from typing import Any, Dict
from app.services.utils.image_utils import extract_cv2_image
import json

class SaveYoloDatasetInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    input_image: Any = Field(title="Input Image", description=UIDataType.ANY.value)
    
    # [ĐÃ SỬA]: Đổi từ DICT sang JSON và đổi tên biến thành bboxes_json
    bboxes_json: Any = Field(default={}, title="BBoxes JSON", description=UIDataType.JSON.value) 
    
    classes_list: str = Field(default="OK, NG", title="Classes (Comma separated)", description=UIDataType.STRING.value)
    image_folder: str = Field(default="dataset/images/train", title="Image Folder", description=UIDataType.STRING.value)
    label_folder: str = Field(default="dataset/labels/train", title="Label Folder", description=UIDataType.STRING.value)

class SaveYoloDatasetOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    saved_status: bool = Field(default=False, title="Saved Success", description=UIDataType.BOOLEAN.value)
    saved_file_name: str = Field(default="", title="Saved File Name", description=UIDataType.STRING.value)

@registry_node
class SaveYoloDatasetNode(BaseNode[SaveYoloDatasetInput, SaveYoloDatasetOutput]):
    INPUT_SCHEMA = SaveYoloDatasetInput
    OUTPUT_SCHEMA = SaveYoloDatasetOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "SAVE YOLO DATASET"
    UI_DESCRIPTION = "Auto format and save Image & Label (.txt) for YOLO Detection training"
    UI_COLOR = "bg-blue-600" 

    async def execute(self) -> None:
        raw_bboxes = self.local_input.bboxes_json
        
        # ==========================================
        # [THÊM MỚI]: BỘ LỌC ÉP KIỂU JSON THÔNG MINH
        # ==========================================
        if isinstance(raw_bboxes, str):
            try:
                bboxes_dict = json.loads(raw_bboxes)
            except Exception:
                bboxes_dict = {}
        elif isinstance(raw_bboxes, dict):
            bboxes_dict = raw_bboxes
        else:
            bboxes_dict = {}

        img_folder = self.local_input.image_folder.strip().strip("'").strip('"')
        lbl_folder = self.local_input.label_folder.strip().strip("'").strip('"')
        classes_str = self.local_input.classes_list
        
        # 1. Parse danh sách Classes để tạo Mapping
        class_mapping = {}
        for idx, cls_name in enumerate(classes_str.split(',')):
            class_mapping[cls_name.strip()] = idx

        # 2. Decode ảnh đầu vào
        try:
            img = extract_cv2_image(self.local_input.input_image)
        except Exception:
            self.local_output = self.OUTPUT_SCHEMA(saved_status=False)
            return

        if not bboxes_dict or img is None:
            self.local_output = self.OUTPUT_SCHEMA(saved_status=False)
            return

        img_h, img_w = img.shape[:2]

        # 3. Tự động tạo thư mục nếu chưa tồn tại
        os.makedirs(img_folder, exist_ok=True)
        os.makedirs(lbl_folder, exist_ok=True)

        # 4. Tạo tên file độc nhất (Dùng timestamp)
        session_id = str(int(time.time() * 1000))
        base_filename = f"yolo_data_{session_id}"
        
        img_path = os.path.join(img_folder, f"{base_filename}.jpg")
        lbl_path = os.path.join(lbl_folder, f"{base_filename}.txt")

        yolo_labels = []

        # 5. Duyệt qua Dictionary để Normalize tọa độ sang chuẩn YOLO
        for label_name, boxes in bboxes_dict.items():
            label_name_clean = str(label_name).strip()
            
            # Bỏ qua nếu label không nằm trong danh sách Classes bạn muốn train
            if label_name_clean not in class_mapping:
                continue
                
            class_id = class_mapping[label_name_clean]

            for box in boxes:
                if len(box) < 4: continue
                x, y, w, h = map(float, box[:4])
                
                if w <= 0 or h <= 0: continue

                # YOLO Math: Tính tọa độ tâm và chuẩn hóa về dải [0.0 - 1.0]
                x_center = (x + w / 2.0) / img_w
                y_center = (y + h / 2.0) / img_h
                norm_w = w / img_w
                norm_h = h / img_h

                # Clamp an toàn
                x_center = max(0.0, min(1.0, x_center))
                y_center = max(0.0, min(1.0, y_center))
                norm_w = max(0.0, min(1.0, norm_w))
                norm_h = max(0.0, min(1.0, norm_h))

                yolo_labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

        # 6. Lưu file
        cv2.imwrite(img_path, img)
        with open(lbl_path, "w", encoding="utf-8") as f:
            f.write("\n".join(yolo_labels))

        # 7. Gán kết quả
        self.local_output = self.OUTPUT_SCHEMA(
            saved_status=True,
            saved_file_name=base_filename
        )