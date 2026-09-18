from __future__ import annotations

from types import SimpleNamespace
import numpy as np

from app.services.vision_app.automation_manager import AutomationManager
from app.services.vision_app.automation_models import AutomationConfig, AutomationServiceDefinition
from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.frame_slot_store import VISION_FRAME_SLOTS
from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.models import (
    CameraDeclaration, CameraDeclarationConfig, IotDeclarationConfig,
    ModbusDeviceDeclaration, ModbusPointDeclaration, VisionProgramDefinition,
    WorkspaceDefinition,
)


class FakeRepo:
    def __init__(self, program): self.program=program
    def get(self, _): return self.program
    def load_master(self, _program_id, _workspace_id=None): return np.zeros((20,30,3),dtype=np.uint8)


class FakeRuntime:
    def __init__(self): self.frames=[]
    def run_test(self, program, master, image):
        self.frames.append(image.copy())
        return SimpleNamespace(
            run_id='run-ws', global_ok=True, overall_ok=True, total_ms=3.5,
            global_scope=None, stations=[], benchmarks=[]
        )


def program_v5():
    return VisionProgramDefinition(
        program_id='p', name='P',
        iot=IotDeclarationConfig(devices=[ModbusDeviceDeclaration(
            declaration_id='sim_plc', alias='sim_plc', driver='simulated',
            points=[ModbusPointDeclaration(point_id='x1',alias='X1',kind='discrete_input',address=0),
                    ModbusPointDeclaration(point_id='y1',alias='Y_OK',kind='coil',address=1)],
        )]),
        cameras=CameraDeclarationConfig(devices=[CameraDeclaration(
            declaration_id='cam_front', alias='front', driver='simulated', image_slot='Current_image', stream_slot='Streaming_frame'
        )]),
        workspaces=[WorkspaceDefinition(workspace_id='front_ws',name='Front',alias='front',input_binding='camera.front.Current_image')],
        active_workspace_id='front_ws',
    )


def test_program_v5_declares_cameras_workspaces_and_typed_hints_before_run():
    program=program_v5()
    assert program.version == 5
    eps={e.path:e for e in EndpointRegistry().build(program)}
    assert 'camera.front.capture' in eps
    assert 'camera.front.Current_image' in eps
    assert 'workspace.front.run_inspection' in eps
    assert eps['workspace.front.result'].allowed_values == ['OK','NG','NONE','ERROR']
    assert eps['device.sim_plc.X1'].allowed_values == ['ON','OFF']
    assert eps['device.sim_plc.Y_OK'].writable is True


def test_simulated_iot_uses_same_declared_runtime_contract():
    program=program_v5(); io=ModbusIOController(); device=program.iot.devices[0]; x1=device.points[0]; y=device.points[1]
    io.set_simulated_point(device,x1,True)
    assert io.read_declared_point(device,x1) is True
    io.write_declared_point(device,y,True)
    assert io.read_declared_point(device,y) is True


def test_workspace_run_reads_bound_simulated_camera_slot():
    program=program_v5(); runtime=FakeRuntime(); manager=AutomationManager(FakeRepo(program),runtime=runtime,io=ModbusIOController())
    frame=np.full((24,32,3),77,dtype=np.uint8)
    VISION_FRAME_SLOTS.put('p','camera.front.Current_image',frame)
    run=manager.run_inspection('p',workspace_alias='front')
    assert run.overall_ok is True
    assert runtime.frames and int(runtime.frames[0].mean()) == 77
    state=manager.state('p')
    assert state.workspace_results['front'] == 'OK'
    assert state.last_workspace == 'front'


def test_automation_can_orchestrate_workspace_and_simulated_device():
    service=AutomationServiceDefinition(
        service_id='s',name='Glue',mode='oneshot',
        script='if device.sim_plc.X1 == ON:\n    workspace.front.run_inspection()\n'
    )
    program=program_v5(); program.automation=AutomationConfig(services=[service])
    runtime=FakeRuntime(); io=ModbusIOController(); io.set_simulated_point(program.iot.devices[0],program.iot.devices[0].points[0],True)
    VISION_FRAME_SLOTS.put('p','camera.front.Current_image',np.zeros((20,30,3),dtype=np.uint8))
    manager=AutomationManager(FakeRepo(program),runtime=runtime,io=io)
    result=manager.run_service('p','s')
    assert result.ok
    assert manager.state('p').workspace_results['front'] == 'OK'
