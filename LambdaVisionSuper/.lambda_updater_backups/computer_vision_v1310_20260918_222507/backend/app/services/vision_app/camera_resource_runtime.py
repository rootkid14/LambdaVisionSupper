from __future__ import annotations

import json
from typing import Any, Callable
from urllib.parse import urlencode
import urllib.request

import cv2
import numpy as np

from app.services.vision_app.camera_runtime import CameraController
from app.services.vision_app.frame_slot_store import VISION_FRAME_SLOTS
from app.services.vision_app.models import CameraCustomApi, CameraDeclaration, CameraConfig


class CameraResourceController:
    """Driver-neutral declared-camera runtime.

    Capture writes to the declaration's image slot. "Streaming" in v0.13 is an
    engineering state + polling contract; the UI repeatedly requests a stream frame.
    This intentionally avoids committing to a push/high-FPS transport before the
    future soft-trigger design is settled.
    """

    def __init__(self, legacy: CameraController | None = None, urlopen: Callable[..., Any] | None = None) -> None:
        self.legacy = legacy or CameraController()
        self._urlopen = urlopen or urllib.request.urlopen

    @staticmethod
    def _legacy_config(camera: CameraDeclaration) -> CameraConfig:
        if camera.driver == 'basler':
            return CameraConfig(
                enabled=camera.enabled,
                driver='basler',
                basler_device_id=camera.basler_device_id,
                exposure_us=camera.exposure_us,
                grab_timeout_ms=camera.grab_timeout_ms,
            )
        if camera.driver == 'http':
            base = f"http://{camera.host}:{camera.port}"
            return CameraConfig(
                enabled=camera.enabled,
                driver='url',
                capture_url=base + camera.capture_path,
                http_timeout_s=camera.http_timeout_s,
            )
        return CameraConfig(enabled=False, driver='manual')

    @staticmethod
    def camera_alias(camera: CameraDeclaration) -> str:
        from app.services.vision_app.endpoint_registry import safe_alias
        return safe_alias(camera.alias, camera.declaration_id)

    def image_slot_path(self, camera: CameraDeclaration) -> str:
        return f"camera.{self.camera_alias(camera)}.{camera.image_slot}"

    def stream_slot_path(self, camera: CameraDeclaration) -> str:
        return f"camera.{self.camera_alias(camera)}.{camera.stream_slot}"

    def capture(self, program_id: str, camera: CameraDeclaration) -> np.ndarray:
        if not camera.enabled:
            raise RuntimeError(f"Camera is disabled: {camera.alias}")
        if camera.driver == 'simulated':
            # Simulator writes its source directly into the same slot. Capture means
            # snapshot the current simulated stream/source frame into Current_image.
            stream_path = self.stream_slot_path(camera)
            image_path = self.image_slot_path(camera)
            if VISION_FRAME_SLOTS.has(program_id, stream_path):
                image = VISION_FRAME_SLOTS.get(program_id, stream_path)
                VISION_FRAME_SLOTS.put(program_id, image_path, image)
                return image
            if VISION_FRAME_SLOTS.has(program_id, image_path):
                return VISION_FRAME_SLOTS.get(program_id, image_path)
            raise FileNotFoundError(f"Simulated camera has no uploaded frame: {camera.alias}")
        image = self.legacy.capture(self._legacy_config(camera))
        VISION_FRAME_SLOTS.put(program_id, self.image_slot_path(camera), image)
        return image

    def stream_frame(self, program_id: str, camera: CameraDeclaration) -> np.ndarray:
        if camera.driver == 'simulated':
            stream = self.stream_slot_path(camera)
            if VISION_FRAME_SLOTS.has(program_id, stream):
                return VISION_FRAME_SLOTS.get(program_id, stream)
            return self.capture(program_id, camera)
        # v0.13 engineering stream preview: one fresh frame per poll.
        image = self.legacy.capture(self._legacy_config(camera))
        VISION_FRAME_SLOTS.put(program_id, self.stream_slot_path(camera), image)
        return image

    def set_exposure(self, camera: CameraDeclaration, value: float) -> None:
        camera.exposure_us = float(value)

    def call_custom(self, camera: CameraDeclaration, api: CameraCustomApi, args: dict[str, Any]) -> dict[str, Any]:
        if camera.driver != 'http':
            raise RuntimeError('Custom APIs are only available for HTTP cameras')
        values = {p.name: args.get(p.name, p.default) for p in api.parameters}
        try:
            path = api.path_template.format(**values)
        except KeyError as exc:
            raise ValueError(f"Missing custom camera API parameter: {exc}") from exc
        url = f"http://{camera.host}:{camera.port}{path}"
        data = None
        headers = {}
        if api.method == 'POST':
            data = json.dumps(values).encode('utf-8')
            headers['content-type'] = 'application/json'
        request = urllib.request.Request(url, method=api.method, data=data, headers=headers)
        with self._urlopen(request, timeout=float(camera.http_timeout_s)) as response:
            raw = response.read()
            status = int(getattr(response, 'status', 200))
        return {'status': status, 'url': url, 'response': raw[:8192].decode('utf-8', errors='replace')}

    def start_stream(self, program_id: str, camera: CameraDeclaration) -> None:
        VISION_FRAME_SLOTS.set_streaming(program_id, self.camera_alias(camera), True)

    def stop_stream(self, program_id: str, camera: CameraDeclaration) -> None:
        VISION_FRAME_SLOTS.set_streaming(program_id, self.camera_alias(camera), False)
