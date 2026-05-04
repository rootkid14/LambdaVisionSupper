from pydantic import BaseModel, Field
from typing import Dict, Any


# ==========================================
# 1. DATA CONTRACTS (Hợp đồng dữ liệu đầu vào)
# ==========================================
class DeployRequest(BaseModel):
    logic_id: str = Field(..., description="Asssign an ID to an Logic Object to deploy")
    workflow_json: Dict[str, Any] = Field(..., description="Nội dung file JSON Đồ thị từ React Flow")

class ExecuteRequest(BaseModel):
    logic_id: str
    payload: Dict[str, Any] = Field(..., description="Dữ liệu động bơm vào Graph (VD: {'raw_image': 'base64...'})")

class DebugRunRequest(BaseModel):
    workflow_json: Dict[str, Any] = Field(..., description="Bản vẽ JSON hiện tại trên Canvas")
    payload: Dict[str, Any] = Field(..., description="Dữ liệu bơm vào (VD: Ảnh Base64, số, chữ...)")