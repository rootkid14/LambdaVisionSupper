from __future__ import annotations

import time
from typing import Any, Callable

from app.services.vision_app.models import ModbusIOConfig


class ModbusIOController:
    """Small synchronous Modbus controller used by Vision App frame runtime.

    The controller opens a short-lived TCP connection for each read/pulse. A future
    production runner can own a persistent connection/poll loop without changing
    the program contract.
    """

    def __init__(self, client_factory: Callable[..., Any] | None = None) -> None:
        self._client_factory = client_factory

    def _factory(self):
        if self._client_factory is not None:
            return self._client_factory
        try:
            from pymodbus.client import ModbusTcpClient
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "pymodbus is not installed. Install it in the backend environment to use Vision I/O."
            ) from exc
        return ModbusTcpClient

    @staticmethod
    def _device_call(callable_obj, *args, device_id: int, **kwargs):
        try:
            return callable_obj(*args, device_id=device_id, **kwargs)
        except TypeError:
            return callable_obj(*args, slave=device_id, **kwargs)

    def _client(self, config: ModbusIOConfig):
        return self._factory()(config.host, port=config.port)

    def read_trigger(self, config: ModbusIOConfig) -> bool:
        client = self._client(config)
        try:
            if not client.connect():
                raise ConnectionError(f"Modbus connection failed: {config.host}:{config.port}")
            if config.trigger_kind == "coil":
                response = self._device_call(
                    client.read_coils,
                    config.trigger_address,
                    count=1,
                    device_id=config.device_id,
                )
            else:
                response = self._device_call(
                    client.read_discrete_inputs,
                    config.trigger_address,
                    count=1,
                    device_id=config.device_id,
                )
            if hasattr(response, "isError") and response.isError():
                raise RuntimeError(f"Modbus trigger read failed: {response}")
            bits = getattr(response, "bits", None) or []
            value = bool(bits[0]) if bits else False
            return value if config.trigger_active_high else not value
        finally:
            try:
                client.close()
            except Exception:
                pass

    def set_coil(self, config: ModbusIOConfig, address: int, value: bool) -> None:
        client = self._client(config)
        try:
            if not client.connect():
                raise ConnectionError(f"Modbus connection failed: {config.host}:{config.port}")
            response = self._device_call(
                client.write_coil,
                int(address),
                bool(value),
                device_id=config.device_id,
            )
            if hasattr(response, "isError") and response.isError():
                raise RuntimeError(f"Modbus coil write failed: {response}")
        finally:
            try:
                client.close()
            except Exception:
                pass

    def pulse_result(self, config: ModbusIOConfig, ok: bool, seconds: float | None = None) -> None:
        address = config.ok_coil if ok else config.ng_coil
        duration = float(seconds if seconds is not None else config.pulse_seconds)
        self.set_coil(config, address, True)
        try:
            time.sleep(max(0.0, duration))
        finally:
            self.set_coil(config, address, False)
