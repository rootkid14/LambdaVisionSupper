from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any
import uuid

import numpy as np


class ColorSpace(str, Enum):
    BGR = "bgr"
    RGB = "rgb"
    GRAY = "gray"
    HSV = "hsv"
    UNKNOWN = "unknown"


@dataclass
class ImageFrame:
    """Runtime image object. NumPy stays native; metadata travels with the pixels."""

    data: np.ndarray
    color_space: ColorSpace = ColorSpace.BGR
    frame_id: str = field(default_factory=lambda: f"img_{uuid.uuid4().hex}")
    source_id: str | None = None
    coordinate_frame: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.data, np.ndarray):
            raise TypeError("ImageFrame.data must be a numpy.ndarray")
        if self.data.ndim not in (2, 3):
            raise ValueError(f"ImageFrame expects HxW or HxWxC, got shape {self.data.shape}")

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.data.shape)

    @property
    def height(self) -> int:
        return int(self.data.shape[0])

    @property
    def width(self) -> int:
        return int(self.data.shape[1])

    @property
    def channels(self) -> int:
        return 1 if self.data.ndim == 2 else int(self.data.shape[2])

    def with_data(
        self,
        data: np.ndarray,
        *,
        color_space: ColorSpace | None = None,
        metadata_update: dict[str, Any] | None = None,
    ) -> "ImageFrame":
        metadata = dict(self.metadata)
        if metadata_update:
            metadata.update(metadata_update)
        return ImageFrame(
            data=data,
            color_space=color_space or self.color_space,
            source_id=self.source_id,
            coordinate_frame=self.coordinate_frame,
            metadata=metadata,
        )


@dataclass
class BinaryMask:
    data: np.ndarray
    mask_id: str = field(default_factory=lambda: f"mask_{uuid.uuid4().hex}")
    coordinate_frame: str | None = None
    reference_image_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.data, np.ndarray):
            raise TypeError("BinaryMask.data must be a numpy.ndarray")
        if self.data.ndim != 2:
            raise ValueError(f"BinaryMask expects HxW, got shape {self.data.shape}")

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.data.shape)

    @classmethod
    def from_image(
        cls,
        data: np.ndarray,
        reference: ImageFrame,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> "BinaryMask":
        return cls(
            data=data,
            coordinate_frame=reference.coordinate_frame,
            reference_image_id=reference.frame_id,
            metadata=dict(metadata or {}),
        )

    def with_data(self, data: np.ndarray, *, metadata_update: dict[str, Any] | None = None) -> "BinaryMask":
        metadata = dict(self.metadata)
        if metadata_update:
            metadata.update(metadata_update)
        return BinaryMask(
            data=data,
            coordinate_frame=self.coordinate_frame,
            reference_image_id=self.reference_image_id,
            metadata=metadata,
        )


@dataclass(frozen=True)
class ROI:
    """Normalized rectangle ROI. x/y/w/h are in [0,1]."""

    x: float
    y: float
    width: float
    height: float
    roi_id: str = field(default_factory=lambda: f"roi_{uuid.uuid4().hex}")

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if not all(0.0 <= float(v) <= 1.0 for v in values):
            raise ValueError("ROI x/y/width/height must be normalized to [0,1]")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("ROI width and height must be > 0")
        if self.x + self.width > 1.0 + 1e-9 or self.y + self.height > 1.0 + 1e-9:
            raise ValueError("ROI extends beyond normalized image bounds")

    def pixel_bounds(self, image: ImageFrame) -> tuple[int, int, int, int]:
        x0 = int(round(self.x * image.width))
        y0 = int(round(self.y * image.height))
        x1 = int(round((self.x + self.width) * image.width))
        y1 = int(round((self.y + self.height) * image.height))
        x0 = max(0, min(image.width - 1, x0))
        y0 = max(0, min(image.height - 1, y0))
        x1 = max(x0 + 1, min(image.width, x1))
        y1 = max(y0 + 1, min(image.height, y1))
        return x0, y0, x1, y1
