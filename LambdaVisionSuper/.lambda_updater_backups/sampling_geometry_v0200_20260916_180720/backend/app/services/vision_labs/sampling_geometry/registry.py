from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from app.services.vision_labs.sampling_geometry.operator import SamplingGeometryOperator


@dataclass(frozen=True)
class SamplingOperatorDefinition:
    operator_id: str
    version: str
    label: str
    category: str
    workspace: str
    description: str
    operator_class: Type[SamplingGeometryOperator]

    def to_manifest(self) -> dict[str, Any]:
        cls = self.operator_class
        return {
            "id": self.operator_id,
            "version": self.version,
            "label": self.label,
            "category": self.category,
            "workspace": self.workspace,
            "description": self.description,
            "inputs": {
                name: spec.to_manifest()
                for name, spec in cls.INPUTS.items()
            },
            "outputs": {
                name: spec.to_manifest()
                for name, spec in cls.OUTPUTS.items()
            },
            "parameters": {
                name: {
                    "type": spec.kind,
                    "default": spec.default,
                    "min": spec.minimum,
                    "max": spec.maximum,
                    "choices": list(spec.choices) if spec.choices is not None else None,
                    "odd": spec.odd,
                    "ui_hint": spec.ui_hint,
                    "label": spec.label,
                    "description": spec.description,
                }
                for name, spec in cls.PARAMETERS.items()
            },
            "guide": dict(cls.GUIDE or {}),
        }


class SamplingOperatorRegistry:
    def __init__(self) -> None:
        self._definitions: dict[tuple[str, str], SamplingOperatorDefinition] = {}

    def register(
        self,
        operator_class: Type[SamplingGeometryOperator],
    ) -> Type[SamplingGeometryOperator]:
        operator_id = operator_class.OPERATOR_ID
        version = operator_class.OPERATOR_VERSION
        if not operator_id:
            raise ValueError("Sampling operator must define OPERATOR_ID")
        key = (operator_id, version)
        self._definitions[key] = SamplingOperatorDefinition(
            operator_id=operator_id,
            version=version,
            label=operator_class.LABEL,
            category=operator_class.CATEGORY,
            workspace=operator_class.WORKSPACE,
            description=operator_class.DESCRIPTION,
            operator_class=operator_class,
        )
        return operator_class

    def get(
        self,
        operator_id: str,
        version: str | None = None,
    ) -> SamplingOperatorDefinition:
        if version is not None:
            key = (operator_id, version)
            if key not in self._definitions:
                raise KeyError(
                    f"Unknown Sampling/Geometry operator {operator_id}@{version}"
                )
            return self._definitions[key]

        candidates = [
            definition
            for (registered_id, _), definition in self._definitions.items()
            if registered_id == operator_id
        ]
        if not candidates:
            raise KeyError(f"Unknown Sampling/Geometry operator {operator_id}")
        return sorted(candidates, key=lambda item: item.version)[-1]

    def list(self, workspace: str | None = None) -> list[SamplingOperatorDefinition]:
        items = list(self._definitions.values())
        if workspace:
            items = [item for item in items if item.workspace == workspace]
        return sorted(
            items,
            key=lambda item: (item.workspace, item.category, item.label),
        )

    def manifests(self, workspace: str | None = None) -> list[dict[str, Any]]:
        return [definition.to_manifest() for definition in self.list(workspace)]


SAMPLING_OPERATOR_REGISTRY = SamplingOperatorRegistry()


def sampling_operator(cls: Type[SamplingGeometryOperator]):
    return SAMPLING_OPERATOR_REGISTRY.register(cls)
