import asyncio
import serial
import serial.tools.list_ports
import threading
from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType

# ==========================================
# 1. SERIAL MANAGER (Quản lý kết nối & Auto-Scan)
# ==========================================
class ESP32SerialManager:
    _instance = None
    _connections = {}  
    _cached_auto_port = None 
    _global_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ESP32SerialManager, cls).__new__(cls)
        return cls._instance

    def _scan_for_esp32(self, baudrate: int) -> str:
        """Thuật toán quét tất cả cổng COM và gửi tín hiệu dò tìm"""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            try:
                ser = serial.Serial()
                ser.port = p.device
                ser.baudrate = baudrate
                ser.timeout = 1.5 # Chờ ESP32 phản hồi
                ser.dtr = False
                ser.rts = False
                
                ser.open()
                ser.reset_input_buffer()
                
                # Gửi lệnh Ping
                ser.write(b"status\n")
                response = ser.readline().decode('utf-8').strip()
                ser.close()
                
                # Nếu ESP32 trả lời đúng mật khẩu
                if "ACK: STATUS" in response or "SYS: ESP32_READY" in response:
                    return p.device
            except Exception:
                continue # Kệ lỗi, quét cổng tiếp theo
        return None

    def send_command(self, port: str, baudrate: int, command: str, timeout: float) -> str:
        with self._global_lock:
            actual_port = port.strip().upper()
            
            # --- LOGIC CHẶN "AUTO" VÀ ĐI QUÉT ---
            if actual_port == "AUTO":
                # Tái sử dụng cổng đã tìm thấy ở nhịp trước
                if self._cached_auto_port and self._cached_auto_port in self._connections:
                    actual_port = self._cached_auto_port
                else:
                    print("[ESP32 Serial] Đang quét toàn bộ hệ thống tìm ESP32...")
                    found_port = self._scan_for_esp32(baudrate)
                    
                    if not found_port:
                        raise ConnectionError("Không tìm thấy ESP32! Hãy chắc chắn cáp đã cắm và chọn đúng Baud Rate.")
                        
                    print(f"[ESP32 Serial] ✅ Đã ghép nối thành công ESP32 tại: {found_port}")
                    self._cached_auto_port = found_port
                    actual_port = found_port

            # --- MỞ CỔNG VÀ GỬI LỆNH (Dùng actual_port đã xác định) ---
            if actual_port not in self._connections:
                try:
                    ser = serial.Serial()
                    ser.port = actual_port
                    ser.baudrate = baudrate
                    ser.timeout = timeout
                    ser.dtr = False
                    ser.rts = False
                    ser.open()
                    self._connections[actual_port] = ser
                except Exception as e:
                    raise ConnectionError(f"Không thể mở cổng {actual_port}. Chi tiết: {e}")

            ser = self._connections[actual_port]
            
            try:
                ser.reset_input_buffer()
                cmd_str = f"{command.lower()}\n"
                ser.write(cmd_str.encode('utf-8'))
                
                response = ser.readline().decode('utf-8').strip()
                
                if not response:
                    raise TimeoutError(f"ESP32 im lặng, không phản hồi lệnh '{command}'")
                    
                return response
                
            except Exception as e:
                # Dọn dẹp cache nếu bị rớt kết nối giữa chừng
                if port.strip().upper() == "AUTO":
                    self._cached_auto_port = None
                    
                try: ser.close()
                except: pass
                if actual_port in self._connections:
                    del self._connections[actual_port]
                raise RuntimeError(f"Mất kết nối vật lý: {e}")

# ==========================================
# 2. KHAI BÁO NODE
# ==========================================
class ESP32SerialInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    com_port: str = Field(default="AUTO", title="COM Port (AUTO/COMx)", description=UIDataType.STRING.value)
    action: str = Field(default="ON", title="Action (ON/OFF/STATUS)", description=UIDataType.STRING.value)
    baud_rate: int = Field(default=9600, title="Baud Rate", description=UIDataType.NUMBER.value)
    timeout_req: float = Field(default=2.0, title="Timeout (s)", description=UIDataType.NUMBER.value)

class ESP32SerialOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    
    success: bool = Field(default=False, title="Success", description=UIDataType.BOOLEAN.value)
    response_msg: str = Field(default="", title="Response Message", description=UIDataType.STRING.value)

@registry_node
class ESP32SerialNode(BaseNode[ESP32SerialInput, ESP32SerialOutput]):
    INPUT_SCHEMA = ESP32SerialInput
    OUTPUT_SCHEMA = ESP32SerialOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "ESP32 Serial Relay"
    UI_DESCRIPTION = "Điều khiển ESP32 qua cáp USB (Tự động tìm cổng COM)"
    UI_COLOR = "#059669"
    REQUIRE_TIMEOUT = True
    CONFIG_FIELDS = []

    async def execute(self) -> None:
        port = self.local_input.com_port
        action = self.local_input.action.strip()
        baud = int(self.local_input.baud_rate)
        timeout = float(self.local_input.timeout_req)
            
        manager = ESP32SerialManager()
            
        try:
            response = await asyncio.to_thread(
                manager.send_command, 
                port, 
                baud,
                action, 
                timeout
            )
            
            is_success = response.startswith("ACK:") or response.startswith("SYS:")
            self.local_output = self.OUTPUT_SCHEMA(success=is_success, response_msg=response)
        except Exception as e:
            print(f"[Lỗi ESP32]: {str(e)}")
            self.local_output = self.OUTPUT_SCHEMA(success=False, response_msg=str(e))