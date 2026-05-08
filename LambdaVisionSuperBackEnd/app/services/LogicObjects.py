from typing import Dict, Any, TYPE_CHECKING
from app.services.LVSTypes import NodeType, GraphNodeType, TokenStatus
from app.services.node_registry import BaseNode, NODE_REGISTRY
from collections import deque
from enum import Enum
import uuid
import base64
import asyncio

if TYPE_CHECKING:
    from app.services.LogicPoolManager import LogicPoolManager


class LogicObject():
    def __init__(self, workflow_json: Dict[str, Any], logicPoolManagerInst: "LogicPoolManager"):
        # Format: {token_id: {status: ..., node_id: ....}} --> the Logic Object will loop through this.
        self.tokens_list : Dict[str, Dict[str, Any]] = {}
        
        # Chứa dánh sách các node được tạo {node_id : instance}
        self.nodes_list: Dict[str, "BaseNode"] = {}

        #Format: {node_id : {"type" : GraphNodeType, "next_node": string}}
        self.nodes_mapping : Dict[str, Dict[str, Any]] = {}
    
        # Format: {"memory slot": "value"} --> 2 pins can share a common key, The system based on the edges scheme to construct the memory pools and assign it to each node.
        self.memory_pool: Dict[str, Any] = {}

        self.extra_memory: Dict[str, Any] = {} #--> Isolated memory location used for caching (the Read/ Write Internal Memory nodes)

        #Format : {"filename" :  Loaded Instance}
        self.logicPoolManagerInst = logicPoolManagerInst
        
        self.logic_timeout = 5.0 #default 5.0 seccond maximum allowed for each logic object
        
        # Chạy ngay khi khởi tạo
        self._compile_graph(workflow_json)

    def reset_state(self):
        """Dọn dẹp sạch sẽ toàn bộ rác bộ nhớ từ các lần chạy (Run) trước đó"""
        # 1. Xóa hàng đợi token và bộ nhớ dùng chung
        self.tokens_list.clear()
        self.memory_pool.clear()
        
        # 2. Rửa sạch Extra Memory (Cực kỳ quan trọng để fix lỗi bóng ma Memory Read/Write)
        self.extra_memory.clear()
        
        # 3. Quét qua toàn bộ các Node và reset Input/Output ảo của chúng
        for node in self.nodes_list.values():
            node.local_input = None
            node.local_output = None
            node.output_exec_map.clear()
            
            # Nếu là ObjectNode (có bộ nhớ riêng), cũng dọn dẹp luôn
            if hasattr(node, 'internal_memory'):
                node.internal_memory.clear()

    def _compile_graph(self, workflow_json: Dict[str, Any]):
        self.logic_timeout = float(workflow_json.get("timeout", 5.0))
        nodes_data = workflow_json.get("nodes", [])
        edges_data = workflow_json.get("edges", [])


        #STEP 1: SPAWN THE NODES BASED ON JSON SCHEME
        for nd in nodes_data:
            node_id = nd["id"]
            node_class_name = nd.get("data", {}).get("class")

            NodeClass = NODE_REGISTRY.get(node_class_name)
            if not NodeClass:
                raise Exception(f"Error: Cannot find class: {node_class_name}")

            node_instance = NodeClass(node_id, self, nd.get("data", {}))

            node_instance.input_memory_map = {} #Format {name_of_input_pin: Memory_slot}  --> For memory pools mapping
            node_instance.output_memory_map = {} #Format {name_of_output_pin: Memory_slot} --> For memory pools mapping
            node_instance.next_nodes = []
            node_instance.prev_nodes = []
            self.memory_generators = {} #format ("memory slot id" : "node_id who can generate it")
 
            self.nodes_list[node_id] = node_instance
        

        #STEP 2: CHECK EDGES SCHEME TO BUILD THE MEMORY POOL (ALOCATE MEMORY SLOT THEN LINK THE PINS OF NODE WITH SLOTS)
        EXEC_KEYWORDS  = ['execute', 'out_true', 'out_false', 'out_case', 'out_default'] # NO NEED TO ALLOCATE MEMORY FOR TRIGGER PINS
        
        for edge in edges_data:
            src_id = edge.get("source")
            src_pin = edge.get("sourceHandle")
            tgt_id = edge.get("target")
            tgt_pin = edge.get("targetHandle")

            if not src_id or not tgt_id or src_id not in self.nodes_list or tgt_id not in self.nodes_list:
                raise Exception(f"there is no src_id {src_id} or tgt_id {tgt_id} or they are not in nodes list")
        
            src_node = self.nodes_list[src_id]
            tgt_node = self.nodes_list[tgt_id]

            #CASE 1 : IS EXECUTION WIRE
            is_exec_wire = any(keyword in src_pin.lower() for keyword in EXEC_KEYWORDS)
            is_receiving_exec_wire = any(keyword in tgt_pin.lower() for keyword in EXEC_KEYWORDS)
            is_execution_valid = (is_exec_wire and is_receiving_exec_wire)
            is_execution_invalid = (is_exec_wire and not is_receiving_exec_wire) or (not is_exec_wire and is_receiving_exec_wire)
            if is_execution_valid:
                src_node.next_nodes.append(tgt_id)
                
                # OUTPUT EXEC MAPPINGS FOR SWITCH NODE
                if src_pin not in src_node.output_exec_map:
                    src_node.output_exec_map[src_pin] = []
                src_node.output_exec_map[src_pin].append(tgt_id)

                if src_id not in tgt_node.prev_nodes:
                    tgt_node.prev_nodes.append(src_id)

            elif is_execution_invalid:
                raise Exception(f"Trying to make a connection between execution and data pins of node {src_id} and {tgt_id}")
            
            else:
            #CASE 2 : IS DATA WIRE
                #NOTE: It might not look important, but do not delete it!!!
                # IF already exist -> Get from the output memory map of this node (this is to avoid 2 uuid was generate on 2 loops in scheme where this node are output to more than one nodes)
                if src_pin in src_node.output_memory_map:
                    memory_slot_key = src_node.output_memory_map[src_pin]
                else:
                    u = uuid.uuid4()
                    short_id = base64.urlsafe_b64encode(u.bytes).rstrip(b'=').decode()
                    memory_slot_key = f"mem_{short_id}"

                    # Inject mapping into the node.
                    src_node.output_memory_map[src_pin] = memory_slot_key

                    self.memory_generators[memory_slot_key] = src_id
                
                # The target node will share the same memory slot id:
                tgt_node.input_memory_map[tgt_pin] = memory_slot_key

                # Allocate an empty memory slot
                self.memory_pool[memory_slot_key] = None
        

        # STEP 3 : COMPLETING NODES MAPPING FOR LOGIC OBJECTS
        for node_id, node in self.nodes_list.items():

            targets = node.next_nodes
            sources = node.prev_nodes # Lấy danh sách các node đang đổ về
            in_degree = len(sources)

            if node.NODE_TYPE == NodeType.JOIN:
                node.token_qty_required = in_degree

            self.nodes_mapping[node_id] = {"type": node.NODE_TYPE, "next_nodes": targets,"prev_nodes": sources, "in_degree": len(sources)}

    def spawn_token(self, node_id):
        token_id = uuid.uuid4()
        self.tokens_list[token_id] = {"status" : TokenStatus.READY, "node_id": node_id}

    def delete_token(self, token_id):
        del self.tokens_list[token_id]        
            
    def assign_token_to(self, token_id, node_id):
        self.tokens_list[token_id] = {"status": TokenStatus.READY, "node_id": node_id}

    async def _run_loop(self, payload: dict = None):
        """MAIN RUNNING LOOP OF THE LOGICOBJECT"""

        for node_id, node_instance in self.nodes_list.items():
            node_instance._reset_cache()
        self.reset_state()

        print(self.extra_memory)

        try:
            self.inject_payload_and_assign_start_token(payload)
        except Exception as e:
            recipient_node = next((n for n in self.nodes_list.values() if n.__class__.__name__ == "ReceivePayloadNode"), None)
            fail_id = recipient_node.node_id if recipient_node else "System_Entry"
            return {
                "success" : False,
                "failed_node_id": fail_id,
                "error_message" : f"Dữ liệu Payload không hợp lệ: {e}"
            }
        
        async def __inner_execution_process():
            while True:
                try:
                    ready_tokens = [t_id for t_id, t_info in self.tokens_list.items() if t_info["status"] == TokenStatus.READY]


                    if not ready_tokens:
                        # Nếu có Token đang PROCESSING (ví dụ chờ API/Tải file), ta tạm nghỉ để nhường CPU
                        if any(t["status"] == TokenStatus.PROCESSING for t in self.tokens_list.values()):
                            await asyncio.sleep(0.01)
                            continue
                        else:
                            break
                    
                    tasks = []

                    for t_id in ready_tokens:
                        node_id = self.tokens_list[t_id]["node_id"]
                        # print(f"active Node {node_id}")
                        node_instance = self.nodes_list[node_id]
                        tasks.append(node_instance._execution_logic(t_id))
                    await asyncio.gather(*tasks)
                except Exception as e:
                    raise Exception(f"Lỗi thực thi vòng lặp Logic Object tại một trong các token: {self.tokens_list}, chi tiết: {e}")

        try:
            if self.logic_timeout > 0:
                await asyncio.wait_for(__inner_execution_process(), timeout=self.logic_timeout)
            else:
                await __inner_execution_process()
        except asyncio.TimeoutError:
            return {
                "success": False,
                "failed_node_id": "System_Graph",
                "error_message": f"GLOBAL TIMEOUT: Đồ thị đã chạy vượt quá giới hạn {self.logic_timeout} giây. Phát hiện vòng lặp vô tận (Infinite Loop) của các khối nối dây!"
            }
        
        except Exception as e:

            return {
                "success" : False,
                "failed_node_id": "node_id",
                "error_message" : f"Lỗi Runtime: {e}"
            }

        return {"success": True}
                

    def inject_payload_and_assign_start_token(self, payload: dict):
        """Inject the AXIOS payload in to the ReceipientNode"""
        for node in self.nodes_list.values():
            if node.__class__.__name__ == "ReceivePayloadNode":
                self.spawn_token(node.node_id)
                if not node.OUTPUT_SCHEMA:
                    return
                payload = payload or {}
                try:
                    node.local_output = node.OUTPUT_SCHEMA(**payload)
                except Exception as e:
                    raise ValueError(f"Dữ liệu API Axios không khớp với thiết kế của ReceivePayloadNode: {e}")
                return
        

    def get_final_output(self):
        """Take Out Final Data from SendResponseNode"""
        for node in self.nodes_list.values():
            if node.__class__.__name__ == "SendResponseNode":
                # Trả về cục Dictionary đã được Node tổng hợp sẵn
                return node.local_output
                
        return {"error": "Không tìm thấy SendResponseNode trong Graph"}


    def reset_graph_state(self):
        """Reset All Nodes memory"""
        for node in self.nodes_list.values():
            node.reset()
    
    async def _safe_load_file(self, file_name : str) -> Any:
        """This function will be used by node so that it safely loads a resource,
            if the required resource is not in ram, then the LogicPoolManager will safely loadit to ram first then give it to
            the node
        """
        if file_name not in self.logicPoolManagerInst._storage_pool:
            await self.logicPoolManagerInst.load_file_to_ram(file_name)
        try:
            loaded_object = self.logicPoolManagerInst._storage_pool[file_name]
            return loaded_object
        except Exception as e:
            raise MemoryError(f"Something Failed when trying to load the resource : {e}")
        
    def _safe_load_LogicObject(self, graph_file_name : str) -> "LogicObject":
        """This function will be Used by nodes so that it safely loads another object in case needed (nested functions concept),
            if the required resource is not in ram, then the LogicPoolManager will safely loadit to ram first then give it to
            the node
        """
        for logic_id, value in self.logicPoolManagerInst._logic_pool.items(): # Thêm .items()
            if graph_file_name == value.get("graph_json_name"): # Phải là câu lệnh if
                return value["instance"]

        #if cannot find -> deploy
        result = self.logicPoolManagerInst.deploy_graph_to_ram(graph_file_name)
        if result["success"] == True:
            logic_id = result["message"]
            return self.logicPoolManagerInst._logic_pool[logic_id]["instance"]
        else:
            raise MemoryError(f"Something fail when trying to load the logic object id from _logic_pool")
        
    def get_in_out_schemas(self) -> dict:
        """API function returning the in/out schema as a flat list so that FE Sequencer can know how do deal with"""
        schemas = {}
        for node in self.nodes_list.values():
            if node.__class__.__name__ == "ReceivePayloadNode":
                schemas["input_schema"] = node.get_schema()
            elif node.__class__.__name__ == "SendResponseNode":
                schemas["output_schema"] = node.get_schema()
        return schemas
