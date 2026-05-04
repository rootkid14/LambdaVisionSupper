from fastapi import APIRouter, HTTPException, Request
from app.schemas.graph import DeployRequest, ExecuteRequest, DebugRunRequest
import uuid
import json
from app.services.utils.image_utils import bytes_to_cv2, cv2_to_base64
import numpy as np
# Import hệ thống Lõi của bạn
from app.services.node_registry import NODE_REGISTRY
from app.services.LogicPoolManager import LogicPoolManager
from pydantic import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.LogicObjects import LogicObject

router = APIRouter()

# Lấy instance duy nhất của SessionManager (Singleton)
logicpoolManager = LogicPoolManager()



@router.get("/catalog", summary="Lấy danh sách các Node cho Frontend")
def get_node_catalog():
    """
    Quét qua Sổ đăng ký (NODE_REGISTRY) và trả về mảng JSON chứa mô tả của tất cả các Node.
    Frontend sẽ gọi API này 1 lần duy nhất lúc bật phần mềm để vẽ Menu.
    """
    try:
        catalog = []
        for node_name, node_class in NODE_REGISTRY.items():
            # Gọi hàm sinh manifest mà bạn đã viết trong BaseNode
            node_manifest = node_class.formulate_frontend_description()
            catalog.append(node_manifest)
            
        return catalog
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc Catalog: {str(e)}")

class Preflight(BaseModel):
    graph: dict
    preflight_payload: dict

@router.post("/preflight", summary="Create a temporary object base on the DebugPackage sent from FE, try run it once, return data and clear")
async def preflight_run(preflight_data: Preflight):
    """
        Use the attached Graph to try to create temporary object in the LogicPoolManager,
        Then use the attached input payload to try running the tempory object, then return the output data.
    """
    try:
        resp = await logicpoolManager.preflight_run(preflight_data.graph, preflight_data.preflight_payload)
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    
@router.post("/deploygraph/{graph_file_name}", summary="deploy a loaded graph to system Ram")
def deploy_graph_to_ram(graph_file_name: str):
    """Used to load a graph from disk to ram to create a Logic Object in memory"""
    try:
        resp = logicpoolManager.deploy_graph_to_ram(graph_file_name)
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    
@router.delete("/undeploygraph/{logic_object_id}", summary="remove a loaded graph from system Ram")
def undeploy_graph_from_ram(logic_object_id: str):
    """Use to remove a logic object from ram"""
    try:
        resp = logicpoolManager.remove_graph_from_ram(logic_object_id)
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    
@router.post("/executelogic/{logic_object_id}", summary="Execute an in-ram logic object")
async def execute_logic(logic_object_id: str, payload: dict):
    """Use to execute the logic object"""
    try:
        resp = await logicpoolManager.execute_trigger(logic_object_id, payload)
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@router.get("/getinoutschema/{logic_object_id}", summary="Get the in/out schema of a logic objects")
def get_in_out_schema(logic_object_id: str):
    try:
        logic_object_instance : "LogicObject" = logicpoolManager._logic_pool[logic_object_id]["instance"]
        resp = logic_object_instance.get_in_out_schemas()
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    
@router.get("/getLogicIDs", summary="Get the list of logic ids activated in the system")
def get_logic_id_list():
    try:
        resp = logicpoolManager.get_list_of_logic_objects()
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    
@router.get("/dependencies", summary="Lấy danh sách mapping Graph dependencies của các Logic Objects")
def get_logic_dependencies():
    """
    Trả về Dictionary mapping giữa Logic ID và tên file Graph JSON vật lý.
    Frontend gọi API này lúc Export Project để ghi vào file JSON tổng.
    """
    try:
        resp = logicpoolManager.get_logic_dependencies()
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    

class SyncDependenciesRequest(BaseModel):
    logic_objects: dict

@router.post("/sync-dependencies", summary="Đánh thức/Nạp lại các Logic Object theo yêu cầu của FE")
def sync_logic_dependencies(payload: SyncDependenciesRequest):
    """
    Nhận một danh sách các Logic Object ID và Graph Name. 
    Tiến hành nạp vào RAM. Trả về báo cáo chi tiết cho từng Object.
    """
    results = {}
    has_error = False
    
    for logic_id, graph_name in payload.logic_objects.items():
        res = logicpoolManager.deploy_exact_graph_to_ram(graph_name, logic_id)
        results[logic_id] = res
        if not res["success"]:
            has_error = True

    return {
        "success": not has_error,
        "details": results
    }