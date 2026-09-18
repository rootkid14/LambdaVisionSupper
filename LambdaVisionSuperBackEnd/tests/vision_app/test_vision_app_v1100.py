from __future__ import annotations

import time
import numpy as np

from app.services.vision_app.automation_manager import AutomationManager
from app.services.vision_app.automation_models import AutomationConfig, AutomationServiceDefinition, VisionRunSnapshot
from app.services.vision_app.automation_runtime import validate_script
from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.models import (
    BenchmarkStep,
    NormalizedRect,
    ScopeRunResult,
    ServiceExecutionResult,
    StationRunResult,
    VisionProgramDefinition,
    VisionProgramRunResult,
)


class FakeRepo:
    def __init__(self, program): self.program = program
    def get(self, _): return self.program
    def load_master(self, _): return np.zeros((40, 50, 3), dtype=np.uint8)


class FakeRuntime:
    def run_test(self, program, master, image):
        logic = ServiceExecutionResult(binding_id="b1", service_id="svc", alias="measure", ok=True, outputs={"score": 0.8, "count": 3})
        global_scope = ScopeRunResult(scope_id="global", scope_name="Global", ok=True, logic_services=[logic])
        return VisionProgramRunResult(program_id=program.program_id, run_id="run-1", global_ok=True, overall_ok=False, global_scope=global_scope, stations=[], benchmarks=[BenchmarkStep(scope="program", phase="total", name="Total", elapsed_ms=3.2)], total_ms=3.2)


class FakeCamera:
    def capture(self, config): return np.ones((40, 50, 3), dtype=np.uint8) * 127


class FakeIO:
    def __init__(self): self.writes=[]; self.trigger=True
    def read_point(self, config, kind, address): return self.trigger
    def set_coil(self, config, address, value): self.writes.append((address, bool(value)))
    def pulse_result(self, config, ok, seconds=None): self.writes.append((config.ok_coil if ok else config.ng_coil, "pulse"))


def test_safe_dsl_rejects_python_escape_constructs():
    assert validate_script("import os")
    assert validate_script("while True:\n    pass")
    assert not validate_script("if device.modbus_1.X1 == ON:\n    system.run_inspection()")


def test_endpoint_registry_contains_system_device_and_dynamic_vision_outputs():
    program = VisionProgramDefinition(program_id="p1", name="P1")
    snapshot = VisionRunSnapshot(program_id="p1", run_id="r1", global_ok=True, overall_ok=True, total_ms=1.0, global_logic={"measure":{"score":0.8}}, roi_logic={"ROI1":{"contour":{"length":123.0}}})
    paths = {item.path for item in EndpointRegistry().build(program, snapshot)}
    assert "system.run_inspection" in paths
    assert "device.modbus_1.X1" in paths
    assert "vision.global_scope.logic.measure.outputs.score" in paths
    assert "vision.roi.ROI1.logic.contour.outputs.length" in paths


def test_logic_ready_event_service_can_commit_final_result():
    service = AutomationServiceDefinition(service_id="judge", name="Judge", mode="event", event="vision.logic_ready", script="if vision.global_scope.logic.measure.outputs.score > 0.5:\n    system.commit_result(OK)\nelse:\n    system.commit_result(NG)\n")
    program = VisionProgramDefinition(program_id="p1", name="P1", automation=AutomationConfig(services=[service]))
    manager = AutomationManager(FakeRepo(program), FakeRuntime(), FakeCamera(), FakeIO())
    result = manager.run_inspection("p1", np.zeros((40,50,3), dtype=np.uint8))
    assert manager.state("p1").result == "OK"
    assert manager.state("p1").last_event == "system.run_finish"
    assert result.overall_ok is True
    assert manager.snapshot("p1").global_logic["measure"]["score"] == 0.8


def test_dry_run_does_not_write_modbus_output():
    service = AutomationServiceDefinition(service_id="dry", name="Dry", mode="oneshot", script="device.modbus_1.Y1 = ON\n")
    program = VisionProgramDefinition(program_id="p1", name="P1", automation=AutomationConfig(services=[service]))
    io = FakeIO(); manager = AutomationManager(FakeRepo(program), FakeRuntime(), FakeCamera(), io)
    result = manager.run_service("p1", "dry", dry_run=True)
    assert result.ok
    assert io.writes == []
    assert any(item.dry_run and item.endpoint == "device.modbus_1.Y1" for item in result.trace)


def test_loop_service_polling_can_use_modbus_endpoint():
    service = AutomationServiceDefinition(service_id="poll", name="Poll", mode="loop", interval_ms=25, script="if device.modbus_1.X1 == ON:\n    system.commit_result(OK)\n")
    program = VisionProgramDefinition(program_id="p1", name="P1", automation=AutomationConfig(services=[service]))
    manager = AutomationManager(FakeRepo(program), FakeRuntime(), FakeCamera(), FakeIO())
    manager.start("p1")
    time.sleep(0.09)
    manager.stop("p1")
    assert manager.state("p1").result == "OK"
    assert len(manager.trace("p1")) >= 1
