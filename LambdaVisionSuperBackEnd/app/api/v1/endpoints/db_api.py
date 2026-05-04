import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Any, Dict
from app.services.DatabaseManager import DatabaseManager
from app.core.config import get_base_dir



IMAGE_STORAGE_DIR = get_base_dir() / "storage" / "images"
IMAGE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()
db_manager = DatabaseManager()

# Schema Pydantic để Validate Payload từ Frontend
class QueryCondition(BaseModel):
    column: str
    operator: str
    value: Any

class QueryPayload(BaseModel):
    table: str
    select_columns: List[str]
    conditions: List[QueryCondition]

@router.get("/tables", summary="Lấy danh sách các bảng trong DB")
def get_database_tables():
    try:
        return db_manager.get_tables()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schema/{table_name}", summary="Lấy cấu trúc Schema của một bảng")
def get_table_schema(table_name: str):
    try:
        return db_manager.get_schema(table_name)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", summary="Biên dịch JSON Query thành SQL và thực thi")
def execute_dynamic_query(payload: QueryPayload):
    try:
        # Pydantic sẽ tự parse object thành dict thông qua .model_dump()
        result = db_manager.execute_dynamic_query(payload.model_dump())
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi truy vấn SQL: {str(e)}")
    

@router.post("/seed", summary="Tạo dữ liệu Dummy (Ghi đè DB hiện tại)")
def seed_database():
    """Gọi API này để tạo lại toàn bộ bảng và dữ liệu mẫu trong SQLite"""
    try:
        return db_manager.force_seed_dummy_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/images/upload", summary="Upload ảnh lỗi (Base64 hoặc File)")
async def upload_image(file: UploadFile = File(...)):
    """
    API dùng để các thiết bị Camera hoặc Node ném ảnh vào kho lưu trữ vật lý.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Không có tên file")
    
    # Chỉ cho phép các định dạng ảnh
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Không hỗ trợ định dạng {file_ext}. Chỉ nhận JPG, PNG, WEBP.")

    # Chống trùng tên file (Có thể dùng UUID, nhưng ở đây giữ tên gốc cho dễ trace)
    file_path = IMAGE_STORAGE_DIR / file.filename

    try:
        # Lưu file bằng Streaming chunks để không làm đầy RAM
        with open(file_path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        return {
            "success": True, 
            "message": f"Upload ảnh {file.filename} thành công.",
            "file_path": file.filename # Trả về tên file để lưu vào cột crop_image_path trong DB
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu ảnh xuống đĩa: {str(e)}")

@router.get("/images/{filename}/download", summary="Tải/Hiển thị ảnh lỗi")
async def download_image(filename: str):
    """
    API này trả về file ảnh vật lý. Frontend sẽ dùng URL của API này nhét thẳng vào thẻ <img src="...">
    """
    file_path = IMAGE_STORAGE_DIR / filename
    
    if not file_path.exists():
        # Xử lý UX: Nếu không tìm thấy ảnh, có thể trả về một ảnh Placeholder mặc định 
        # (ví dụ: storage/images/not_found.jpg) thay vì quăng lỗi 404 làm vỡ giao diện.
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ảnh: {filename}")
        
    return FileResponse(
        path=file_path,
        filename=filename,
        # Nếu muốn trình duyệt hiển thị luôn (để làm thẻ <img>) thay vì tải về (Save As), 
        # hãy bỏ content_disposition_type="attachment" hoặc set thành "inline"
        content_disposition_type="inline" 
    )


class ColumnDefinition(BaseModel):
    name: str
    type: str # TEXT, REAL, INTEGER, BOOLEAN

class CreateTablePayload(BaseModel):
    table_name: str
    columns: List[ColumnDefinition]

class InsertPayload(BaseModel):
    table: str
    data: Dict[str, Any]

@router.post("/tables/create", summary="Tạo bảng mới")
def create_new_table(payload: CreateTablePayload):
    try:
        # Giả định db_manager có hàm create_dynamic_table
        db_manager.create_dynamic_table(payload.table_name, payload.model_dump()["columns"])
        return {"success": True, "message": f"Đã tạo bảng {payload.table_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/insert", summary="Ghi dữ liệu vào bảng")
def insert_data(payload: InsertPayload):
    try:
        # Giả định db_manager có hàm insert_dynamic_data
        inserted_id = db_manager.insert_dynamic_data(payload.table, payload.data)
        return {"success": True, "inserted_id": inserted_id}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
class DropTablePayload(BaseModel):
    table_name: str

@router.post("/tables/drop", summary="Xóa toàn bộ bảng và dữ liệu")
def drop_table(payload: DropTablePayload):
    try:
        db_manager.drop_dynamic_table(payload.table_name)
        return {"success": True, "message": f"Đã xóa vĩnh viễn bảng {payload.table_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))