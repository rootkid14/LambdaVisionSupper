from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import urllib.request

import cv2
import numpy as np

from app.services.vision_app.models import CameraConfig


@dataclass
class CameraDevice:
    name: str
    id: str
    kind: str


class CameraController:
    """Unified camera facade for Basler/pypylon and arbitrary HTTP image endpoints.

    Basler follows the same contract as the supplied reference implementation:
    enumerate by GigE IP / serial, create InstantCamera, convert to BGR8, optionally
    set ExposureTime, then grab the latest image. HTTP cameras simply return image
    bytes from a configured GET URL; an optional focus URL template is independent.
    """

    def __init__(self, urlopen: Callable[..., Any] | None = None, pylon_module: Any | None = None) -> None:
        self._urlopen = urlopen or urllib.request.urlopen
        self._pylon = pylon_module

    def _load_pylon(self):
        if self._pylon is not None:
            return self._pylon
        try:
            from pypylon import pylon
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Basler driver requires pypylon. Install Basler pylon runtime + pypylon on this backend host."
            ) from exc
        return pylon

    def basler_scan(self) -> list[dict[str, str]]:
        pylon = self._load_pylon()
        devices: list[dict[str, str]] = []
        factory = pylon.TlFactory.GetInstance()
        for dev in factory.EnumerateDevices():
            dev_class = dev.GetDeviceClass()
            device_id = ""
            display = dev.GetFriendlyName()
            if dev_class == "BaslerGigE":
                try:
                    ip = dev.GetPropertyValue("IpAddress")
                    device_id = str(ip)
                    display = f"Basler GigE ({ip})"
                except Exception:
                    pass
            if not device_id:
                try:
                    serial = dev.GetSerialNumber()
                    device_id = str(serial)
                    display = f"Basler {dev_class} (SN:{serial})"
                except Exception:
                    pass
            if device_id:
                devices.append({"name": display, "id": device_id, "kind": str(dev_class)})
        return devices

    @staticmethod
    def _decode_image(raw: bytes) -> np.ndarray:
        if not raw:
            raise RuntimeError("Camera returned an empty response body")
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError("Camera response is not a decodable image")
        return image

    def _capture_url(self, config: CameraConfig) -> np.ndarray:
        if not config.capture_url.strip():
            raise ValueError("Camera capture URL is blank")
        request = urllib.request.Request(config.capture_url.strip(), method="GET")
        with self._urlopen(request, timeout=float(config.http_timeout_s)) as response:
            raw = response.read()
        return self._decode_image(raw)

    def _capture_basler(self, config: CameraConfig) -> np.ndarray:
        device_id = config.basler_device_id.strip()
        if not device_id:
            raise ValueError("Basler device id/IP is blank")
        pylon = self._load_pylon()
        factory = pylon.TlFactory.GetInstance()
        info = pylon.DeviceInfo()
        if "." in device_id and device_id.replace(".", "").isdigit():
            info.SetPropertyValue("IpAddress", device_id)
        else:
            info.SetPropertyValue("SerialNumber", device_id)

        camera = pylon.InstantCamera(factory.CreateDevice(info))
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        try:
            camera.Open()
            try:
                camera.ExposureTime.SetValue(float(config.exposure_us))
            except Exception:
                pass
            camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            result = camera.RetrieveResult(int(config.grab_timeout_ms), pylon.TimeoutHandling_ThrowException)
            try:
                if not result.GrabSucceeded():
                    raise RuntimeError("Basler grab did not succeed")
                image = converter.Convert(result).GetArray()
                return np.ascontiguousarray(image)
            finally:
                result.Release()
        finally:
            try:
                if camera.IsGrabbing():
                    camera.StopGrabbing()
            except Exception:
                pass
            try:
                camera.Close()
            except Exception:
                pass

    def capture(self, config: CameraConfig) -> np.ndarray:
        if config.driver == "url":
            return self._capture_url(config)
        if config.driver == "basler":
            return self._capture_basler(config)
        raise RuntimeError("Camera driver is Manual Upload. Select Basler or URL for camera capture.")

    def focus(
        self,
        config: CameraConfig,
        *,
        x: float = 0.5,
        y: float = 0.5,
        w: float = 1.0,
        h: float = 1.0,
        focal_length: float | None = None,
    ) -> dict[str, Any]:
        if config.driver != "url":
            raise RuntimeError("Focus URL is only available for URL cameras")
        template = config.focus_url_template.strip()
        if not template:
            raise ValueError("Focus URL template is blank")
        values = {
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "focal_length": "" if focal_length is None else focal_length,
        }
        try:
            url = template.format(**values)
        except KeyError as exc:
            raise ValueError(f"Unknown focus URL placeholder: {exc}") from exc
        request = urllib.request.Request(url, method="GET")
        with self._urlopen(request, timeout=float(config.http_timeout_s)) as response:
            raw = response.read()
            status = getattr(response, "status", 200)
            content_type = ""
            try:
                content_type = response.headers.get("content-type", "")
            except Exception:
                pass
        return {
            "url": url,
            "status": int(status),
            "content_type": content_type,
            "response": raw[:4096].decode("utf-8", errors="replace"),
        }
