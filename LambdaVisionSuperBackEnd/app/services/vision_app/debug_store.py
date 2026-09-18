from __future__ import annotations

from collections import OrderedDict
from threading import RLock
import uuid

import cv2
import numpy as np

from app.services.vision_app.models import DebugImageRef


class VisionDebugStore:
    def __init__(self, max_runs: int = 24) -> None:
        self.max_runs = max(4, int(max_runs))
        self._lock = RLock()
        self._runs: OrderedDict[str, dict[str, bytes]] = OrderedDict()
        self._refs: dict[str, list[DebugImageRef]] = {}

    @staticmethod
    def _as_preview(image: np.ndarray) -> np.ndarray:
        array = np.asarray(image)
        if array.dtype == bool:
            array = array.astype(np.uint8) * 255
        if array.dtype != np.uint8:
            finite = np.nan_to_num(array.astype(np.float32))
            low, high = float(np.min(finite)), float(np.max(finite))
            if high > low:
                finite = (finite - low) * (255.0 / (high - low))
            array = np.clip(finite, 0, 255).astype(np.uint8)
        if array.ndim == 2:
            return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
        if array.ndim == 3 and array.shape[2] == 1:
            return cv2.cvtColor(array[:, :, 0], cv2.COLOR_GRAY2BGR)
        return np.ascontiguousarray(array[:, :, :3])

    @staticmethod
    def _encode(image: np.ndarray) -> bytes:
        preview = VisionDebugStore._as_preview(image)
        ok, encoded = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            raise RuntimeError("Could not encode debug image")
        return encoded.tobytes()

    def new_run(self) -> str:
        run_id = f"vision_{uuid.uuid4().hex}"
        with self._lock:
            self._runs[run_id] = {}
            self._refs[run_id] = []
            while len(self._runs) > self.max_runs:
                old, _ = self._runs.popitem(last=False)
                self._refs.pop(old, None)
        return run_id

    def put(self, run_id: str, key: str, image: np.ndarray, *, label: str, scope: str, phase: str) -> DebugImageRef:
        safe_key = key.replace("/", "_").replace(" ", "_")
        ref = DebugImageRef(key=safe_key, label=label, scope=scope, phase=phase)
        with self._lock:
            if run_id not in self._runs:
                self._runs[run_id] = {}
                self._refs[run_id] = []
            self._runs[run_id][safe_key] = self._encode(image)
            self._refs[run_id].append(ref)
        return ref

    def refs(self, run_id: str) -> list[DebugImageRef]:
        with self._lock:
            return list(self._refs.get(run_id, []))

    def get(self, run_id: str, key: str) -> bytes:
        with self._lock:
            try:
                return self._runs[run_id][key]
            except KeyError as exc:
                raise FileNotFoundError(f"Debug image not found: {run_id}/{key}") from exc


VISION_DEBUG_STORE = VisionDebugStore()
