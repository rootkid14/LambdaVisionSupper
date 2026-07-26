import os
import time
import tkinter as tk
from tkinter import messagebox, ttk
from threading import Thread
import serial
from PIL import Image, ImageTk
import io

# Cấu hình đường dẫn Symlink và Thư mục lưu ảnh
CAMERAS = {
    "Top Left": "/dev/cam_top_left",
    "Top Right": "/dev/cam_top_right"
}
SAVE_DIR = os.path.expanduser("~/Desktop/Captured_Images")
os.makedirs(SAVE_DIR, exist_ok=True)

class CameraCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HỆ THỐNG CHỤP & KIỂM TRA ẢNH AUTOMATION")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        # Biến tạm lưu dữ liệu ảnh sau khi chụp thành công (chờ Save)
        self.temp_images = {} 

        # --- GIAO DIỆN CHÍNH ---
        # Khung chứa nút bấm điều khiển
        control_frame = ttk.Frame(root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_capture = ttk.Button(control_frame, text="📸 CHỤP THỬ (PREVIEW)", command=self.trigger_capture_thread)
        self.btn_capture.pack(side=tk.LEFT, padx=10)

        self.btn_save = ttk.Button(control_frame, text="💾 LƯU ẢNH VÀO PC", command=self.save_images, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Đang kiểm tra kết nối thiết bị...")
        lbl_status = ttk.Label(control_frame, textvariable=self.status_var, font=("Helvetica", 10, "italic"))
        lbl_status.pack(side=tk.RIGHT, padx=10)

        # Khung hiển thị Preview ảnh (Chia làm 2 cột Trái - Phải)
        self.preview_frame = ttk.Frame(root, padding=10)
        self.preview_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Cột Cam Trái
        self.left_frame = ttk.LabelFrame(self.preview_frame, text=" CAM TOP LEFT ")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_preview_left = ttk.Label(self.left_frame, text="Chưa có dữ liệu ảnh")
        self.lbl_preview_left.pack(expand=True)

        # Cột Cam Phải
        self.right_frame = ttk.LabelFrame(self.preview_frame, text=" CAM TOP RIGHT ")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_preview_right = ttk.Label(self.right_frame, text="Chưa có dữ liệu ảnh")
        self.lbl_preview_right.pack(expand=True)

        # Khởi chạy luồng kiểm tra phần cứng ban đầu
        Thread(target=self.check_connections, daemon=True).start()

    def check_connections(self):
        available = [name for name, path in CAMERAS.items() if os.path.exists(path)]
        if len(available) == len(CAMERAS):
            self.root.after(0, lambda: self.status_var.set("🟢 Sẵn sàng chụp ảnh."))
        else:
            missing = [k for k in CAMERAS.keys() if k not in available]
            self.root.after(0, lambda: self.status_var.set(f"🔴 Thiếu thiết bị: {', '.join(missing)}"))

    def trigger_capture_thread(self):
        self.btn_capture.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)
        self.status_var.set("⏳ Đang truyền dữ liệu ảnh từ Serial...")
        Thread(target=self.capture_and_validate, daemon=True).start()

    def capture_and_validate(self):
        success_count = 0
        self.temp_images.clear() # Reset bộ nhớ đệm ảnh cũ

        for name, path in CAMERAS.items():
            if not os.path.exists(path):
                print(f"Không tìm thấy symlink {path}")
                continue
                
            try:
                # Đặt timeout = 2 giây để chống sập / treo luồng nếu đứt cáp giữa chừng
                ser = serial.Serial(path, baudrate=115200, timeout=2.0)
                ser.flushInput()
                ser.flushOutput()
                time.sleep(0.1)
                
                ser.write(b'C') # Gửi lệnh chụp
                
                header = ser.readline().decode('utf-8', errors='ignore').strip()
                if "IMG_START:" in header:
                    try:
                        img_len = int(header.split(":")[1])
                    except (ValueError, IndexError):
                        continue
                    
                    # Đọc dữ liệu nhị phân với cơ chế bảo vệ Timeout của PySerial
                    img_data = ser.read(img_len)
                    _ = ser.readline() # Đọc nốt dòng \nIMG_END
                    
                    # --- CƠ CHẾ CHỐNG SẬP: KIỂM TRA TÍNH TOÀN VẸN FILE JPEG ---
                    if len(img_data) == img_len and img_data.startswith(b'\xff\xd8') and img_data.endswith(b'\xff\xd9'):
                        try:
                            # Thử nạp ảnh vào RAM thông qua Pillow, nếu ảnh hỏng hàm này sẽ ném lỗi ngay lập tức
                            image = Image.open(io.BytesIO(img_data))
                            image.verify() # Xác thực cấu trúc tệp nội bộ
                            
                            # Mở lại để hiển thị (vì verify() làm đóng luồng dữ liệu)
                            image = Image.open(io.BytesIO(img_data))
                            # Resize nhanh về kích thước preview phù hợp khung hình giao diện
                            image.thumbnail((320, 240))
                            
                            # Lưu vào bộ nhớ đệm tạm thời nếu hợp lệ
                            self.temp_images[name] = {
                                "raw_data": img_data,
                                "tk_image": ImageTk.PhotoImage(image)
                            }
                            success_count += 1
                        except Exception as img_err:
                            print(f"Ảnh từ {name} lỗi cấu trúc cấu phần: {img_err}")
                    else:
                        print(f"Ảnh từ {name} bị mất gói hoặc không đúng định dạng JPEG.")
                ser.close()
            except Exception as e:
                print(f"Lỗi cổng kết nối {name}: {e}")

        # Đồng bộ kết quả trả về giao diện chính
        self.root.after(0, lambda: self.update_ui_after_capture(success_count))

    def update_ui_after_capture(self, success_count):
        self.btn_capture.config(state=tk.NORMAL)
        
        # Cập nhật ảnh Preview lên khung giao diện
        if "Top Left" in self.temp_images:
            self.lbl_preview_left.config(image=self.temp_images["Top Left"]["tk_image"], text="")
        else:
            self.lbl_preview_left.config(image="", text="❌ Ảnh lỗi hoặc Cam mất kết nối")

        if "Top Right" in self.temp_images:
            self.lbl_preview_right.config(image=self.temp_images["Top Right"]["tk_image"], text="")
        else:
            self.lbl_preview_right.config(image="", text="❌ Ảnh lỗi hoặc Cam mất kết nối")

        # Xử lý trạng thái nút Lưu
        if success_count == 2:
            self.status_var.set("🟢 Ảnh hợp lệ! Nhấn 'Lưu Ảnh' để hoàn tất.")
            self.btn_save.config(state=tk.NORMAL)
            self.btn_save.focus_set() # Kích hoạt focus cho người dùng dễ ấn
        else:
            self.status_var.set(f"⚠️ Thất bại. Chỉ nhận được {success_count}/2 ảnh sạch.")
            messagebox.showwarning("Cảnh báo chất lượng", "Dữ liệu ảnh truyền về bị nhiễu hoặc hỏng. Vui lòng bấm chụp lại!")

    def save_images(self):
        if not self.temp_images:
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        try:
            for name, data in self.temp_images.items():
                cam_prefix = name.lower().replace(" ", "_")
                file_path = os.path.join(SAVE_DIR, f"{timestamp}_{cam_prefix}.jpg")
                
                with open(file_path, "wb") as f:
                    f.write(data["raw_data"])
                    
            messagebox.showinfo("Thành công", f"Đã lưu thành công 2 ảnh vào thư mục:\nDesktop/Captured_Images")
            self.btn_save.config(state=tk.DISABLED)
            self.status_var.set("🟢 Đã lưu ảnh thành công.")
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống file", f"Không thể ghi ảnh xuống ổ đĩa: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraCaptureApp(root)
    root.mainloop()