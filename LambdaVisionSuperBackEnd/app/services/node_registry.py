from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Generic, TypeVar, TYPE_CHECKING
from pydantic import BaseModel, Field, create_model, ConfigDict
from app.services.LVSTypes import NodeType, UIDataType, map_fe_type_to_python, UIConfigField, UIConfigType, TokenStatus
import asyncio

if TYPE_CHECKING:
    from app.services.LogicObjects import LogicObject


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
    CONFIG_FIELDS : List[UIConfigField] = None #For inline config fields (Note: type does not need .value)
    INLINE_TYPE = None
    
    # Đặt Timeout mặc định cho tất cả các Node là 5 giây (<= 0 means allow infinite loop)
    REQUIRE_TIMEOUT = True
    NODE_TIMEOUT = 1.0

    #UI VARIABLES (OVERRID BY CHILDREN CLASSES)
    UI_DESCRIPTION : str = "No Description"
    UI_COLOR: str = "bg-gray-500"
    UI_LABEL: str = "Base Node"

    # ==========================================
    # MAGIC METHOD: ÉP BUỘC CÓ TRƯỜNG TIMEOUT
    # ==========================================
    @classmethod
    def get_default_config(cls) -> List[UIConfigField]:
        return [
            UIConfigField(
                id="timeout_limit", 
                label="Timeout (s)", 
                type=UIConfigType.NUMBER.value, 
                default=cls.NODE_TIMEOUT
            )
        ]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Nếu class con quên khai báo CONFIG_FIELDS, tạo mảng rỗng
        if getattr(cls, 'CONFIG_FIELDS', None) is None:
            cls.CONFIG_FIELDS = []
            
        # Kiểm tra xem class con đã tự định nghĩa trường timeout_limit chưa
        has_timeout = any(f.id == "timeout_limit" for f in cls.CONFIG_FIELDS)
        
        # Tiêm trường timeout vào đầu mảng config
        if not has_timeout and cls.REQUIRE_TIMEOUT:
            cls.CONFIG_FIELDS = cls.get_default_config() + cls.CONFIG_FIELDS


    def __init__(self, node_id: str, parent: "LogicObject", node_data: dict = None):
        self.node_id = node_id
        self.parent = parent
        self.node_data = node_data or {}
        self.next_nodes : List[str] = [] 

        self.output_exec_map: Dict[str, List[str]] = {}

        self.prev_nodes : List[str] = []
        self.input_memory_map = {} 
        self.output_memory_map = {} 
        
        # Trạng thái Runtime
        self.has_executed = False
        self.is_resolving_data = False # CHỐT CHẶN BẢO VỆ CYCLIC LOOP
        self.kept_tokens = []
        self.token_count = 0
        self.token_qty_required = 0
        
        # Bóc tách inline_val từ thẳng node_data
        self.inline_val = self.node_data.get("inlineValue") 
        
        # ĐỌC CẤU HÌNH TIMEOUT TỪ FRONTEND TRUYỀN XUỐNG
        raw_timeout = self.get_config_field_value("timeout_limit", self.NODE_TIMEOUT)
        try:
            self.timeout_limit = float(raw_timeout)
        except (TypeError, ValueError):
            self.timeout_limit = self.NODE_TIMEOUT
        
        self.local_input: TInput = None
        self.local_output: TOutput = None

    def _reset_cache(self):
        """LogicObject sẽ gọi hàm này ở giây đầu tiên của mỗi chu kỳ chạy"""
        self.local_input = None
        self.local_output = None
        self.has_executed = False
        self.is_resolving_data = False
        self.kept_tokens = []
        self.token_count = 0

    def _receive_token(self, token_id) -> None:
        """Swith the token state to processing"""
        if token_id is None:
            return
        if (self.NODE_TYPE is NodeType.JOIN and token_id not in self.kept_tokens): 
            self.parent.delete_token(token_id)
            self.kept_tokens.append(token_id)
            self.token_count += 1
        else:
            self.parent.tokens_list[token_id] = {"status": TokenStatus.PROCESSING, "node_id": self.node_id}

    def _forward_token(self, token_id) -> None:
        """Move the token to next guy(s)"""
        if token_id is None:
            return
        if(self.NODE_TYPE is NodeType.SPLIT): 
            self.parent.delete_token(token_id)
            for node_id in self.next_nodes:
                self.parent.spawn_token(node_id)
        else:
            if self.next_nodes:
                self.parent.tokens_list[token_id] = {"status": TokenStatus.READY, "node_id": self.next_nodes[0]} 
            else:
                # Nếu không còn next_nodes, Token này đã hoàn thành sứ mệnh
                self.parent.delete_token(token_id)

    async def _execution_logic(self, token_id) -> List[str]:
        """The main logic execution of this node, will be called by Logic Object in its main loop"""

        if self.has_executed:
            self._forward_token(token_id)

        self._receive_token(token_id)

        # print(f"Node {self.node_id} has memory map of: input: {self.input_memory_map}, output: {self.output_memory_map}")

        # Recursive call to previous node to get it running so the data appears.
        try:
            for pin_name, mem_slot in self.input_memory_map.items():
                if self.parent.memory_pool.get(mem_slot) is None:
                    generator_node_id = self.parent.memory_generators.get(mem_slot)
                    # print(f"node {self.node_id} is recursively called {generator_node_id} for {mem_slot}")
                    if generator_node_id:
                        generator_node = self.parent.nodes_list[generator_node_id]
                        if not generator_node.has_executed:
                            await generator_node._execution_logic(None)
        except Exception as e:
            raise Exception(f"Something failed at recursive back loop of node {self.node_id} {e}, maybe its input memory is unexpectedly empty")
                            
           
        #Extract input from parent's Memory pool
        raw_inputs = {}
        #safely get self.input_memory_map.items() which is the {pin_name : memory_slot_id} 
        for pin_name, mem_slot in getattr(self, 'input_memory_map', {}).items():
            raw_inputs[pin_name] = self.parent.memory_pool.get(mem_slot) # {pinname: value}

        if self.INPUT_SCHEMA:
            # Lọc bỏ None để Pydantic tự động ăn giá trị Default
            clean_inputs = {k: v for k, v in raw_inputs.items() if v is not None}
            try:
                self.local_input = self.INPUT_SCHEMA(**clean_inputs)
            except Exception as e:
                raise Exception(f"Lỗi trích xuất input values của node {self.node_id} \n{e}")

        try:
            if self.timeout_limit > 0:
                target_pin = await asyncio.wait_for(self.execute(), self.timeout_limit)
            else:
                target_pin = await self.execute()
        except asyncio.TimeoutError:
            raise RuntimeError(f"TIMEOUT: Khối [{self.UI_LABEL}] đã chạy vượt quá {self.timeout_limit} giây! Vui lòng kiểm tra lại vòng lặp vô hạn hoặc nghẽn mạng.")
        except Exception as e:
            # Re-raise lỗi bình thường để hệ thống bắt
            raise RuntimeError(f"Lỗi logic tại [{self.UI_LABEL}]: {str(e)}")
        
        #Get Data from ouputs pin to write to Memory Pool:
        if self.local_output and hasattr(self, 'output_memory_map'):
            for pin_name, mem_slot in self.output_memory_map.items():
                #Pin names is the Output class attribute, use it to extract the value to write to memory pool
                val = getattr(self.local_output, pin_name, None)
                self.parent.memory_pool[mem_slot] = val

        #MOVE_TOKEN
        if isinstance(target_pin, str) and target_pin in self.output_exec_map:
            # Node chủ động yêu cầu rẽ nhánh (VD: return "out_case_0")
            target_nodes = self.output_exec_map[target_pin]
            if not target_nodes:
                 self.parent.delete_token(token_id) # Chân rẽ nhánh không cắm dây -> Hủy Token
            else:
                 # Đẩy Token sang node được cắm ở nhánh đó
                 self.parent.tokens_list[token_id] = {"status": TokenStatus.READY, "node_id": target_nodes[0]}
        else:
            # Các node tuyến tính bình thường (không return gì cả) -> chạy luồng cũ
            self._forward_token(token_id)


    def get_config_field_value(self, config_id: str, fallback_value: Any = None) -> Any:
        """
        Trích xuất giá trị cấu hình theo thứ tự ưu tiên:
        1. Lấy giá trị user đã đổi (nằm thẳng ở node_data)
        2. Lấy giá trị default từ mảng config_fields (nếu user chưa từng chạm vào FE)
        3. Lấy giá trị fallback_value truyền vào nếu hoàn toàn không tìm thấy.
        """
        # Ưu tiên 1: Lấy trực tiếp từ node_data (do người dùng đã đổi trên UI)
        if config_id in self.node_data:
            return self.node_data[config_id]
            
        # Ưu tiên 2: Móc vào mảng config_fields để tìm giá trị default
        config_fields = self.node_data.get("config_fields", [])
        for field in config_fields:
            if field.get("id") == config_id:
                return field.get("default", fallback_value)
                
        # Ưu tiên 3: Trả về fallback
        return fallback_value



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
    

