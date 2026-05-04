import asyncio
import aiohttp
import time
from typing import Dict, Optional

async def check_server_status(hostname: str, timeout: float = 3.0) -> Dict:
    """
    Ping đến endpoint /status để kiểm tra kết nối và đo độ trễ.
    """
    url = f"http://{hostname}/status"
    start_time = time.perf_counter()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                # Đo thời gian ngay khi nhận được Header
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                status_code = response.status
                is_alive = (status_code == 200)

                res = {
                    "alive": is_alive,
                    "ping": round(latency_ms, 2),
                    "status_code": status_code
                }

                data = None 
                if is_alive:
                    data = await response.json()
                
                if data:
                    res.update(data)    

                return res
    except asyncio.TimeoutError:
        return {"hostname": hostname, "alive": False, "latency": None, "error": "Timeout"}
    except Exception as e:
        return {"hostname": hostname, "alive": False, "latency": None, "error": str(e)}


