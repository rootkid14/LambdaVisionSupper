import re

# 1. DANH SÁCH CÁC THƯ VIỆN CỐT LÕI (Bắt buộc giữ nguyên phiên bản)
# Thêm hoặc bớt tùy theo nhu cầu dự án của bạn
CORE_PACKAGES = [
    'torch', 'torchaudio', 'torchvision', 
    'tensorflow', 'tensorflow-intel',
    'opencv-python', 'opencv-contrib-python-headless'
]

# Đọc file requirements.txt hiện tại
try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
except FileNotFoundError:
    print("Không tìm thấy file requirements.txt!")
    exit()

clean_lines = []
for line in lines:
    line = line.strip()
    
    # Bỏ qua dòng trống
    if not line:
        continue
        
    # Giữ nguyên các dòng cấu hình của pip (như link tải pytorch)
    if line.startswith('--') or line.startswith('-i'):
        clean_lines.append(line + '\n')
        continue

    # Tách tên package ra khỏi các ký hiệu version (==, >=, <=, ~)
    parts = re.split(r'([=><~]+)', line, maxsplit=1)
    package_name = parts[0].strip()

    # Nếu là thư viện cốt lõi -> Giữ nguyên cả dòng
    if package_name.lower() in CORE_PACKAGES:
        clean_lines.append(line + '\n')
    # Nếu là thư viện phụ -> Chỉ lấy tên package
    else:
        clean_lines.append(package_name + '\n')

# Ghi ra file mới
with open('requirements_offline.txt', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)

print("🎉 Đã dọn dẹp xong! File mới của bạn là: requirements_offline.txt")