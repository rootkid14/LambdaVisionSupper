from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import Lock
from typing import Iterable
import re

import cv2
import numpy as np

from app.services.vision_app.models import (
    NormalizedRect,
    UtilityBatchRequest,
    UtilityGatherAugmentation,
    UtilityGatherPlan,
    UtilityGatherRoi,
)


_IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}
_SAFE_STEM = re.compile(r'[^A-Za-z0-9_.-]+')


class UtilityGatherRuntime:
    """Filesystem-oriented image/ROI harvesting for Vision App Utilities.

    v0.15.1 keeps gathering AI-agnostic while adding deterministic ROI sampling
    augmentation. The same plan is used by manual capture, offline batch and
    Workspace-active collection.
    """

    FULL_OUTPUT_ID = '__full__'

    def __init__(self) -> None:
        self._counter = 0
        self._lock = Lock()

    @staticmethod
    def _folder(path: str) -> Path:
        value = str(path or '').strip()
        if not value:
            raise ValueError('Folder path is empty')
        return Path(value).expanduser()

    @classmethod
    def _images(cls, source_dir: str) -> list[Path]:
        root = cls._folder(source_dir)
        if not root.exists():
            raise FileNotFoundError(f'Image source folder not found: {root}')
        if not root.is_dir():
            raise NotADirectoryError(f'Image source is not a folder: {root}')
        return sorted(
            (item for item in root.iterdir() if item.is_file() and item.suffix.lower() in _IMAGE_SUFFIXES),
            key=lambda item: item.name.lower(),
        )

    def folder_info(self, source_dir: str) -> dict:
        images = self._images(source_dir)
        return {
            'source_dir': str(self._folder(source_dir)),
            'count': len(images),
            'first_name': images[0].name if images else '',
            'last_name': images[-1].name if images else '',
        }

    def folder_image(self, source_dir: str, index: int) -> tuple[np.ndarray, Path, int, int]:
        images = self._images(source_dir)
        if not images:
            raise FileNotFoundError(f'No supported images in source folder: {source_dir}')
        resolved = max(0, min(int(index), len(images) - 1))
        path = images[resolved]
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f'Could not decode image: {path}')
        return image, path, resolved, len(images)

    @staticmethod
    def _safe_stem(value: str) -> str:
        stem = _SAFE_STEM.sub('_', value.strip()).strip('._-')
        return (stem or 'sample')[:120]

    def _capture_stem(self) -> str:
        with self._lock:
            self._counter += 1
            counter = self._counter
        now = datetime.now(timezone.utc).astimezone()
        return f"capture_{now.strftime('%Y%m%d_%H%M%S_%f')}_{counter:06d}"

    @staticmethod
    def _destination(plan: UtilityGatherPlan, destination: str) -> Path:
        value = str(destination or '').strip()
        if not value:
            raise ValueError('Enabled output has no destination folder')
        target = Path(value).expanduser()
        if target.is_absolute():
            return target
        base = str(plan.base_dir or '').strip()
        if not base:
            raise ValueError(f'Relative destination requires a base folder: {value}')
        return Path(base).expanduser() / target

    @staticmethod
    def _next_path(folder: Path, stem: str, extension: str) -> Path:
        candidate = folder / f'{stem}.{extension}'
        if not candidate.exists():
            return candidate
        index = 1
        while True:
            candidate = folder / f'{stem}_{index:03d}.{extension}'
            if not candidate.exists():
                return candidate
            index += 1

    @staticmethod
    def _encode(image: np.ndarray, plan: UtilityGatherPlan) -> tuple[str, bytes]:
        extension = 'png' if plan.image_format == 'png' else 'jpg'
        params: list[int] = []
        if extension == 'jpg':
            params = [int(cv2.IMWRITE_JPEG_QUALITY), int(plan.jpeg_quality)]
        ok, encoded = cv2.imencode(f'.{extension}', image, params)
        if not ok:
            raise RuntimeError(f'Failed to encode gathered image as {extension}')
        return extension, encoded.tobytes()

    @staticmethod
    def _roi_map(rois: Iterable[UtilityGatherRoi]) -> dict[str, UtilityGatherRoi]:
        result: dict[str, UtilityGatherRoi] = {}
        for roi in rois:
            if roi.roi_id in result:
                raise ValueError(f'Duplicate gather ROI id: {roi.roi_id}')
            result[roi.roi_id] = roi
        return result

    @staticmethod
    def _rect_tuple(rect: NormalizedRect) -> tuple[float, float, float, float]:
        return float(rect.x), float(rect.y), float(rect.w), float(rect.h)

    @staticmethod
    def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
        ax, ay, aw, ah = a; bx, by, bw, bh = b
        x0 = max(ax, bx); y0 = max(ay, by)
        x1 = min(ax + aw, bx + bw); y1 = min(ay + ah, by + bh)
        inter = max(0.0, x1 - x0) * max(0.0, y1 - y0)
        union = aw * ah + bw * bh - inter
        return 0.0 if union <= 0.0 else inter / union

    @staticmethod
    def _clamp_rect(cx: float, cy: float, w: float, h: float) -> tuple[float, float, float, float]:
        w = min(1.0, max(1e-6, w)); h = min(1.0, max(1e-6, h))
        x = min(max(0.0, cx - w / 2.0), max(0.0, 1.0 - w))
        y = min(max(0.0, cy - h / 2.0), max(0.0, 1.0 - h))
        return x, y, w, h

    @staticmethod
    def _unit_from_hash(seed: str, offset: int) -> float:
        raw = sha256(seed.encode('utf-8')).digest()
        start = (offset * 4) % (len(raw) - 4)
        value = int.from_bytes(raw[start:start + 4], 'big') / 0xFFFFFFFF
        return value

    @classmethod
    def _variant_rects(
        cls,
        roi: UtilityGatherRoi,
        augmentation: UtilityGatherAugmentation,
        *,
        seed_stem: str,
    ) -> list[tuple[str, tuple[float, float, float, float]]]:
        base = cls._rect_tuple(roi.rect)
        result: list[tuple[str, tuple[float, float, float, float]]] = []
        if augmentation.include_original or not augmentation.enabled:
            result.append(('orig', base))
        if not augmentation.enabled or int(augmentation.extra_variants) <= 0:
            return result

        min_scale = min(float(augmentation.min_scale), float(augmentation.max_scale))
        max_scale = max(float(augmentation.min_scale), float(augmentation.max_scale))
        shift_x = max(0.0, float(augmentation.shift_x_pct))
        shift_y = max(0.0, float(augmentation.shift_y_pct))
        bx, by, bw, bh = base
        center_x = bx + bw / 2.0; center_y = by + bh / 2.0
        target = int(augmentation.extra_variants)
        attempts = 0
        index = 0
        while len(result) < target + (1 if augmentation.include_original else 0) and attempts < max(64, target * 12):
            seed = f'{seed_stem}|{roi.roi_id}|{index}'
            dx = (cls._unit_from_hash(seed, 0) * 2.0 - 1.0) * shift_x * bw
            dy = (cls._unit_from_hash(seed, 1) * 2.0 - 1.0) * shift_y * bh
            scale = min_scale + cls._unit_from_hash(seed, 2) * (max_scale - min_scale)
            candidate = cls._clamp_rect(center_x + dx, center_y + dy, bw * scale, bh * scale)
            attempts += 1; index += 1
            if cls._iou(base, candidate) + 1e-9 < float(augmentation.min_iou):
                continue
            if any(all(abs(a - b) < 1e-6 for a, b in zip(candidate, existing)) for _, existing in result):
                continue
            result.append((f'v{len(result):02d}', candidate))
        return result

    @staticmethod
    def _crop_rect(image: np.ndarray, rect: tuple[float, float, float, float], roi_id: str) -> np.ndarray:
        height, width = image.shape[:2]
        x, y, w, h = rect
        x0 = max(0, min(width - 1, int(round(x * width))))
        y0 = max(0, min(height - 1, int(round(y * height))))
        x1 = max(x0 + 1, min(width, int(round((x + w) * width))))
        y1 = max(y0 + 1, min(height, int(round((y + h) * height))))
        crop = image[y0:y1, x0:x1]
        if crop.size == 0:
            raise ValueError(f'ROI produced an empty crop: {roi_id}')
        return np.ascontiguousarray(crop)

    def save_frame(self, image: np.ndarray, plan: UtilityGatherPlan, *, stem: str | None = None) -> dict:
        arr = np.asarray(image)
        if arr.ndim not in {2, 3} or arr.size == 0:
            raise ValueError('Gather source image is empty or invalid')
        roi_by_id = self._roi_map(plan.rois)
        active_routes = [route for route in plan.routes if route.enabled]
        if not active_routes:
            raise ValueError('At least one gather output must be enabled')

        seen: set[str] = set()
        for route in active_routes:
            if route.output_id in seen:
                raise ValueError(f'Duplicate gather route: {route.output_id}')
            seen.add(route.output_id)
            if route.output_id != self.FULL_OUTPUT_ID and route.output_id not in roi_by_id:
                raise KeyError(f'Gather route refers to unknown ROI: {route.output_id}')

        sample_stem = self._safe_stem(stem or self._capture_stem())
        saved: list[dict] = []
        failed: list[dict] = []
        for route in active_routes:
            variants: list[tuple[str, np.ndarray, tuple[float, float, float, float] | None]]
            if route.output_id == self.FULL_OUTPUT_ID:
                variants = [('orig', arr, None)]
            else:
                roi = roi_by_id[route.output_id]
                variants = []
                for variant_name, rect in self._variant_rects(roi, plan.augmentation, seed_stem=sample_stem):
                    try:
                        variants.append((variant_name, self._crop_rect(arr, rect, roi.roi_id), rect))
                    except Exception as exc:
                        failed.append({'output_id': route.output_id, 'variant': variant_name, 'error': str(exc)})
            for variant_name, payload, rect in variants:
                try:
                    folder = self._destination(plan, route.destination)
                    folder.mkdir(parents=True, exist_ok=True)
                    extension, encoded = self._encode(payload, plan)
                    variant_suffix = '' if variant_name == 'orig' else f'__{variant_name}'
                    path = self._next_path(folder, sample_stem + variant_suffix, extension)
                    temporary = path.with_name(path.name + '.tmp')
                    temporary.write_bytes(encoded)
                    temporary.replace(path)
                    item = {
                        'output_id': route.output_id,
                        'variant': variant_name,
                        'path': str(path),
                        'width': int(payload.shape[1]),
                        'height': int(payload.shape[0]),
                    }
                    if rect is not None:
                        item['rect'] = {'x': rect[0], 'y': rect[1], 'w': rect[2], 'h': rect[3]}
                    saved.append(item)
                except Exception as exc:
                    failed.append({'output_id': route.output_id, 'variant': variant_name, 'error': str(exc)})

        return {
            'stem': sample_stem,
            'saved_count': len(saved),
            'failed_count': len(failed),
            'saved': saved,
            'failed': failed,
        }

    def process_folder(self, request: UtilityBatchRequest) -> dict:
        images = self._images(request.source_dir)
        if not images:
            raise FileNotFoundError(f'No supported images in source folder: {request.source_dir}')

        processed = 0
        saved_count = 0
        failed_count = 0
        errors: list[dict] = []
        for path in images:
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                failed_count += 1
                errors.append({'source': str(path), 'error': 'decode failed'})
                continue
            try:
                result = self.save_frame(image, request, stem=f'{self._safe_stem(path.stem)}__gathered')
                processed += 1
                saved_count += int(result['saved_count'])
                failed_count += int(result['failed_count'])
                for item in result['failed']:
                    if len(errors) < 50:
                        errors.append({'source': str(path), **item})
            except Exception as exc:
                failed_count += 1
                if len(errors) < 50:
                    errors.append({'source': str(path), 'error': str(exc)})

        return {
            'source_dir': str(self._folder(request.source_dir)),
            'source_count': len(images),
            'processed_count': processed,
            'saved_count': saved_count,
            'failed_count': failed_count,
            'errors': errors,
        }
