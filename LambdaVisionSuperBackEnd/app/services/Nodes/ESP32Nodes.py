import numpy as np
import cv2
import asyncio
import aiohttp
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any

from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType
from app.services.DevicePoolManager import HTTPDevicePoolManager 
from app.services.utils.image_utils import bytes_to_cv2, cv2_to_base64
    

class ESP32DirectHTTPInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    url : str = Field(default="/status", title="URL", description=UIDataType.STRING.value)

class ESP32DirectHTTPOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    success: bool = Field(default=False, title="Success", description=UIDataType.BOOLEAN.value)

@registry_node
class ESP32DirectHTTPOutput(BaseNode[ESP32DirectHTTPInput, ESP32DirectHTTPOutput]):
    INPUT_SCHEMA = ESP32DirectHTTPInput
    OUTPUT_SCHEMA = ESP32DirectHTTPOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "ESP32 HTTP MESSAGE"
    UI_DESCRIPTION = "Send a message without requiring the device to be in device pool"
    UI_COLOR = "#00897B"
    REQUIRE_TIMEOUT = 5.0

    CONFIG_FIELDS = [
        UIConfigField(
            id="host",
            label="Host Name",
            type=UIConfigType.TEXT,
            default="lambda-relay.local"
        )
    ]

    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)
        self.host : str = self.get_config_field_value("host")

    async def execute(self):
        action = self.local_input.url

        # Remove it incase user do it reduntdently
        host = self.host.replace("http://", "").replace("https://", "")

        url = f"http://{host}{self.local_input.url}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=2.0) as response:
                    if response.status == 200:
                        self.local_output = self.OUTPUT_SCHEMA(success=True)
                    else:
                        raise RuntimeError(f"ESP32 phản hồi lỗi: HTTP Code {response.status}")
                    
        except asyncio.TimeoutError:
            raise TimeoutError(f"Không thể kết nối đến ESP32 tại '{host}'. Thiết bị có thể đã mất mạng.")
            
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Lỗi giao tiếp mạng với ESP32: {str(e)}")
        

class ESP32CameraInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    # Tên thiết bị bạn đã Add trên giao diện (ví dụ: "cam_01")
    device_id: str = Field(default="esp32cam", title="Device ID", description=UIDataType.STRING.value)
    
    # Cấu hình phơi sáng
    auto_exposure: bool = Field(default=True, title="Auto Exposure (AEC)", description=UIDataType.BOOLEAN.value)
    manual_exposure: int = Field(default=300, title="Manual Exp (if AEC off)", description=UIDataType.NUMBER.value)

class ESP32CameraOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    # Cổng xuất ma trận ảnh OpenCV cho các Node khác xử lý tiếp
    image_out: Any = Field(default=None, title="Image", description=UIDataType.BASE64.value)
    success: bool = Field(default=False, title="Success", description=UIDataType.BOOLEAN.value)

# ==========================================
# 2. KHỞI TẠO NODE CAMERA
# ==========================================
@registry_node
class ESP32CameraNode(BaseNode[ESP32CameraInput, ESP32CameraOutput]):
    INPUT_SCHEMA = ESP32CameraInput
    OUTPUT_SCHEMA = ESP32CameraOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "ESP32-S3 Camera"
    UI_DESCRIPTION = "Thu thập hình ảnh từ ESP32 qua Device Bus"
    UI_COLOR = "#3b82f6" # Màu xanh dương
    REQUIRE_TIMEOUT = 10
    CONFIG_FIELDS = []

    async def execute(self) -> None:
        device_id = self.local_input.device_id.strip()
        is_auto = self.local_input.auto_exposure
        exp_val = int(self.local_input.manual_exposure)
        
        # 1. Gọi Device Bus Singleton để lấy thông tin kết nối
        device_bus = HTTPDevicePoolManager()
        device_ctx = device_bus.get_device_context(device_id)
        
        if not device_ctx:
            print(f"[Camera Node] Lỗi: Không tìm thấy thiết bị '{device_id}' trong Pool.")
            self.local_output = self.OUTPUT_SCHEMA(success=False, image_out=None)
            return
            
        session = device_ctx["session"]
        host = device_ctx["host"]
        
        # 2. Chuẩn bị URL kèm tham số phơi sáng
        aec_param = 1 if is_auto else 0
        url = f"http://{host}/capture?aec={aec_param}&exp={exp_val}"
        
        try:
            # 3. Gửi lệnh chụp qua Session giữ kết nối (Keep-Alive)
            async with session.get(url, timeout=10.0) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    
                    # 4. Giải mã luồng JPEG thành mảng ma trận ảnh OpenCV
                    np_arr = np.frombuffer(image_bytes, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    if img is None:
                        raise ValueError("Dữ liệu ảnh bị hỏng hoặc giải mã thất bại.")
                        
                    # 6. Trả kết quả thành công ra cổng xuất
                    img = cv2_to_base64(img)
                    self.local_output = self.OUTPUT_SCHEMA(success=True, image_out=img)
                else:
                    raise ConnectionError(f"ESP32 báo lỗi HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            print(f"[Camera Node] Timeout: ESP32 {device_id} chụp ảnh quá lâu hoặc mất mạng.")
            self.local_output = self.OUTPUT_SCHEMA(success=False, image_out=None)
        except Exception as e:
            print(f"[Camera Node] Lỗi thu thập ảnh: {str(e)}")
            self.local_output = self.OUTPUT_SCHEMA(success=False, image_out=None)