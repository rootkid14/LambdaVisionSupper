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
  version:6,
  program_kind:'sampling_program_v2',
  source_board:defaultSourceBoard(),
  input_source:'inspected_image',
  global_domain:{methods:[]},
  local_domain:{grid:{rows:4,cols:6,gap_px:0},methods:[]},
  output_shape:{
    global_layout:'vector',
    local_layout:'matrix',
    local_vector_order:'patch_major',
    local_matrix_axis:'patch_rows',
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

const migrateV1=(snapshot:any):SamplingProgramDefinition=>{
  if(snapshot?.program_kind!=='sampling_program_v1') return {...defaultProgram(),...snapshot,version:6,program_kind:'sampling_program_v2'};
  const old=snapshot.output_shape??{};
  return {
    ...defaultProgram(),
    ...snapshot,
    version:6,
    program_kind:'sampling_program_v2',
    output_shape:{
      global_layout:'vector',
      local_layout:old.local_layout==='flatten'?'vector':'matrix',
      local_vector_order:old.local_order==='feature_major'?'feature_major':'patch_major',
      local_matrix_axis:old.local_order==='feature_major'?'patch_columns':'patch_rows',
      include_global:old.include_global!==false,
      include_local:old.include_local!==false,
      include_combined:!!old.include_combined,
    },
  };
};

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
  const [formulationDirty,setFormulationDirty]=useState(false);
  const [executionMode,setExecutionMode]=useState<'live'|'manual'>('manual');
  const [busy,setBusy]=useState(false);
  const [formulating,setFormulating]=useState(false);
  const [error,setError]=useState('');
  const [serviceName,setServiceName]=useState('Sampling Program');
  const [editingService,setEditingService]=useState<LabServiceDefinition|null>(null);
  const liveRunTimer=useRef<number|null>(null);
  const liveFormulateTimer=useRef<number|null>(null);

  const refreshServices=useCallback(async()=>{
    const services=await LabServiceAPI.list();
    setImageServices(services.filter((s)=>s.lab_type==='image_processing'));
  },[]);

  useEffect(()=>{let alive=true;(async()=>{try{const [session,methods]=await Promise.all([SamplingGeometryAPI.createSession(),SamplingGeometryAPI.programMethods(),refreshServices().then(()=>null)]);if(!alive)return;setSessionId(session.session_id);setCatalog(methods);}catch(e:any){setError(e?.message||'Failed to initialize Sampling LAB');}})();return()=>{alive=false;if(sessionId)void SamplingGeometryAPI.closeSession(sessionId);revoke(sourceUrl);};},[]);

  const invalidateSampling=()=>{setRun(null);setFormulationDirty(false);};

  const buildBoard=useCallback(async()=>{if(!sessionId||!inputFile)return;try{setBusy(true);setError('');const cfg={...sourceBoardConfig,enable_geometry:false};const manifest=await SamplingGeometryAPI.buildSourceBoard(sessionId,inputFile,cfg);setSourceBoard(manifest);setProgram((p)=>({...p,source_board:cfg,input_source:'inspected_image'}));const blob=await SamplingGeometryAPI.sourcePreview(sessionId,'inspected_image');revoke(sourceUrl);setSourceUrl(URL.createObjectURL(blob));invalidateSampling();}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Build Source failed');}finally{setBusy(false);}},[sessionId,inputFile,sourceBoardConfig,sourceUrl]);

  const methods=activeDomain==='global'?program.global_domain.methods:program.local_domain.methods;
  const selectedMethod=methods.find((m)=>m.id===selectedMethodId)??null;

  const addMethod=(item:SamplingMethodCatalogItem)=>{const method=defaultMethod(item);setProgram((p)=>activeDomain==='global'?{...p,global_domain:{methods:[...p.global_domain.methods,method]}}:{...p,local_domain:{...p.local_domain,methods:[...p.local_domain.methods,method]}});setSelectedMethodId(method.id);invalidateSampling();};
  const updateMethod=(methodId:string,patch:Partial<SamplingMethodDefinition>)=>{setProgram((p)=>{const update=(list:SamplingMethodDefinition[])=>list.map((m)=>m.id===methodId?{...m,...patch}:m);return activeDomain==='global'?{...p,global_domain:{methods:update(p.global_domain.methods)}}:{...p,local_domain:{...p.local_domain,methods:update(p.local_domain.methods)}};});invalidateSampling();};
  const removeMethod=(methodId:string)=>{setProgram((p)=>activeDomain==='global'?{...p,global_domain:{methods:p.global_domain.methods.filter((m)=>m.id!==methodId)}}:{...p,local_domain:{...p.local_domain,methods:p.local_domain.methods.filter((m)=>m.id!==methodId)}});if(selectedMethodId===methodId)setSelectedMethodId(null);invalidateSampling();};
  const moveMethod=(methodId:string,delta:number)=>{setProgram((p)=>{const move=(list:SamplingMethodDefinition[])=>{const next=[...list],index=next.findIndex((m)=>m.id===methodId),target=index+delta;if(index<0||target<0||target>=next.length)return next;[next[index],next[target]]=[next[target],next[index]];return next;};return activeDomain==='global'?{...p,global_domain:{methods:move(p.global_domain.methods)}}:{...p,local_domain:{...p.local_domain,methods:move(p.local_domain.methods)}};});invalidateSampling();};
  const setLocalGrid=(patch:Partial<SamplingProgramDefinition['local_domain']['grid']>)=>{setProgram((p)=>({...p,local_domain:{...p.local_domain,grid:{...p.local_domain.grid,...patch}}}));invalidateSampling();};
  const setOutputShape=(patch:Partial<SamplingProgramDefinition['output_shape']>)=>{setProgram((p)=>({...p,output_shape:{...p.output_shape,...patch}}));if(run)setFormulationDirty(true);};

  const runNow=useCallback(async()=>{if(!sessionId||!sourceBoard)return;try{setBusy(true);setError('');const result=await SamplingGeometryAPI.runProgram(sessionId,{...program,source_board:{...sourceBoardConfig,enable_geometry:false}});setRun(result);setFormulationDirty(false);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Sampling Program run failed');}finally{setBusy(false);}},[sessionId,sourceBoard,program,sourceBoardConfig]);

  const formulateNow=useCallback(async()=>{if(!sessionId||!sourceBoard||!run)return;try{setFormulating(true);setError('');const result=await SamplingGeometryAPI.formulateProgram(sessionId,{...program,source_board:{...sourceBoardConfig,enable_geometry:false}});setRun(result);setFormulationDirty(false);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Formulation failed. If sampling parameters changed, Run Program again.');}finally{setFormulating(false);}},[sessionId,sourceBoard,run,program,sourceBoardConfig]);

  const samplingSignature=useMemo(()=>JSON.stringify({source_board:program.source_board,input_source:program.input_source,global_domain:program.global_domain,local_domain:program.local_domain}),[program.source_board,program.input_source,program.global_domain,program.local_domain]);
  const formulationSignature=useMemo(()=>JSON.stringify(program.output_shape),[program.output_shape]);
  useEffect(()=>{if(executionMode!=='live'||!sourceBoard)return;if(liveRunTimer.current)window.clearTimeout(liveRunTimer.current);liveRunTimer.current=window.setTimeout(()=>void runNow(),260);return()=>{if(liveRunTimer.current)window.clearTimeout(liveRunTimer.current);};},[executionMode,sourceBoard,samplingSignature]);
  useEffect(()=>{if(executionMode!=='live'||!sourceBoard||!run||!formulationDirty)return;if(liveFormulateTimer.current)window.clearTimeout(liveFormulateTimer.current);liveFormulateTimer.current=window.setTimeout(()=>void formulateNow(),120);return()=>{if(liveFormulateTimer.current)window.clearTimeout(liveFormulateTimer.current);};},[executionMode,sourceBoard,formulationSignature,formulationDirty]);

  const channelPreview=async(channel:string)=>{if(!sessionId)return null;try{const blob=await SamplingGeometryAPI.channelPreview(sessionId,'inspected_image',channel);return URL.createObjectURL(blob);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Channel preview failed');return null;}};
  const inspectSource=async(name:string)=>{if(!sessionId)return;try{const blob=await SamplingGeometryAPI.sourcePreview(sessionId,name);revoke(sourceUrl);setSourceUrl(URL.createObjectURL(blob));}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Source preview failed');}};

  const deploy=async(saveAsNew=false)=>{try{setBusy(true);setError('');const outputs:Record<string,any>={};if(program.output_shape.include_global)outputs.global_data={node_id:'sampling_program',port:'global_data',label:'Global vector'};if(program.output_shape.include_local)outputs.local_data={node_id:'sampling_program',port:'local_data',label:'Local vector / matrix'};if(program.output_shape.include_combined)outputs.combined_data={node_id:'sampling_program',port:'combined_data',label:'Combined flat vector'};if(!Object.keys(outputs).length)throw new Error('Expose at least one formulated output.');const service=await LabServiceAPI.deploy({service_id:saveAsNew?null:editingService?.service_id??null,name:serviceName,lab_type:'sampling_geometry',workspace_type:'sampling',pipeline_snapshot:{...program,source_board:{...sourceBoardConfig,enable_geometry:false}},outputs,description:'Sampling LAB v0.6 · Global/Local sampling → Vector/2-D Matrix formulation'});setEditingService(service);setServiceName(service.name);await refreshServices();}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Deploy failed');}finally{setBusy(false);}};

  useEffect(()=>{if(!editServiceId||!catalog.length)return;(async()=>{try{const service=await LabServiceAPI.get(editServiceId);if(service.lab_type!=='sampling_geometry')return;const snapshot:any=service.pipeline_snapshot;if(!['sampling_program_v1','sampling_program_v2'].includes(snapshot.program_kind)){setError('This is a legacy Sampling pipeline service. It remains runnable, but the v0.6 editor only edits Sampling Program services.');return;}const migrated=migrateV1(snapshot);setEditingService(service);setServiceName(service.name);setProgram({...migrated,source_board:{...defaultSourceBoard(),...(migrated.source_board??{}),enable_geometry:false}});setSourceBoardConfig({...defaultSourceBoard(),...(migrated.source_board??{}),enable_geometry:false});setRun(null);setFormulationDirty(false);}catch(e:any){setError(e?.message||'Failed to load Sampling service');}})();},[editServiceId,catalog.length]);

  return {sessionId,inputFile,setInputFile,sourceBoardConfig,setSourceBoardConfig,sourceBoard,sourceUrl,imageServices,catalog,activeDomain,setActiveDomain,selectedMethodId,setSelectedMethodId,selectedMethod,program,run,formulationDirty,executionMode,setExecutionMode,busy,formulating,error,setError,serviceName,setServiceName,editingService,buildBoard,addMethod,updateMethod,removeMethod,moveMethod,setLocalGrid,setOutputShape,runNow,formulateNow,channelPreview,inspectSource,deploy};
};
