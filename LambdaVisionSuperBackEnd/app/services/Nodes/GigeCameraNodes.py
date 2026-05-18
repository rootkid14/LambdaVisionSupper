# import asyncio
# import numpy as np
# from typing import Dict, List
# from pydantic import BaseModel, Field, ConfigDict
# from typing import Any, Optional
# from app.services.node_registry import BaseNode, registry_node
# from app.services.LVSTypes import NodeType, UIDataType, UIConfigField, UIConfigType
# from app.external_libs.MvImport.MvCameraControl_class import *
# from ctypes import *
# import sys
# import os
# import pypylon.pylon as pylon
# import threading
# from app.services.utils.image_utils import cv2_to_base64
# import time

# class BaslerCameraManager:
#     _instance = None
#     _locks = {}  # Chỉ lưu Lock để xếp hàng các luồng, không lưu Camera Handle nữa
#     _global_lock = threading.Lock() 

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(BaslerCameraManager, cls).__new__(cls)
#         return cls._instance
    
#     def _get_lock(self, serial_number: str):
#         """Mỗi Serial Number có một cái cờ (Lock) để tránh 2 node gọi mở cam cùng lúc"""
#         with self._global_lock:
#             if serial_number not in self._locks:
#                 self._locks[serial_number] = threading.Lock()
#             return self._locks[serial_number]
    
#     def get_image(self, serial_number: str, timeout_ms: int = 5000, exposure_us: float = 50000.0) -> np.ndarray:
#         # Bỏ qua exposure_us do Node truyền vào, ép cứng 50000 theo yêu cầu
        
#         cam_lock = self._get_lock(serial_number)

#         with cam_lock:
#             cam = None
#             try:
#                 # 1. TẠO MỚI HANDLE TỪ SỐ 0
#                 info = pylon.DeviceInfo()
#                 info.SetPropertyValue('SerialNumber', serial_number)
#                 cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice(info))

#                 # 2. MỞ KẾT NỐI USB/MẠNG
#                 cam.Open()

#                 # 3. ÉP CỨNG EXPOSURE (Vì vừa Open, 100% phần cứng đang ở trạng thái cho phép ghi)
#                 try: cam.ExposureAuto.SetValue("Off")
#                 except: pass
                
#                 try: cam.ExposureTime.SetValue(exposure_us)
#                 except: 
#                     try: cam.ExposureTimeAbs.SetValue(exposure_us)
#                     except: pass

#                 # Tắt Trigger để GrabOne hoạt động mượt nhất
#                 try: cam.TriggerMode.SetValue("Off")
#                 except: pass

#                 # 4. CHỤP ĐÚNG 1 TẤM ẢNH BẰNG LỆNH CHUYÊN DỤNG (GRAB ONE)
#                 # Lệnh này tự Start -> Đợi Ảnh -> Stop cực kỳ sạch sẽ
#                 res = cam.GrabOne(timeout_ms)
#                 img = None
                
#                 if res.GrabSucceeded():
#                     img = res.GetArray().copy()
#                 res.Release()

#                 if img is None:
#                     raise TimeoutError(f"Camera {serial_number} lấy ảnh thất bại.")

#                 return img
            
#             except Exception as e:
#                 print(f"[Basler Error] Lỗi vòng đời 1-Shot: {e}")
#                 raise RuntimeError(str(e))
                
#             finally:
#                 # 5. GIẢI PHÓNG TOÀN BỘ PHẦN CỨNG (Quan trọng nhất)
#                 # Cho dù có lỗi đứt cáp hay chụp thành công, Block 'finally' luôn chạy
#                 # Đảm bảo camera được Close và nhả RAM hoàn toàn.
#                 if cam is not None and cam.IsOpen():
#                     try: cam.Close()
#                     except: pass

#     # Hai hàm release bên dưới hiện tại chỉ để trống (pass) để không làm vỡ logic 
#     # của các class Node khác đang gọi đến nó. Bản thân kiến trúc này không cần 
#     # release thủ công vì nó tự dọn dẹp ở Block finally phía trên rồi.
#     def release_one(self, serial_number: str):
#         pass

#     def _release_all(self):
#         """Bảo hiểm cuối cùng: Được gọi khi tắt/reload Server"""
#         with self._global_lock:
#             for serial, context in self._cameras.items():
#                 cam = context.get("active_cam")
                
#                 # Nếu lúc tắt server mà vẫn có camera đang chụp dở (khác None) -> Ép đóng!
#                 if cam is not None:
#                     try:
#                         if cam.IsOpen(): cam.Close()
#                         print(f"[Basler Info] Đã ép đóng an toàn camera {serial} do server tắt.")
#                     except: pass
#                 context["active_cam"] = None

