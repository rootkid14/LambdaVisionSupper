from typing import Any, Dict
from pydantic import Field, BaseModel
import aiohttp
import json
import asyncio
from app.services.ConnectionBus import APIManualRoutingBus

from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType

class APIInput(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict, title="RequestBody", description=UIDataType.JSON)

class APIOutput(BaseModel):
    response: Dict[str, Any] = Field(..., title="Response Data", description=UIDataType.JSON)
    status_code: int = Field(..., title="Status Code", description=UIDataType.NUMBER)

#SAMPLE JSON:
# {
#   "id": "node_api_12345",          // ID duy nhất của instance này trên Canvas
#   "type": "universal_node",       // Kiểu Component hiển thị ở FE
#   "position": { "x": 250, "y": 100 }, // Tọa độ vị trí trên màn hình
#   "data": {                        // Đây là "Trái tim" chứa dữ liệu của Node
#     "className": "APINode",        // Tên Class ở BE để LogicPoolManager khởi tạo
#     "label": "Send API Request",   // Tên hiển thị
    
#     /* PHẦN CONFIG FIELDS (Dữ liệu tĩnh bạn nhập tay) */
#     "serverId": "worker_ai_01",    // Giá trị từ SERVER_POOL_DROPDOWN
#     "endpoint": "/api/v1/predict", // Giá trị từ TEXT field
#     "method": "POST",              // Giá trị từ SELECT field

#     /* PHẦN ĐỊNH NGHĨA PIN (Nếu là Dynamic Node) */
#     "inputs": [                    // Danh sách các chân đầu vào
#       { "id": "payload", "label": "RequestBody", "dataType": "json" }
#     ],
#     "outputs": [                   // Danh sách các chân đầu ra
#       { "id": "response", "label": "Response Data", "dataType": "json" },
#       { "id": "status_code", "label": "Status", "dataType": "number" }
#     ]
#   }
# }


@registry_node
class APINode(BaseNode[APIInput, APIOutput]):
    INPUT_SCHEMA = APIInput
    OUTPUT_SCHEMA = APIOutput
    NODE_TYPE = NodeType.API
    UI_LABEL = "Send API Request"
    UI_DESCRIPTION = "Gọi API thông qua HTTP"
    UI_COLOR = "bg-blue-600"
    CONFIG_FIELDS = [
        UIConfigField(
            id="serverId",
            label="Choose Host",
            type=UIConfigType.SERVER_POOL_DROPDOWN.value
        ),
        UIConfigField(
            id="endpoint",
            label="Endpoint (/api/...)",
            type=UIConfigType.TEXT.value,
            default="/"
        ),
        UIConfigField(
            id="method",
            label="HTTP Method",
            type=UIConfigType.SELECT.value,
            options=["POST", "GET", "PUT", "DELETE"],
            default="POST"
        )
    ]


    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)
        self.server_id = self.node_data.get("serverId") # Chọn từ List
        self.endpoint = self.node_data.get("endpoint", "/") # VD: /api/v1/data
        self.method = self.node_data.get("method", "POST").upper()

    async def execute(self) -> None:
        """Call an API"""
        if not self.server_id:
            raise ValueError(f"Khối {self.node_id}: Chưa chọn Server ID!")
        
        bus = APIManualRoutingBus()
        request_body = self.local_input.payload if self.local_input else {}

        context = bus.get_server_context(self.server_id)
        if not context:
            raise ValueError(f"Không thể tìm thấy Server '{self.server_id}'")

        session: aiohttp.ClientSession = context["session"]
        host: str = context["host"]

        endpoint = self.endpoint if self.endpoint.startswith('/') else f"/{self.endpoint}"
        url = f"http://{host}{endpoint}"
        
        try:
            resp_data, status = await self._make_request(session, url, request_body)
        except (aiohttp.ClientError, ConnectionResetError, asyncio.TimeoutError) as e:
            print(f"[{self.server_id}] Rớt TCP ({e}). Đang kích hoạt Lazy Reconnect...")
            
            # KÍCH HOẠT LAZY RECONNECT
            session = await bus.reconect_server(self.server_id)
            try:
                resp_data, status = await self._make_request(session, url, request_body)
            except Exception as final_err:
                raise RuntimeError(f"API call {url} failed: {final_err}")

        # 3. Đóng gói Output
        self.local_output = self.OUTPUT_SCHEMA(
            response=resp_data,
            status_code=status
        )

    async def _make_request(self, session: aiohttp.ClientSession, url: str, payload: dict):
        """Hàm thực thi HTTP thuần túy"""
        if self.method == "POST":
            async with session.post(url, json=payload, timeout=10.0) as resp:
                # Dùng text() rồi parse JSON thay vì json() trực tiếp để tránh lỗi 
                # nếu server ngoài thỉnh thoảng trả về text (như lỗi 502 của Nginx)
                text_data = await resp.text()
                try:
                    json_data = json.loads(text_data)
                except json.JSONDecodeError:
                    json_data = {"raw_text": text_data}
                return json_data, resp.status
                
        elif self.method == "GET":
            async with session.get(url, timeout=10.0) as resp:
                text_data = await resp.text()
                try:
                    json_data = json.loads(text_data)
                except json.JSONDecodeError:
                    json_data = {"raw_text": text_data}
                return json_data, resp.status
        else:
            raise ValueError(f"Method {self.method} chưa được hỗ trợ")
        

