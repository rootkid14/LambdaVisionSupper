import asyncio
import requests
from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from app.services.node_registry import BaseNode, registry_node, NodeType, UIDataType, UIConfigField, UIConfigType

class ESP32RelayInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    ip_address: str = Field(default="esp-relay.local", title="ESP32 IP/Host", description=UIDataType.STRING.value)
    action: str = Field(default="ON", title="Action (ON/OFF/STATUS)", description=UIDataType.STRING.value)
    timeout_req: float = Field(default=2.0, title="Timeout (s)", description=UIDataType.NUMBER.value)

class ESP32RelayOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
    success: bool = Field(default=False, title="Success", description=UIDataType.BOOLEAN.value)
    response_data: Any = Field(default={}, title="Response JSON", description=UIDataType.ANY.value)

@registry_node
class ESP32RelayNode(BaseNode[ESP32RelayInput, ESP32RelayOutput]):
    INPUT_SCHEMA = ESP32RelayInput
    OUTPUT_SCHEMA = ESP32RelayOutput
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "ESP32 Relay Control"
    UI_DESCRIPTION = "Gửi lệnh HTTP điều khiển ESP32 qua chân cắm"
    UI_COLOR = "#059669"
    
    # MẢNG CONFIG BÂY GIỜ TRỐNG (Hoặc chỉ giữ lại các hằng số ít thay đổi)
    CONFIG_FIELDS = []

    def _send_http_request(self, ip: str, action: str, timeout: float) -> dict:
        ip = ip.strip()
        base_url = ip if ip.startswith("http") else f"http://{ip}"
        
        # Chuẩn hóa action về chữ hoa để so sánh
        act = action.upper()
        if act == "ON":
            res = requests.post(f"{base_url}/relay/on", timeout=timeout)
        elif act == "OFF":
            res = requests.post(f"{base_url}/relay/off", timeout=timeout)
        else:
            res = requests.get(f"{base_url}/status", timeout=timeout)
            
        res.raise_for_status()
        return res.json()

    async def execute(self) -> None:
        # LẤY TRỰC TIẾP TỪ INPUT PIN
        ip = self.local_input.ip_address
        action = self.local_input.action
        timeout = self.local_input.timeout_req
            
        try:
            response = await asyncio.to_thread(self._send_http_request, ip, action, timeout)
            self.local_output = self.OUTPUT_SCHEMA(success=True, response_data=response)
        except Exception as e:
            self.local_output = self.OUTPUT_SCHEMA(success=False, response_data={"error": str(e)})