class FlowNodeInput(BaseModel):
    execute_in: Any = Field(default="GO", title="execute", description=UIDataType.EXECUTE.value)

class FlowNodeOutput(BaseModel):
    execute_out: Any = Field(default="GO", title="execute", description=UIDataType.EXECUTE.value)

@registry_node
class JoinNode(BaseNode[FlowNodeInput, FlowNodeOutput]):
    """This node only forward the token when all of its previous nodes has reached it"""
    INPUT_SCHEMA = FlowNodeInput
    OUTPUT_SCHEMA = FlowNodeOutput
    UI_LABEL = "JOIN"
    UI_DESCRIPTION = "Join Previous Nodes"
    UI_COLOR = "#8b5cf6"
    NODE_TYPE = NodeType.JOIN

    async def execute(self):
        if self.token_count >= self.token_qty_required:
            if self.next_nodes:
                self.parent.spawn_token(self.next_nodes[0])
        

@registry_node
class SplitNode(BaseNode[FlowNodeInput, FlowNodeOutput]):
    """This node split into many tokens and do multiple things at once"""
    INPUT_SCHEMA = FlowNodeInput
    OUTPUT_SCHEMA = FlowNodeOutput
    UI_LABEL = "SPLIT"
    UI_DESCRIPTION = "SPLIT execution into several tokens"
    UI_COLOR = "#8b5cf6"
    NODE_TYPE = NodeType.SPLIT

    async def execute(self):
        return await super().execute()




