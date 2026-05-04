import aiohttp
import asyncio
from typing import Dict, Any, List
import os
from app.services.utils.ping_measurer import check_server_status
from app.core.config import settings

class APIManualRoutingBus:
    _instance = None
    # FORMAT MỚI: {"Server_id: {"host": hostname, "session": instance, "alive" : True, "ping" : 10}"}}
    _active_server: Dict[str, Dict[str, Any]] = {}

    MASTER_URL = settings.MASTER_URL
    MASTER_API = settings.MASTER_API
    ROLE = settings.NODE_ROLE.lower()

    _heartbeat_interval = 5

    def __new__(cls):
        """Only 1 Instance is allowed on 1 server"""
        if cls._instance is None:
            cls._instance = super(APIManualRoutingBus, cls).__new__(cls)
        return cls._instance
    

    async def _heartbeat_monitor(self):
        """Function used for measurement the connection status with other worker severs..."""
        while True:
            try:
                for sev_id, sev_info in self._active_server.items():
                    res = await check_server_status(sev_info["host"], timeout= 3.0)
                    if res.get("alive"):
                        self._active_server[sev_id].update(res)
                    else:
                        self._active_server[sev_id]["alive"] = False
                        self._active_server[sev_id]["ping"] = 999999
                        self._active_server[sev_id]["hardware"] = {"cpu_percent": 0, "ram_percent": 0, "ram_used_mb": 0, "ram_total_mb": 0}
                
                # QUAN TRỌNG: Lùi lề ra ngoài vòng lặp FOR
                await asyncio.sleep(self._heartbeat_interval)
            except Exception:
                # Bắt buộc phải có sleep ở đây, nếu không khi lỗi xảy ra sẽ sinh ra Infinite Loop
                await asyncio.sleep(self._heartbeat_interval)
    
    def _change_heartbeat_interval(self, new_interval):
        """FOR API CALL : CHANGE THE FREQUENCY IN WHICH THE SERVICE MEASURE PING TO ITS CONNECTED WORKERS SERVERS"""
        self._heartbeat_interval = int(new_interval)
    
    async def _create_http_session(self) -> aiohttp.ClientSession:
        """Create a TCP Connector instance with a server for better performance"""
        #force_close allow to keep this TCP alive for resuse, keep it for 300s without using
        connector = aiohttp.TCPConnector(force_close=False, keepalive_timeout=300)
        return aiohttp.ClientSession(connector=connector)
    
    async def add_new_server(self, server_info: Dict[str, str]):
        """API function: use when FE need to add a new Server to the server pool"""
        sev_id = server_info["server_id"]
        host = server_info["host"]
        if sev_id in self._active_server:
            response = {"success": False, "message": f"{sev_id} with host {host} already exists in the system"}
            return response
        
        try:
            session = await self._create_http_session()
            self._active_server[sev_id] = {
            "session": session,
            "host": host,
            "alive": True,
            "ping": 0
            }

            res = await check_server_status(host, timeout= 3.0)
            if res["alive"]:
                self._active_server[sev_id]["ping"] = res["ping"]
                response = {"success": True, "message": f"{sev_id} with host {host} connected sucessfully"}
                return response
            else:
                await session.close()
                self._active_server.pop(sev_id, None)
                raise ConnectionError(f"{sev_id} response with code {res['status_code']}")
            
        except Exception as e:
            response = {"success": False, "message": f"Cannot Connect to {sev_id} with host {host} : {e}"}
            return response
        
    async def remove_server(self, server_id: str):
        """API Function: use when FE need to remove a server from the server pool"""
        sev_info = self._active_server[server_id]
        session : aiohttp.ClientSession = sev_info["session"]
        if not session.closed:
            await session.close()
        self._active_server.pop(server_id, None)
        response = {"success": True, "message": f"server {server_id} has been removed from the pool"}
        return response


    async def get_server_context(self, server_id: str) -> Dict[str, Any]:
        """Return Session + HostName for the Node to use, If does not have yet. Ask it from the Master and Cache it"""
        if server_id in self._active_server:
            return self._active_server[server_id]
        
        if self.ROLE == "master":
            # Master là Bản gốc. Nếu Master không có, tức là mạng xưởng chưa từng cắm máy này.
            print(f"[Master] Lỗi: Server {server_id} chưa được đăng ký vào hệ thống!")
            return None
        
        #If it does not exist in cache yet -> Ask for it from Master Server
        async with aiohttp.ClientSession() as temp_session:
            try:
                master_api = f"{self.MASTER_URL}/{self.MASTER_API}/infra/servers/{server_id}"
                async with temp_session.get(master_api, timeout=5.0) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Master Failed to Retrieve the Server {server_id}")
                    
                    data = await resp.json()
                    target_host = data.get("host")
            except Exception as e:
                print(f"Error: Fail to search for Server ID from Master Server: {e}")
                return None
        
        #Cache the IP (host) and connect P2P
        await self.add_new_server({
            "server_id" : server_id,
            "host" : target_host
        })

        return self._active_server.get(server_id)
    
    
    async def reconect_server(self, server_id: str) -> aiohttp.ClientSession:
        """Lazy Reconnect"""
        if server_id not in self._active_server:
            raise ValueError(f"Error: {server_id} is not yet registered in the pool")
        old_context = self._active_server[server_id]
        if not old_context["session"].closed:
            await old_context["session"].close()
        
        new_session = await self._create_http_session()
        try:
            host = old_context["host"]
            async with new_session.get(f"http://{host}/status", timeout=3.0) as resp:
                if resp.status != 200:
                    raise ConnectionError(f"http://{host}/status returned code: {resp.status}")
        except Exception as e:
            await new_session.close()
            raise ConnectionError(f"{str(e)}")
        
        self._active_server[server_id]["session"] = new_session
        return new_session
    
    def get_all_active_server(self):
        """RETURN THE LIST OF CURRENTLY ACTIVE SERVER, MAYBE USEFUL FOR FRONT END"""
        return self._active_server