# class CameraInput(BaseModel):
#     model_config = ConfigDict(arbitrary_types_allowed=True)
#     execute_in : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
#     cam_ip : str = Field(default="", title="Camera IP", description=UIDataType.STRING.value)
#     exposure : float = Field(default=40000, title="Exposure", description=UIDataType.NUMBER.value)

# class CameraOutput(BaseModel):
#     model_config = ConfigDict(arbitrary_types_allowed=True)
#     execute_out : Any = Field(default="GO", title="Execute", description=UIDataType.EXECUTE.value)
#     image: Any = Field(default=None, title="Output Image", description=UIDataType.ANY.value)

# @registry_node
# class BaslerCameraNode(BaseNode[CameraInput, CameraOutput]):
#     INPUT_SCHEMA = CameraInput
#     OUTPUT_SCHEMA = CameraOutput
#     NODE_TYPE = NodeType.PROGRAM
#     UI_LABEL = "Basler GigE"
#     UI_DESCRIPTION = "Control Basler Camera"
#     UI_COLOR = "#005a9e"
#     REQUIRE_TIMEOUT = 5.0

#     CONFIG_FIELDS = [
#         UIConfigField(
#             id="output_format",
#             label="Image Output Format",
#             type=UIConfigType.SELECT,
#             options=["Base64", "NumpyArray"],
#             default="Base64"
#         )
#     ]
#     def __init__(self, node_id, parent, node_data = None):
#         super().__init__(node_id, parent, node_data)
#         self.cam = None
#         self.output_format = self.get_config_field_value("output_format")
        
#     async def execute(self):
#         manager = BaslerCameraManager()

#         try:
#             # Use a seperate thread to avoid blocking the system
#             img = await asyncio.to_thread(manager.get_image, self.local_input.cam_ip, 5000, self.local_input.exposure)

#             if (self.output_format == "Base64"):
#                 img = cv2_to_base64(img)

#             self.local_output = self.OUTPUT_SCHEMA(image=img)        
#         except Exception as e:
#             manager.release_one(self.local_input.cam_ip)
#             raise RuntimeError(str(e))

        
# # ==========================================
# # HIKROBOT MANAGER & NODE
# # ==========================================

# class HikCameraManager:
#     _instance = None
#     _cameras = {}  # Format: {"ip": {"lock": threading.Lock(), "cam": instance}}
#     _global_lock = threading.Lock()

#     def __new__(cls):
#         with cls._global_lock: # Thêm lock ở đây để an toàn tuyệt đối khi tạo Singleton
#             if cls._instance is None:
#                 cls._instance = super(HikCameraManager, cls).__new__(cls)
#         return cls._instance

#     def _get_camera_context(self, ip_address: str) -> dict:
#         with self._global_lock:
#             if ip_address not in self._cameras:
#                 self._cameras[ip_address] = {
#                     "lock": threading.Lock(),
#                     "cam": None
#                 }
#             return self._cameras[ip_address]

#     def _init_camera_unsafe(self, ip_address: str, cam_dict: dict) -> None:
#         cam = cam_dict["cam"]
        
#         # 1. Kiểm tra nếu camera đã sống
#         if cam is not None:
#             # Hikrobot SDK API trả về bool cho hàm IsDeviceConnected
#             if cam.MV_CC_IsDeviceConnected():
#                 return
#             else:
#                 try:
#                     cam.MV_CC_StopGrabbing()
#                     cam.MV_CC_CloseDevice()
#                     cam.MV_CC_DestroyHandle()
#                 except: pass

#         # 2. Khởi tạo mới
#         new_cam = MvCamera()
#         deviceList = MV_CC_DEVICE_INFO_LIST()
#         ret = new_cam.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)
        
#         if ret != 0 or deviceList.nDeviceNum == 0:
#             raise ConnectionError("Không tìm thấy Camera Hikrobot nào trên mạng LAN.")

#         target_device = None
#         for i in range(deviceList.nDeviceNum):
#             mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
#             nip = mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp
#             ip_str = f"{(nip >> 24) & 255}.{(nip >> 16) & 255}.{(nip >> 8) & 255}.{nip & 255}"
            
#             if ip_str == ip_address:
#                 target_device = mvcc_dev_info
#                 break

#         if not target_device:
#             raise ConnectionError(f"Không tìm thấy Hikrobot với IP: {ip_address}")

#         ret = new_cam.MV_CC_CreateHandle(target_device)
#         if ret != 0: raise ConnectionError(f"Tạo Handle thất bại. Mã lỗi: {ret}")

#         ret = new_cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
#         if ret != 0: raise ConnectionError(f"Mở Camera thất bại. Mã lỗi: {ret}")

