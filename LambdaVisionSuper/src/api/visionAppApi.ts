import { axiosClient, api_version } from './axiosClient';

export type RoiSearchMethod = 'manual' | 'blur_template' | 'fourier';
export type CameraDriver = 'manual' | 'basler' | 'url';
export type ControlPrimitiveAction = 'trigger_camera'|'run_inspection'|'out_ok'|'out_ng'|'clear_working_screen';

export interface NormalizedRect { x:number; y:number; w:number; h:number; }
export interface GeometryConstraint { enabled:boolean; search_margin_px:number; max_shift_px:number; }
export interface RoiLocatorConfig { method:RoiSearchMethod; blur_kernel:number; template_threshold:number; geometry:GeometryConstraint; }
export interface RoiSearchConfig extends RoiLocatorConfig {}
export interface MasterRoi { roi_id:string; name:string; alias:string; rect:NormalizedRect; enabled:boolean; search?:RoiSearchConfig|null; }
export interface ModbusIOConfig {
  enabled:boolean; host:string; port:number; device_id:number;
  trigger_kind:'discrete_input'|'coil'; trigger_address:number; trigger_active_high:boolean;
  ok_coil:number; ng_coil:number; pulse_seconds:number; poll_interval_ms:number;
}

export interface ControlBinding { binding_id:string; enabled:boolean; source:'keyboard'|'modbus_trigger'; key:string; action:ControlPrimitiveAction; }
export interface ControlMapperConfig { bindings:ControlBinding[]; }
export interface AutomationServiceDefinition {
  service_id:string; name:string; enabled:boolean; mode:'loop'|'event'|'oneshot';
  interval_ms:number; event:string; script:string; timeout_ms:number; concurrency:'skip'|'queue_latest';
}
export interface AutomationConfig { enabled:boolean; services:AutomationServiceDefinition[]; }
export interface AutomationEndpoint {
  path:string; kind:'state'|'action'|'event'|'data'; data_type:string; readable:boolean; writable:boolean; callable:boolean;
  description:string; source:string; example:string; last_value:any; allowed_values:any[]; unit:string; object_type:string; parameters:{name:string;data_type:string;default:any;description:string}[];
}
export interface AutomationTraceEntry {
  timestamp:string; service_id:string; service_name:string; phase:string; level:'info'|'warning'|'error';
  message:string; endpoint:string; value:any; dry_run:boolean;
}
export interface AutomationSystemState {
  program_id:string; scheduler_running:boolean; online:boolean; active_workspace:string; workspace_activation_sequence:number; last_workspace:string; workspace_results:Record<string,string>; run_state:'IDLE'|'CAPTURING'|'INSPECTING'|'DECIDING'|'FINISHED'|'ERROR';
  result:'NONE'|'OK'|'NG'|'ERROR'; run_id:string; last_run_ms?:number|null; last_error:string;
  frame_sequence:number; clear_sequence:number; result_sequence:number; last_event:string; keyboard_states:Record<string,boolean>;
}
export interface AutomationValidationIssue { line:number; column:number; severity:'error'|'warning'; message:string; }
export interface AutomationExecutionResult {
  ok:boolean; service_id:string; dry_run:boolean; result_value:any; issues:AutomationValidationIssue[]; trace:AutomationTraceEntry[];
}
export type ModbusPointKind='coil'|'discrete_input'|'holding_register'|'input_register';
export interface ModbusPointDeclaration {
  point_id:string; alias:string; enabled:boolean; kind:ModbusPointKind; address:number; description:string; pulse_seconds:number;
}
export interface ModbusDeviceDeclaration {
  declaration_id:string; alias:string; enabled:boolean; driver:'modbus_tcp'|'simulated'; host:string; port:number; unit_id:number; points:ModbusPointDeclaration[];
}
export interface IotDeclarationConfig { devices:ModbusDeviceDeclaration[]; }
export interface CameraApiParameter { name:string; data_type:'number'|'integer'|'bool'|'string'; default:any; description:string; }
export interface CameraCustomApi { api_id:string; alias:string; enabled:boolean; method:'GET'|'POST'; path_template:string; description:string; parameters:CameraApiParameter[]; }
export interface CameraDeclaration {
  declaration_id:string; alias:string; enabled:boolean; driver:'basler'|'http'|'simulated';
  basler_device_id:string; exposure_us:number; grab_timeout_ms:number; host:string; port:number; capture_path:string; stream_path:string; http_timeout_s:number;
  image_slot:string; stream_slot:string; custom_apis:CameraCustomApi[];
}
export interface CameraDeclarationConfig { devices:CameraDeclaration[]; }
export interface CameraConfig {
  enabled:boolean; driver:CameraDriver; basler_device_id:string; exposure_us:number; grab_timeout_ms:number;
  capture_url:string; focus_url_template:string; http_timeout_s:number;
}
export interface WorkingServiceBinding {
  binding_id:string; service_id:string; version?:number|null; enabled:boolean; label:string; alias:string;
  decision?:any;
}
export interface ScopeDecisionConfig { script:string; }
export interface ScopePipelineConfig {
  enable_filter:boolean; filter_services:WorkingServiceBinding[];
  enable_logic:boolean; logic_services:WorkingServiceBinding[];
  enable_decision:boolean; decision:ScopeDecisionConfig;
}
export interface WorkspaceDefinition {
  workspace_id:string; name:string; alias:string; enabled:boolean;
  iot:IotDeclarationConfig; cameras:CameraDeclarationConfig; camera_id:string; input_binding:string;
  master:{rois:MasterRoi[]; master_shape:number[]; locator:RoiLocatorConfig};
  working:{global_scope:ScopePipelineConfig;station_scopes:Record<string,ScopePipelineConfig>;station_execution:'sequential'|'parallel';global_services?:WorkingServiceBinding[];station_services?:Record<string,WorkingServiceBinding[]>};
}
export interface SimulatorConfig { enabled:boolean; camera_sequence_mode:'fixed'|'next'|'loop'; stream_fps:number; }
export interface VisionProgramDefinition {
  version:number; program_id:string; name:string; description:string;
  io:ModbusIOConfig;
  iot:IotDeclarationConfig;
  camera:CameraConfig;
  cameras:CameraDeclarationConfig;
  control:ControlMapperConfig;
  automation:AutomationConfig;
  master:{rois:MasterRoi[]; master_shape:number[]; locator:RoiLocatorConfig};
  working:{
    global_scope:ScopePipelineConfig;
    station_scopes:Record<string,ScopePipelineConfig>;
    station_execution:'sequential'|'parallel';
    global_services?:WorkingServiceBinding[];
    station_services?:Record<string,WorkingServiceBinding[]>;
  };
  workspaces:WorkspaceDefinition[];
  active_workspace_id:string;
  simulator:SimulatorConfig;
}
export interface LocatedRoi { roi_id:string; name:string; rect:NormalizedRect; score:number; method:string; found:boolean; message:string; }
export interface DebugImageRef { key:string; label:string; scope:string; phase:string; }
export interface BenchmarkStep { scope:string; phase:string; name:string; elapsed_ms:number; detail:string; }
export interface ServiceExecutionResult { binding_id:string; service_id:string; alias:string; ok:boolean; outputs:Record<string,any>; message:string; elapsed_ms:number; }
export interface ScopeRunResult { scope_id:string; scope_name:string; ok:boolean; elapsed_ms:number; filter_services:ServiceExecutionResult[]; logic_services:ServiceExecutionResult[]; decision:any; }
export interface VisionRunResult {
  program_id:string; run_id:string; global_ok:boolean; overall_ok:boolean; located_rois:LocatedRoi[]; total_ms:number;
  global_scope?:ScopeRunResult|null; stations:any[]; debug_images:DebugImageRef[]; benchmarks:BenchmarkStep[];
}
export interface TriggerRunnerStatus {
  program_id:string; armed:boolean; running_cycle:boolean; last_triggered:boolean; last_result?:string|null;
  last_error:string; last_cycle_ms?:number|null; cycles:number;
}
export interface BaslerDevice { name:string; id:string; kind:string; }

