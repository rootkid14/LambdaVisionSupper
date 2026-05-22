from fastapi import APIRouter, Request, HTTPException
import psutil
from typing import Any
from app.services.ConnectionBus import APIManualRoutingBus
from app.services.DevicePoolManager import HTTPDevicePoolManager
from app.services.LogicPoolManager import LogicPoolManager
import aiohttp
import os
import json
import asyncio
from fastapi.responses import StreamingResponse
import httpx
from app.services.utils.ping_measurer import check_server_status
from app.core.config import settings


root_router = APIRouter()
server_bus = APIManualRoutingBus()
device_pool = HTTPDevicePoolManager()
logic_pool = LogicPoolManager()
global_proxy_client = httpx.AsyncClient()

@root_router.get("/status", status_code=200)
def check_server_health() -> Any:
    """
    Master sẽ gọi API này để kiểm tra xem Worker còn sống không 
    và đang chịu tải (RAM/CPU) như thế nào.
    """
    # Lấy thông số phần cứng hiện tại của Worker
    cpu_usage = psutil.cpu_percent(interval=0.1)
    ram_info = psutil.virtual_memory()
    #Sanitize the device information (remove the ClientSession from the dict)
    raw_devices = device_pool.get_all_active_device()
    safe_device_list = {}
    for dev_id, dev_info in raw_devices.items():
        safe_device_list[dev_id] = {
            "host": dev_info.get("host"),
            "alive": dev_info.get("alive"),
            "ping": dev_info.get("ping")
        }
    
    logic_obj_count = len(logic_pool._logic_pool)

    return {
        "role": server_bus.ROLE,
        "hardware": {
            "cpu_percent": cpu_usage,
            "ram_used_mb": round(ram_info.used / (1024 * 1024), 2),
            "ram_total_mb": round(ram_info.total / (1024 * 1024), 2),
            "ram_percent": ram_info.percent
        },
        "device_list" : safe_device_list,
        "logic_obj_count": logic_obj_count
    }


@root_router.get("/fleetstatus", summary="Check health of worker server that this server is owning")
async def get_fleet_overview_status():
    """FE will call this API frequently to update the fleet dashboard, Master server act as the aggregator"""
    
    # if server_bus.ROLE != "master":
    #     return {"error": "Only Master can aggregate fleet status"}
    
    # 1. Report status of the Master server itself
    master_cpu = psutil.cpu_percent(interval=0.1)
    master_ram  = psutil.virtual_memory()
    
    raw_devices = device_pool.get_all_active_device()
    safe_device_list = {
        dev_id: {
            "host": dev_info.get("host"),
            "alive": dev_info.get("alive"),
            "ping": dev_info.get("ping")
        } for dev_id, dev_info in raw_devices.items()
    }

    all_status = [{
        "server_id": "master_gateway",
        "host": settings.MASTER_URL,
        "alive": True,
        "role": "master",
        "ping": 0,
        "hardware": {
            "cpu_percent": master_cpu,
            "ram_used_mb": round(master_ram.used / (1024 * 1024), 2),
            "ram_total_mb": round(master_ram.total / (1024 * 1024), 2),
            "ram_percent": master_ram.percent
        },
        "device_list": safe_device_list
    }]

    # 2. Thu thập dữ liệu từ tất cả Worker
    all_servers_info = server_bus.get_all_active_server()
    
    # Tạo danh sách các task để chạy đồng thời (concurrency)
    tasks = []
    server_ids = []

    for sev_id, sev_info in all_servers_info.items():
        # Sử dụng lại hàm check_server_status bạn đã viết để lấy data + ping
        tasks.append(check_server_status(sev_info["host"], timeout=2.0))
        server_ids.append(sev_id)

    # Chạy tất cả các request cùng một lúc
    responses = await asyncio.gather(*tasks)

    # 3. Tổng hợp kết quả
    for i, res in enumerate(responses):
        sev_id = server_ids[i]
        sev_info = all_servers_info[sev_id]
        
        server_report = {
            "server_id": sev_id,
            "host": sev_info["host"],
            "alive": res.get("alive", False),
            "role": res.get("role", "worker"),
            "ping": res.get("ping", 9999),
            "hardware": res.get("hardware", {}),
            "device_list": res.get("device_list", {}),
            "logic_obj_count" : res.get("logic_obj_count", 0)
        }
        all_status.append(server_report)

    return all_status
    

@root_router.api_route("/proxy/{server_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(server_id: str, path: str, request: Request):
    """USING THE MASTER SERVER AS THE GATEWAY FOR FE TO CONNECT TO EACH WORKER SERVER IN THE FLEET"""
    if server_id == "master":
        raise HTTPException(status_code=400, detail="Not allowed to proxy to Master BE server")
        
    active_servers = server_bus._active_server
    if server_id not in active_servers:
        raise HTTPException(status_code=404, detail=f"Worker Server {server_id} is not in the fleet")
        
    target_host = active_servers[server_id]["host"]
    target_url = f"http://{target_host}/{path}"
    
    # 1. Chuẩn hóa Headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None) # QUAN TRỌNG: Xóa để tránh xung đột Chunked Encoding khi Upload File
    
    # 2. Xử lý body an toàn (Không truyền content cho GET/DELETE, KHÔNG dùng await stream)
    method = request.method
    if method in ["POST", "PUT", "PATCH"]:
        payload_body = request.stream() # Đã XÓA chữ await
    else:
        payload_body = None
        
    try:
        req = global_proxy_client.build_request(
            method=method,
            url=target_url,
            headers=headers,
            content=payload_body,
            params=request.query_params
        )
        response = await global_proxy_client.send(req, stream=True)
        
        # 3. Chuẩn hóa header trả về cho Frontend
        resp_headers = dict(response.headers)
        resp_headers.pop("content-encoding", None) # Tránh lỗi giải nén kép trên trình duyệt
        resp_headers.pop("content-length", None)
        
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=resp_headers
        )
        
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Lỗi Gateway: Không thể kết nối tới Worker {server_id} - {str(exc)}")
    except Exception as e:
        # 4. Bắt toàn bộ lỗi nội bộ thành HTTPException để CORSMiddleware vẫn hoạt động
        raise HTTPException(status_code=500, detail=f"Lỗi Proxy nội bộ: {str(e)}")