#         new_cam.MV_CC_SetEnumValue("TriggerMode", 1)
#         new_cam.MV_CC_SetEnumValue("TriggerSource", 7)
#         new_cam.MV_CC_StartGrabbing()

#         cam_dict["cam"] = new_cam

#     def get_image(self, ip_address: str, timeout_ms: int = 5000, exposure_us: float = 10000.0) -> np.ndarray:
#         cam_dict = self._get_camera_context(ip_address)

#         with cam_dict["lock"]:
#             self._init_camera_unsafe(ip_address, cam_dict)
#             cam = cam_dict["cam"]

#             # --- THÊM SET EXPOSURE Ở ĐÂY ---
#             # Tắt Auto Exposure (0 = Off)
#             cam.MV_CC_SetEnumValue("ExposureAuto", 0)
#             # Set giá trị thời gian phơi sáng
#             ret = cam.MV_CC_SetFloatValue("ExposureTime", float(exposure_us))
#             if ret != 0:
#                 print(f"[Hikrobot] Cảnh báo không thể set Exposure cho {ip_address}. Mã lỗi: {ret}")

#             # Phát lệnh chụp
#             ret = cam.MV_CC_SetCommandValue("TriggerSoftware")
#             if ret != 0: 
#                 raise RuntimeError(f"Gửi lệnh kích hoạt thất bại. Mã lỗi: {ret}")

#             # Đón ảnh về
#             stOutFrame = MV_FRAME_OUT()
#             ret = cam.MV_CC_GetImageBuffer(stOutFrame, timeout_ms)
#             if ret != 0:
#                 raise TimeoutError(f"Timeout khi kéo ảnh Hikrobot {ip_address} (Lỗi {ret})")

#             pData = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen).from_address(addressof(stOutFrame.pBufAddr.contents))
#             temp_array = np.frombuffer(pData, count=int(stOutFrame.stFrameInfo.nFrameLen), dtype=np.uint8)

#             w = stOutFrame.stFrameInfo.nWidth
#             h = stOutFrame.stFrameInfo.nHeight

#             if stOutFrame.stFrameInfo.nFrameLen == w * h * 3:
#                 img = temp_array.reshape((h, w, 3)).copy() 
#             else:
#                 img = temp_array.reshape((h, w)).copy()    

#             cam.MV_CC_FreeImageBuffer(stOutFrame)

#             return img

#     def release_one(self, ip_address: str):
#         cam_dict = None
#         with self._global_lock:
#             if ip_address in self._cameras:
#                 cam_dict = self._cameras.pop(ip_address)

#         if cam_dict:
#             with cam_dict["lock"]:
#                 cam = cam_dict["cam"]
#                 if cam:
#                     try:
#                         cam.MV_CC_StopGrabbing()
#                         cam.MV_CC_CloseDevice()
#                         cam.MV_CC_DestroyHandle()
#                     except: pass


# # ----------------------------------------
# # HIKROBOT NODE
# # ----------------------------------------
# @registry_node
# class HikrobotCameraNode(BaseNode[CameraInput, CameraOutput]):
#     INPUT_SCHEMA = CameraInput  # Dùng chung Schema với Basler
#     OUTPUT_SCHEMA = CameraOutput
#     NODE_TYPE = NodeType.PROGRAM
#     UI_LABEL = "Hikrobot GigE"
#     UI_DESCRIPTION = "Control Hikrobot Camera via MVS SDK"
#     UI_COLOR = "#d32f2f" # Màu đỏ cho dễ phân biệt với màu xanh của Basler
#     REQUIRE_TIMEOUT = 5.0

#     CONFIG_FIELDS = [
#         UIConfigField(
#             id="output_format",
#             label="Image Output Format",
#             type=UIConfigType.SELECT,
#             options=["Base64", "NumpyArray"],
#             default="Base64"
#         )
#     ]

#     def __init__(self, node_id, parent, node_data=None):
#         super().__init__(node_id, parent, node_data)
#         self.output_format = self.get_config_field_value("output_format")
        
#     async def execute(self):
#         manager = HikCameraManager()

#         try:
#             # Đẩy vào Thread Pool
#             img = await asyncio.to_thread(manager.get_image, self.local_input.cam_ip, 5000, self.local_input.exposure)

#             if self.output_format == "Base64":
#                 img = cv2_to_base64(img)

#             self.local_output = self.OUTPUT_SCHEMA(image=img)        
#         except Exception as e:
#             # Nếu có lỗi (VD: đứt mạng ngang chừng), giải phóng để lần chạy sau Node có thể kết nối lại
#             manager.release_one(self.local_input.cam_ip)
#             raise RuntimeError(str(e))