const rawBody = (blob:Blob) => ({headers:{'Content-Type':'application/octet-stream'},transformRequest:[(d:any)=>d],timeout:120000});

export const VisionAppAPI = {
  listPrograms: async () => (await axiosClient.get(`${api_version}/computer-vision/programs`)).data.programs as (VisionProgramDefinition & {master_exists?:boolean})[],
  newProgram: async (name:string) => (await axiosClient.post(`${api_version}/computer-vision/programs/new`, {name})).data as {program:VisionProgramDefinition;master_exists:boolean},
  getProgram: async (id:string) => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}`)).data as {program:VisionProgramDefinition;master_exists:boolean},
  saveProgram: async (program:VisionProgramDefinition) => (await axiosClient.put(`${api_version}/computer-vision/programs/${encodeURIComponent(program.program_id)}`, program)).data.program as VisionProgramDefinition,
  removeProgram: async (id:string) => { await axiosClient.delete(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}`); },
  uploadMaster: async (id:string,file:Blob,workspaceId?:string) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master`, file,{...rawBody(file),params:{workspace_id:workspaceId}})).data,
  masterPreview: async (id:string,workspaceId?:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master`,{params:{workspace_id:workspaceId},responseType:'blob'})).data,
  masterBlurPreview: async (id:string,kernel:number,workspaceId?:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master/blur-preview`,{params:{kernel,workspace_id:workspaceId},responseType:'blob'})).data,
  locateRois: async (id:string,file:Blob,workspaceId?:string):Promise<LocatedRoi[]> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/locate-rois`,file,{...rawBody(file),params:{workspace_id:workspaceId}})).data.rois,
  runTest: async (id:string,file:Blob,workspaceId?:string):Promise<VisionRunResult> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/test-run`,file,{...rawBody(file),params:{workspace_id:workspaceId}})).data.run,
  runWorkspaceBound: async (id:string,workspaceAlias:string):Promise<VisionRunResult> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/workspaces/${encodeURIComponent(workspaceAlias)}/run`)).data.run,
  activateWorkspace: async (id:string,workspaceAlias:string):Promise<AutomationSystemState> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/workspaces/${encodeURIComponent(workspaceAlias)}/activate`)).data.state,
  previewScope: async (id:string,scopeId:string,file?:Blob|null,workspaceId?:string) => {
    const url=`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/scope-preview/${encodeURIComponent(scopeId)}`;
    const response=file
      ? await axiosClient.post(url,file,{...rawBody(file),params:{workspace_id:workspaceId}})
      : await axiosClient.post(url,null,{timeout:120000,params:{workspace_id:workspaceId}});
    return response.data as {run_id:string;preview_source:'test'|'master';debug_images:DebugImageRef[];benchmarks:BenchmarkStep[]};
  },
  debugImage: async (runId:string,key:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/debug/${encodeURIComponent(runId)}/${encodeURIComponent(key)}`,{responseType:'blob'})).data,
  readTrigger: async (id:string):Promise<boolean> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/iot/trigger`)).data.triggered,
  pulse: async (id:string,result:'ok'|'ng',seconds?:number) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/iot/pulse`,{result,seconds})).data,
  scanBasler: async () => (await axiosClient.get(`${api_version}/computer-vision/cameras/basler/scan`)).data as {success:boolean;devices:BaslerDevice[];error?:string},
  captureCamera: async (id:string):Promise<Blob> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/camera/capture`,null,{responseType:'blob',timeout:120000})).data,
  focusCamera: async (id:string,payload:{x:number;y:number;w:number;h:number;focal_length?:number|null}) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/camera/focus`,payload)).data,
  captureDeclaredCamera: async (id:string,cameraAlias:string):Promise<Blob> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/cameras/${encodeURIComponent(cameraAlias)}/capture`,null,{responseType:'blob',timeout:120000})).data,
  declaredStreamFrame: async (id:string,cameraAlias:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/cameras/${encodeURIComponent(cameraAlias)}/stream-frame`,{responseType:'blob',timeout:120000})).data,
  uploadSimCameraFrame: async (id:string,cameraAlias:string,file:Blob) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/cameras/${encodeURIComponent(cameraAlias)}/sim-frame`,file,rawBody(file))).data,
  setSimIotPoint: async (id:string,deviceAlias:string,pointAlias:string,value:any) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/simulator/iot/${encodeURIComponent(deviceAlias)}/${encodeURIComponent(pointAlias)}`,{value})).data,
  programOnline: async (id:string):Promise<AutomationSystemState> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/online`)).data.state,
  programOffline: async (id:string):Promise<AutomationSystemState> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/offline`)).data.state,
  automationKeyboard: async (id:string,key:string,pressed:boolean):Promise<AutomationSystemState> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/keyboard`,{key,pressed})).data.state,
  runnerStart: async (id:string):Promise<TriggerRunnerStatus> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/runner/start`)).data.status,
  runnerStop: async (id:string):Promise<TriggerRunnerStatus> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/runner/stop`)).data.status,
  runnerStatus: async (id:string):Promise<TriggerRunnerStatus> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/runner/status`)).data.status,
  automationEndpoints: async (id:string):Promise<AutomationEndpoint[]> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/endpoints`)).data.endpoints,
  automationEndpointsPreview: async (program:VisionProgramDefinition):Promise<AutomationEndpoint[]> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(program.program_id)}/automation/endpoints/preview`,program)).data.endpoints,
  automationValidate: async (id:string,script:string):Promise<AutomationValidationIssue[]> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/validate`,{script})).data.issues,
  automationRunService: async (id:string,serviceId:string,dryRun=false):Promise<AutomationExecutionResult> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/services/${encodeURIComponent(serviceId)}/run`,null,{params:{dry_run:dryRun}})).data.execution,
  automationStart: async (id:string):Promise<AutomationSystemState> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/start`)).data.state,
  automationStop: async (id:string):Promise<AutomationSystemState> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/stop`)).data.state,
  automationState: async (id:string):Promise<AutomationSystemState> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/state`)).data.state,
  automationTrace: async (id:string):Promise<AutomationTraceEntry[]> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/trace`)).data.trace,
  automationClearTrace: async (id:string) => { await axiosClient.delete(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/trace`); },
  automationLatestFrame: async (id:string,workspaceId?:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/latest-frame`,{params:{workspace_id:workspaceId},responseType:'blob'})).data,
  automationSetLatestFrame: async (id:string,file:Blob,workspaceId?:string) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/automation/latest-frame`,file,{...rawBody(file),params:{workspace_id:workspaceId}})).data,
};
