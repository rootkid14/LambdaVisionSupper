from __future__ import annotations

import time
from typing import Any, Callable

from app.services.vision_app.models import ModbusDeviceDeclaration, ModbusIOConfig, ModbusPointDeclaration


class ModbusIOController:
    """Synchronous Modbus adapter with an in-memory simulated driver."""

    def __init__(self, client_factory: Callable[..., Any] | None = None) -> None:
        self._client_factory = client_factory
        self._simulated_values: dict[tuple[str, str], Any] = {}

    def _factory(self):
        if self._client_factory is not None:
            return self._client_factory
        try:
            from pymodbus.client import ModbusTcpClient
        except Exception as exc:  # pragma: no cover
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

    def _client(self, config: Any):
        return self._factory()(config.host, port=config.port)

    @staticmethod
    def _unit_id(config: Any) -> int:
        return int(getattr(config, "unit_id", getattr(config, "device_id", 1)))

    def read_declared_point(self, device: ModbusDeviceDeclaration, point: ModbusPointDeclaration) -> Any:
        if device.driver == "simulated":
            default = False if point.data_type == "bool" else 0
            return self._simulated_values.get((device.declaration_id, point.point_id), default)
        client = self._client(device)
        try:
            if not client.connect():
                raise ConnectionError(f"Modbus connection failed: {device.host}:{device.port}")
            unit = self._unit_id(device)
            address = int(point.address)
            if point.kind == "coil":
                response = self._device_call(client.read_coils, address, count=1, device_id=unit)
                values = getattr(response, "bits", None) or []
                value = bool(values[0]) if values else False
            elif point.kind == "discrete_input":
                response = self._device_call(client.read_discrete_inputs, address, count=1, device_id=unit)
                values = getattr(response, "bits", None) or []
                value = bool(values[0]) if values else False
            elif point.kind == "holding_register":
                response = self._device_call(client.read_holding_registers, address, count=1, device_id=unit)
                values = getattr(response, "registers", None) or []
                value = int(values[0]) if values else 0
            elif point.kind == "input_register":
                response = self._device_call(client.read_input_registers, address, count=1, device_id=unit)
                values = getattr(response, "registers", None) or []
                value = int(values[0]) if values else 0
            else:
                raise ValueError(f"Unsupported Modbus point kind: {point.kind}")
            if hasattr(response, "isError") and response.isError():
                raise RuntimeError(f"Modbus point read failed: {response}")
            return value
        finally:
            try:
                client.close()
            except Exception:
                pass

    def write_declared_point(self, device: ModbusDeviceDeclaration, point: ModbusPointDeclaration, value: Any) -> None:
        if not point.writable:
            raise ValueError(f"Declared point {device.alias}.{point.alias} is read-only")
        if device.driver == "simulated":
            self._simulated_values[(device.declaration_id, point.point_id)] = bool(value) if point.data_type == "bool" else int(value)
            return
        client = self._client(device)
        try:
            if not client.connect():
                raise ConnectionError(f"Modbus connection failed: {device.host}:{device.port}")
            unit = self._unit_id(device)
            if point.kind == "coil":
                response = self._device_call(client.write_coil, int(point.address), bool(value), device_id=unit)
            elif point.kind == "holding_register":
                response = self._device_call(client.write_register, int(point.address), int(value), device_id=unit)
            else:
                raise ValueError(f"Unsupported writable Modbus kind: {point.kind}")
            if hasattr(response, "isError") and response.isError():
                raise RuntimeError(f"Modbus point write failed: {response}")
        finally:
            try:
                client.close()
            except Exception:
                pass

    def set_simulated_point(self, device: ModbusDeviceDeclaration, point: ModbusPointDeclaration, value: Any) -> None:
        self._simulated_values[(device.declaration_id, point.point_id)] = bool(value) if point.data_type == "bool" else int(value)

    def pulse_declared_point(self, device: ModbusDeviceDeclaration, point: ModbusPointDeclaration, seconds: float | None = None) -> None:
        if point.kind != "coil":
            raise ValueError("Only coil declarations can be pulsed")
        duration = float(seconds if seconds is not None else point.pulse_seconds)
        self.write_declared_point(device, point, True)
        try:
            time.sleep(max(0.0, duration))
        finally:
            self.write_declared_point(device, point, False)

    # Legacy v0.8-v0.12 adapter methods retained.
    def read_point(self, config: ModbusIOConfig, kind: str, address: int) -> bool:
        device = ModbusDeviceDeclaration(declaration_id="legacy", alias="legacy", host=config.host, port=config.port, unit_id=config.device_id)
        point = ModbusPointDeclaration(point_id="legacy", alias="legacy", kind=kind, address=address)
        return bool(self.read_declared_point(device, point))

    def read_trigger(self, config: ModbusIOConfig) -> bool:
        value = self.read_point(config, config.trigger_kind, config.trigger_address)
        return value if config.trigger_active_high else not value

    def set_coil(self, config: ModbusIOConfig, address: int, value: bool) -> None:
        device = ModbusDeviceDeclaration(declaration_id="legacy", alias="legacy", host=config.host, port=config.port, unit_id=config.device_id)
        point = ModbusPointDeclaration(point_id="legacy", alias="legacy", kind="coil", address=address)
        self.write_declared_point(device, point, value)

    def pulse_result(self, config: ModbusIOConfig, ok: bool, seconds: float | None = None) -> None:
        address = config.ok_coil if ok else config.ng_coil
        duration = float(seconds if seconds is not None else config.pulse_seconds)
        self.set_coil(config, address, True)
        try:
            time.sleep(max(0.0, duration))
        finally:
            self.set_coil(config, address, False)
