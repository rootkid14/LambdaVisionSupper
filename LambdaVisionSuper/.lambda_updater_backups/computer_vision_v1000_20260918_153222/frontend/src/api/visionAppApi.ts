import { axiosClient, api_version } from './axiosClient';

export type RoiSearchMethod = 'manual' | 'blur_template' | 'fourier';
export type CameraDriver = 'manual' | 'basler' | 'url';
export type ControlPrimitiveAction = 'trigger_camera'|'run_inspection'|'out_ok'|'out_ng'|'clear_working_screen';

export interface NormalizedRect { x:number; y:number; w:number; h:number; }
export interface GeometryConstraint { enabled:boolean; search_margin_px:number; max_shift_px:number; }
export interface RoiLocatorConfig { method:RoiSearchMethod; blur_kernel:number; template_threshold:number; geometry:GeometryConstraint; }
export interface RoiSearchConfig extends RoiLocatorConfig {}
export interface MasterRoi { roi_id:string; name:string; rect:NormalizedRect; enabled:boolean; search?:RoiSearchConfig|null; }
export interface ModbusIOConfig {
  enabled:boolean; host:string; port:number; device_id:number;
  trigger_kind:'discrete_input'|'coil'; trigger_address:number; trigger_active_high:boolean;
  ok_coil:number; ng_coil:number; pulse_seconds:number; poll_interval_ms:number;
}

export interface ControlBinding { binding_id:string; enabled:boolean; source:'keyboard'|'modbus_trigger'; key:string; action:ControlPrimitiveAction; }
export interface ControlMapperConfig { bindings:ControlBinding[]; }
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
export interface VisionProgramDefinition {
  version:number; program_id:string; name:string; description:string;
  io:ModbusIOConfig;
  camera:CameraConfig;
  control:ControlMapperConfig;
  master:{rois:MasterRoi[]; master_shape:number[]; locator:RoiLocatorConfig};
  working:{
    global_scope:ScopePipelineConfig;
    station_scopes:Record<string,ScopePipelineConfig>;
    station_execution:'sequential'|'parallel';
    global_services?:WorkingServiceBinding[];
    station_services?:Record<string,WorkingServiceBinding[]>;
  };
}
export interface LocatedRoi { roi_id:string; name:string; rect:NormalizedRect; score:number; method:string; found:boolean; message:string; }
export interface DebugImageRef { key:string; label:string; scope:string; phase:string; }
export interface BenchmarkStep { scope:string; phase:string; name:string; elapsed_ms:number; detail:string; }
export interface ScopeRunResult { scope_id:string; scope_name:string; ok:boolean; elapsed_ms:number; filter_services:any[]; logic_services:any[]; decision:any; }
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
  uploadMaster: async (id:string,file:Blob) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master`, file, rawBody(file))).data,
  masterPreview: async (id:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master`,{responseType:'blob'})).data,
  masterBlurPreview: async (id:string,kernel:number):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master/blur-preview`,{params:{kernel},responseType:'blob'})).data,
  locateRois: async (id:string,file:Blob):Promise<LocatedRoi[]> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/locate-rois`,file,rawBody(file))).data.rois,
  runTest: async (id:string,file:Blob):Promise<VisionRunResult> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/test-run`,file,rawBody(file))).data.run,
  previewScope: async (id:string,scopeId:string,file:Blob) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/scope-preview/${encodeURIComponent(scopeId)}`,file,rawBody(file))).data as {run_id:string;debug_images:DebugImageRef[]},
  debugImage: async (runId:string,key:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/debug/${encodeURIComponent(runId)}/${encodeURIComponent(key)}`,{responseType:'blob'})).data,
  readTrigger: async (id:string):Promise<boolean> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/iot/trigger`)).data.triggered,
  pulse: async (id:string,result:'ok'|'ng',seconds?:number) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/iot/pulse`,{result,seconds})).data,
  scanBasler: async () => (await axiosClient.get(`${api_version}/computer-vision/cameras/basler/scan`)).data as {success:boolean;devices:BaslerDevice[];error?:string},
  captureCamera: async (id:string):Promise<Blob> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/camera/capture`,null,{responseType:'blob',timeout:120000})).data,
  focusCamera: async (id:string,payload:{x:number;y:number;w:number;h:number;focal_length?:number|null}) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/camera/focus`,payload)).data,
  runnerStart: async (id:string):Promise<TriggerRunnerStatus> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/runner/start`)).data.status,
  runnerStop: async (id:string):Promise<TriggerRunnerStatus> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/runner/stop`)).data.status,
  runnerStatus: async (id:string):Promise<TriggerRunnerStatus> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/runner/status`)).data.status,
};
