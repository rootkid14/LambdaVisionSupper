from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from app.services.vision_labs.image.operator import ImageOperator


@dataclass(frozen=True)
class OperatorDefinition:
    operator_id: str
    version: str
    label: str
    category: str
    description: str
    operator_class: Type[ImageOperator]

    def to_manifest(self) -> dict[str, Any]:
        cls = self.operator_class
        return {
            "id": self.operator_id,
            "version": self.version,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "inputs": {name: spec.to_manifest() for name, spec in cls.INPUTS.items()},
            "outputs": {name: spec.to_manifest() for name, spec in cls.OUTPUTS.items()},
            "parameters": {name: spec.to_manifest() for name, spec in cls.PARAMETERS.items()},
        }


class ImageOperatorRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, OperatorDefinition] = {}

    def register(self, definition: OperatorDefinition) -> None:
        existing = self._definitions.get(definition.operator_id)
        if existing and existing.operator_class is not definition.operator_class:
            print(f"[IMAGE LAB] Operator {definition.operator_id} already registered; overwriting.")
        self._definitions[definition.operator_id] = definition

    def get(self, operator_id: str) -> OperatorDefinition:
        try:
            return self._definitions[operator_id]
        except KeyError as exc:
            raise KeyError(f"Unknown Image LAB operator: {operator_id}") from exc

    def list(self) -> list[OperatorDefinition]:
        return sorted(
            self._definitions.values(),
            key=lambda x: (x.category.lower(), x.label.lower(), x.operator_id),
        )

    def manifests(self) -> list[dict[str, Any]]:
        return [definition.to_manifest() for definition in self.list()]

    def clear(self) -> None:
        self._definitions.clear()


IMAGE_OPERATOR_REGISTRY = ImageOperatorRegistry()


def image_operator(
    *,
    id: str,
    version: str = "1.0",
    label: str | None = None,
    category: str = "other",
    description: str = "",
):
    """Decorator used to register an ImageOperator with a stable semantic ID."""

    def decorator(cls: Type[ImageOperator]) -> Type[ImageOperator]:
        if not issubclass(cls, ImageOperator):
            raise TypeError("@image_operator can only decorate ImageOperator subclasses")

        cls.OPERATOR_ID = id
        cls.OPERATOR_VERSION = version
        cls.LABEL = label or cls.__name__
        cls.CATEGORY = category
        cls.DESCRIPTION = description

        IMAGE_OPERATOR_REGISTRY.register(
            OperatorDefinition(
                operator_id=id,
                version=version,
                label=cls.LABEL,
                category=category,
                description=description,
                operator_class=cls,
            )
        )
        return cls

    return decorator
