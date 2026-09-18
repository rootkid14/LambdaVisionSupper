from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ContourSet:
    contours: list[np.ndarray]
    source_shape: tuple[int, int]

    @property
    def shape(self) -> tuple[int, ...]:
        return (len(self.contours),)


@dataclass
class Polyline:
    points: np.ndarray
    closed: bool = False
    source_shape: tuple[int, int] | None = None

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.points.shape)


@dataclass
class ProfileSet:
    x: np.ndarray
    series: np.ndarray
    labels: list[str] = field(default_factory=list)
    geometry: dict[str, Any] | None = None
    units: str = "sample"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.series.shape)


@dataclass
class Histogram1D:
    bins: np.ndarray
    values: np.ndarray
    channel: str = "gray"
    normalized: bool = True

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.values.shape)


@dataclass
class FeatureVector:
    values: np.ndarray
    names: list[str]
    groups: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.values.shape)


@dataclass
class FeatureMatrix:
    values: np.ndarray
    feature_names: list[str]
    row_labels: list[str] = field(default_factory=list)
    geometry: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.values.shape)


@dataclass
class Spectrum2D:
    magnitude: np.ndarray
    source_shape: tuple[int, int]
    window: str = "none"
    channel: str = "gray"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.magnitude.shape)


@dataclass
class MeasurementTable:
    columns: list[str]
    rows: list[dict[str, float | int | str]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return (len(self.rows), len(self.columns))