class TerminalNodeDefaultPin(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    execute: Any = Field(default="GO", title="execute", description=UIDataType.EXECUTE.value)

        
@registry_node
class SendResponseNode(BaseNode[TerminalNodeDefaultPin, None]):
    """This Node act as the final node in the LogicHandling Graph, it is the user way to define what data they want to get back"""
    INPUT_SCHEMA = TerminalNodeDefaultPin
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
            data_type_str = pin.get("dataType")
            
            if data_type_str == UIDataType.EXECUTE.value:
                continue 
                
            py_type = map_fe_type_to_python(data_type_str)
            fields[pin_id] = (py_type, Field(default=None, title=pin.get("label", pin_id)))

        if fields:
            self.INPUT_SCHEMA = create_model(
                f'DynamicInput_{self.node_id}', 
                __config__=ConfigDict(arbitrary_types_allowed=True), 
                **fields
            )
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
class ReceivePayloadNode(BaseNode[None, TerminalNodeDefaultPin]):
    OUTPUT_SCHEMA = TerminalNodeDefaultPin
    NODE_TYPE = NodeType.PROGRAM
    UI_LABEL = "Data In"
    UI_DESCRIPTION = "Define what data need to receive from FE"
    UI_COLOR = "bg-purple-600"

    def __init__(self, node_id, parent, node_data = None):
        super().__init__(node_id, parent, node_data)

        self.has_executed = True

        dynamic_outputs = node_data.get("outputs", [])
        fields = {}

        for pin in dynamic_outputs:
            pin_id = pin["id"]
            data_type_str = pin.get("dataType")
            
            #Remove Execution Pin from the BE built Pydantic to avoid error
            if data_type_str == UIDataType.EXECUTE.value:
                continue 
                
            py_type = map_fe_type_to_python(data_type_str)
            fields[pin_id] = (py_type, Field(default=None, title=pin.get("label", pin_id)))

        if fields:
            self.OUTPUT_SCHEMA = create_model(
                f'DynamicOutput_{self.node_id}', 
                __config__=ConfigDict(arbitrary_types_allowed=True), 
                **fields
            )
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
        self.intialize_object()

    @abstractmethod
    def intialize_object(self):
        """This function run once when deploy the graph"""
        pass
    
    def reset_object_memory(self):
        """This clear up object internal memory"""
        self.internal_memory = None

