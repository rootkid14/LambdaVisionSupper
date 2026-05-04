from fastapi import APIRouter
from typing import Any

router = APIRouter()

@router.get("/health-check", status_code=200)
def perform_health_check() -> Any:
    """
    Kiểm tra trạng thái hoạt động của API.
    Trả về 200 nếu hệ thống sẵn sàng xử lý yêu cầu.
    """
    return {
        "status": "ok",
        "message": "Hệ thống LambdaVisionSupper đang hoạt động ổn định!"
    }