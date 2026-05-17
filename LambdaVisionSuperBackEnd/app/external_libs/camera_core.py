import cv2
import numpy as np
import threading
import time
import sys
import os
from ctypes import *
import socket
import struct
from tkinter import messagebox

# --- SAFE IMPORTS ---
HIK_AVAILABLE = False
BASLER_AVAILABLE = False

try:
    hik_dll_path = None
    
    # A. Determine potential locations for the DLL folder
    possible_roots = []
    
    if getattr(sys, 'frozen', False):
        # 1. The folder where main.exe lives (User copied it here?)
        exe_dir = os.path.dirname(sys.executable)
        possible_roots.append(exe_dir)
        
        # 2. The _internal folder (PyInstaller default)
        internal_dir = os.path.join(exe_dir, "_internal")
        if os.path.exists(internal_dir):
            possible_roots.append(internal_dir)
    else:
        # 3. Dev Mode (Project Root)
        possible_roots.append(os.path.dirname(os.path.abspath(__file__)))

    # B. Hunt for the specific DLL directory
    target_dll_dir = None
    found_root = None
    
    for root in possible_roots:
        candidate = os.path.join(root, "MvImport", "Runtime", "x64")
        if os.path.exists(candidate):
            target_dll_dir = candidate
            found_root = root
            print(f"DEBUG: Found Hikrobot DLLs at: {target_dll_dir}")
            break
    
    if target_dll_dir:
        # C. FORCE Windows to see this directory
        # Method 1: Python 3.8+ Safe DLL Add
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(target_dll_dir)
            
        # Method 2: Environment Path (Legacy)
        os.environ["PATH"] = target_dll_dir + os.pathsep + os.environ["PATH"]
        
        # Method 3: Direct Pre-Load (The "Silver Bullet")
        try:
            dll_file = os.path.join(target_dll_dir, "MvCameraControl.dll")
            ctypes.cdll.LoadLibrary(dll_file)
        except Exception as e:
            print(f"DEBUG: Direct DLL load warning: {e}")

        # D. Fix Python Import Path
        # We must ensure Python can find the 'MvImport' package folder
        if found_root and found_root not in sys.path:
            sys.path.append(found_root)

        # E. Perform the Import
        from MvImport.MvCameraControl_class import *
        HIK_AVAILABLE = True
        print("DEBUG: Hikrobot SDK imported successfully")
        
    else:
        print("DEBUG: Could not find 'MvImport/Runtime/x64' in any expected location.")

except ImportError:
    messagebox.showerror(title="HIK SDK error", message="MVImport failure")
    pass 
except Exception as e:
    print(f"Hikrobot SDK Critical Fail: {e}")
    pass

# Try Import Basler
try:
    from pypylon import pylon
    BASLER_AVAILABLE = True
except ImportError:
    pass

# ==========================================
# BASE INTERFACE
# ==========================================
class CameraInterface:
    def __init__(self, ip_address=None):
        self.is_connected = False
        self.is_grabbing = False
        self.callback = None
        self.thread = None
        self.ip_address = ip_address  # This is now the TARGET IP (String)

    def connect(self): raise NotImplementedError
    def disconnect(self): 
        self.stop_stream()
        self.is_connected = False
    def start_stream(self, callback_func): raise NotImplementedError
    def stop_stream(self): raise NotImplementedError
    def snap(self): raise NotImplementedError
    
    @staticmethod
    def scan(): return []

    def set_exposure(self, value_us): 
        """Sets exposure time in microseconds"""
        pass

