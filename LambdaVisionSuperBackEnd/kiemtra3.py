import serial
import time

# ================= CẤU HÌNH =================
PORT = '/dev/ttyACM0'  # Cổng kết nối của ESP32
BAUD = 115200          # Tốc độ Baud

def main():
    print(f"[*] Đang khởi tạo kết nối tới {PORT} ở tốc độ {BAUD}...")
    try:
        # Khởi tạo cổng Serial (thêm timeout để readline() không bị treo)
        ser = serial.Serial(PORT, BAUD, timeout=1)
        
        # Đợi 1 giây để cổng ổn định và bỏ qua rác (nếu có) trong buffer
        time.sleep(1) 
        ser.reset_input_buffer()
        print("[*] Kết nối thành công! Đã sẵn sàng gửi lệnh.\n")
        
    except Exception as e:
        print(f"[!] Lỗi kết nối: {e}")
        print("[!] Hãy chắc chắn rằng bạn đã đóng Serial Monitor của VSCode!")
        return

    while True:
        # Lấy lệnh từ bàn phím
        cmd = input(">> Nhập lệnh (P = Ping, E = Relay, Q = Thoát): ").strip().upper()
        
        if cmd == 'Q':
            print("[*] Đang đóng kết nối...")
            break
            
        elif cmd in ['P', 'E', 'L', 'C']:
            # Gửi ký tự lệnh xuống dạng bytes
            ser.write(cmd.encode('utf-8'))
            
            # Chờ 0.1s để ESP32 kịp xử lý lệnh và gửi phản hồi
            time.sleep(0.1) 
            
            # Đọc tất cả các dòng phản hồi có trong bộ đệm (buffer)
            while ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    print(f"   [ESP32] -> {response}")
                    
        else:
            print("   [!] Lệnh không hợp lệ.")

    # Đóng cổng sau khi thoát
    ser.close()
    print("[*] Hoàn tất.")

if __name__ == '__main__':
    main()