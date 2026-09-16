from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SamplingPortSpec:
    data_type: str
    optional: bool = False
    label: str | None = None

    def to_manifest(self) -> dict[str, Any]:
        return {
            "type": self.data_type,
            "optional": self.optional,
            "label": self.label,
        }


def SamplingPort(
    data_type: str,
    *,
    optional: bool = False,
    label: str | None = None,
) -> SamplingPortSpec:
    return SamplingPortSpec(
        data_type=str(data_type),
        optional=optional,
        label=label,
    )