# ==========================================
# 1. HIKROBOT IMPLEMENTATION (Hybrid: IP + USB)
# ==========================================
# ==========================================
# 1. HIKROBOT IMPLEMENTATION (Hybrid: IP + USB)
# ==========================================
# ==========================================
# 1. HIKROBOT IMPLEMENTATION (Hybrid: IP + USB)
# ==========================================
class HikRobotCamera(CameraInterface):
    def __init__(self, ip_address=None):
        super().__init__(ip_address)
        self.cam = None
        self.pData = None
        self.buf_size = 0
        self.stFrameInfo = None

    @staticmethod
    def _int_to_ip(int_ip):
        """Helper: Converts Hikrobot 32-bit int IP to '192.168.x.x' string"""
        return socket.inet_ntoa(struct.pack('!L', int_ip))

    @staticmethod
    def _decode_sn(ch_serial_number):
        """Helper: Decodes the C-type char array from USB devices"""
        try:
            # chSerialNumber is a c_ubyte array or similar in ctypes
            chars = []
            for c in ch_serial_number:
                if c == 0: break
                chars.append(chr(c))
            return "".join(chars)
        except:
            return "Unknown_SN"

    @staticmethod
    def scan():
        """Returns list of IPs (GigE) or Serial Numbers (USB)"""
        if not HIK_AVAILABLE: return []
        
        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        results = []
        
        if ret == 0:
            for i in range(deviceList.nDeviceNum):
                # 1. Dereference the pointer to get the actual Structure
                device = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
                
                # Strategy A: GigE Camera -> Use IP
                if device.nTLayerType == MV_GIGE_DEVICE:
                    # FIX: Use 'SpecialInfo' (not pSpecialInfo) and access Union directly
                    ip_int = device.SpecialInfo.stGigEInfo.nCurrentIp
                    ip_str = HikRobotCamera._int_to_ip(ip_int)
                    results.append({"name": f"Hikrobot GigE ({ip_str})", "id": ip_str})
                
                # Strategy B: USB Camera -> Use Serial Number
                elif device.nTLayerType == MV_USB_DEVICE:
                    # FIX: Use 'SpecialInfo' (not pSpecialInfo)
                    raw_sn = device.SpecialInfo.stUsb3VInfo.chSerialNumber
                    sn = HikRobotCamera._decode_sn(raw_sn)
                    results.append({"name": f"Hikrobot USB ({sn})", "id": sn})
                    
        return results

    def connect(self):
        if not HIK_AVAILABLE: raise RuntimeError("Hikrobot SDK missing.")
        
        # 1. Scan All Devices
        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        
        target_device = None
        target_id = str(self.ip_address).strip()
        
        # 2. Find Match
        for i in range(deviceList.nDeviceNum):
            device = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            is_match = False
            
            # Check GigE IP
            if device.nTLayerType == MV_GIGE_DEVICE:
                ip_int = device.SpecialInfo.stGigEInfo.nCurrentIp
                current_ip = self._int_to_ip(ip_int)
                if current_ip == target_id: is_match = True
            
            # Check USB Serial
            elif device.nTLayerType == MV_USB_DEVICE:
                raw_sn = device.SpecialInfo.stUsb3VInfo.chSerialNumber
                sn = self._decode_sn(raw_sn)
                if sn == target_id: is_match = True
            
            if is_match:
                target_device = device
                break
        
        if not target_device:
            raise RuntimeError(f"Hikrobot Camera with ID {target_id} not found.")

        # 3. Create Handle & Open
        self.cam = MvCamera()
        # Must pass the original structure (target_device) to CreateHandle
        ret = self.cam.MV_CC_CreateHandle(target_device)
        if ret != 0: raise RuntimeError(f"Hik CreateHandle failed: {hex(ret)}")

        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0: raise RuntimeError(f"Hik OpenDevice failed: {hex(ret)}")

        # 4. Config (Safe Try/Except)
        try: 
            self.cam.MV_CC_SetEnumValue("TriggerMode", 1)    
            self.cam.MV_CC_SetEnumValue("TriggerSource", 7)  
        except: pass
        
        # Buffer Allocation
        self.buf_size = 30 * 1024 * 1024 
        self.pData = (c_ubyte * self.buf_size)()
        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()
        
        self.is_connected = True
        return True

    def set_exposure(self, value_us):
        if self.is_connected: 
            ret = self.cam.MV_CC_SetFloatValue("ExposureTime", float(value_us))

    def start_stream(self, callback_func):
        if not self.is_connected: return
        self.cam.MV_CC_SetEnumValue("TriggerMode", 0) 
        self.callback = callback_func
        self.is_grabbing = True
        ret = self.cam.MV_CC_StartGrabbing()
        if ret != 0: raise RuntimeError(f"Hik StartGrabbing failed: {hex(ret)}")
        self.thread = threading.Thread(target=self._run_thread, daemon=True)
        self.thread.start()

    def _run_thread(self):
        while self.is_grabbing:
            ret = self.cam.MV_CC_GetOneFrameTimeout(self.pData, self.buf_size, self.stFrameInfo, 1000)
            if ret == 0:
                h, w = self.stFrameInfo.nHeight, self.stFrameInfo.nWidth
                data = np.frombuffer(self.pData, count=int(self.stFrameInfo.nFrameLen), dtype=np.uint8)
                
                if self.stFrameInfo.enPixelType == PixelType_Gvsp_Mono8:
                    img = data.reshape((h, w))
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                else:
                    try: img = data.reshape((h, w, 3)) 
                    except: 
                        img = data.reshape((h, w))
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                
                if self.callback: self.callback(img)

    def stop_stream(self):
        self.is_grabbing = False
        if self.cam: self.cam.MV_CC_StopGrabbing()

    def snap(self):
        if not self.is_connected: return None
        self.cam.MV_CC_SetEnumValue("TriggerMode", 1) 
        self.cam.MV_CC_SetEnumValue("TriggerSource", 7)
        self.cam.MV_CC_StartGrabbing()
        self.cam.MV_CC_SetCommandValue("TriggerSoftware")
        
        ret = self.cam.MV_CC_GetOneFrameTimeout(self.pData, self.buf_size, self.stFrameInfo, 1000)
        img = None
        if ret == 0:
            h, w = self.stFrameInfo.nHeight, self.stFrameInfo.nWidth
            data = np.frombuffer(self.pData, count=int(self.stFrameInfo.nFrameLen), dtype=np.uint8)
            
            if self.stFrameInfo.enPixelType == PixelType_Gvsp_Mono8:
                img = data.reshape((h, w))
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                try: img = data.reshape((h, w, 3)) 
                except: 
                    img = data.reshape((h, w))
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    
        self.cam.MV_CC_StopGrabbing()
        return img

    def disconnect(self):
        self.stop_stream()
        if self.cam:
            self.cam.MV_CC_CloseDevice()
            self.cam.MV_CC_DestroyHandle()
        self.is_connected = False

