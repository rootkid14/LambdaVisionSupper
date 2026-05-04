from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.api.root_api import root_router
from app.services.DevicePoolManager import HTTPDevicePoolManager
from app.services.ConnectionBus import APIManualRoutingBus
from app.services.LogicPoolManager import LogicPoolManager
import importlib
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio
from app.services.DatabaseManager import DatabaseManager
import sys

def load_all_nodes():
    """Scann all .py file in the services/Nodes AND storage/pluggins to activate the @registry_node mechanism"""
    base_dir = Path(__file__).parent.parent
    
    # 1. Quét thư mục Nodes mặc định (Core Nodes)
    nodes_dir = Path(__file__).parent / "services" / "Nodes"
    loaded_count = 0

    print("[BOOT] Bắt đầu nạp Core Nodes...")
    for file_path in nodes_dir.rglob("*.py"):
        if file_path.name != "__init__.py":
            relative_path = file_path.relative_to(base_dir)
            module_name = str(relative_path).replace("\\", ".").replace("/", ".").rstrip(".py")
            try:
                importlib.import_module(module_name)
                loaded_count += 1
            except Exception as e:
                print(f"  [!] Lỗi khi nạp Core module {module_name}: {e}")

    # 2. Quét thư mục Plugins (Custom Nodes của người dùng)
    # Lấy đường dẫn giống hệt cách LogicPoolManager lấy
    plugins_dir = base_dir / "storage" / "pluggins"
    if plugins_dir.exists():
        print("[BOOT] Bắt đầu nạp Custom Plugins...")
        for file_path in plugins_dir.rglob("*.py"):
            if file_path.name != "__init__.py":
                # Nạp theo đường dẫn tuyệt đối (Absolute Path Loading) giống hệt cách Watchdog làm
                module_name = f"external_plugins.{file_path.stem}"
                try:
                    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        
                        # Cập nhật luôn _plugin_mtimes để Watchdog không cần nạp lại vòng đầu tiên
                        LogicPoolManager()._plugin_mtimes[str(file_path)] = file_path.stat().st_mtime
                        loaded_count += 1
                        print(f"  + Đã nạp Plugin: {file_path.name}")
                except Exception as e:
                    print(f"  [!] Lỗi khi nạp Plugin {file_path.name}: {e}")
                    
    print(f"[OK] Hoàn tất nạp tổng cộng {loaded_count} module Logic.\n")

@asynccontextmanager
async def lifespan(app: FastAPI):
    device_pool = HTTPDevicePoolManager()
    server_bus = APIManualRoutingBus()
    logicpoolmanager = LogicPoolManager()

    # --- Khi app đã khởi động xong và sẵn sàng chạy ---
    task_device = asyncio.create_task(device_pool._heartbeat_monitor())
    task_server = asyncio.create_task(server_bus._heartbeat_monitor())
    task_plugins = asyncio.create_task(logicpoolmanager._plugins_heartbeat_monitor())

    load_all_nodes()

    yield

    # --- KHI APP SHUTDOWN ---
    task_device.cancel()
    task_server.cancel()
    task_plugins.cancel()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

#Initializing the subsystems
httpDevicePool = HTTPDevicePoolManager()
apimanualroutingbus = APIManualRoutingBus()
logicpoolmanager = LogicPoolManager()
db_manager = DatabaseManager()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Đổi thành "*" để fix triệt để lỗi chặn kết nối
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(root_router, tags=["root"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8600)