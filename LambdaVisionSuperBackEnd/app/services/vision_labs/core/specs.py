from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class DataType(str, Enum):
    IMAGE = "image"
    BINARY_MASK = "binary_mask"
    ROI = "roi"


@dataclass(frozen=True)
class PortSpec:
    """Schema of one operator input/output connector."""

    data_type: DataType
    optional: bool = False
    label: str | None = None

    def to_manifest(self) -> dict[str, Any]:
        return {
            "type": self.data_type.value,
            "optional": self.optional,
            "label": self.label,
        }


def ImagePort(*, optional: bool = False, label: str | None = None) -> PortSpec:
    return PortSpec(DataType.IMAGE, optional=optional, label=label)


def BinaryMaskPort(*, optional: bool = False, label: str | None = None) -> PortSpec:
    return PortSpec(DataType.BINARY_MASK, optional=optional, label=label)


def ROIPort(*, optional: bool = False, label: str | None = None) -> PortSpec:
    return PortSpec(DataType.ROI, optional=optional, label=label)


@dataclass(frozen=True)
class ParameterSpec:
    """Declarative parameter schema used by BE validation and FE auto-rendering."""

    kind: str
    default: Any = None
    minimum: float | int | None = None
    maximum: float | int | None = None
    choices: tuple[Any, ...] | None = None
    odd: bool = False
    ui_hint: str | None = None
    label: str | None = None
    description: str | None = None

    def validate(self, value: Any) -> Any:
        if self.kind == "integer":
            if isinstance(value, bool):
                raise ValueError("boolean is not a valid integer")
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"expected integer, got {value!r}") from exc
        elif self.kind == "float":
            if isinstance(value, bool):
                raise ValueError("boolean is not a valid float")
            try:
                value = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"expected float, got {value!r}") from exc
        elif self.kind == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"expected boolean, got {value!r}")
        elif self.kind == "enum":
            if self.choices is None:
                raise ValueError("enum parameter has no choices")

            # HTML <select> values arrive as strings. Preserve the declared
            # enum choice type by mapping an equivalent string representation
            # back to the original choice object.
            if value not in self.choices:
                sentinel = object()
                matched = next(
                    (
                        choice
                        for choice in self.choices
                        if str(choice) == str(value)
                    ),
                    sentinel,
                )
                if matched is not sentinel:
                    value = matched
        elif self.kind == "string":
            if not isinstance(value, str):
                raise ValueError(f"expected string, got {value!r}")

        if self.minimum is not None and value < self.minimum:
            raise ValueError(f"value {value} is smaller than minimum {self.minimum}")
        if self.maximum is not None and value > self.maximum:
            raise ValueError(f"value {value} is larger than maximum {self.maximum}")
        if self.choices is not None and value not in self.choices:
            raise ValueError(f"value {value!r} must be one of {list(self.choices)!r}")
        if self.odd and isinstance(value, int) and value % 2 == 0:
            raise ValueError(f"value {value} must be odd")
        return value

    def to_manifest(self) -> dict[str, Any]:
        return {
            "type": self.kind,
            "default": self.default,
            "min": self.minimum,
            "max": self.maximum,
            "choices": list(self.choices) if self.choices is not None else None,
            "odd": self.odd,
            "ui_hint": self.ui_hint,
            "label": self.label,
            "description": self.description,
        }


def IntParam(
    *,
    default: int = 0,
    min: int | None = None,
    max: int | None = None,
    odd: bool = False,
    ui_hint: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> ParameterSpec:
    return ParameterSpec(
        kind="integer",
        default=default,
        minimum=min,
        maximum=max,
        odd=odd,
        ui_hint=ui_hint,
        label=label,
        description=description,
    )


def FloatParam(
    *,
    default: float = 0.0,
    min: float | None = None,
    max: float | None = None,
    ui_hint: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> ParameterSpec:
    return ParameterSpec(
        kind="float",
        default=default,
        minimum=min,
        maximum=max,
        ui_hint=ui_hint,
        label=label,
        description=description,
    )


def BoolParam(
    *,
    default: bool = False,
    ui_hint: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> ParameterSpec:
    return ParameterSpec(
        kind="boolean",
        default=default,
        ui_hint=ui_hint,
        label=label,
        description=description,
    )


def EnumParam(
    choices: Iterable[Any],
    *,
    default: Any,
    ui_hint: str | None = "select",
    label: str | None = None,
    description: str | None = None,
) -> ParameterSpec:
    return ParameterSpec(
        kind="enum",
        default=default,
        choices=tuple(choices),
        ui_hint=ui_hint,
        label=label,
        description=description,
    )


class ExecutionMode(str, Enum):
    INTERACTIVE = "interactive"
    FINAL = "final"


@dataclass
class ExecutionContext:
    mode: ExecutionMode = ExecutionMode.FINAL
    debug: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
