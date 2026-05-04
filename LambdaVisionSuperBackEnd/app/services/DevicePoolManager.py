import aiohttp
import asyncio
from typing import Dict, Any, List
from app.services.utils.ping_measurer import check_server_status

class HTTPDevicePoolManager:
    _instance = None
    # FORMAT MỚI: {"device_id": {"session": ClientSession, "host": "cam.local", "alive" : True, "ping" : 10}}
    _active_devices: Dict[str, Dict[str, Any]] = {}

    _heartbeat_interval = 5

    def __new__(cls):
        """Only 1 Instance is allowed on 1 server"""
        if cls._instance is None:
            cls._instance = super(HTTPDevicePoolManager, cls).__new__(cls)
        return cls._instance
    
    def _change_heartbeat_interval(self, new_interval):
        """FOR API CALL : CHANGE THE FREQUENCY IN WHICH THE SERVICE MEASURE PING TO ITS CONNECTED WORKERS SERVERS"""
        self._heartbeat_interval = int(new_interval)

    async def _heartbeat_monitor(self):
        """Function used for measurement the connection status with other worker severs..."""
        while True:
            try:
                for dev_id, dev_info in self._active_devices.items():
                    res = await check_server_status(dev_info["host"], timeout= 3.0)
                    if res["alive"]:
                        self._active_devices[dev_id]["alive"] = True
                        self._active_devices[dev_id]["ping"] = res["ping"]
                    else:
                        self._active_devices[dev_id]["alive"] = False
                        self._active_devices[dev_id]["ping"] = 999999
                
                await asyncio.sleep(self._heartbeat_interval)
            except Exception:
                await asyncio.sleep(self._heartbeat_interval)
    
    async def _create_http_session(self) -> aiohttp.ClientSession:
        """Create a TCP Connector instance with a device"""
        #force_close allow to keep this TCP alive for resuse, keep it for 300s without using
        connector = aiohttp.TCPConnector(force_close=False, keepalive_timeout=300)
        return aiohttp.ClientSession(connector=connector)
    
    async def add_new_device(self, device_info : Dict[str, str]):
        """API Function for adding new device into the pool"""
        device_id = device_info["device_id"]
        device_host = device_info["host"]
        if device_id in self._active_devices:
            response = {"success": False, "message": f"{device_id} with host {device_host} already exists in the system"}
            return response
        try:
            session = await self._create_http_session()
            self._active_devices[device_id] = {
            "session": session,
            "host": device_host,
            "alive": True,
            "ping": 0
            }

            res = await check_server_status(device_host, timeout= 3.0)
            if res["alive"]:
                self._active_devices[device_id]["ping"] = res["ping"]
                response = {"success": True, "message": f"{device_id} with host {device_host} connected sucessfully"}
                return response
            else:
                await session.close()
                self._active_devices.pop(device_id, None)
                raise ConnectionError(f"{device_id} response with code {res['status_code']}")
            
        except Exception as e:
            response = {"success": False, "message": f"Cannot Connect to {device_id} with host {device_host} : {str(e)}"}
            return response

    async def remove_device(self, device_id: str):
        """API Function: use when FE need to remove a device from the device pool"""
        dev_info = self._active_devices[device_id]
        session : aiohttp.ClientSession = dev_info["session"]
        if not session.closed:
            await session.close()
        self._active_devices.pop(device_id, None)
        response = {"success": True, "message": f"server {device_id} has been removed from the pool"}
        return response    


    def get_device_context(self, device_id: str) -> Dict[str, Any]:
        """Return Session + HostName for the Device Node to use"""
        if device_id not in self._active_devices:
            print(f"Error: {device_id} is not yet registered in the pool")
            return None
        return self._active_devices[device_id]
        
    
    async def reconnect_device(self, device_id: str) -> aiohttp.ClientSession:
        """Lazy Reconnect"""
        if device_id not in self._active_devices:
            raise ValueError(f"Error: {device_id} is not yet registered in the pool")
        old_context = self._active_devices[device_id]
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
        
        self._active_devices[device_id]["session"] = new_session
        return new_session
    
    def get_all_active_device(self):
        """RETURN THE LIST OF CURRENTLY ACTIVE Devices, MAYBE USEFUL FOR FRONT END"""
        return self._active_devices