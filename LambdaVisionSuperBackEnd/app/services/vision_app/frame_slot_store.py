from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Any

import cv2
import numpy as np


class FrameSlotStore:
    """Volatile per-program camera/workspace frame slots.

    The declaration model names the slots. The store only keeps the latest frame for
    each slot and a monotonically increasing sequence so UI/automation can observe
    changes without serialising image bytes into program.json.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._frames: dict[str, dict[str, np.ndarray]] = defaultdict(dict)
        self._sequence: dict[str, dict[str, int]] = defaultdict(dict)
        self._streaming: dict[str, dict[str, bool]] = defaultdict(dict)

    def put(self, program_id: str, slot_path: str, image: np.ndarray) -> int:
        arr = np.ascontiguousarray(image.copy())
        with self._lock:
            self._frames[program_id][slot_path] = arr
            seq = self._sequence[program_id].get(slot_path, 0) + 1
            self._sequence[program_id][slot_path] = seq
            return seq

    def get(self, program_id: str, slot_path: str) -> np.ndarray:
        with self._lock:
            frame = self._frames.get(program_id, {}).get(slot_path)
            if frame is None:
                raise FileNotFoundError(f"Frame slot is empty: {slot_path}")
            return np.ascontiguousarray(frame.copy())

    def has(self, program_id: str, slot_path: str) -> bool:
        with self._lock:
            return slot_path in self._frames.get(program_id, {})

    def sequence(self, program_id: str, slot_path: str) -> int:
        with self._lock:
            return self._sequence.get(program_id, {}).get(slot_path, 0)

    def set_streaming(self, program_id: str, camera_alias: str, value: bool) -> None:
        with self._lock:
            self._streaming[program_id][camera_alias] = bool(value)

    def streaming(self, program_id: str, camera_alias: str) -> bool:
        with self._lock:
            return bool(self._streaming.get(program_id, {}).get(camera_alias, False))

    def jpeg(self, program_id: str, slot_path: str, quality: int = 92) -> bytes:
        image = self.get(program_id, slot_path)
        ok, encoded = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            raise RuntimeError('Frame slot JPEG encoding failed')
        return encoded.tobytes()


VISION_FRAME_SLOTS = FrameSlotStore()