# ==========================================
# 2. BASLER IMPLEMENTATION
# ==========================================
class BaslerCamera(CameraInterface):
    def __init__(self, ip_address=None):
        # Note: 'ip_address' here is treated as a generic 'device_id' (IP or Serial)
        super().__init__(ip_address)
        self.cam = None
        self.converter = None

    @staticmethod
    def scan():
        if not BASLER_AVAILABLE: return []
        devices = []
        try:
            tl_factory = pylon.TlFactory.GetInstance()
            for dev in tl_factory.EnumerateDevices():
                # --- FIX 1: Support Both GigE and USB ---
                friendly_name = dev.GetFriendlyName()
                dev_class = dev.GetDeviceClass()
                
                device_id = None
                display_name = friendly_name

                # Strategy A: It's a GigE Camera -> Use IP
                if dev_class == "BaslerGigE":
                    try:
                        ip = dev.GetPropertyValue("IpAddress")
                        device_id = ip
                        display_name = f"Basler GigE ({ip})"
                    except: pass
                
                # Strategy B: It's a USB Camera -> Use Serial Number
                # (Fallback for GigE if IP fetch fails, or native USB)
                if not device_id:
                    try:
                        sn = dev.GetSerialNumber()
                        device_id = sn
                        display_name = f"Basler {dev_class} (SN:{sn})"
                    except: pass

                if device_id:
                    devices.append({"name": display_name, "id": device_id})

        except Exception as e:
            print(f"Basler Scan Error: {e}")
            pass
        return devices

    def connect(self):
        if not BASLER_AVAILABLE: raise RuntimeError("Basler SDK missing.")
        
        try:
            tl_factory = pylon.TlFactory.GetInstance()
            di = pylon.DeviceInfo()
            
            # --- FIX 2: Hybrid Connection Logic ---
            target_id = str(self.ip_address).strip()
            
            if "." in target_id and target_id.replace(".", "").isdigit():
                # It looks like an IP Address (e.g., 192.168.1.10)
                di.SetPropertyValue("IpAddress", target_id)
                # print(f"Connecting Basler via IP: {target_id}")
            else:
                # Treat as Serial Number (e.g., 24765123)
                di.SetPropertyValue("SerialNumber", target_id)
                # print(f"Connecting Basler via Serial: {target_id}")

            # Create specific device
            self.cam = pylon.InstantCamera(tl_factory.CreateDevice(di))
            self.cam.Open()
            
        except Exception as e:
            raise RuntimeError(f"Basler Connect Error ({self.ip_address}): {e}")

        # Setup Converter
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        
        self.is_connected = True
        return True
    
    def set_exposure(self, value_us):
        if self.is_connected:
            try: self.cam.ExposureTime.SetValue(float(value_us))
            except: pass

    def start_stream(self, callback_func):
        if not self.is_connected: return
        self.callback = callback_func
        self.is_grabbing = True
        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        self.thread = threading.Thread(target=self._run_thread, daemon=True)
        self.thread.start()

    def _run_thread(self):
        while self.is_grabbing and self.cam.IsGrabbing():
            grabResult = self.cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                image = self.converter.Convert(grabResult)
                img = image.GetArray()
                if self.callback: self.callback(img)
            grabResult.Release()

    def stop_stream(self):
        self.is_grabbing = False
        if self.cam: self.cam.StopGrabbing()

    def snap(self):
        if not self.is_connected: return None
        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        res = self.cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        img = None
        if res.GrabSucceeded():
            image = self.converter.Convert(res)
            img = image.GetArray()
        res.Release()
        self.cam.StopGrabbing()
        return img

    def disconnect(self):
        self.stop_stream()
        if self.cam: self.cam.Close()
        self.is_connected = False

# 