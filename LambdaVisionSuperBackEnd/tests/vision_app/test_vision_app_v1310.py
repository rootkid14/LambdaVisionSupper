from __future__ import annotations
from app.services.vision_app.automation_models import AutomationServiceDefinition, AutomationSystemState
from app.services.vision_app.automation_runtime import AutomationExecutionContext, SafeAutomationInterpreter, validate_script
from app.services.vision_app.endpoint_registry import EndpointRegistry
from app.services.vision_app.models import CameraApiParameter, CameraCustomApi, CameraDeclaration, CameraDeclarationConfig, VisionProgramDefinition, WorkspaceDefinition

def test_keyboard_endpoint_registry_and_state():
    program=VisionProgramDefinition(program_id='p',name='P')
    state=AutomationSystemState(program_id='p', keyboard_states={'space': True})
    eps={e.path:e for e in EndpointRegistry().build(program,state=state)}
    assert eps['keyboard.space'].last_value is True
    assert eps['keyboard.space'].allowed_values == ['ON','OFF']

def test_named_camera_api_arguments_are_safe_dsl_supported():
    script='camera.pi.focus(x=0.5, y=0.5, w=1.0, h=1.0)\n'
    assert validate_script(script)==[]
    calls=[]
    service=AutomationServiceDefinition(service_id='s',name='S',script=script)
    ctx=AutomationExecutionContext(program=VisionProgramDefinition(program_id='p',name='P'),snapshot=None,event={},read_endpoint=lambda p:None,write_endpoint=lambda p,v,d:None,call_action=lambda p,a,k,d:calls.append((p,a,k)),trace=lambda e:None,dry_run=True)
    result=SafeAutomationInterpreter(ctx,service).execute(script)
    assert result.ok
    assert calls[0][2]=={'x':0.5,'y':0.5,'w':1.0,'h':1.0}

def test_camera_custom_endpoint_describes_parameters():
    camera=CameraDeclaration(declaration_id='pi',alias='pi',driver='http',custom_apis=[CameraCustomApi(api_id='focus',alias='focus',path_template='/focus?x={x}&y={y}',parameters=[CameraApiParameter(name='x',default=.5),CameraApiParameter(name='y',default=.5)])])
    program=VisionProgramDefinition(program_id='p',name='P',cameras=CameraDeclarationConfig(devices=[camera]),workspaces=[WorkspaceDefinition(workspace_id='w',camera_id='pi',input_binding='camera.pi.Current_image')])
    ep={e.path:e for e in EndpointRegistry().build(program)}['camera.pi.focus']
    assert [p['name'] for p in ep.parameters]==['x','y']
    assert 'x=0.5' in ep.example

def test_workspace_has_single_camera_id_contract():
    assert WorkspaceDefinition(workspace_id='w',camera_id='camera_a').camera_id=='camera_a'
