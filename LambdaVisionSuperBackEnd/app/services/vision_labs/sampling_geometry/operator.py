from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.services.vision_labs.core import ExecutionContext, ParameterSpec
from app.services.vision_labs.sampling_geometry.specs import SamplingPortSpec


class SamplingGeometryOperator(ABC):
    INPUTS: dict[str, SamplingPortSpec] = {}
    OUTPUTS: dict[str, SamplingPortSpec] = {}
    PARAMETERS: dict[str, ParameterSpec] = {}

    OPERATOR_ID: str = ""
    OPERATOR_VERSION: str = "1.0"
    LABEL: str = "Sampling / Geometry Operator"
    CATEGORY: str = "Other"
    WORKSPACE: str = "geometry"
    DESCRIPTION: str = ""
    CATALOG_VISIBLE: bool = True

    GUIDE: dict[str, Any] = {}

    @classmethod
    def resolve_parameters(
        cls,
        supplied: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        supplied = dict(supplied or {})
        unknown = set(supplied) - set(cls.PARAMETERS)
        if unknown:
            raise ValueError(
                f"Unknown parameter(s) for {cls.OPERATOR_ID or cls.__name__}: "
                f"{sorted(unknown)}"
            )

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
