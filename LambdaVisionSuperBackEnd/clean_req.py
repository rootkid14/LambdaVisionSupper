import cv2
import time
import subprocess

cam_id = 0
device = f"/dev/video{cam_id}"

cap = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)
if not cap.isOpened():
    print("Không thể kết nối với webcam")
    exit()

# Ổn định đường truyền: Dùng định dạng MJPG để ảnh mượt, không lag ở độ phân giải cao
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Trạng thái ban đầu: Khóa nét hay tự động
focus_status = "AUTO" 

print("--------------------------------------------------")
print("HƯỚNG DẪN VẬN HÀNH (GIẢ LẬP IPHONE FOCUS):")
print("  - Nhấn 'f': Ép camera QUÉT LẠI NÉT (Trigger Focus)")
print("  - Nhấn 'l': KHÓA CỨNG tiêu cự hiện tại (Lock)")
print("  - Nhấn 'c': CHỤP ẢNH")
print("  - Nhấn 'q': Thoát")
print("--------------------------------------------------")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Giao diện Preview hiển thị trạng thái cho người vận hành
    preview_frame = frame.copy()
    if focus_status == "HUNTING":
        color = (0, 255, 255) # Vàng khi đang quét
        text = "Focus: SCANNING..."
    elif focus_status == "AUTO":
        color = (0, 255, 0) # Xanh lá khi ở chế độ tự động
        text = "Focus: AUTO"
    else:
        color = (0, 0, 255) # Đỏ khi đã khóa cứng
        text = "Focus: LOCKED"
        
    cv2.putText(preview_frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow('Webcam Stream', preview_frame)

    key = cv2.waitKey(1) & 0xFF

    # 1. TRIGGER FOCUS (ÉP LẤY NÉT LẠI)
    if key == ord('f'):
        focus_status = "HUNTING"
        print(" [!] Đang ép camera quét lại tiêu cự...")
        
        # Mẹo: Tắt đi bật lại liên tục để reset thuật toán của phần cứng
        subprocess.run(["v4l2-ctl", "-d", device, "-c", "focus_automatic_continuous=0"], stdout=subprocess.DEVNULL)
        time.sleep(0.1) # Chờ một chút để driver nhận lệnh tắt
        subprocess.run(["v4l2-ctl", "-d", device, "-c", "focus_automatic_continuous=1"], stdout=subprocess.DEVNULL)
        
        focus_status = "AUTO"

    # 2. LOCK FOCUS (KHÓA NẾT)
    elif key == ord('l'):
        subprocess.run(["v4l2-ctl", "-d", device, "-c", "focus_automatic_continuous=0"], stdout=subprocess.DEVNULL)
        focus_status = "LOCKED"
        print(" [OK] Đã khóa cứng tiêu cự.")

    # 3. CHỤP ẢNH
    elif key == ord('c'):
        filename = f"capture_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame) # Lưu ảnh gốc siêu sạch, không chứa chữ trạng thái
        print(f" [SAVE] Đã chụp ảnh: {filename}")

    elif key == ord('q'):
        break

# Trả lại trạng thái mặc định khi thoát ứng dụng
subprocess.run(["v4l2-ctl", "-d", device, "-c", "focus_automatic_continuous=1"], stdout=subprocess.DEVNULL)
cap.release()
cv2.destroyAllWindows()