class callLogicObjectInput(BaseModel):
    """This pin only for the purpose of connecting with the graph so that kahn's algorithm work, it has no use"""
    Trigger: str = Field(title="Trigger", description=UIDataType.ANY)

@registry_node
class CallLogicObjectNode(BaseNode[callLogicObjectInput, APIOutput]):
    INPUT_SCHEMA = callLogicObjectInput # Chỉ cần Payload
    OUTPUT_SCHEMA = APIOutput
    NODE_TYPE = NodeType.API
    UI_LABEL = "Call Sub-Graph"
    UI_DESCRIPTION = "Kích hoạt một Logic Graph khác trên các máy chủ nội bộ"
    UI_COLOR = "bg-emerald-600"
    CONFIG_FIELDS = [
        UIConfigField(
            id="serverId",
            label="Select Server",
            type=UIConfigType.SELECT,
            options=["sev1", "sev2"],
            default=""
        ),
        UIConfigField(
            id="logicId",
            label="Logic Object ID",
            type=UIConfigType.TEXT,
            default=""
        )
    ]

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        
        # 1. Chọn máy chủ từ APIManualRoutingBus (VD: "worker_ai_1")
        self.target_server_id = self.node_data.get("serverId") 
        
        # 2. Chọn Logic ID đang có trên máy chủ đó (VD: "yolo_defect_detect")
        self.target_logic_id = self.node_data.get("logicId")

    async def execute(self) -> None:
        if not self.target_server_id or not self.target_logic_id:
            raise ValueError("Chưa cấu hình Server ID hoặc Logic ID!")

        bus = APIManualRoutingBus()
        context = bus.get_server_context(self.target_server_id)
        session : aiohttp.ClientSession = context["session"]
        host = context["host"]

        # Endpoint chuẩn hóa của toàn hệ thống Lambda Vision
        url = f"http://{host}/api/v1/logic/{self.target_logic_id}/trigger"
        payload = self.local_input.payload

        try:
            async with session.post(url, json=payload, timeout=30.0) as resp:
                result : dict = await resp.json()
                
                if not result.get("success"):
                    raise RuntimeError(f"Sub-graph thất bại: {result.get('error_message')}")
                
                self.local_output = self.OUTPUT_SCHEMA(data=result.get("data"))
                
        except Exception as e:
            raise RuntimeError(f"Lỗi khi gọi {self.target_logic_id} trên {self.target_server_id}: {e}")