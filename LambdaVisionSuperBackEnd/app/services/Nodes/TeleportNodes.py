from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from app.services.node_registry import BaseNode, registry_node
from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType, TokenStatus

# ==========================================
# 1. PORTAL IN (ĐIỂM NHẢY - HỐ ĐEN)
# ==========================================
class PortalInInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_in: Any = Field(default="GO", title="Execute In", description=UIDataType.EXECUTE.value)
    payload: Any = Field(default=None, title="Payload In", description=UIDataType.ANY.value)

@registry_node
class PortalInNode(BaseNode[PortalInInput, None]):
    INPUT_SCHEMA = PortalInInput
    OUTPUT_SCHEMA = None # KHÔNG CÓ CỔNG RA! Nó nuốt chửng Token và Dây dẫn
    NODE_TYPE = NodeType.TELEPORT_IN
    UI_LABEL = "TELEPORT (IN)"
    UI_DESCRIPTION = "Thu nhận Token và Dữ liệu để dịch chuyển tức thời"
    UI_COLOR = "bg-cyan-600"

    
    
    CONFIG_FIELDS = [
        UIConfigField(id="channel_name", label="Channel Name", type=UIConfigType.TEXT.value, default="Channel_A")
    ]

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        self.channel_name = self.node_data.get("channel_name", "Channel_A")

    async def execute(self) -> None:
        """Lưu trữ dữ liệu vào Không gian chung (Ether / Extra Memory)"""
        if self.local_input and self.local_input.payload is not None:
            memory_key = f"portal_data_{self.channel_name}"
            self.parent.extra_memory[memory_key] = self.local_input.payload


    def _forward_token(self, token_id) -> None:
        """GHI ĐÈ: Bẻ cong không gian Token"""
        if token_id is None:
            return
            
        # 1. Hủy diệt Token hiện tại (Nó đã đi vào Hố Đen)
        self.parent.delete_token(token_id)
        
        # 2. Tìm TẤT CẢ các điểm đáp (White Hole) có cùng Kênh
        for n_id, node in self.parent.nodes_list.items():
            if node.__class__.__name__ == "PortalOutNode" and getattr(node, "channel_name", "") == self.channel_name:
                # 3. Phép thuật: Khởi tạo Token mới ném thẳng vào tọa độ của các điểm đáp!
                self.parent.spawn_token(n_id)


# ==========================================
# 2. PORTAL OUT (ĐIỂM ĐÁP - LỖ TRẮNG)
# ==========================================
class PortalOutOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute_out: Any = Field(default="GO", title="Execute Out", description=UIDataType.EXECUTE.value)
    payload: Any = Field(default=None, title="Payload Out", description=UIDataType.ANY.value)

@registry_node
class PortalOutNode(BaseNode[None, PortalOutOutput]):
    INPUT_SCHEMA = None # KHÔNG CÓ CỔNG VÀO! (Token tự động rơi xuống đây)
    OUTPUT_SCHEMA = PortalOutOutput
    NODE_TYPE = NodeType.TELEPORT_OUT
    UI_LABEL = "TELEPORT (OUT)"
    UI_DESCRIPTION = "Điểm xuất hiện của Token và Dữ liệu từ không gian ảo"
    UI_COLOR = "bg-purple-500"

    CONFIG_FIELDS = [
        UIConfigField(id="channel_name", label="Channel Name", type=UIConfigType.TEXT.value, default="Channel_A")
    ]

    def __init__(self, node_id, parent, node_data=None):
        super().__init__(node_id, parent, node_data)
        self.channel_name = self.node_data.get("channel_name", "Channel_A")

    async def execute(self) -> None:
        """Nhận Token và bốc Dữ liệu từ Không gian chung ra"""
        memory_key = f"portal_data_{self.channel_name}"
        
        # Lấy dữ liệu (nếu có). Nếu không có (chỉ truyền tín hiệu chạy) thì trả về None
        payload_data = self.parent.extra_memory.get(memory_key, None)
        
        self.local_output = self.OUTPUT_SCHEMA(
            execute_out="GO",
            payload=payload_data
        )