import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SamplingGeometryAPI } from '../../../api/samplingGeometryApi';
import { LabServiceAPI, type LabServiceDefinition } from '../../../api/labServiceApi';
import type { SourceBoardConfig, SourceBoardManifest } from '../SamplingGeometry/types';
import type {
  SamplingDomain,
  SamplingMethodCatalogItem,
  SamplingMethodDefinition,
  SamplingProgramDefinition,
  SamplingProgramRun,
} from './types';

const pin=()=>({service_id:'',version:null,output_name:''});
export const defaultSourceBoard=():SourceBoardConfig=>({image_service:pin(),enable_geometry:false});
const id=(kind:string)=>`${kind}_${Date.now()}_${Math.random().toString(36).slice(2,7)}`;

export const defaultProgram=():SamplingProgramDefinition=>({
  version:5,
  program_kind:'sampling_program_v1',
  source_board:defaultSourceBoard(),
  input_source:'inspected_image',
  global_domain:{methods:[]},
  local_domain:{grid:{rows:4,cols:6,gap_px:0},methods:[]},
  output_shape:{
    global_layout:'vector',
    local_layout:'spatial_tensor',
    local_order:'patch_major',
    include_global:true,
    include_local:true,
    include_combined:false,
  },
});

const defaultMethod=(item:SamplingMethodCatalogItem):SamplingMethodDefinition=>({
  id:id(item.kind),kind:item.kind,label:item.label,enabled:true,
  channels:['gray'],measures:[...item.default_measures],
  placement:{mode:item.supports_placement?'center':'domain',center_x:.5,center_y:.5,rows:2,cols:2},
  sampling_mode:'count',sample_count:64,sample_step:4,histogram_bins:16,
  parameters:item.kind==='rays'?{axis:'x',ray_count:5}:item.kind==='cross'?{length_ratio:.8}:item.kind==='rings'?{ring_count:3,max_radius_ratio:.4}:{},
});

const revoke=(url:string|null)=>{if(url?.startsWith('blob:'))URL.revokeObjectURL(url);};

