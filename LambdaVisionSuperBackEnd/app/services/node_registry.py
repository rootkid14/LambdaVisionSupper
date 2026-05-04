from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Generic, TypeVar, TYPE_CHECKING
from pydantic import BaseModel, Field, ValidationError, create_model, ConfigDict
from app.services.LVSTypes import NodeType, UIDataType, map_fe_type_to_python, UIConfigField

if TYPE_CHECKING:
    from LogicObjects import LogicObject


NODE_REGISTRY: Dict[str, Type["BaseNode"]] = {}


def unregister_node(class_name: str):
    """Xóa một Node khỏi Registry (Dùng khi người dùng xóa file Plugin)"""
    if class_name in NODE_REGISTRY:
        del NODE_REGISTRY[class_name]
        print(f"Đã gỡ bỏ Node {class_name} khỏi Registry.")
        

def registry_node(cls: Type["BaseNode"]):
    """DECORATOR USED FOR REGISTRATION OF NEW LOGIC CLASS"""
    class_name = cls.__name__

    if class_name in NODE_REGISTRY:
        print(f"Node {class_name} already exist, overwriting")
    NODE_REGISTRY[class_name] = cls
    return cls


# Lấy biến đại diện generic cho toàn bộ class con họ pydantic BaseModel
TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

class BaseNode(ABC, Generic[TInput, TOutput]): 
    
    # DECLARE THE TEMPLATE VARIABLES
    INPUT_SCHEMA: Type[TInput] = None
    OUTPUT_SCHEMA: Type[TOutput] = None
    NODE_TYPE = None
    METHOD_NODE_LIST : List[str] = None #ONLY FOR OBJECT NODE
    CONFIG_FIELDS : List[UIConfigField] = None #For inline config fields
    INLINE_TYPE = None

    #UI VARIABLES (OVERRID BY CHILDREN CLASSES)
    UI_DESCRIPTION : str = "No Description"
    UI_COLOR: str = "bg-gray-500"
    UI_LABEL: str = "Base Node"

    def __init__(self, node_id: str, parent: "LogicObject", node_data: dict = None):
        self.node_id = node_id
        self.parent = parent
        self.node_data = node_data or {}
        
        # Bóc tách inline_val từ thẳng node_data
        self.inline_val = self.node_data.get("inlineValue") 
        
        self.local_input: TInput = None
        self.local_output: TOutput = None

    async def resolve_and_execute(self):
        """1. Gom dữ liệu -> 2. Kiểm duyệt Input -> 3. Chạy & tạo output """
        raw_kwargs = {}
        # LOCALIZE MAPPING FOR THIS NODES
        self.local_mapping = self.parent.nodes_mapping.get(self.node_id, {})

        # Find the input values by tracing the connection of this node with previous nodes that connect to it
        for input_param_name, data in self.local_mapping.items():
            src_node_id = data["source_node"]
            src_pin = data["source_pin"]
            
            src_node = self.parent.nodes_list.get(src_node_id)
            
            # Ensure that the source node exists and already have some output
            if not src_node or src_node.local_output is None :
                raise ValueError(f"Node '{src_node_id}' chưa chạy hoặc thất bại, không có dữ liệu cho pin '{src_pin}'")
            
            try:
                raw_kwargs[input_param_name] = getattr(src_node.local_output, src_pin)
            except Exception as e:
                raise ValueError(f"Không thể trích xuất {src_pin} từ {src_node.node_id}")

        # --- Pydantic Sanity check for inputs before intialize local_input ---
        if self.INPUT_SCHEMA:
            try:
                self.local_input = self.INPUT_SCHEMA(**raw_kwargs)
            except ValidationError as e:
                raise ValueError(f"Dữ liệu đầu vào của Node {self.node_id} bị sai định dạng:\n{e}")
        else:
            pass

        try:
            await self.execute()
        except Exception as e:
            raise ValueError(f"{self.node_id} đã xảy ra lỗi trong quá trình thực thi logic:\n{e}")

    @abstractmethod
    async def execute(self) -> None:
        """This class use the self.local_inputs as paramters
            And use the self.local_outputs = OUTPUT_SCHEMA(dict) to return the outputs
        """
        pass
    
    @classmethod
    def formulate_frontend_description(cls):
        """This is a class method, used for sending the FE the description of how to draw this as a node on the FE UI"""
        manifest = {
            "type" : str(cls.NODE_TYPE.value),
            "class": cls.__name__,
            "label" : cls.UI_LABEL,
            "description": cls.UI_DESCRIPTION,
            "color": cls.UI_COLOR,
            "inputs": [],
            "outputs": [],
            "config_fields": [field.model_dump(exclude_none=True) for field in cls.CONFIG_FIELDS] if cls.CONFIG_FIELDS else []
        }
        if cls.INPUT_SCHEMA:
            for fieldname, fieldInfor in cls.INPUT_SCHEMA.model_fields.items():
                manifest["inputs"].append({
                    "id": fieldname,
                    "label": fieldInfor.title or fieldname,
                    "dataType": fieldInfor.description or "unknown"
                })
        if cls.OUTPUT_SCHEMA:
            for fieldname, fieldInfor in cls.OUTPUT_SCHEMA.model_fields.items():
                manifest["outputs"].append({
                    "id" : fieldname,
                    "label": fieldInfor.title or fieldname,
                    "dataType": fieldInfor.description or "unknown"
                })
        if cls.NODE_TYPE == NodeType.IN_LINE:
            manifest.update({"inlineInputType" : cls.INLINE_TYPE})
        if cls.NODE_TYPE == NodeType.OBJECT:
            manifest.update({"functions" : cls.METHOD_NODE_LIST})
        return manifest
    
    def reset(self):
        self.local_input = None
        self.local_output = None
        
