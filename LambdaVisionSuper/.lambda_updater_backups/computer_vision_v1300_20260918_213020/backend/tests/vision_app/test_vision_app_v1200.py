from __future__ import annotations

from app.services.vision_app.automation_manager import AutomationManager
from app.services.vision_app.automation_models import AutomationConfig, AutomationServiceDefinition
from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.models import (
    IotDeclarationConfig,
    MasterRoi,
    ModbusDeviceDeclaration,
    ModbusPointDeclaration,
    NormalizedRect,
    ScopePipelineConfig,
    VisionProgramDefinition,
    WorkingServiceBinding,
)


class FakeRepo:
    def __init__(self, program): self.program = program
    def get(self, _): return self.program


class FakeIO:
    def __init__(self): self.reads=[]; self.writes=[]; self.pulses=[]
    def read_declared_point(self, device, point):
        self.reads.append((device.alias, point.alias))
        return 17 if point.kind.endswith("register") else True
    def write_declared_point(self, device, point, value): self.writes.append((device.alias, point.alias, value))
    def pulse_declared_point(self, device, point, seconds=None): self.pulses.append((device.alias, point.alias, seconds))


def declared_program():
    roi = MasterRoi(roi_id="r1", name="Upper Bearing", rect=NormalizedRect(x=.1,y=.1,w=.2,h=.2))
    logic = WorkingServiceBinding(binding_id="b1", service_id="contour", alias="contour")
    return VisionProgramDefinition(
        program_id="p",
        name="P",
        iot=IotDeclarationConfig(devices=[ModbusDeviceDeclaration(
            declaration_id="plc",
            alias="plc_left",
            host="192.168.1.50",
            points=[
                ModbusPointDeclaration(point_id="x", alias="X_START", kind="discrete_input", address=2),
                ModbusPointDeclaration(point_id="y", alias="Y_OK", kind="coil", address=7),
                ModbusPointDeclaration(point_id="p", alias="pressure", kind="input_register", address=12),
            ],
        )]),
        master={"rois":[roi]},
        working={"station_scopes":{"r1":ScopePipelineConfig(enable_logic=True,logic_services=[logic])}},
    )


def test_declared_iot_and_roi_objects_exist_before_any_run():
    program = declared_program()
    endpoints = {item.path:item for item in EndpointRegistry().build(program)}
    assert "device.plc_left" in endpoints
    assert endpoints["device.plc_left"].data_type == "modbus_tcp_device"
    assert "device.plc_left.X_START" in endpoints
    assert endpoints["device.plc_left.X_START"].writable is False
    assert "device.plc_left.Y_OK" in endpoints
    assert endpoints["device.plc_left.Y_OK"].writable is True
    assert "device.plc_left.Y_OK.pulse" in endpoints
    assert "device.plc_left.pressure" in endpoints
    assert "vision.roi.Upper_Bearing" in endpoints
    assert "vision.roi.Upper_Bearing.logic.contour" in endpoints
    assert "vision.roi.Upper_Bearing.logic.contour.outputs" in endpoints


def test_automation_runtime_reads_writes_and_pulses_declared_device_aliases():
    service = AutomationServiceDefinition(
        service_id="svc", name="Declared IO", mode="oneshot",
        script=(
            "if device.plc_left.X_START == ON:\n"
            "    device.plc_left.Y_OK = ON\n"
            "    device.plc_left.Y_OK.pulse(0.25)\n"
        ),
    )
    program = declared_program()
    program.automation = AutomationConfig(services=[service])
    io = FakeIO()
    manager = AutomationManager(FakeRepo(program), runtime=None, camera=None, io=io)
    result = manager.run_service("p", "svc")
    assert result.ok
    assert io.reads == [("plc_left", "X_START")]
    assert io.writes == [("plc_left", "Y_OK", True)]
    assert io.pulses == [("plc_left", "Y_OK", 0.25)]


def test_program_v4_contains_iot_declaration_engine():
    program = VisionProgramDefinition(program_id="p", name="P")
    assert program.version == 4
    assert program.iot.devices
    assert program.iot.devices[0].alias == "modbus_1"
