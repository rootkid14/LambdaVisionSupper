import serial
import cv2
import numpy as np
import time
import os

# ================= CONFIGURATION =================
PORTS = {
    "CAM_1": "/dev/ttyACM0",
    "CAM_2": "/dev/ttyACM1"
}
BAUD = 2000000
BASE_SAVE_DIR = "/home/hieu/Desktop/TE_Data/testcam"  # Base directory to store all images

def init_camera(port_name, baud):
    """Initialize Serial port for Camera"""
    try:
        ser = serial.Serial()
        ser.port = port_name
        ser.baudrate = baud
        ser.timeout = 2.0
        
        # Enable DTR/RTS for Native USB (ttyACM) to establish connection
        ser.dtr = True
        ser.rts = True
        
        ser.open()
        return ser
    except Exception as e:
        print(f"[!] Connection error on {port_name}: {e}")
        return None

def capture_and_save(ser, cam_label, save_dir):
    """Send command, receive image, and save to disk"""
    if ser is None or not ser.is_open:
        print(f"[!] {cam_label}: Port is not open, skipping capture.")
        return False

    try:
        # Clear buffer before sending new command
        ser.reset_input_buffer()
        
        # 1. Send 'C' command
        ser.write(b'C')
        ser.flush()

        # 2. Wait for Header (Timeout 2s)
        img_len = 0
        start_time = time.time()
        
        while (time.time() - start_time) < 2.0:
            line_bytes = ser.readline()
            if not line_bytes: continue
            
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            if line.startswith("IMG_START:"):
                img_len = int(line.split(":")[1])
                break

        if img_len <= 0:
            print(f"[!] {cam_label}: Timeout, no response from ESP32.")
            return False

        # 3. Read binary data
        img_data = ser.read(img_len)
        
        # 4. Read footer to clear buffer
        ser.readline() 

        # 5. Decode and save image
        if len(img_data) == img_len:
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is not None:
                # Create unique filename using timestamp
                timestamp = str(int(time.time() * 1000))
                filename = f"{cam_label}_{timestamp}.jpg"
                filepath = os.path.join(save_dir, filename)
                
                # Save file
                cv2.imwrite(filepath, img)
                print(f"[+] {cam_label}: Capture successful -> {filename}")
                return True
            else:
                print(f"[!] {cam_label}: JPEG decode error.")
                return False
        else:
            print(f"[!] {cam_label}: Packet loss ({len(img_data)}/{img_len} bytes).")
            return False

    except Exception as e:
        print(f"[!] {cam_label}: Error during capture: {e}")
        return False

def main():
    # 1. Create base directory and specific camera directories
    os.makedirs(BASE_SAVE_DIR, exist_ok=True)
    print(f"[*] Base directory for images: {os.path.abspath(BASE_SAVE_DIR)}")
    
    cam_dirs = {}
    for cam_label in PORTS.keys():
        cam_dir = os.path.join(BASE_SAVE_DIR, cam_label)
        os.makedirs(cam_dir, exist_ok=True)
        cam_dirs[cam_label] = cam_dir

    # 2. Initialize connections for all cameras
    print("[*] Initializing camera connections...")
    active_cameras = {}
    
    for cam_label, port_name in PORTS.items():
        ser = init_camera(port_name, BAUD)
        if ser:
            active_cameras[cam_label] = ser
            print(f"  -> Connected to {cam_label} ({port_name})")

    if not active_cameras:
        print("[!] Could not connect to any camera. Please check cables and permissions (chmod).")
        return

    # 3. Wait for ESP32 to boot up (only wait once)
    print("[*] Waiting for ESP32 boards to boot up (2s)...")
    time.sleep(2.0)
    
    for ser in active_cameras.values():
        ser.reset_input_buffer()
        ser.reset_output_buffer()

    print("\n" + "="*40)
    print("SYSTEM IS READY!")
    print(" - Press [ENTER] to capture from all cameras.")
    print(" - Type 'q' and press [ENTER] to exit the program.")
    print("="*40 + "\n")

    # 4. User input loop
    try:
        while True:
            cmd = input("Your command: ").strip().lower()
            
            if cmd == 'q':
                break
                
            # If just Enter (empty string), proceed to capture
            if cmd == '':
                print("\n[*] Capturing images...")
                for cam_label, ser in active_cameras.items():
                    # Pass the specific directory for this camera
                    capture_and_save(ser, cam_label, cam_dirs[cam_label])
                print("[*] Capture cycle complete!\n")
            else:
                print("[!] Invalid command.")

    except KeyboardInterrupt:
        print("\n[*] Force quitting program...")

    finally:
        # 5. Safely close ports
        print("\n[*] Closing connections...")
        for cam_label, ser in active_cameras.items():
            if ser and ser.is_open:
                ser.close()
                print(f"  -> Closed {cam_label}")
        print("[*] Goodbye!")

if __name__ == '__main__':
    main()