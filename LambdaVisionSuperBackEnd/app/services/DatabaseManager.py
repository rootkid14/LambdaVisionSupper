import os
from sqlalchemy import create_engine, MetaData, Table, select, text
from pathlib import Path
from app.core.config import get_base_dir
from datetime import datetime

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        db_dir = get_base_dir() / "storage"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "lambdainspection.db"
        
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.metadata = MetaData()
        
        self.metadata.reflect(bind=self.engine)
        if not self.metadata.tables:
            self.force_seed_dummy_data()

    def get_tables(self) -> list:
        self.metadata.reflect(bind=self.engine)
        return list(self.metadata.tables.keys())

    def get_schema(self, table_name: str) -> dict:
        self.metadata.reflect(bind=self.engine)
        if table_name not in self.metadata.tables:
            raise ValueError(f"Bảng {table_name} không tồn tại")
            
        table = self.metadata.tables[table_name]
        schema_config = {}
        
        for col in table.columns:
            col_type = str(col.type).upper()
            
            # 1. CẢI TIẾN: Nhận diện chi tiết kiểu dữ liệu
            dataType = 'text'
            if 'INT' in col_type or 'FLOAT' in col_type or 'NUMERIC' in col_type:
                dataType = 'number'
            elif 'DATETIME' in col_type or 'TIMESTAMP' in col_type or 'DATE' in col_type:
                dataType = 'datetime'
            elif 'BOOL' in col_type or 'BOOLEAN' in col_type:
                dataType = 'boolean'
                
            is_image = 'image' in col.name.lower() or 'path' in col.name.lower()
            
            schema_config[col.name] = {
                "originalName": col.name,
                "displayName": col.name.replace("_", " ").upper(),
                "isVisible": True,
                "isImage": is_image if dataType == 'text' else False,
                "dataType": dataType
            }
            
        return schema_config

    def execute_dynamic_query(self, payload: dict) -> list:
        table_name = payload.get("table")
        select_cols = payload.get("select_columns", [])
        conditions = payload.get("conditions", [])

        self.metadata.reflect(bind=self.engine)
        if table_name not in self.metadata.tables:
            raise ValueError(f"Bảng {table_name} không tồn tại")
            
        table = self.metadata.tables[table_name]

        cols_to_select = [table.c[col] for col in select_cols if col in table.c]
        if not cols_to_select:
            cols_to_select = [table]
            
        stmt = select(*cols_to_select)

        # 2. CẢI TIẾN: Xử lý các toán tử SQL nâng cao
        for cond in conditions:
            col_name = cond.get("column")
            op = cond.get("operator")
            val = cond.get("value")
            
            if col_name in table.c:
                column = table.c[col_name]
                if op == "==":
                    stmt = stmt.where(column == val)
                elif op == "!=":
                    stmt = stmt.where(column != val)
                elif op == ">":
                    stmt = stmt.where(column > val)
                elif op == "<":
                    stmt = stmt.where(column < val)
                elif op == "CONTAINS":
                    stmt = stmt.where(column.like(f"%{val}%"))
                elif op == "BETWEEN":
                    # Xử lý dải ngày tháng (From - To)
                    if isinstance(val, list) and len(val) == 2:
                        if val[0] and val[1]:
                            stmt = stmt.where(column.between(val[0], val[1]))
                        elif val[0]: # Chỉ có From
                            stmt = stmt.where(column >= val[0])
                        elif val[1]: # Chỉ có To
                            stmt = stmt.where(column <= val[1])

        stmt = stmt.limit(100)

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def force_seed_dummy_data(self):
        """Xóa trắng DB hiện tại và tạo lại các bảng Dummy để Test"""
        with self.engine.connect() as conn:
            # 1. Xóa các bảng cũ (nếu có)
            conn.execute(text("DROP TABLE IF EXISTS inspection_logs"))
            conn.execute(text("DROP TABLE IF EXISTS system_events"))
            conn.execute(text("DROP TABLE IF EXISTS production_stats"))
            
            # 2. Tạo bảng 1: inspection_logs (Chứa Ảnh và Số thập phân)
            conn.execute(text("""
                CREATE TABLE inspection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    defect_type TEXT,
                    confidence FLOAT,
                    crop_image_path TEXT
                )
            """))
            conn.execute(text("""
                INSERT INTO inspection_logs (defect_type, confidence, crop_image_path)
                VALUES 
                ('Scratch', 0.95, 'mock_scratch.jpg'),
                ('Dent', 0.88, 'mock_dent.jpg'),
                ('Missing Part', 0.99, 'mock_missing.jpg'),
                ('OK', 1.0, 'mock_ok.jpg')
            """))
            
            # 3. Tạo bảng 2: system_events (Chứa Text và Cảnh báo)
            conn.execute(text("""
                CREATE TABLE system_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    severity TEXT,
                    message TEXT
                )
            """))
            conn.execute(text("""
                INSERT INTO system_events (severity, message)
                VALUES 
                ('INFO', 'System started successfully'),
                ('WARNING', 'Camera temperature high: 45C'),
                ('ERROR', 'Conveyor belt motor stalled'),
                ('INFO', 'User admin logged in')
            """))

            # 4. Tạo bảng 3: production_stats (Toàn Số nguyên)
            conn.execute(text("""
                CREATE TABLE production_stats (
                    shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shift_date DATE DEFAULT CURRENT_DATE,
                    total_scanned INTEGER,
                    total_passed INTEGER,
                    total_failed INTEGER
                )
            """))
            conn.execute(text("""
                INSERT INTO production_stats (total_scanned, total_passed, total_failed)
                VALUES 
                (1500, 1450, 50),
                (2000, 1980, 20)
            """))
            
            conn.commit()
            
            # 5. CỰC KỲ QUAN TRỌNG: Xóa bộ nhớ đệm Metadata và quét lại cấu trúc DB mới
            self.metadata.clear()
            self.metadata.reflect(bind=self.engine)
            
            return {"success": True, "message": "Đã tạo thành công 3 bảng mẫu: inspection_logs, system_events, production_stats"}
    
    # === BỔ SUNG: TẠO BẢNG ĐỘNG ===
    def create_dynamic_table(self, table_name: str, columns: list):
        from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
        
        self.metadata.reflect(bind=self.engine)
        if table_name in self.metadata.tables:
            raise ValueError(f"Bảng {table_name} đã tồn tại!")

        # SQLAlchemy luôn yêu cầu ít nhất 1 khóa chính (Primary Key)
        # Chúng ta sẽ tự động tạo một cột 'id' làm khóa chính cho an toàn.
        table_columns = [Column('id', Integer, primary_key=True, autoincrement=True)]

        for col in columns:
            name = col.get("name")
            col_type = col.get("type").upper()
            
            # Map kiểu dữ liệu UI sang SQLAlchemy
            sql_type = String
            if col_type == "INTEGER": sql_type = Integer
            elif col_type == "REAL": sql_type = Float
            elif col_type == "BOOLEAN": sql_type = Boolean
            elif col_type == "DATETIME": sql_type = DateTime
            
            table_columns.append(Column(name, sql_type))

        # Tạo bảng và Commit vào DB
        new_table = Table(table_name, self.metadata, *table_columns)
        new_table.create(self.engine)
        
        # Cập nhật lại Metadata
        self.metadata.clear()
        self.metadata.reflect(bind=self.engine)
        return True

    # === BỔ SUNG: INSERT DỮ LIỆU ĐỘNG ===
    def insert_dynamic_data(self, table_name: str, data: dict):
        self.metadata.reflect(bind=self.engine)
        if table_name not in self.metadata.tables:
            raise ValueError(f"Bảng {table_name} không tồn tại!")
            
        table = self.metadata.tables[table_name]
        
        valid_data = {}
        
        # Duyệt qua các dữ liệu được gửi lên
        for k, v in data.items():
            if k in table.c:
                col = table.c[k]
                
                # PHÉP THUẬT ÉP KIỂU NGÀY THÁNG CỦA PYTHON
                if str(col.type).upper() in ['DATETIME', 'DATE', 'TIMESTAMP']:
                    if isinstance(v, str):
                        try:
                            # JS gửi lên chuỗi ISO có chữ 'Z' ở cuối (nghĩa là múi giờ UTC)
                            # Ta đổi 'Z' thành '+00:00' để hàm từ chuẩn của Python đọc được mượt mà
                            clean_time_str = v.replace('Z', '+00:00')
                            valid_data[k] = datetime.fromisoformat(clean_time_str)
                        except Exception as e:
                            print(f"Lỗi parse thời gian cho cột {k}: {e}")
                            valid_data[k] = v # Lỗi thì cứ nhét string vào (biết đâu DB tự hiểu)
                    else:
                        valid_data[k] = v
                else:
                    valid_data[k] = v
        
        if not valid_data:
             raise ValueError("Không có dữ liệu hợp lệ nào để Insert.")

        with self.engine.connect() as conn:
            from sqlalchemy import insert
            stmt = insert(table).values(**valid_data)
            result = conn.execute(stmt)
            conn.commit()
            
            return result.inserted_primary_key[0] if result.inserted_primary_key else None