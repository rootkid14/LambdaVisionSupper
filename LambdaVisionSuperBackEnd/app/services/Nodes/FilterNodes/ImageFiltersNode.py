import cv2
import numpy as np
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType
from app.services.utils.image_utils import base64_to_cv2, cv2_to_base64
import random
import os
import time
from app.core.config import get_base_dir

def ensure_bgr(image: np.ndarray) -> np.ndarray:
    """Checks if image is 1-channel (grayscale/binary) and converts to 3-channel BGR."""
    if len(image.shape) == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image

def extract_cv2_image(image_input: Any) -> np.ndarray:
    """Helper để tự động nhận diện đầu vào là Numpy hay Base64 string"""
    if isinstance(image_input, np.ndarray):
        return image_input.copy()
    elif isinstance(image_input, str):
        return base64_to_cv2(image_input)
    else:
        raise ValueError("Đầu vào không phải là Numpy Array hoặc Base64 String hợp lệ.")

# --- COMMON SCHEMAS ---
class ImageFilterInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    image: Any = Field(..., title="Input Image", description=UIDataType.ANY.value)

class ImageFilterOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    image_np: np.ndarray = Field(..., title="Image (Numpy)", description=UIDataType.NUMPY_ARRAY.value)
    

# ==========================================
# 1. BRIGHTNESS & CONTRAST NODE
# ==========================================
class BrightnessContrastInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    alpha: float = Field(default=1.0, title="Contrast (Alpha)", description=UIDataType.NUMBER.value)
    beta: int = Field(default=0, title="Brightness (Beta)", description=UIDataType.NUMBER.value)

@registry_node
class BrightnessContrastNode(BaseNode[BrightnessContrastInput, ImageFilterOutput]):
    INPUT_SCHEMA = BrightnessContrastInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Brightness & Contrast"
    UI_DESCRIPTION = "Điều chỉnh độ sáng và độ tương phản của ảnh"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        alpha = self.local_input.alpha
        beta = self.local_input.beta
        
        res = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        res_bgr = ensure_bgr(res)
        
        self.local_output = self.OUTPUT_SCHEMA(
            image_np=res_bgr,
        )

# ==========================================
# 2. GAUSSIAN BLUR NODE
# ==========================================
class GaussianBlurInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    ksize: int = Field(default=3, title="Kernel Size", description=UIDataType.NUMBER.value)

@registry_node
class GaussianBlurNode(BaseNode[GaussianBlurInput, ImageFilterOutput]):
    INPUT_SCHEMA = GaussianBlurInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Gaussian Blur"
    UI_DESCRIPTION = "Làm mờ ảnh bằng bộ lọc Gaussian"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        k = self.local_input.ksize
        if k % 2 == 0: k += 1 # Ensure odd
        
        res = cv2.GaussianBlur(img, (k, k), 0)
        self.local_output = self.OUTPUT_SCHEMA(image_np=res)

# ==========================================
# 3. ADAPTIVE THRESHOLD NODE
# ==========================================
class AdaptiveThresholdInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    block_size: int = Field(default=11, title="Block Size", description=UIDataType.NUMBER.value)
    c_val: int = Field(default=2, title="C Constant", description=UIDataType.NUMBER.value)

@registry_node
class AdaptiveThresholdNode(BaseNode[AdaptiveThresholdInput, ImageFilterOutput]):
    INPUT_SCHEMA = AdaptiveThresholdInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Adaptive Threshold"
    UI_DESCRIPTION = "Nhị phân hóa ảnh cục bộ (Adaptive)"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        bs = self.local_input.block_size
        if bs % 2 == 0: bs += 1
        c = self.local_input.c_val

        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        res = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, bs, c)
        res_bgr = ensure_bgr(res)
        
        self.local_output = self.OUTPUT_SCHEMA(image_np=res_bgr)

# ==========================================
# 4. MORPHOLOGY NODE
# ==========================================
class MorphologyInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    operation: str = Field(default="Erode", title="Operation", description=UIDataType.STRING.value)
    ksize: int = Field(default=3, title="Kernel Size", description=UIDataType.NUMBER.value)
    iters: int = Field(default=1, title="Iterations", description=UIDataType.NUMBER.value)

@registry_node
class MorphologyNode(BaseNode[MorphologyInput, ImageFilterOutput]):
    INPUT_SCHEMA = MorphologyInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Morphology"
    UI_DESCRIPTION = "Xử lý hình thái học (Erode, Dilate, Open, Close)"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        
        op_map = {
            "Erode": cv2.MORPH_ERODE, "Dilate": cv2.MORPH_DILATE, 
            "Open": cv2.MORPH_OPEN, "Close": cv2.MORPH_CLOSE, "Gradient": cv2.MORPH_GRADIENT
        }
        
        operation_str = self.local_input.operation
        op_code = op_map.get(operation_str, cv2.MORPH_ERODE)
        
        k = self.local_input.ksize
        iters = self.local_input.iters
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
        res = cv2.morphologyEx(img, op_code, kernel, iterations=iters)
        
        self.local_output = self.OUTPUT_SCHEMA(image_np=res)

