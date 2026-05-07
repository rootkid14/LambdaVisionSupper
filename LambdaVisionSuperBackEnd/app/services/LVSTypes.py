from enum import Enum
from pydantic import create_model, BaseModel, Field
from typing import Any, Dict, Optional, List
import numpy as np

class UIDataType(str, Enum):
    """Định nghĩa chuẩn xác các kiểu dữ liệu mà Frontend có thể hiểu
    Lưu ý : các kiểu ở đây sẽ xuất hiện toàn bộ trong môi trường tạo Graph lập trình của logic object
    nhưng với UIEngine, sẽ chỉ có một số kiểu mà UIEngine có thể hứng, vì thế nên nếu dự định trả 
    kiểu nào về cho phía FE nhận thì phải kiểm tra ở UIEngine xem bảng GlobalTagsTable có kiểu đó không
    Nếu không có trong bảng GlobalTagsTable thì Sequencer của UIEngine sẽ không nhận được (thiết kế này 
    là vì mục đích an toàn, nao kia có xem lại cũng đừng cố sửa nó nữa, Đám types này của chúng ta đã hoàn hảo rồi)
    """
    NUMPY_ARRAY = "numpy_array"
    TENSOR = "tensor"
    NUMBER = 'number'
    STRING = "string"
    BOOLEAN = "boolean"
    ANY = "any"
    OBJECT_REF = "object_ref"
    JSON = "json"
    DICT = "dict"
    LIST = "list"
    BASE64 = "base64"
    EXECUTE = "execute"


class FileType(str, Enum):
    """Define the file type the system can use"""
    FILE = "file"
    GRAPH = "graph"
    PLUGIN = "plugin"

class NodeType(Enum):
    PROGRAM = 1
    IN_LINE = 2
    OBJECT = 3
    FUNCTION = 4
    API = 5
    JOIN = 6
    SPLIT = 7
    MEMORY = 8
    MEMORY_READ = 9
    TELEPORT_IN = 10
    TELEPORT_OUT = 11

class TokenStatus(int, Enum):
    READY = 0
    PROCESSING = 1

class GraphNodeType(int, Enum):
    NORMAL = 0
    SPLIT = 1
    JOIN = 2


def map_fe_type_to_python(fe_type: str) -> Any:
    """Translate data type from FrontEnd Json to Python Type for pydantic"""
    mapping = {
        "boolean" : bool,
        "number" : float,
        "string" : str,
        "numpy_array" : np.ndarray,
        "tensor" : Any,
        "any": Any,
        "object_ref" : Any,
        "json" : Dict[str, Any],
        "dict": Dict[str, Any],
        "list": List[Any],
        "base64": str,
        "execute": Any
    }
    return mapping.get(fe_type, Any)


class UIConfigType(str, Enum):
    """Danh sách các loại UI Control được phép render trên Frontend"""
    TEXT = "text"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    SELECT = "select" # Bắt buộc phải có thêm mảng 'options'
    
    # Các Dropdown gọi API động
    SERVER_POOL_DROPDOWN = "server_pool_dropdown"
    DEVICE_POOL_DROPDOWN = "device_pool_dropdown"
    ACTIVE_LOGIC_DROPDOWN = "active_logic_dropdown"

class UIConfigField(BaseModel):
    """Schema giúp IDE gợi ý khi viết UI_CONFIG_FIELDS cho các Node"""
    id: str = Field(..., description="ID của trường dữ liệu (sẽ lưu vào node_data)")
    label: str = Field(..., description="Tên hiển thị trên giao diện")
    type: UIConfigType = Field(..., description="Loại điều khiển UI")
    
    # Các trường phụ (chỉ dùng cho một số loại cụ thể)
    default: Optional[Any] = None
    options: Optional[List[str]] = Field(default=None, description="Chỉ dùng khi type là SELECT")