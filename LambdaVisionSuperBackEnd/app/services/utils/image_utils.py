import cv2
import numpy as np
import base64
from typing import Any

def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    """
    Dịch mảng byte nhị phân thô (đã được nén bằng JPEG/PNG/WebP) 
    thành ma trận ảnh OpenCV (Numpy Array - hệ màu BGR).
    """
    # Bước 1: Chuyển chuỗi byte thô thành mảng Numpy 1 chiều (kiểu uint8)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    
    # Bước 2: Yêu cầu OpenCV đọc "Magic Bytes" và giải mã mảng đó thành ảnh màu
    img_cv2 = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    # Bước 3: DÒNG BẢO VỆ (Cực kỳ quan trọng)
    # Nếu imdecode trả về None, nghĩa là ảnh bị hỏng hoặc thiết bị gửi nhầm 
    # dữ liệu thô (Raw RGB/YUV) thay vì ảnh đã nén.
    if img_cv2 is None:
        raise ValueError(
            "Lỗi định dạng nhị phân! Ảnh bị hỏng hoặc Camera đang gửi "
            "Raw Sensor Data (YUV/RGB) thay vì chuẩn nén JPEG/PNG/WebP."
        )
        
    return img_cv2

def cv2_to_base64(img: np.ndarray) -> str:
    # Nén ảnh thành JPEG với chất lượng 85% để cân bằng giữa dung lượng và độ nét
    success, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        return ""
    
    # Mã hóa nhị phân sang chuỗi văn bản an toàn
    base64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_str}"


def base64_to_cv2(base64_string: str) -> np.ndarray:
    """
    Chuyển đổi chuỗi Base64 (có hoặc không có tiền tố data:image/...) 
    thành ma trận ảnh OpenCV (Numpy Array).
    """
    try:
        # Bước 1: Kiểm tra và tách tiền tố nếu có (ví dụ: data:image/jpeg;base64,...)
        if "," in base64_string:
            # Chỉ lấy phần dữ liệu sau dấu phẩy
            base64_string = base64_string.split(",")[1]

        # Bước 2: Giải mã chuỗi Base64 thành mảng byte nhị phân
        image_bytes = base64.b64decode(base64_string)

        # Bước 3: Tận dụng hàm bytes_to_cv2 bạn đã viết để giải mã ảnh
        # (Hoặc gộp code vào đây nếu bạn muốn hàm này chạy độc lập)
        return bytes_to_cv2(image_bytes)
        
    except Exception as e:
        raise ValueError(f"Dữ liệu Base64 không hợp lệ hoặc bị lỗi: {str(e)}")
    
def extract_cv2_image(image_input: Any) -> np.ndarray:
    """Helper để tự động nhận diện đầu vào là Numpy hay Base64 string"""
    if isinstance(image_input, np.ndarray):
        return image_input.copy()
    elif isinstance(image_input, str):
        return base64_to_cv2(image_input)
    else:
        raise ValueError("Đầu vào không phải là Numpy Array hoặc Base64 String hợp lệ.")