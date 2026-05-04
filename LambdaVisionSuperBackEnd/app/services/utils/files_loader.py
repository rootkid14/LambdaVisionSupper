import cv2
import os
from pathlib import Path
from ultralytics import YOLO
from app.core.config import get_base_dir

def load_ai_models(destination_storage, ai_model_name):
    """
    Tải model AI dựa trên phần mở rộng (PT, ONNX, Engine) và lưu vào bộ nhớ đệm.
    """
    # 1. Xác định đường dẫn tuyệt đối tới file model
    base_path = get_base_dir() / "storage" / "file_storage"
    model_full_path = base_path / ai_model_name
    
    # 2. Kiểm tra sự tồn tại của file
    if not model_full_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file model tại: {model_full_path}")

    # 3. Phân loại và nạp model dựa trên phần mở rộng
    ext = model_full_path.suffix.lower()
    
    try:
        if ext in ['.pt', '.yaml']:
            # Nạp model YOLO chuẩn (PyTorch)
            model = YOLO(str(model_full_path))
            destination_storage[ai_model_name] = model
        
        elif ext in ['.onnx', '.engine', '.openvino']:
            # Nạp các định dạng đã được export để tối ưu hiệu năng
            model = YOLO(str(model_full_path), task='detect')
            destination_storage[ai_model_name] = model
            
        else:
            raise ValueError(f"Định dạng {ext} hiện chưa được LambdaVision hỗ trợ.")
            
    except Exception as e:
        print(f"[ERROR] Thất bại khi nạp model {ai_model_name}: {e}")
        raise e

def load_image(destination_storage, image_file_name):
    """
    Tải ảnh từ ổ cứng bằng OpenCV và lưu vào bộ nhớ đệm dưới dạng ma trận Numpy.
    """
    # 1. Xác định đường dẫn ảnh (có thể tùy chỉnh thư mục tùy theo logic của bạn)
    image_path = get_base_dir() / "storage" / "file_storage" / image_file_name
    
    try:
        # 2. Đọc ảnh bằng OpenCV (Hỗ trợ JPG, PNG, BMP, WEBP...)[cite: 1]
        img = cv2.imread(str(image_path))
        
        if img is None:
            raise ValueError(f"Tệp tin không phải là ảnh hợp lệ hoặc bị hỏng: {image_path}")
            
        # 3. Lưu ma trận ảnh vào storage[cite: 1]
        destination_storage[image_file_name] = img
        
    except Exception as e:
        print(f"[ERROR] Không thể nạp ảnh {image_file_name}: {e}")
        raise e