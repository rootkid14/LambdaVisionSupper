from __future__ import annotations

from app.services.vision_app.models import ControlMapperConfig, ControlPrimitiveAction


class ControlMapperRuntime:
    """Pure mapping layer between primitive input events and Vision App actions.

    It intentionally does not own camera, Modbus or UI state. The future IDE/sandbox can
    emit the same actions, keeping orchestration separate from hardware adapters.
    """

    @staticmethod
    def actions_for_keyboard(config: ControlMapperConfig, key: str) -> list[ControlPrimitiveAction]:
        normalized = key.strip().lower()
        return [
            binding.action
            for binding in config.bindings
            if binding.enabled and binding.source == "keyboard" and binding.key.strip().lower() == normalized
        ]

    @staticmethod
    def actions_for_modbus_trigger(config: ControlMapperConfig) -> list[ControlPrimitiveAction]:
        return [binding.action for binding in config.bindings if binding.enabled and binding.source == "modbus_trigger"]
