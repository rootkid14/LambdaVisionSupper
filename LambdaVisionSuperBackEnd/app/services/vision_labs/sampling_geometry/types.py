from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ContourSet:
    contours: list[np.ndarray]
    source_shape: tuple[int, int]
    ids: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ids or len(self.ids) != len(self.contours):
            self.ids = list(range(len(self.contours)))

    @property
    def shape(self) -> tuple[int, ...]:
        return (len(self.contours),)


@dataclass
class Polyline:
    points: np.ndarray
    closed: bool = False
    source_shape: tuple[int, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.points.shape)


@dataclass
class SamplingHousing:
    kind: str
    source_shape: tuple[int, int]
    elements: list[dict[str, Any]]
    geometry: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return (len(self.elements),)


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

@dataclass
class DataBlock:
    block_id: str
    label: str
    values: np.ndarray
    source_element: str
    channel: str
    kind: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(np.asarray(self.values).shape)


@dataclass
class DataBlockSet:
    blocks: list[DataBlock]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return (len(self.blocks),)


@dataclass
class ComposedData:
    values: np.ndarray
    layout: str
    block_order: list[str]
    block_shapes: dict[str, list[int]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(np.asarray(self.values).shape)