# ==========================================
# 5. CANNY EDGE DETECT NODE
# ==========================================
class CannyEdgeInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    t1: int = Field(default=50, title="Threshold 1", description=UIDataType.NUMBER.value)
    t2: int = Field(default=150, title="Threshold 2", description=UIDataType.NUMBER.value)

@registry_node
class CannyEdgeNode(BaseNode[CannyEdgeInput, ImageFilterOutput]):
    INPUT_SCHEMA = CannyEdgeInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Canny Edge Detect"
    UI_DESCRIPTION = "Tìm kiếm và trích xuất biên cạnh"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        t1 = self.local_input.t1
        t2 = self.local_input.t2
        
        edges = cv2.Canny(img, t1, t2)
        res_bgr = ensure_bgr(edges)
        
        self.local_output = self.OUTPUT_SCHEMA(image_np=res_bgr)


class GammaCorrectionInput(ImageFilterInput):
    gamma: float = Field(default=1.0, title="Gamma", description=UIDataType.NUMBER.value)

@registry_node
class GammaCorrectionNode(BaseNode[GammaCorrectionInput, ImageFilterOutput]):
    INPUT_SCHEMA = GammaCorrectionInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Gamma Correction"
    UI_DESCRIPTION = "Chỉnh sáng phi tuyến tính (Mô phỏng phơi sáng)"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        gamma = self.local_input.gamma
        
        if gamma == 1.0:
            res_bgr = img
        else:
            invGamma = 1.0 / gamma
            # Pre-compute bảng tra cứu LUT (Look-Up Table) để tăng tốc độ xử lý ảnh
            table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            res_bgr = cv2.LUT(img, table)
        
        self.local_output = self.OUTPUT_SCHEMA(
            image_np=res_bgr
        )

# ==========================================
# 7. CLAHE NODE (Mô phỏng HDR / Ánh sáng cực đoan)
# ==========================================
class CLAHEInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    clip_limit: float = Field(default=2.0, title="Clip Limit", description=UIDataType.NUMBER.value)
    grid_size: int = Field(default=8, title="Grid Size", description=UIDataType.NUMBER.value)

@registry_node
class CLAHENode(BaseNode[CLAHEInput, ImageFilterOutput]):
    INPUT_SCHEMA = CLAHEInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "CLAHE (HDR Effect)"
    UI_DESCRIPTION = "Cân bằng sáng cục bộ, giữ lại chi tiết trong vùng đổ bóng"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        clip = self.local_input.clip_limit
        grid = self.local_input.grid_size
        
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid))
        
        # CLAHE hoạt động tốt nhất trên kênh cường độ sáng (Lightness)
        if len(img.shape) == 3:
            # Chuyển sang LAB, apply CLAHE lên kênh L, rồi chuyển ngược lại BGR
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            cl = clahe.apply(l)
            merged = cv2.merge((cl, a, b))
            res_bgr = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        else:
            res_bgr = clahe.apply(img)
            res_bgr = ensure_bgr(res_bgr)
            
        self.local_output = self.OUTPUT_SCHEMA(
            image_np=res_bgr
        )


class RotateImageInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image: Any = Field(..., title="Input Image", description=UIDataType.ANY.value)
    max_degree: float = Field(default=15.0, title="Rotate Range (+/-)", description=UIDataType.NUMBER.value)

@registry_node
class RotateImageNode(BaseNode[RotateImageInput, ImageFilterOutput]):
    INPUT_SCHEMA = RotateImageInput
    OUTPUT_SCHEMA = ImageFilterOutput  # Dùng lại schema Output có sẵn chứa cả Numpy và Base64
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Rotate Image"
    UI_DESCRIPTION = "Xoay ảnh ngẫu nhiên theo một góc biên độ cho trước"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        max_deg = float(self.local_input.max_degree)
        
        # Sinh góc xoay ngẫu nhiên từ -max_deg đến +max_deg
        angle = random.uniform(-max_deg, max_deg)
        
        # Lấy kích thước ảnh và tính tâm xoay
        (h, w) = img.shape[:2]
        center = (w / 2, h / 2)
        
        # Ma trận xoay
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Thực hiện xoay. borderMode=cv2.BORDER_REPLICATE giúp lấp đầy viền đen bằng các pixel cạnh
        rotated_img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        self.local_output = self.OUTPUT_SCHEMA(
            image_np=rotated_img
        )


class SaveImageInput(BaseModel):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image: Any = Field(..., title="Input Image", description=UIDataType.ANY.value)
    folder_path: str = Field(default="storage/dataset/augmented", title="Save Folder", description=UIDataType.STRING.value)
    prefix: str = Field(default="aug", title="File Prefix", description=UIDataType.STRING.value)

class SaveImageOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    success: bool = Field(..., title="Is Success", description=UIDataType.BOOLEAN.value)

@registry_node
class SaveImageNode(BaseNode[SaveImageInput, SaveImageOutput]):
    INPUT_SCHEMA = SaveImageInput
    OUTPUT_SCHEMA = SaveImageOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Save Image to Disk"
    UI_DESCRIPTION = "Lưu ảnh (Base64/Numpy) xuống ổ cứng"
    UI_COLOR = "bg-blue-600"

    async def execute(self) -> None:
        try:
            # Tự động giải mã (Base64 -> Numpy) hoặc copy trực tiếp Numpy
            img = extract_cv2_image(self.local_input.image)
            
            raw_folder_path = self.local_input.folder_path
            prefix = self.local_input.prefix
            
            # Xử lý đường dẫn an toàn
            save_folder = raw_folder_path.strip().strip("'").strip('"')
            if save_folder.startswith('r'):
                save_folder = save_folder[1:].strip("'").strip('"')
                
            # Gắn vào Base Dir của project
            full_path = os.path.join(str(get_base_dir()), save_folder)
            os.makedirs(full_path, exist_ok=True)
            
            # Sinh tên file chống trùng lặp
            filename = f"{prefix}_{int(time.time() * 1000)}_{random.randint(100, 999)}.jpg"
            file_path = os.path.join(full_path, filename)
            
            # Lưu ảnh
            success = cv2.imwrite(file_path, img)
            
            self.local_output = self.OUTPUT_SCHEMA(success=bool(success))
            
        except Exception as e:
            print(f"[SaveImageNode] Lỗi: {e}")
            self.local_output = self.OUTPUT_SCHEMA(success=False)
            raise e
        
class StretchImageInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    scale_x: float = Field(default=1.0, title="Scale X", description=UIDataType.NUMBER.value)
    scale_y: float = Field(default=1.0, title="Scale Y", description=UIDataType.NUMBER.value)

@registry_node
class StretchImageNode(BaseNode[StretchImageInput, ImageFilterOutput]):
    INPUT_SCHEMA = StretchImageInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Stretch Image"
    UI_DESCRIPTION = "Kéo giãn/Co lại ảnh theo trục X và Y độc lập"
    UI_COLOR = "bg-blue-500"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        sx = float(self.local_input.scale_x)
        sy = float(self.local_input.scale_y)
        
        # Tránh lỗi sập OpenCV nếu hệ số scale truyền vào là 0 hoặc âm
        sx = max(0.1, sx)
        sy = max(0.1, sy)
        
        h, w = img.shape[:2]
        new_w = int(w * sx)
        new_h = int(h * sy)
        
        # Dùng nội suy tuyến tính (INTER_LINEAR) cho chất lượng mượt mà nhất
        res = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        self.local_output = self.OUTPUT_SCHEMA(
            image_np=res
        )

# ==========================================
# 2. SKEW IMAGE NODE
# ==========================================
class SkewImageInput(ImageFilterInput):
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    skew_x: float = Field(default=0.0, title="Skew X Factor", description=UIDataType.NUMBER.value)
    skew_y: float = Field(default=0.0, title="Skew Y Factor", description=UIDataType.NUMBER.value)

@registry_node
class SkewImageNode(BaseNode[SkewImageInput, ImageFilterOutput]):
    INPUT_SCHEMA = SkewImageInput
    OUTPUT_SCHEMA = ImageFilterOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Skew Image"
    UI_DESCRIPTION = "Làm xiên/méo ảnh theo hệ số trục X và Y (Affine Transformation)"
    UI_COLOR = "#B0C01D"

    async def execute(self) -> None:
        img = extract_cv2_image(self.local_input.image)
        sx = float(self.local_input.skew_x)
        sy = float(self.local_input.skew_y)
        
        h, w = img.shape[:2]
        
        # 1. Tính toán kích thước ảnh mới để các góc sau khi bóp méo không bị cắt cụt lẹm ra ngoài khung
        new_w = int(w + abs(h * sx))
        new_h = int(h + abs(w * sy))
        
        # 2. Dịch chuyển bù (Translation) để giữ trọng tâm ảnh nằm trong khung hình an toàn
        offset_x = abs(h * sx) if sx < 0 else 0
        offset_y = abs(w * sy) if sy < 0 else 0
        
        # 3. Tạo Ma trận biến đổi Affine: [Shear X, Shear Y] kết hợp [Offset X, Offset Y]
        M = np.float32([
            [1, sx, offset_x],
            [sy, 1, offset_y]
        ])
        
        # 4. Thực thi bóp méo với borderMode=REPLICATE để tự động sao chép viền, không để lại mảng đen
        res = cv2.warpAffine(img, M, (new_w, new_h), borderMode=cv2.BORDER_REPLICATE)
        
        self.local_output = self.OUTPUT_SCHEMA(
            image_np=res
        )