export const useSamplingProgramController=()=>{
  const [search]=useSearchParams();
  const editServiceId=search.get('editService');
  const [sessionId,setSessionId]=useState<string|null>(null);
  const [inputFile,setInputFile]=useState<File|null>(null);
  const [sourceBoardConfig,setSourceBoardConfig]=useState<SourceBoardConfig>(defaultSourceBoard());
  const [sourceBoard,setSourceBoard]=useState<SourceBoardManifest|null>(null);
  const [sourceUrl,setSourceUrl]=useState<string|null>(null);
  const [imageServices,setImageServices]=useState<LabServiceDefinition[]>([]);
  const [catalog,setCatalog]=useState<SamplingMethodCatalogItem[]>([]);
  const [activeDomain,setActiveDomain]=useState<SamplingDomain>('global');
  const [selectedMethodId,setSelectedMethodId]=useState<string|null>(null);
  const [program,setProgram]=useState<SamplingProgramDefinition>(defaultProgram());
  const [run,setRun]=useState<SamplingProgramRun|null>(null);
  const [executionMode,setExecutionMode]=useState<'live'|'manual'>('manual');
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const [serviceName,setServiceName]=useState('Sampling Program');
  const [editingService,setEditingService]=useState<LabServiceDefinition|null>(null);
  const liveTimer=useRef<number|null>(null);

  const refreshServices=useCallback(async()=>{
    const services=await LabServiceAPI.list();
    setImageServices(services.filter((s)=>s.lab_type==='image_processing'));
  },[]);

  useEffect(()=>{let alive=true;(async()=>{try{const [session,methods]=await Promise.all([SamplingGeometryAPI.createSession(),SamplingGeometryAPI.programMethods(),refreshServices().then(()=>null)]);if(!alive)return;setSessionId(session.session_id);setCatalog(methods);}catch(e:any){setError(e?.message||'Failed to initialize Sampling LAB');}})();return()=>{alive=false;if(sessionId)void SamplingGeometryAPI.closeSession(sessionId);revoke(sourceUrl);};},[]);

  const buildBoard=useCallback(async()=>{if(!sessionId||!inputFile)return;try{setBusy(true);setError('');const cfg={...sourceBoardConfig,enable_geometry:false};const manifest=await SamplingGeometryAPI.buildSourceBoard(sessionId,inputFile,cfg);setSourceBoard(manifest);setProgram((p)=>({...p,source_board:cfg,input_source:'inspected_image'}));const blob=await SamplingGeometryAPI.sourcePreview(sessionId,'inspected_image');revoke(sourceUrl);setSourceUrl(URL.createObjectURL(blob));setRun(null);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Build Source failed');}finally{setBusy(false);}},[sessionId,inputFile,sourceBoardConfig,sourceUrl]);

  const methods=activeDomain==='global'?program.global_domain.methods:program.local_domain.methods;
  const selectedMethod=methods.find((m)=>m.id===selectedMethodId)??null;

  const addMethod=(item:SamplingMethodCatalogItem)=>{const method=defaultMethod(item);setProgram((p)=>activeDomain==='global'?{...p,global_domain:{methods:[...p.global_domain.methods,method]}}:{...p,local_domain:{...p.local_domain,methods:[...p.local_domain.methods,method]}});setSelectedMethodId(method.id);setRun(null);};
  const updateMethod=(methodId:string,patch:Partial<SamplingMethodDefinition>)=>{setProgram((p)=>{const update=(list:SamplingMethodDefinition[])=>list.map((m)=>m.id===methodId?{...m,...patch}:m);return activeDomain==='global'?{...p,global_domain:{methods:update(p.global_domain.methods)}}:{...p,local_domain:{...p.local_domain,methods:update(p.local_domain.methods)}};});setRun(null);};
  const removeMethod=(methodId:string)=>{setProgram((p)=>activeDomain==='global'?{...p,global_domain:{methods:p.global_domain.methods.filter((m)=>m.id!==methodId)}}:{...p,local_domain:{...p.local_domain,methods:p.local_domain.methods.filter((m)=>m.id!==methodId)}});if(selectedMethodId===methodId)setSelectedMethodId(null);setRun(null);};
  const moveMethod=(methodId:string,delta:number)=>{setProgram((p)=>{const move=(list:SamplingMethodDefinition[])=>{const next=[...list],index=next.findIndex((m)=>m.id===methodId),target=index+delta;if(index<0||target<0||target>=next.length)return next;[next[index],next[target]]=[next[target],next[index]];return next;};return activeDomain==='global'?{...p,global_domain:{methods:move(p.global_domain.methods)}}:{...p,local_domain:{...p.local_domain,methods:move(p.local_domain.methods)}};});setRun(null);};
  const setLocalGrid=(patch:Partial<SamplingProgramDefinition['local_domain']['grid']>)=>{setProgram((p)=>({...p,local_domain:{...p.local_domain,grid:{...p.local_domain.grid,...patch}}}));setRun(null);};
  const setOutputShape=(patch:Partial<SamplingProgramDefinition['output_shape']>)=>{setProgram((p)=>({...p,output_shape:{...p.output_shape,...patch}}));setRun(null);};

  const runNow=useCallback(async()=>{if(!sessionId||!sourceBoard)return;try{setBusy(true);setError('');const result=await SamplingGeometryAPI.runProgram(sessionId,{...program,source_board:{...sourceBoardConfig,enable_geometry:false}});setRun(result);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Sampling Program run failed');}finally{setBusy(false);}},[sessionId,sourceBoard,program,sourceBoardConfig]);

  const programSignature=useMemo(()=>JSON.stringify(program),[program]);
  useEffect(()=>{if(executionMode!=='live'||!sourceBoard)return;if(liveTimer.current)window.clearTimeout(liveTimer.current);liveTimer.current=window.setTimeout(()=>void runNow(),260);return()=>{if(liveTimer.current)window.clearTimeout(liveTimer.current);};},[executionMode,sourceBoard,programSignature]);

  const channelPreview=async(channel:string)=>{if(!sessionId)return null;try{const blob=await SamplingGeometryAPI.channelPreview(sessionId,'inspected_image',channel);return URL.createObjectURL(blob);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Channel preview failed');return null;}};

  const inspectSource=async(name:string)=>{if(!sessionId)return;try{const blob=await SamplingGeometryAPI.sourcePreview(sessionId,name);revoke(sourceUrl);setSourceUrl(URL.createObjectURL(blob));}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Source preview failed');}};

  const deploy=async(saveAsNew=false)=>{try{setBusy(true);setError('');const outputs:Record<string,any>={};if(program.output_shape.include_global)outputs.global_data={node_id:'sampling_program',port:'global_data',label:'Global composed data'};if(program.output_shape.include_local)outputs.local_data={node_id:'sampling_program',port:'local_data',label:'Local composed data'};if(program.output_shape.include_combined)outputs.combined_data={node_id:'sampling_program',port:'combined_data',label:'Combined flat data'};if(!Object.keys(outputs).length)throw new Error('Expose at least one output shape.');const service=await LabServiceAPI.deploy({service_id:saveAsNew?null:editingService?.service_id??null,name:serviceName,lab_type:'sampling_geometry',workspace_type:'sampling',pipeline_snapshot:{...program,source_board:{...sourceBoardConfig,enable_geometry:false}},outputs,description:'Sampling LAB v0.5 · Global/Local Sampling Program'});setEditingService(service);setServiceName(service.name);await refreshServices();}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Deploy failed');}finally{setBusy(false);}};

  useEffect(()=>{if(!editServiceId||!catalog.length)return;(async()=>{try{const service=await LabServiceAPI.get(editServiceId);if(service.lab_type!=='sampling_geometry')return;const snapshot=service.pipeline_snapshot as any;if(snapshot.program_kind!=='sampling_program_v1'){setError('This is a legacy Sampling service. It remains runnable, but v0.5 editor only edits Sampling Program v1 services.');return;}setEditingService(service);setServiceName(service.name);setProgram({...defaultProgram(),...snapshot,source_board:{...defaultSourceBoard(),...(snapshot.source_board??{}),enable_geometry:false}});setSourceBoardConfig({...defaultSourceBoard(),...(snapshot.source_board??{}),enable_geometry:false});}catch(e:any){setError(e?.message||'Failed to load Sampling service');}})();},[editServiceId,catalog.length]);

  return {sessionId,inputFile,setInputFile,sourceBoardConfig,setSourceBoardConfig,sourceBoard,sourceUrl,imageServices,catalog,activeDomain,setActiveDomain,selectedMethodId,setSelectedMethodId,selectedMethod,program,setProgram,methods,run,executionMode,setExecutionMode,busy,error,setError,serviceName,setServiceName,editingService,buildBoard,addMethod,updateMethod,removeMethod,moveMethod,setLocalGrid,setOutputShape,runNow,channelPreview,inspectSource,deploy};
};
