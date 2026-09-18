import { axiosClient, api_version } from './axiosClient';

export interface ContourServicePin { service_id:string; version?:number|null; output_name:string; }
export interface EarlyContourFilter { min_area:number; min_perimeter:number; min_bbox_width:number; min_bbox_height:number; min_points:number; max_retained:number; }
export interface ContourSourceConfig { image_service:ContourServicePin; source_mode:'auto'|'canny'|'mask_boundary'; canny_low:number; canny_high:number; blur_kernel:number; retrieval:'list'|'external'|'tree'; early_filter:EarlyContourFilter; }
export interface ContourStage { id:string; kind:'metric_filter'|'largest_n'|'region_filter'|'simplify'; enabled:boolean; parameters:Record<string,any>; }
export interface ContourDefinition { version:number; source:ContourSourceConfig; stages:ContourStage[]; }

export const ContourExtractorAPI={
  createSession: async()=> (await axiosClient.post(`${api_version}/contour-extractor/sessions`)).data,
  closeSession: async(id:string)=>{await axiosClient.delete(`${api_version}/contour-extractor/sessions/${encodeURIComponent(id)}`);},
  setDefinition: async(id:string,definition:ContourDefinition)=> (await axiosClient.put(`${api_version}/contour-extractor/sessions/${encodeURIComponent(id)}/definition`,definition)).data,
  run: async(id:string,file:File,definition:ContourDefinition)=> { await ContourExtractorAPI.setDefinition(id,definition); return (await axiosClient.post(`${api_version}/contour-extractor/sessions/${encodeURIComponent(id)}/run`,file,{headers:{'Content-Type':'application/octet-stream'},timeout:120_000,transformRequest:[(d)=>d]})).data; },
  contours: async(id:string,selection='final',offset=0,limit=200)=> (await axiosClient.get(`${api_version}/contour-extractor/sessions/${encodeURIComponent(id)}/contours`,{params:{selection,offset,limit}})).data,
  geometry: async(id:string,ids:number[])=> (await axiosClient.get(`${api_version}/contour-extractor/sessions/${encodeURIComponent(id)}/contours/geometry`,{params:{ids:ids.join(',')}})).data.contours,
  preview: async(id:string,name:string):Promise<Blob>=> (await axiosClient.get(`${api_version}/contour-extractor/sessions/${encodeURIComponent(id)}/preview/${encodeURIComponent(name)}`,{params:{max_width:2200,quality:94},responseType:'blob'})).data,
};
