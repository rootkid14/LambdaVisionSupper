from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.services.vision_labs.core import ExecutionContext, ParameterSpec, PortSpec


class ImageOperator(ABC):
    """Base contract for Image Processing LAB algorithms.

    Operator authors should only care about:
    INPUTS + OUTPUTS + PARAMETERS + process().
    """

    INPUTS: dict[str, PortSpec] = {}
    OUTPUTS: dict[str, PortSpec] = {}
    PARAMETERS: dict[str, ParameterSpec] = {}

    OPERATOR_ID: str = ""
    OPERATOR_VERSION: str = "1.0"
    LABEL: str = "Image Operator"
    CATEGORY: str = "other"
    DESCRIPTION: str = ""

    @classmethod
    def resolve_parameters(cls, supplied: dict[str, Any] | None = None) -> dict[str, Any]:
        supplied = dict(supplied or {})
        unknown = set(supplied) - set(cls.PARAMETERS)
        if unknown:
            raise ValueError(f"Unknown parameter(s) for {cls.OPERATOR_ID or cls.__name__}: {sorted(unknown)}")

        resolved: dict[str, Any] = {}
        for name, spec in cls.PARAMETERS.items():
            value = supplied[name] if name in supplied else spec.default
            resolved[name] = spec.validate(value)
        return resolved

    @abstractmethod
    def process(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        raise NotImplementedError