@registry_node
class SendResponseNode(BaseNode):
    """This Node act as the final node in the LogicHandling Graph, it is the user way to define what data they want to get back"""
    OUTPUT_SCHEMA = None
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Data Out"
    UI_DESCRIPTION = "Define Output Data and Send back to API"
    UI_COLOR = "bg-rose-600"

    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)

        dynamic_inputs = node_data.get("inputs", [])
        fields = {}
        for pin in dynamic_inputs:
            pin_id = pin["id"]
            py_type = map_fe_type_to_python(pin.get("dataType"))
            fields[pin_id] = (py_type, Field(title=pin.get("label", pin_id)))

        if fields:
            # Stick the dynamic pydantic model into class Instance rather than stick to Class.
            self.INPUT_SCHEMA = create_model(f'DynamicInput_{self.node_id}',__config__=ConfigDict(arbitrary_types_allowed=True), **fields)
        else:
            self.INPUT_SCHEMA = None
    
    async def execute(self):
        """
            Thanks to Pydantic, the self.local_input is now sanitized.
            The data is directly flow to local_output so that the ResponseFormation class can take the result out and send back to FE.
        """
        if self.local_input:
            final_data = self.local_input.model_dump()
        else:
            final_data = {}
        
        self.local_output = final_data
    
    def get_schema(self) -> Dict[str, str]:
        """Return a schema directly from the node_data to avoid Pydantic annotation parsing issues"""
        # Node này lấy dữ liệu từ FE thông qua "inputs"
        dynamic_inputs = self.node_data.get("inputs", [])
        if not dynamic_inputs:
            return {}
        
        path = {}
        for pin in dynamic_inputs:
            pin_id = pin.get("id")
            data_type = pin.get("dataType", "any")
            if pin_id:
                path[f".{pin_id}"] = data_type
        
        return path



@registry_node
class ReceivePayloadNode(BaseNode):
    OUTPUT_SCHEMA = None
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Data In"
    UI_DESCRIPTION = "Define what data need to receive from FE"
    UI_COLOR = "bg-purple-600"

    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)

        dynamic_outputs = node_data.get("outputs", [])
        fields = {}
        for pin in dynamic_outputs:
            pin_id = pin["id"]
            py_type = map_fe_type_to_python(pin.get("dataType"))
            fields[pin_id] = (py_type, Field(title=pin.get("label", pin_id)))

        if fields:
            self.OUTPUT_SCHEMA = create_model(f'DynamicOutput_{self.node_id}', __config__=ConfigDict(arbitrary_types_allowed=True), **fields)
        else:
            self.OUTPUT_SCHEMA = None

    async def execute(self) -> None:
        """Left Empty because we will inject data from LogicObject to this special EntryNode"""
        pass

    def get_schema(self) -> Dict[str, str]:
        """Return a schema directly from the node_data to avoid Pydantic annotation parsing issues"""
        # Node này cung cấp dữ liệu cho FE thông qua "outputs"
        dynamic_outputs = self.node_data.get("outputs", [])
        if not dynamic_outputs:
            return {}
        
        path = {}
        for pin in dynamic_outputs:
            pin_id = pin.get("id")
            data_type = pin.get("dataType", "any")
            if pin_id:
                path[f".{pin_id}"] = data_type
        
        return path
    

@registry_node
class ObjectNode(BaseNode[TInput, TOutput]):

    NODE_TYPE = NodeType.OBJECT

    """A Node that act as an individual Object with its own methods and persistent state"""
    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)
        self.internal_memory: Dict[str, Any] = {}  #Any persistent memory data of this node will be put in side here (use fule if the function node need to access)

    @abstractmethod
    def intialize_object(self):
        """This function run once when deploy the graph"""
        pass
    
    def reset_object_memory(self):
        """This clear up object internal memory"""
        self.internal_memory = None

