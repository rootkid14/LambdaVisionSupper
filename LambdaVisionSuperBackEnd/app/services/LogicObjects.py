from typing import Dict, Any, TYPE_CHECKING
from app.services.LVSTypes import NodeType
from app.services.node_registry import BaseNode, NODE_REGISTRY
from collections import deque

if TYPE_CHECKING:
    from app.services.LogicPoolManager import LogicPoolManager

class LogicObject():
    def __init__(self, workflow_json: Dict[str, Any], logicPoolManagerInst: "LogicPoolManager"):
        # Chứa dánh sách các node đã được tạo
        self.nodes_list: Dict[str, "BaseNode"] = {}
        
        # Format: {node_id: {input_pin: {"source_node": "...", "source_pin": "..."}}}
        self.nodes_mapping: Dict[str, Dict[str, Dict[str, str]]] = {} 

        #Format : {"filename" :  Loaded Instance}
        self.logicPoolManagerInst = logicPoolManagerInst
        
        self.sequence: list = []
        
        # Chạy ngay khi khởi tạo
        self.initialize_logic_object(workflow_json)

    def build_execution_sequence(self, workflow_json: Dict[str, Any]):
        """Kahn's Topological Sort Algorithm for translating the graph to a linear list"""
        nodes = workflow_json.get("nodes", [])
        for node in nodes:
            node_id = node.get("id")
            node_data = node.get("data", {})
            node_class_name = node_data.get("class")

            #Get the class from the REGISTRY
            node_class = NODE_REGISTRY.get(node_class_name)

            #Create a new node instance
            if not node_class:
                raise ValueError(f"Không tìm thấy node class {node_class_name} trong registry")

            new_node = node_class(node_id, self, node_data)
            self.nodes_list[node_id] = new_node
                

        in_degree = {node_id : 0 for node_id in self.nodes_list}
        graph = {node_id : [] for node_id in self.nodes_list}

        unique_dependencies = set()
        for target_node_id, pins in self.nodes_mapping.items():
            for target_pin, source_info in pins.items():
                source_node_id = source_info["source_node"]
                unique_dependencies.add((source_node_id, target_node_id))
        for source_id, target_id in unique_dependencies:
            if source_id in self.nodes_list and target_id in self.nodes_list:
                graph[source_id].append(target_id)
                in_degree[target_id] += 1

        queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])

        sorted_node_ids = []

        while (queue):
            current_id = queue.popleft()
            sorted_node_ids.append(current_id)

            for neighbor_id in graph[current_id]:
                in_degree[neighbor_id] -= 1

                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
        
        self.sequence = sorted_node_ids


    def initialize_logic_object(self, workflow_json: Dict[str, Any]):
        """Quét JSON để tạo danh sách node và nối dây (nodes_mapping)"""
        # ==========================================
        # BƯỚC 1: (Xây dựng bản đồ kết nối)
        # ==========================================
        edges = workflow_json.get("edges", [])
        for edge in edges:
            source_node = edge.get("source")
            source_pin = edge.get("sourceHandle")
            
            receive_node = edge.get("target")
            input_pin = edge.get("targetHandle")

            if receive_node not in self.nodes_mapping:
                self.nodes_mapping[receive_node] = {}
        
            # Ghi chép lại: "Tham số [input_pin] của tao node này lấy từ [source_node][source_pin]"
            self.nodes_mapping[receive_node][input_pin] = {
                "source_node": source_node,
                "source_pin": source_pin
            }

        # Tạo node và tái tạo lại sequence chạy chuẩn
        self.build_execution_sequence(workflow_json)

    def inject_payload(self, payload: dict):
        """Inject the AXIOS payload in to the ReceipientNode"""
        for node in self.nodes_list.values():
            if node.__class__.__name__ == "ReceivePayloadNode":
                if not node.OUTPUT_SCHEMA:
                    return
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


    async def run_nodes_loop(self, payload:dict = None):
        if payload is None: 
            payload = {}
            
        self.reset_graph_state()
        try:
            self.inject_payload(payload)
        except Exception as e:
            recipient_node = next((n for n in self.nodes_list.values() if n.__class__.__name__ == "ReceivePayloadNode"), None)
            fail_id = recipient_node.node_id if recipient_node else "System_Entry"
            return {
                "success" : False,
                "failed_node_id": fail_id,
                "error_message" : f"Dữ liệu Payload không hợp lệ: {e}"
            }
        
        for node_id in self.sequence:
            try:
                node = self.nodes_list[node_id]
                await node.resolve_and_execute()
            except Exception as e:
                return {
                    "success" : False,
                    "failed_node_id": node_id,
                    "error_message" : str(e)
                }
        return {"success": True}
    
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
