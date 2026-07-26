import serial
import cv2
import numpy as np
import time

# ================= CẤU HÌNH =================
PORT = '/dev/ttyACM0'  # Cổng của bạn trên Linux
BAUD = 2000000          # Đã đồng bộ với cấu hình ESP32 mới nhất

def main():
    print(f"[*] Đang kết nối tới {PORT} ở tốc độ {BAUD}...")
    
    try:
        # Khởi tạo cổng Serial (timeout 2s để tránh treo)
        ser = serial.Serial(PORT, BAUD, timeout=2)
    except Exception as e:
        print(f"[!] Lỗi kết nối: {e}")
        print("[!] Bạn đã cấp quyền cho cổng chưa? Hãy thử: sudo chmod a+rw /dev/ttyACM0")
        return

    time.sleep(2) # Đợi mạch ổn định sau khi mở cổng
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    
    print("[*] Kết nối thành công! Bắt đầu lấy luồng ảnh...")
    print("[*] Nhấn phím 'q' trên cửa sổ Camera để thoát.")

    while True:
        try:
            # 1. Gửi lệnh 'C' (Capture) xuống ESP32
            ser.write(b'C')
            
            # 2. Chờ và đọc dòng Header (IMG_START)
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if line.startswith("IMG_START:"):
                # Lấy kích thước ảnh (bytes)
                img_len = int(line.split(":")[1])
                
                # 3. Đọc chính xác số bytes của bức ảnh
                img_data = ser.read(img_len)
                
                # 4. Dọn dẹp buffer phần Footer (IMG_END)
                while True:
                    footer = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "IMG_END" in footer:
                        break
                
                # 5. Kiểm tra và giải mã ảnh
                if len(img_data) == img_len:
                    # Chuyển dữ liệu nhị phân thành mảng numpy
                    np_arr = np.frombuffer(img_data, np.uint8)
                    
                    # Giải mã JPEG thành khung hình OpenCV
                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    if img is not None:
                        # Hiển thị ảnh
                        img = cv2.resize(img, (1024,768))
                        cv2.imshow("ESP32-S3 Live Camera", img)
                    else:
                        print("[!] Ảnh bị hỏng (decode failed)")
                else:
                    print(f"[!] Mất gói tin. Cần {img_len} bytes nhưng chỉ nhận {len(img_data)} bytes")
            
            # 6. Tạo độ trễ và kiểm tra phím thoát ('q')
            # waitKey(30) tạo tốc độ làm mới ~30fps
            if cv2.waitKey(30) & 0xFF == ord('q'):
                print("[*] Đang đóng luồng...")
                break
                
        except KeyboardInterrupt:
            # Xử lý khi nhấn Ctrl+C trên Terminal
            break
        except Exception as e:
            print(f"[!] Lỗi vòng lặp: {e}")
            break

    # Dọn dẹp tài nguyên
    ser.close()
    cv2.destroyAllWindows()
    print("[*] Đã ngắt kết nối.")

if __name__ == '__main__':
    main()