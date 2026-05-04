import os
import re
from pathlib import Path

def minify_python_for_llm(src_dir, output_file):
    src_path = Path(src_dir)
    combined_content = []

    if not src_path.is_dir():
        print(f"Lỗi: Không tìm thấy thư mục '{src_dir}'")
        return

    # Quét tất cả file .py
    for file_path in src_path.rglob('*.py'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                optimized_lines = []
                for line in lines:
                    # 1. Loại bỏ các dòng chỉ có comment (bắt đầu bằng #)
                    # 2. Loại bỏ các dòng trống (chỉ có khoảng trắng hoặc xuống dòng)
                    clean_line = line.rstrip() # Xóa khoảng trắng thừa bên phải (vẫn giữ thụt lề bên trái)
                    
                    if clean_line and not clean_line.strip().startswith('#'):
                        # Loại bỏ comment nằm ở cuối dòng (inline comment)
                        # Lưu ý: Regex này đơn giản hóa, có thể ảnh hưởng nếu chuỗi string có chứa '#'
                        clean_line = re.sub(r'\s*#.*$', '', clean_line)
                        optimized_lines.append(clean_line)
                
                # Gộp các dòng lại thành một khối code liên tục
                file_content = "\n".join(optimized_lines)
                
                # Thêm header để AI phân biệt file
                file_header = f"### FILE: {file_path.as_posix()} ###\n"
                combined_content.append(file_header + file_content)
                
                print(f"Đã xử lý: {file_path}")
        except Exception as e:
            print(f"Lỗi khi đọc file {file_path}: {e}")

    # Ghi ra file tổng hợp
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Phân tách các file bằng 2 dấu xuống dòng cho rõ ràng
            f.write("\n\n".join(combined_content))
        print(f"\n✅ Xong! File Python tổng hợp đã lưu tại '{output_file}'")
    except Exception as e:
        print(f"Lỗi khi ghi file: {e}")

if __name__ == "__main__":
    # Thay 'src' bằng tên thư mục chứa code python của bạn
    SOURCE_DIRECTORY = '.' 
    OUTPUT_FILENAME = 'py_context_for_llm.txt'
    
    minify_python_for_llm(SOURCE_DIRECTORY, OUTPUT_FILENAME)