import numpy as np
import cv2
import asyncio
import aiohttp
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from zeroconf import Zeroconf
import socket
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


class ESP32CameraMDNSInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    # Sử dụng mDNS hostname thay vì ID
    mdns_hostname: str = Field(default="esp32cam.local", title="mDNS Hostname", description=UIDataType.STRING.value)
    
    auto_exposure: bool = Field(default=True, title="Auto Exposure (AEC)", description=UIDataType.BOOLEAN.value)
    manual_exposure: int = Field(default=300, title="Manual Exp", description=UIDataType.NUMBER.value)

class ESP32CameraMDNSOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    image_out: Any = Field(default=None, title="Image", description=UIDataType.BASE64.value)
    success: bool = Field(default=False, title="Success", description=UIDataType.BOOLEAN.value)

@registry_node
class ESP32CameraMDNSNode(BaseNode[ESP32CameraMDNSInput, ESP32CameraMDNSOutput]):
    INPUT_SCHEMA = ESP32CameraMDNSInput
    OUTPUT_SCHEMA = ESP32CameraMDNSOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "ESP32 mDNS Camera"
    UI_DESCRIPTION = "Kết nối trực tiếp ESP32 qua mDNS (Không cần Device Bus)"
    UI_COLOR = "#10b981" 
    REQUIRE_TIMEOUT = 10

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        self._cached_ip = None
        self._http_session = None

    def resolve_native_mdns(self, hostname: str) -> str:
        """Sử dụng thư viện socket mặc định để phân giải tên miền .local"""
        # Loại bỏ tiền tố http:// nếu người dùng lỡ nhập vào Node
        hostname = hostname.replace("http://", "").split(":")[0]
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror as e:
            print(f"[mDNS Resolver] Lỗi phân giải {hostname}: {e}")
            return None

    async def _get_session(self):
        """Quản lý HTTP Session cục bộ cho Node"""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    async def execute(self) -> None:
        hostname = self.local_input.mdns_hostname.strip()
        is_auto = self.local_input.auto_exposure
        exp_val = int(self.local_input.manual_exposure)
        
        # 1. Phân giải IP (Sử dụng Cache nếu có)
        target_ip = self._cached_ip
        if not target_ip:
            print(f"[Camera Node] Đang quét mDNS tìm '{hostname}'...")
            
            # Sử dụng hàm socket native bọc trong asyncio để không block luồng
            target_ip = await asyncio.to_thread(self.resolve_native_mdns, hostname)
            
            if not target_ip:
                print(f"[Camera Node] Lỗi: Không tìm thấy '{hostname}' trong mạng LAN.")
                self.local_output = self.OUTPUT_SCHEMA(success=False, image_out=None)
                return
            
            print(f"[Camera Node] Đã phân giải {hostname} -> {target_ip}")
            self._cached_ip = target_ip # Lưu cache cho khung hình tiếp theo
        
        # 2. Chuẩn bị Request
        aec_param = 1 if is_auto else 0
        url = f"http://{target_ip}/capture?aec={aec_param}&exp={exp_val}"
        session = await self._get_session()
        
        try:
            # 3. Gửi lệnh chụp
            async with session.get(url, timeout=5.0) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    
                    # 4. Giải mã JPEG
                    np_arr = np.frombuffer(image_bytes, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    if img is None:
                        raise ValueError("Dữ liệu ảnh bị hỏng.")
                        
                    # 5. Đóng gói kết quả (giả định cv2_to_base64 đã được import)
                    img_base64 = cv2_to_base64(img)
                    self.local_output = self.OUTPUT_SCHEMA(success=True, image_out=img_base64)
                else:
                    raise ConnectionError(f"HTTP {response.status}")
                    
        except (asyncio.TimeoutError, aiohttp.ClientError, ConnectionError) as e:
            print(f"[Camera Node] Mất kết nối tới {hostname} ({target_ip}). Xóa cache IP.")
            self._cached_ip = None # Xóa cache để frame sau tự động quét mDNS lại
            self.local_output = self.OUTPUT_SCHEMA(success=False, image_out=None)
            
        except Exception as e:
            print(f"[Camera Node] Lỗi xử lý ảnh: {str(e)}")
            self.local_output = self.OUTPUT_SCHEMA(success=False, image_out=None)
            
    def __del__(self):
        """Dọn dẹp session khi xóa node"""
        if self._http_session and not self._http_session.closed:
            asyncio.create_task(self._http_session.close())