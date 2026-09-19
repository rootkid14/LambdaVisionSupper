from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Iterable
import re

import cv2
import numpy as np

from app.services.vision_app.models import UtilityBatchRequest, UtilityGatherPlan, UtilityGatherRoi


_IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}
_SAFE_STEM = re.compile(r'[^A-Za-z0-9_.-]+')


class UtilityGatherRuntime:
    """Filesystem-oriented image/ROI harvesting for Vision App Utilities.

    This runtime deliberately does not know AI classes, datasets, training, Working
    Logic, or inspection decisions.  It receives one image plus an explicit
    extraction/routing plan and persists the requested visual samples.
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
    def _crop(image: np.ndarray, roi: UtilityGatherRoi) -> np.ndarray:
        height, width = image.shape[:2]
        rect = roi.rect
        x0 = max(0, min(width - 1, int(round(rect.x * width))))
        y0 = max(0, min(height - 1, int(round(rect.y * height))))
        x1 = max(x0 + 1, min(width, int(round((rect.x + rect.w) * width))))
        y1 = max(y0 + 1, min(height, int(round((rect.y + rect.h) * height))))
        crop = image[y0:y1, x0:x1]
        if crop.size == 0:
            raise ValueError(f'ROI produced an empty crop: {roi.roi_id}')
        return np.ascontiguousarray(crop)

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
            try:
                payload = arr if route.output_id == self.FULL_OUTPUT_ID else self._crop(arr, roi_by_id[route.output_id])
                folder = self._destination(plan, route.destination)
                folder.mkdir(parents=True, exist_ok=True)
                extension, encoded = self._encode(payload, plan)
                path = self._next_path(folder, sample_stem, extension)
                temporary = path.with_name(path.name + '.tmp')
                temporary.write_bytes(encoded)
                temporary.replace(path)
                saved.append({
                    'output_id': route.output_id,
                    'path': str(path),
                    'width': int(payload.shape[1]),
                    'height': int(payload.shape[0]),
                })
            except Exception as exc:
                failed.append({'output_id': route.output_id, 'error': str(exc)})

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
