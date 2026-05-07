import numpy as np
import cv2
import asyncio
import aiohttp
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any

from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType
from app.services.DevicePoolManager import HTTPDevicePoolManager 

# ==========================================
# 1. ĐỊNH NGHĨA SCHEMA ĐẦU VÀO / ĐẦU RA
# ==========================================

class ESPCameraOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image: np.ndarray = Field(..., title="Image Data", description="numpy_array")

# ==========================================
# 2. KHỞI TẠO CLASS NODE
# ==========================================
@registry_node
class ESP32CameraNode(BaseNode[None, ESPCameraOutput]):
    INPUT_SCHEMA = None
    OUTPUT_SCHEMA = ESPCameraOutput
    NODE_TYPE = NodeType.OBJECT

    METHOD_NODE_LIST = ['MakeNumberNode'] #Currently does not have any related method nodes
    
    # Dữ liệu hiển thị trên FE
    UI_LABEL = "ESP32-S3 Camera"
    UI_DESCRIPTION = "Chụp ảnh từ ESP32 qua HTTP Pool"
    UI_COLOR = "bg-teal-600" 

    CONFIG_FIELDS = [
        UIConfigField(
            id="deviceID",
            label="Select a Device",
            default="",
            type=UIConfigType.DEVICE_POOL_DROPDOWN
        )
    ]

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        self.device_id = self.get_config_field_value("deviceID", "")
    # ==========================================
    # 3. LUỒNG THỰC THI CHÍNH
    # ==========================================
    async def execute(self) -> None:
        if not self.device_id:
            raise ValueError(f"Khối {self.node_id}: Chưa chọn thiết bị ESP32 trong cấu hình!")

        pool = HTTPDevicePoolManager()
        
        # 1. Xin Context từ Pool
        context = pool.get_device_context(self.device_id)
        if not context:
            raise ValueError(f"Khối {self.node_id}: Thiết bị '{self.device_id}' chưa đi qua Pre-flight check.")
            
        session: aiohttp.ClientSession = context["session"]
        host: str = context["host"]

        # 2. Gọi lệnh lấy ảnh (Có bọc chống lỗi và Lazy Reconnect)
        try:
            img_array = await self._fetch_image(session, host)
        except (aiohttp.ClientError, ConnectionResetError, asyncio.TimeoutError) as e:
            print(f"[{self.device_id}] Rớt TCP ({e}). Đang kích hoạt Lazy Reconnect...")
            
            # Khôi phục đường ống và thử lại Lần 2
            session = await pool.reconnect_device(self.device_id)
            try:
                img_array = await self._fetch_image(session, host)
            except Exception as final_err:
                raise RuntimeError(f"Lỗi kết nối với camera {self.device_id}: {final_err}")

        # 3. Đóng gói dữ liệu đầu ra cho các Node AI phía sau
        self.local_output = self.OUTPUT_SCHEMA(
            image=img_array
        )

    # ==========================================
    # 4. HÀM XỬ LÝ ẢNH NỘI BỘ
    # ==========================================
    async def _fetch_image(self, session: aiohttp.ClientSession, host: str) -> np.ndarray:
        """Thực hiện HTTP GET, nhận Byte và giải mã thành Numpy Array"""
        url = f"http://{host}/capture"
        
        async with session.get(url, timeout=5.0) as resp:
            if resp.status == 423:
                raise RuntimeError("ESP32 đang bị khóa bởi tiến trình khác (Locked)")
            if resp.status != 200:
                raise RuntimeError(f"ESP32 trả về lỗi HTTP {resp.status}")
                
            # Đợi tải đủ bytes (HTTP Content-Length đảm bảo việc này)
            image_bytes = await resp.read()
            
            # Giải mã ảnh (Offload sang Thread pool để không block asyncio loop)
            img_array = await asyncio.to_thread(self._decode_jpg, image_bytes)
            
            if img_array is None:
                raise ValueError("Dữ liệu trả về bị hỏng, không thể giải mã JPEG")
                
            return img_array

    def _decode_jpg(self, image_bytes: bytes) -> np.ndarray:
        """Chạy bởi asyncio.to_thread để tránh nghẽn CPU"""
        np_arr = np.frombuffer(image_bytes, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)