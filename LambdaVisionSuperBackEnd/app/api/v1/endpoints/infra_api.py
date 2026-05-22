from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Any
from fastapi.responses import FileResponse, JSONResponse
from app.services.ConnectionBus import APIManualRoutingBus
from app.services.LogicPoolManager import LogicPoolManager
from app.services.DevicePoolManager import HTTPDevicePoolManager
from pydantic import BaseModel
from app.services.LVSTypes import FileType
import json

VALID_FOLDERS = {"graphs", "models", "plugins", "projects"}

router = APIRouter()
server_bus = APIManualRoutingBus()
logic_pool = LogicPoolManager()
device_bus = HTTPDevicePoolManager()

@router.get("/servers/{server_id}", summary="Look up for host of a server (for workers server)")
def get_server_info(server_id: str):
    context = server_bus.get_server_context(server_id)
    if not context:
        raise HTTPException(status_code=404, detail="Server does not exist in Master Server memory")
    
    return{
        "server_id" : server_id,
        "host" : context["host"]
    }

#================================================================================================================
#======================             RESOURCES MANAGEMENT API GROUP                                 ==============
#================================================================================================================

@router.post("/resources/files/{filetype}/upload", summary="Upload Model/File nặng lên Disk")
async def upload_file(filetype : str ,file: UploadFile = File(...)):
    # ĐÃ SỬA: Bypass cho 'projects'
    try:
        if filetype != "projects":
            FileType(filetype)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"File Type {filetype} is not valid")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có tên file")
        
    res = await logic_pool.save_heavy_file(file, file.filename, filetype)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res["error_message"])
        
    return res


@router.get("/resources/files/{filetype}/{filename}/download", summary="Download File từ Disk")
async def download_file(filetype:str, filename: str):
    # ĐÃ SỬA: Bypass cho 'projects'
    try:
        if filetype != "projects":
            FileType(filetype)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"File Type {filetype} is not valid")

    try:
        file_path = logic_pool.get_file_path(filename, filetype)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
            content_disposition_type="attachment"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {e}")
    

    

@router.get("/resources/status", summary="Get all files and graphs status on the local storage of this server")
def get_resource_status():
    try:
        res = logic_pool.get_resource_status()
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Something failed during fetching of resource status {e}")
    

@router.delete("/resources/delete/{file_type}/{file_name}", summary="Delete a file")
def delete_file( file_type: str, file_name : str):
    try:
        if file_type == "file":
            resp = logic_pool.delete_file_from_disk(file_name, file_type="file")
        elif file_type == "graph":
            resp = logic_pool.delete_file_from_disk(file_name, file_type="graph")
        elif file_type == "plugin":
            resp = logic_pool.delete_file_from_disk(file_name, file_type="plugins")
        elif file_type == "projects":
            resp = logic_pool.delete_file_from_disk(file_name, file_type="projects")
        else:
            raise HTTPException(status_code=400, detail=f"UNKNOWN FILE TYPE {e}")    
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Something failed during deletion of file {e}")
    

#================================================================================================================
#======================             SERVER BUS MANAGEMENT API GROUP                                ==============
#================================================================================================================

@router.get("/servers", summary="Fetch the list of connected servers in the Bus")
def get_all_local_servers():
    active_servers = server_bus.get_all_active_server()
    result = []
    for sev_id, sev_info in active_servers.items():
        result.append({
            "id" : sev_id,
            "host" : sev_info["host"],
            "status" : "online" if not sev_info["session"].closed else "offline",
            "ping" : sev_info["ping"]
        })
    return result


class ServerInfo(BaseModel):
    server_id : str
    host : str

@router.post("/servers/add", summary="Add a server in to Bus Cache")
async def add_local_server(info : ServerInfo):
    res = await server_bus.add_new_server({"server_id" : info.server_id, "host" : info.host})
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.delete("/servers/delete/{server_id}", summary="Remove a server from the Bus")
async def remove_local_server(server_id : str):
    try:
        res = await server_bus.remove_server(server_id)
        return res
    except KeyError:
        raise HTTPException(status_code=404, detail="Server không tồn tại trong Cache")
    
#================================================================================================================
#======================             DEVICE BUS MANAGEMENT API GROUP                                ==============
#================================================================================================================


@router.get("/devices", summary="Fetch the list of connected IOT devices in the device bus")
async def get_all_local_devices():
    active_devices = device_bus.get_all_active_device()
    result = []
    for dev_id, dev_info in active_devices.items():
        result.append({
            "id" : dev_id,
            "host" : dev_info["host"],
            "status" : "online" if not dev_info["session"].closed else "offline",
            "ping" : dev_info["ping"]
        })
    return result


class DeviceInfo(BaseModel):
    device_id : str
    host : str


@router.post("/devices/add", summary="Add a device in to Bus Cache")
async def add_local_device(info : DeviceInfo):
    res = await device_bus.add_new_device({"device_id" : info.device_id, "host" : info.host})
    print(res)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.delete("/devices/delete/{device_id}", summary="Remove a device from the Bus")
async def remove_local_device(device_id : str):
    try:
        res = await device_bus.remove_device(device_id)
        return res
    except KeyError:
        raise HTTPException(status_code=404, detail="Server không tồn tại trong Cache")
    

#================================================================================================================
#======================                   OTHER SETTINGS                                           ==============
#================================================================================================================
@router.post("/servers/heartbeat/{new_interval}", summary="Changing the frequency in which server bus heartbeat is monitored")
def change_server_bus_heartbeat(new_interal : float):
    try:
        server_bus._change_heartbeat_interval(new_interal)
        return({"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    

@router.post("/devices/heartbeat/{new_interval}", summary="Changing the frequency in which device bus heartbeat is monitored")
def change_server_bus_heartbeat(new_interal : float):
    try:
        device_bus._change_heartbeat_interval(new_interal)
        return({"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    
@router.post("/resources/files/load-to-ram/{filename}", summary="Load a heavy file from Disk to RAM")
async def load_file_to_memory(filename: str):
    """
    API dùng để nạp một file từ Ổ cứng (Disk) lên Bộ nhớ (RAM)
    thông qua LogicPoolManager để các Node sử dụng.
    """
    try:
        # Gọi hàm xử lý đã có sẵn trong LogicPoolManager
        res = await logic_pool.load_file_to_ram(filename)
        
        if not res["success"]:
            raise HTTPException(status_code=400, detail=res.get("error_message") or res.get("message"))
        
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi load file lên RAM: {str(e)}")


@router.post("/resources/files/unload-from-ram/{filename}", summary="Unload a heavy file from RAM")
def unload_file_from_memory(filename: str):
    """API dùng để giải phóng RAM cho một file"""
    try:
        res = logic_pool.unload_file_from_ram(filename)
        if not res["success"]:
            raise HTTPException(status_code=400, detail=res.get("error_message"))
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi giải phóng file: {str(e)}")
    
@router.get("/resources/files/{filetype}/{filename}/content", summary="Đọc nội dung file (JSON) từ Disk")
async def get_file_content(filetype: str, filename: str):
    # ĐÃ SỬA: Bypass cho 'projects'
    try:
        if filetype != "projects":
            FileType(filetype)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Loại file '{filetype}' không hợp lệ")

    try:
        file_path = logic_pool.get_file_path(filename, filetype)
        with open(file_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
            
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy file: {str(e)}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="File bị hỏng hoặc không phải là định dạng JSON chuẩn")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi đọc file: {e}")