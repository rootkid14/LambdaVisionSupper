import asyncio
import time
from typing import Dict, Any
from app.services.LogicObjects import LogicObject
from pathlib import Path
import json
import uuid
import os
from app.services.utils.files_loader import load_ai_models, load_image
from fastapi import UploadFile
import shutil
from app.core.config import get_base_dir
import importlib.util
import sys
from app.services.LVSTypes import FileType

class LogicPoolManager:
    _instance = None
    
    # Format: { "logic_id": {"instance": LogicObject, "lock": asyncio.Lock(), "last_used": 1690000000.0, "graph_json_name" : graphjsonname} }
    _logic_pool: Dict[str, Dict[str, Any]] = {}
    
    #Format: {"filename": Loaded Instance}
    _storage_pool: Dict[str, Any] = {}

    #Tracking the modification time of pluggins file
    _plugin_mtimes = {}
    
    BASE_STORAGE_DIR = get_base_dir() / "storage"
    GRAPH_DIR = BASE_STORAGE_DIR / "graph_storage"
    FILE_DIR = BASE_STORAGE_DIR / "file_storage"
    PLUGIN_DIR = BASE_STORAGE_DIR / "pluggins"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogicPoolManager, cls).__new__(cls)
            cls._instance._init_storage()
        return cls._instance
            
    def _init_storage(self):
        """Initialize the storage for files and graphs"""
        self.GRAPH_DIR.mkdir(parents=True, exist_ok=True)
        self.FILE_DIR.mkdir(parents=True, exist_ok=True)
        self.PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        
    def deploy_graph_to_ram(self, graph_file_name : str) -> dict:
        """Load a logic object file (graph_json) in to ram and give it a unique ID in RAM"""
        try:
            file_path = self.GRAPH_DIR / f"{graph_file_name}.json"
            if not file_path.exists():
                raise FileNotFoundError(f"Graph '{graph_file_name}' không tồn tại trên disk, hãy upload file graph.json lên disk trước")
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_json = json.load(f)

            logic_obj = LogicObject(workflow_json, self)
            logic_id = f"{graph_file_name}{uuid.uuid4()}"
            self._logic_pool[logic_id] = {
                "instance": logic_obj,
                "lock": asyncio.Lock(),
                "last_used": time.time(),
                "graph_json_name" : graph_file_name
            }
            return {"success": True, "data": {'name': logic_id, 'graph_file': graph_file_name}}
        except Exception as e:
            return {"success": False, "error_message": f"Load LogicObject to Ram failed: {e}"}
        
    async def preflight_run(self, graph_json, input_payload) -> dict:
        """For API call: Use to try / test a new graph"""
        try:
            temp_logic_obj = LogicObject(graph_json, self)
            status = await temp_logic_obj._run_loop(input_payload)

            # 2. XỬ LÝ LỖI (Catch Lỗi)
            if not status["success"]:
                return {
                    "success": False,
                    "failed_node_id": status["failed_node_id"],
                    "error_message": status["error_message"],
                    "data": {}
                }

            # 3. TRẢ VỀ DỮ LIỆU HOÀN CHỈNH (Nếu thành công)
            final_data = temp_logic_obj.get_final_output()
            
            # Xử lý trường hợp Node cuối cùng không có data
            if "error" in final_data:
                return {
                    "success": False,
                    "failed_node_id": "api.send_response",
                    "error_message": final_data["error"],
                    "data": {}
                }

            return {
                "success": True,
                "failed_node_id": None,
                "error_message": None,
                "data": final_data
            }
        
        except Exception as e:
            return {
                "success": False,
                "failed_node_id": None,
                "error_message": str(e),
                "data": {}
            }
        
    def remove_graph_from_ram(self, logic_id: str):
        """API Function: Giải phóng RAM"""
        if logic_id in self._logic_pool:
            del self._logic_pool[logic_id]
            return {"success": True}
        return {"success": False, "error_message": "Không tìm thấy trên RAM"}

    async def execute_trigger(self, logic_id: str, payload: dict):
        """Trigger một LogicObject bất kỳ bằng ID"""
        logic_data = self._logic_pool.get(logic_id)
        if not logic_data:
            return {"success": False, "error_message": f"LogicObject {logic_id} không tồn tại hoặc đã bị xóa khỏi RAM."}

        # Cập nhật lại thời gian sử dụng để không bị dọn rác
        logic_data["last_used"] = time.time()
        
        logic_obj : LogicObject = logic_data["instance"]
        lock = logic_data["lock"]

        if lock.locked():
            return {
                "success": False, 
                "error_message": "Logic Object này đang bận xử lý một tiến trình khác. Vui lòng chờ hoặc gửi yêu cầu sau."
            }

        async with lock:
            # 1. Yêu cầu LogicObject chạy vòng lặp
            # Cấp PoolManager sẽ chỉ quản lý theo cơ chế concurrency. Sau này Dùng asyncio.to_thread ở cấp độ Nodes nếu cần thêm tài nguyên CPU để tính toán.
            status = await logic_obj._run_loop(payload)

            # 2. XỬ LÝ LỖI (Catch Lỗi)
            if not status["success"]:
                return {
                    "success": False,
                    "logic_object_id": logic_id,
                    "failed_node_id": status["failed_node_id"],
                    "error_message": status["error_message"],
                    "data": {}
                }

            # 3. TRẢ VỀ DỮ LIỆU HOÀN CHỈNH (Nếu thành công)
            final_data = logic_obj.get_final_output()
            
            # Xử lý trường hợp Node cuối cùng không có data
            if "error" in final_data:
                return {
                    "success": False,
                    "logic_object_id": logic_id,
                    "failed_node_id": "SendResponseNode",
                    "error_message": final_data["error"],
                    "data": {}
                }

            return {
                "success": True,
                "logic_object_id": logic_id,
                "failed_node_id": None,
                "error_message": None,
                "data": final_data
            }
        
    #DISK MANAGEMENT:
    def delete_file_from_disk(self, file_name: str, file_type: str = "file") -> dict:
        """DELETE A FILE FROM THE PERSISTEN STORAGE OF THIS SERVER
            filetype: "file", "graph", "plugins"
        """
        if file_type == "file":
            file_path = self.FILE_DIR / f"{file_name}"
        elif file_type == "graph":
            file_path = self.GRAPH_DIR / f"{file_name}"
        else:
            file_path = self.PLUGIN_DIR / f"{file_name}"

        if file_path.exists():
            file_path.unlink()
            return {"success": True}
        return {"success": False, "error_message": "File không tồn tại"}
    

    def get_resource_status(self) -> dict:
        """Hàm này gộp cả dữ liệu Disk và RAM trả về cho Tab Resource của FE"""
        # 1. Quét File Storage (Models, Configs)
        files_data : Dict[str, dict] = {} #{filename: {size: {}, inram: True}}
        inRam_files = list(self._storage_pool.keys())
        files_name_list = [f.name for f in self.FILE_DIR.iterdir() if f.is_file()]

        # TẠO DANH SÁCH CÁC FILES LƯU TRỮ VÀ TÌNH TRẠNG IN RAM
        for file_name in files_name_list:
            size = os.path.getsize(f"{self.FILE_DIR}/{file_name}")
            inRam = False
            if(file_name in inRam_files):
                inRam = True
            files_data[file_name] = {"size": size, "inram": inRam}
               

        # 2. Quét Graph Storage & Đối chiếu với RAM
        graphs_data = [{"name" : f.name, "size": f.stat().st_size}
                       for f in self.GRAPH_DIR.iterdir() if f.is_file() and f.suffix == ".json"]

        #3. Quét danh sách Plugins Storage
        plugins_data = [{"name": f.name, "size": f.stat().st_size} 
                   for f in self.PLUGIN_DIR.iterdir() if f.is_file() and f.suffix == ".py"]
        
        #4. Quét danh sách active Logic Objects:
        active_logics_data = [{"name": logic_id, "graph_file": value.get("graph_json_name")} for logic_id, value in self._logic_pool.items()]

        return {
            "files": files_data,
            "graphs": graphs_data,
            "plugins": plugins_data,
            "active_logics": active_logics_data
        }
    
    #Handle loading a file onto RAM:
    async def load_file_to_ram(self, filename: str) -> dict:
        """Load Disk files to Ram so that Logic Objects can access and use as resource"""
        if filename in self._storage_pool:
            return {"success" : True, "message" : "File is already loaded to ram"}
        
        file_path = self.FILE_DIR / filename
        if not file_path.exists():
            return {"success" : False, "message" : "File does not exist on disk"}
        
        try:
            ext = file_path.suffix.lower()
            if ext in ['.pt', '.onnx']:
                #Use await with thread to avoid blocking when loading a very heavy files
                await asyncio.to_thread(load_ai_models, self._storage_pool, filename)
            elif ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._storage_pool[filename] = json.load(f)
            elif ext in ['.png', '.jpeg', '.jpg']:
                #Use await with thread to avoid blocking when loading a very heavy files
                await asyncio.to_thread(load_image, self._storage_pool, filename)
            else:
                return {"success": False, "error_message": f"Un-Supported file type"}

            return {"success": True, "message": f"Đã nạp {filename} vào RAM"}
        except Exception as e:
            return {"success": False, "error_message": f"Lỗi khi load file: {e}"}
        
    def unload_file_from_ram(self, filename: str) -> dict:
        if filename in self._storage_pool:
            del self._storage_pool[filename]
            return {"success": True, "message": f"Đã giải phóng {filename} khỏi RAM"}
        return {"success": False, "error_message": "File không nằm trong RAM"}
    
    async def save_heavy_file(self, file: UploadFile, filename: str, filetype: str = FileType.FILE.value) -> dict:
        """Save heavy files safely by taking small chunks from httpx stream than save chunks by chunks to disk
            using thread so that the system is not blocked
        """
        if filetype == FileType.FILE.value:
            file_path = self.FILE_DIR/ filename
        elif filetype == FileType.GRAPH.value:
            file_path = self.GRAPH_DIR / filename
        elif filetype == FileType.PLUGIN.value:
            file_path = self.PLUGIN_DIR / filename
        else:
            return {"success": False, "message": f"UKNOWN FILE TYPE {filetype}"}
        try:
            def _write_disk():
                #w: open, if not exist -> create new, then write (+) as binary file
                with open(file_path, "wb+") as file_object:
                    #shutil copyfileobj seperate files into chunk and then append in small chunks until finish
                    shutil.copyfileobj(file.file, file_object)
            
            await asyncio.to_thread(_write_disk)
            return {"success": True, "message": f"Đã lưu {filename} thành công ({file_path.stat().st_size / 1024 / 1024:.2f} MB)"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi ghi đĩa: {e}"}
        
  
        
    def get_file_path(self, filename: str, filetype: str) -> Path:
        """Trả về đường dẫn vật lý để API tự xử lý Streaming Download"""
        if filetype == FileType.FILE.value:
            file_path = self.FILE_DIR / filename
        elif filetype == FileType.GRAPH.value:
            file_path = self.GRAPH_DIR / filename
        elif filetype == FileType.PLUGIN.value:
            file_path = self.PLUGIN_DIR / filename
        else:
            raise TypeError(f"UNKOWN FILE TYPE: {filetype}")
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} không tồn tại trên hệ thống")
        return file_path

        
    
    async def _plugins_heartbeat_monitor(self, interval: float = 5.0):
        """A watch dog loop that scan and reload the pluggins dirrectory every 5 secconds"""
        # Import NODE_REGISTRY và unregister_node ở đây để tránh circular import
        from app.services.node_registry import NODE_REGISTRY, unregister_node

        while True:
            try:
                if self.PLUGIN_DIR.exists():
                    current_files = set()

                    # 1. QUÉT FILE MỚI & FILE BỊ SỬA (Hot-Reload)
                    for file_path in self.PLUGIN_DIR.rglob("*.py"):
                        if file_path.name == "__init__.py":
                            continue
                        
                        file_path_str = str(file_path)
                        current_files.add(file_path_str)

                        current_mtime = file_path.stat().st_mtime
                        last_mtime = self._plugin_mtimes.get(file_path_str)

                        if last_mtime is None or current_mtime > last_mtime:
                            module_name = f"external_plugins.{file_path.stem}"
                            try:
                                spec = importlib.util.spec_from_file_location(module_name, file_path_str)
                                if spec and spec.loader:
                                    module = importlib.util.module_from_spec(spec)
                                    sys.modules[module_name] = module
                                    spec.loader.exec_module(module) # Khởi chạy module (kích hoạt @registry_node)
                                    self._plugin_mtimes[file_path_str] = current_mtime
                                    print(f"Đã nạp/cập nhật Plugin: {file_path.name}")
                            except Exception as e:
                                print(f"Lỗi khi nạp Plugin {file_path.name}: {e}")
                                self._plugin_mtimes[file_path_str] = current_mtime # Vẫn cập nhật mtime để không thử lại liên tục nếu lỗi cú pháp

                    # 2. PHÁT HIỆN FILE BỊ XÓA (Hot-Unload)
                    tracked_files = list(self._plugin_mtimes.keys())
                    for tracked_file in tracked_files:
                        if tracked_file not in current_files:
                            # File đã bị xóa khỏi đĩa!
                            deleted_path = Path(tracked_file)
                            module_name = f"external_plugins.{deleted_path.stem}"
                            
                            print(f"Phát hiện Plugin bị xóa: {deleted_path.name}. Đang tiến hành dọn dẹp...")

                            # Lấy module ra từ sys.modules (nếu còn)
                            if module_name in sys.modules:
                                deleted_module = sys.modules[module_name]
                                
                                # Tìm tất cả các class trong module này mà đang có mặt trong NODE_REGISTRY
                                classes_to_remove = []
                                for name, obj in vars(deleted_module).items():
                                    # Kiểm tra xem nó có phải là class và class đó có nằm trong Registry không
                                    if isinstance(obj, type) and name in NODE_REGISTRY and NODE_REGISTRY[name] == obj:
                                        classes_to_remove.append(name)
                                
                                # Gỡ từng class khỏi Registry
                                for cls_name in classes_to_remove:
                                    unregister_node(cls_name)

                                # Xóa module khỏi bộ nhớ hệ thống
                                del sys.modules[module_name]
                            
                            # Ngừng theo dõi file này
                            del self._plugin_mtimes[tracked_file]

            except Exception as e:
                print(f"Lỗi vòng lặp Plugin Watchdog: {e}")

            await asyncio.sleep(interval)

    def get_list_of_logic_objects(self) -> list:
        """API function : Return a list of logic objects ids in system"""
        response = list(self._logic_pool.keys())
        return response
    
    def get_logic_dependencies(self) -> dict:
        """API function: Trả về mapping { logic_object_id : graph_file_name }"""
        dependencies = {}
        for logic_id, data in self._logic_pool.items():
            # Trích xuất tên file graph tương ứng với logic_id đang chạy
            graph_name = data.get("graph_json_name")
            if graph_name:
                dependencies[logic_id] = graph_name
        return dependencies
    
    def deploy_exact_graph_to_ram(self, graph_file_name: str, exact_logic_id: str) -> dict:
        """Nạp Graph vào RAM nhưng gán cứng một ID do Frontend chỉ định"""
        # Nếu đã tồn tại trên RAM rồi thì thôi, báo thành công luôn
        if exact_logic_id in self._logic_pool:
            return {"success": True, "message": f"Logic Object {exact_logic_id} đã sẵn sàng trên RAM.", "status": "exist"}

        try:
            file_path = self.GRAPH_DIR / f"{graph_file_name}.json"
            if not file_path.exists():
                return {"success": False, "error_message": f"Không tìm thấy file thiết kế '{graph_file_name}.json' trên hệ thống của Worker này."}

            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_json = json.load(f)

            logic_obj = LogicObject(workflow_json, self)
            
            # Gán cứng ID mà Frontend yêu cầu
            self._logic_pool[exact_logic_id] = {
                "instance": logic_obj,
                "lock": asyncio.Lock(),
                "last_used": time.time(),
                "graph_json_name": graph_file_name
            }
            return {"success": True, "message": f"Đã nạp thành công {graph_file_name} vào RAM.", "status": "loaded"}
        except Exception as e:
            return {"success": False, "error_message": f"Lỗi nạp Graph {graph_file_name}: {e}"}