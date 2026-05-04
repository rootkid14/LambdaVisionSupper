from pydantic_settings import BaseSettings, SettingsConfigDict
import sys
from pathlib import Path

def get_base_dir() -> Path:
    """Xác định đường dẫn gốc an toàn kể cả khi chạy bằng Python thuần hay đã build thành EXE"""
    if getattr(sys, 'frozen', False):
        # Nếu đang chạy dưới dạng file thực thi (.exe)
        return Path(sys.executable).parent
    else:
        # Nếu đang chạy bằng file .py bình thường (cấu trúc: app/core/...)
        return Path(__file__).parent.parent.parent
    
class Settings(BaseSettings):
    PROJECT_NAME: str = "LambdaVisionSupper"
    API_V1_STR: str = "/api/v1"
    MASTER_URL: str = "http://192.168.1.11:8600"
    MASTER_API: str = "/api/v1"
    NODE_ROLE: str = "worker"
    model_config = SettingsConfigDict(env_file=".env")
    
settings = Settings()