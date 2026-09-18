import { axiosClient, api_version } from './axiosClient';

export type RoiSearchMethod = 'manual' | 'blur_template' | 'fourier';

export interface NormalizedRect { x:number; y:number; w:number; h:number; }
export interface ServicePin { service_id:string; version?:number|null; output_name:string; }
export interface GeometryConstraint { enabled:boolean; search_margin_px:number; max_shift_px:number; }
export interface RoiSearchConfig { method:RoiSearchMethod; blur_kernel:number; template_threshold:number; geometry:GeometryConstraint; }
export interface MasterRoi { roi_id:string; name:string; rect:NormalizedRect; search:RoiSearchConfig; enabled:boolean; }
export interface ModbusIOConfig {
  enabled:boolean; host:string; port:number; device_id:number;
  trigger_kind:'discrete_input'|'coil'; trigger_address:number; trigger_active_high:boolean;
  ok_coil:number; ng_coil:number; pulse_seconds:number; poll_interval_ms:number;
}
export interface DecisionRule {
  mode:'service_success'|'scalar_gt'|'scalar_gte'|'scalar_lt'|'scalar_lte'|'scalar_eq';
  output_name:string; value_path:string; threshold:number;
}
export interface WorkingServiceBinding {
  binding_id:string; service_id:string; version?:number|null; enabled:boolean; label:string; decision:DecisionRule;
}
export interface VisionProgramDefinition {
  version:number; program_id:string; name:string; description:string;
  io:ModbusIOConfig;
  master:{rois:MasterRoi[]; master_shape:number[]};
  working:{global_services:WorkingServiceBinding[]; station_services:Record<string,WorkingServiceBinding[]>};
}
export interface LocatedRoi { roi_id:string; name:string; rect:NormalizedRect; score:number; method:string; found:boolean; message:string; }
export interface VisionRunResult {
  program_id:string; global_ok:boolean; overall_ok:boolean; located_rois:LocatedRoi[]; total_ms:number;
  global_services:any[]; stations:any[];
}

export const VisionAppAPI = {
  listPrograms: async () => (await axiosClient.get(`${api_version}/computer-vision/programs`)).data.programs as (VisionProgramDefinition & {master_exists?:boolean})[],
  newProgram: async (name:string) => (await axiosClient.post(`${api_version}/computer-vision/programs/new`, {name})).data as {program:VisionProgramDefinition;master_exists:boolean},
  getProgram: async (id:string) => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}`)).data as {program:VisionProgramDefinition;master_exists:boolean},
  saveProgram: async (program:VisionProgramDefinition) => (await axiosClient.put(`${api_version}/computer-vision/programs/${encodeURIComponent(program.program_id)}`, program)).data.program as VisionProgramDefinition,
  removeProgram: async (id:string) => { await axiosClient.delete(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}`); },
  uploadMaster: async (id:string,file:File) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master`, file, {headers:{'Content-Type':'application/octet-stream'},transformRequest:[(d)=>d]})).data,
  masterPreview: async (id:string):Promise<Blob> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/master`,{responseType:'blob'})).data,
  locateRois: async (id:string,file:File):Promise<LocatedRoi[]> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/locate-rois`,file,{headers:{'Content-Type':'application/octet-stream'},transformRequest:[(d)=>d],timeout:60000})).data.rois,
  runTest: async (id:string,file:File):Promise<VisionRunResult> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/test-run`,file,{headers:{'Content-Type':'application/octet-stream'},transformRequest:[(d)=>d],timeout:120000})).data.run,
  readTrigger: async (id:string):Promise<boolean> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/iot/trigger`)).data.triggered,
  pulse: async (id:string,result:'ok'|'ng',seconds?:number) => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/iot/pulse`,{result,seconds})).data,
};
