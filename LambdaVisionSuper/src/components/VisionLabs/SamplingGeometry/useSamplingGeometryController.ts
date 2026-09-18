import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SamplingGeometryAPI } from '../../../api/samplingGeometryApi';
import { LabServiceAPI, type LabServiceDefinition } from '../../../api/labServiceApi';
import type {
  ActiveSamplingWorkspace, ExecutionMode, SamplingArtifact, SamplingOperatorManifest,
  SamplingPipelineDefinition, SamplingStackItem, SourceBoardConfig, SourceBoardManifest,
  SpatialSamplingUnit, WorkspaceState,
} from './types';

const blankPin = () => ({ service_id: '', version: null, output_name: '' });
const defaultSourceBoard = (): SourceBoardConfig => ({ image_service: blankPin(), enable_geometry: false });
const defaultSpectralState = (): WorkspaceState => ({ stack: [], selectedNodeId: null, selectedPort: null, sourceName: 'inspected_image', timings: {}, pending: false });
const defaultsFor = (operator: SamplingOperatorManifest) => Object.fromEntries(Object.entries(operator.parameters ?? {}).map(([name, spec]) => [name, spec.default]));
const makeId = (prefix: string) => `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2,7)}`;
const firstEntry = <T,>(record: Record<string,T>): [string,T] | null => { const e=Object.entries(record)[0]; return e ? e as [string,T] : null; };
const safeAlias = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'') || 'data';

export const buildSpectralPipeline = (state: WorkspaceState, sourceBoard: SourceBoardConfig): SamplingPipelineDefinition => {
  const nodes = state.stack.map((item) => ({ id:item.id, operator_id:item.operator.id, operator_version:item.operator.version, parameters:{...item.parameters}, enabled:item.enabled }));
  const connections: any[]=[]; const inputs:Record<string,any>={}; const input_sources:Record<string,string>={};
  state.stack.forEach((item,index)=>{
    const primary=firstEntry(item.operator.inputs);
    if (primary) {
      if (index===0) { const alias=`primary__${item.id}__${primary[0]}`; inputs[alias]={node_id:item.id,port:primary[0]}; input_sources[alias]=state.sourceName; }
      else { const prev=firstEntry(state.stack[index-1].operator.outputs); if(prev) connections.push({source:{node_id:state.stack[index-1].id,port:prev[0]},target:{node_id:item.id,port:primary[0]}}); }
    }
  });
  const outputs:Record<string,any>={};
  state.stack.forEach((item)=>Object.entries(item.exposedOutputs).forEach(([port,alias])=>{ if(alias) outputs[alias]={node_id:item.id,port}; }));
  if(!Object.keys(outputs).length && state.stack.length){ const last=state.stack.at(-1)!; const out=firstEntry(last.operator.outputs); if(out) outputs.result={node_id:last.id,port:out[0]}; }
  return { version:3, workspace:'spectral', nodes, connections, inputs, outputs, input_sources, source_board:sourceBoard };
};

export const buildSpatialPipeline = (units: SpatialSamplingUnit[], sourceBoard: SourceBoardConfig): SamplingPipelineDefinition => {
  const nodes:any[]=[]; const connections:any[]=[]; const inputs:Record<string,any>={}; const input_sources:Record<string,string>={}; const outputs:Record<string,any>={};
  units.forEach((unit)=>{
    const housingId=`${unit.id}__housing`; const extractorId=`${unit.id}__extractor`;
    nodes.push({id:housingId,operator_id:unit.housing.id,operator_version:unit.housing.version,parameters:{...unit.housingParameters},enabled:true});
    nodes.push({id:extractorId,operator_id:unit.extractor.id,operator_version:unit.extractor.version,parameters:{...unit.extractorParameters},enabled:true});
    const housingInput=firstEntry(unit.housing.inputs); if(housingInput){ const alias=`${unit.id}__housing_image`; inputs[alias]={node_id:housingId,port:housingInput[0]}; input_sources[alias]='inspected_image'; }
    connections.push({source:{node_id:housingId,port:'housing'},target:{node_id:extractorId,port:'housing'}});
    const refAlias=`${unit.id}__extractor_image`; inputs[refAlias]={node_id:extractorId,port:'image'}; input_sources[refAlias]='inspected_image';
    if(unit.exposedAlias) outputs[unit.exposedAlias]={node_id:extractorId,port:'data'};
    // Keep data artifact in final result for editor runs even when not exposed.
    outputs[`__editor_${unit.id}`]={node_id:extractorId,port:'data'};
  });
  return { version:3, workspace:'spatial', nodes, connections, inputs, outputs, input_sources, source_board:sourceBoard };
};

export const useSamplingGeometryController = () => {
  const [searchParams] = useSearchParams();
  const editServiceId = searchParams.get('editService');
  const [sessionId,setSessionId]=useState<string|null>(null);
  const [operators,setOperators]=useState<SamplingOperatorManifest[]>([]);
  const [services,setServices]=useState<LabServiceDefinition[]>([]);
  const [workspace,setWorkspace]=useState<ActiveSamplingWorkspace>('spatial');
  const [executionMode,setExecutionMode]=useState<ExecutionMode>('manual');
  const [inputFile,setInputFile]=useState<File|null>(null);
  const [sourceBoardConfig,setSourceBoardConfig]=useState<SourceBoardConfig>(defaultSourceBoard());
  const [sourceBoard,setSourceBoard]=useState<SourceBoardManifest|null>(null);
  const [sourceUrls,setSourceUrls]=useState<Record<string,string>>({});
  const [spatialUnits,setSpatialUnits]=useState<SpatialSamplingUnit[]>([]);
  const [spectralState,setSpectralState]=useState<WorkspaceState>(defaultSpectralState());
  const [artifact,setArtifact]=useState<SamplingArtifact|null>(null);
  const [artifactPreviewUrl,setArtifactPreviewUrl]=useState<string|null>(null);
  const [inspector,setInspector]=useState<{nodeId:string;port:string;title:string}|null>(null);
  const [fftNodeId,setFftNodeId]=useState<string|null>(null);
  const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  const [serviceName,setServiceName]=useState('Sampling Service');
  const [editingService,setEditingService]=useState<LabServiceDefinition|null>(null);
  const liveTimer=useRef<number|null>(null);

  const revoke=(url?:string|null)=>{ if(url) URL.revokeObjectURL(url); };
  const refreshServices=useCallback(async()=>{ try{setServices(await LabServiceAPI.list());}catch{} },[]);
  useEffect(()=>{ let active=true; let created:string|null=null; (async()=>{ try{ const [session,catalog]=await Promise.all([SamplingGeometryAPI.createSession(),SamplingGeometryAPI.operators()]); if(!active)return; created=session.session_id; setSessionId(created); setOperators(catalog.filter((op)=>op.catalog_visible!==false && op.workspace!=='geometry')); await refreshServices(); }catch(e:any){setError(e?.message||'Failed to initialize Sampling LAB');} })(); return()=>{active=false;if(created)SamplingGeometryAPI.closeSession(created).catch(()=>{});Object.values(sourceUrls).forEach(revoke);revoke(artifactPreviewUrl);};},[]);

  const imageServices=useMemo(()=>services.filter((service)=>service.lab_type==='image_processing' && Object.values(service.inputs).filter((p)=>p.type==='image').length===1),[services]);
  const housingOperators=useMemo(()=>operators.filter((op)=>op.workspace==='spatial' && op.id.startsWith('sampling.spatial.housing.')),[operators]);
  const extractorOperator=useMemo(()=>operators.find((op)=>op.id==='sampling.spatial.data_extractor')??null,[operators]);
  const spectralOperators=useMemo(()=>operators.filter((op)=>op.workspace==='spectral'),[operators]);

  const buildBoard=useCallback(async()=>{ if(!sessionId||!inputFile)return; try{setBusy(true);setError('');const manifest=await SamplingGeometryAPI.buildSourceBoard(sessionId,inputFile,{...sourceBoardConfig,enable_geometry:false});setSourceBoard(manifest);const next:Record<string,string>={};for(const name of ['raw_image','inspected_image']){try{const blob=await SamplingGeometryAPI.sourcePreview(sessionId,name);next[name]=URL.createObjectURL(blob);}catch{}}setSourceUrls((old)=>{Object.values(old).forEach(revoke);return next;});setArtifact(null);revoke(artifactPreviewUrl);setArtifactPreviewUrl(null);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Failed to build Sampling Source Board');}finally{setBusy(false);}},[sessionId,inputFile,sourceBoardConfig,artifactPreviewUrl]);

  const addSpatialUnit=(housing:SamplingOperatorManifest)=>{ if(!extractorOperator)return; const id=makeId('unit'); setSpatialUnits((units)=>[...units,{id,name:`${housing.label} ${units.length+1}`,housing,housingParameters:defaultsFor(housing),extractor:extractorOperator,extractorParameters:defaultsFor(extractorOperator),visible:true,exposedAlias:'',housingArtifact:null,blocksArtifact:null,dataArtifact:null}]); };
  const updateUnit=(id:string,patch:Partial<SpatialSamplingUnit>)=>setSpatialUnits((units)=>units.map((unit)=>unit.id===id?{...unit,...patch}:unit));
  const updateHousingParam=(id:string,name:string,value:any)=>setSpatialUnits((units)=>units.map((u)=>u.id===id?{...u,housingParameters:{...u.housingParameters,[name]:value}}:u));
  const updateExtractorParam=(id:string,name:string,value:any)=>setSpatialUnits((units)=>units.map((u)=>u.id===id?{...u,extractorParameters:{...u.extractorParameters,[name]:value}}:u));
  const removeUnit=(id:string)=>setSpatialUnits((units)=>units.filter((u)=>u.id!==id));
  const toggleUnitVisible=(id:string)=>setSpatialUnits((units)=>units.map((u)=>u.id===id?{...u,visible:!u.visible}:u));
  const toggleUnitExpose=(id:string)=>setSpatialUnits((units)=>units.map((u)=>u.id===id?{...u,exposedAlias:u.exposedAlias?'':safeAlias(u.name)}:u));
  const setUnitExposeName=(id:string,name:string)=>setSpatialUnits((units)=>units.map((u)=>u.id===id?{...u,exposedAlias:name.replace(/[^A-Za-z0-9_]/g,'_')}:u));

  const fetchSpatialArtifacts=useCallback(async()=>{ if(!sessionId)return; const next=[] as SpatialSamplingUnit[]; for(const unit of spatialUnits){ const housingId=`${unit.id}__housing`; const extractorId=`${unit.id}__extractor`; let housingArtifact=null,blocksArtifact=null,dataArtifact=null; try{housingArtifact=await SamplingGeometryAPI.artifact(sessionId,housingId,'housing');}catch{} try{blocksArtifact=await SamplingGeometryAPI.artifact(sessionId,extractorId,'blocks');}catch{} try{dataArtifact=await SamplingGeometryAPI.artifact(sessionId,extractorId,'data');}catch{} next.push({...unit,housingArtifact,blocksArtifact,dataArtifact}); } setSpatialUnits(next);},[sessionId,spatialUnits]);

  const runSpatial=useCallback(async()=>{ if(!sessionId||!sourceBoard||!spatialUnits.length)return; try{setBusy(true);setError('');const pipeline=buildSpatialPipeline(spatialUnits,{...sourceBoardConfig,enable_geometry:false});await SamplingGeometryAPI.setPipeline(sessionId,pipeline);await SamplingGeometryAPI.run(sessionId);await fetchSpatialArtifacts();}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Spatial Sampling run failed');}finally{setBusy(false);}},[sessionId,sourceBoard,spatialUnits,sourceBoardConfig,fetchSpatialArtifacts]);

  const fetchArtifact=useCallback(async(nodeId:string,port:string,title:string)=>{if(!sessionId)return;try{const next=await SamplingGeometryAPI.artifact(sessionId,nodeId,port);setArtifact(next);setInspector({nodeId,port,title});setFftNodeId((next as any).type==='spectrum_2d'?nodeId:null);revoke(artifactPreviewUrl);if(['spectrum_2d','image','binary_mask','composed_data','data_block_set'].includes((next as any).type)){try{const blob=await SamplingGeometryAPI.artifactPreview(sessionId,nodeId,port);setArtifactPreviewUrl(URL.createObjectURL(blob));}catch{setArtifactPreviewUrl(null);}}else setArtifactPreviewUrl(null);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Inspect failed');}},[sessionId,artifactPreviewUrl]);
  const inspectUnit=(id:string,kind:'housing'|'blocks'|'data')=>{const unit=spatialUnits.find((u)=>u.id===id);if(!unit)return;const nodeId=kind==='housing'?`${id}__housing`:`${id}__extractor`;const port=kind==='housing'?'housing':kind;void fetchArtifact(nodeId,port,`${unit.name} · ${kind}`);};

  const selectSpectralNode=(id:string,port?:string)=>setSpectralState((s)=>({...s,selectedNodeId:id,selectedPort:port??firstEntry(s.stack.find((i)=>i.id===id)?.operator.outputs??{})?.[0]??null}));

  const addSpectral=(operator:SamplingOperatorManifest)=>{const item:SamplingStackItem={id:makeId('spec'),operator,parameters:defaultsFor(operator),enabled:true,referenceBindings:{},exposedOutputs:{}};setSpectralState((s)=>({...s,stack:[...s.stack,item],selectedNodeId:item.id,selectedPort:firstEntry(operator.outputs)?.[0]??null,pending:true}));};
  const updateSpectralParameter=(id:string,name:string,value:any)=>setSpectralState((s)=>({...s,stack:s.stack.map((i)=>i.id===id?{...i,parameters:{...i.parameters,[name]:value}}:i),pending:true}));
  const moveSpectral=(id:string,delta:number)=>setSpectralState((s)=>{const index=s.stack.findIndex((i)=>i.id===id),target=index+delta;if(index<0||target<0||target>=s.stack.length)return s;const n=[...s.stack];[n[index],n[target]]=[n[target],n[index]];return{...s,stack:n,pending:true};});
  const removeSpectral=(id:string)=>setSpectralState((s)=>({...s,stack:s.stack.filter((i)=>i.id!==id),pending:true}));
  const toggleSpectralExpose=(id:string,port:string)=>setSpectralState((s)=>({...s,stack:s.stack.map((i)=>{if(i.id!==id)return i;const out={...i.exposedOutputs};if(out[port])delete out[port];else out[port]=safeAlias(`${i.operator.label}_${port}`);return{...i,exposedOutputs:out};})}));
  const setSpectralExposeName=(id:string,port:string,name:string)=>setSpectralState((s)=>({...s,stack:s.stack.map((i)=>i.id===id?{...i,exposedOutputs:{...i.exposedOutputs,[port]:name.replace(/[^A-Za-z0-9_]/g,'_') }}:i)}));
  const runSpectral=useCallback(async()=>{if(!sessionId||!sourceBoard||!spectralState.stack.length)return;try{setBusy(true);setError('');const pipeline=buildSpectralPipeline(spectralState,{...sourceBoardConfig,enable_geometry:false});await SamplingGeometryAPI.setPipeline(sessionId,pipeline);const result=await SamplingGeometryAPI.run(sessionId);setSpectralState((s)=>({...s,timings:result.result?.timings_ms??{},pending:false}));const target=spectralState.stack.at(-1)!;const port=firstEntry(target.operator.outputs)?.[0];if(port)await fetchArtifact(target.id,port,`${target.operator.label} · ${port}`);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Spectral run failed');}finally{setBusy(false);}},[sessionId,sourceBoard,spectralState,sourceBoardConfig,fetchArtifact]);

  const runNow=workspace==='spatial'?runSpatial:runSpectral;
  const spatialConfigSignature=useMemo(()=>JSON.stringify(spatialUnits.map((u)=>({id:u.id,housing:u.housing.id,housingParameters:u.housingParameters,extractorParameters:u.extractorParameters}))),[spatialUnits]);
  useEffect(()=>{if(executionMode!=='live'||!sourceBoard)return;if(liveTimer.current)window.clearTimeout(liveTimer.current);liveTimer.current=window.setTimeout(()=>{void runNow();},220);return()=>{if(liveTimer.current)window.clearTimeout(liveTimer.current);};},[executionMode,workspace,spatialConfigSignature,spectralState.pending,sourceBoard]);

  const deploy=async(saveAsNew=false)=>{try{setBusy(true);setError('');let pipeline:SamplingPipelineDefinition;let outputs:Record<string,any>={};if(workspace==='spatial'){pipeline=buildSpatialPipeline(spatialUnits,{...sourceBoardConfig,enable_geometry:false});spatialUnits.forEach((u)=>{if(u.exposedAlias)outputs[u.exposedAlias]={node_id:`${u.id}__extractor`,port:'data',label:`${u.name} · composed data`};});}else{pipeline=buildSpectralPipeline(spectralState,{...sourceBoardConfig,enable_geometry:false});spectralState.stack.forEach((item)=>Object.entries(item.exposedOutputs).forEach(([port,alias])=>{if(alias)outputs[alias]={node_id:item.id,port,label:`${item.operator.label} · ${port}`};}));}if(!Object.keys(outputs).length)throw new Error('Expose at least one extracted/analysis output before deploy.');const service=await LabServiceAPI.deploy({service_id:saveAsNew?null:editingService?.service_id??null,name:serviceName,lab_type:'sampling_geometry',workspace_type:workspace,pipeline_snapshot:pipeline,outputs,description:`Sampling LAB v0.3 · ${workspace}`});setEditingService(service);setServiceName(service.name);await refreshServices();}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Deploy failed');}finally{setBusy(false);}};

  useEffect(()=>{if(!editServiceId||!operators.length)return;(async()=>{try{const service=await LabServiceAPI.get(editServiceId);if(service.lab_type!=='sampling_geometry')return;const pipeline=service.pipeline_snapshot as SamplingPipelineDefinition;setEditingService(service);setServiceName(service.name);setSourceBoardConfig({...defaultSourceBoard(),...(pipeline.source_board as any??{}),enable_geometry:false});if(service.workspace_type==='spatial'){const opMap=new Map(operators.map((o)=>[o.id,o]));const units:SpatialSamplingUnit[]=[];for(const node of pipeline.nodes??[]){if(!node.operator_id.startsWith('sampling.spatial.housing.'))continue;const housing=opMap.get(node.operator_id);const extractorNode=(pipeline.nodes??[]).find((n:any)=>n.id===node.id.replace('__housing','__extractor'));const extractor=opMap.get('sampling.spatial.data_extractor');if(!housing||!extractor||!extractorNode)continue;const unitId=node.id.replace(/__housing$/,'');const exposed=Object.entries(service.outputs??{}).find(([,b]:any)=>b.node_id===extractorNode.id && b.port==='data');units.push({id:unitId,name:housing.label,housing,housingParameters:{...node.parameters},extractor,extractorParameters:{...extractorNode.parameters},visible:true,exposedAlias:exposed?.[0]??''});}setSpatialUnits(units);setWorkspace('spatial');}else{const opMap=new Map(operators.map((o)=>[o.id,o]));const stack:SamplingStackItem[]=(pipeline.nodes??[]).map((node:any)=>{const op=opMap.get(node.operator_id);if(!op)return null;const exposedOutputs:Record<string,string>={};Object.entries(service.outputs??{}).forEach(([alias,b]:any)=>{if(b.node_id===node.id)exposedOutputs[b.port]=alias;});return{id:node.id,operator:op,parameters:{...node.parameters},enabled:node.enabled!==false,referenceBindings:{},exposedOutputs};}).filter(Boolean) as any;setSpectralState({...defaultSpectralState(),stack,pending:true});setWorkspace('spectral');}}catch(e:any){setError(e?.message||'Failed to load Sampling service');}})();},[editServiceId,operators.length]);

  const channelPreview=async(channel:string)=>{if(!sessionId)return null;try{const blob=await SamplingGeometryAPI.channelPreview(sessionId,'inspected_image',channel);return URL.createObjectURL(blob);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Channel preview failed');return null;}};

  const inspectSource=async(name:string)=>{if(!sessionId)return;try{const next=await SamplingGeometryAPI.sourceArtifact(sessionId,name);setArtifact(next);setInspector({nodeId:`source:${name}`,port:name,title:`Source · ${name}`});setFftNodeId(null);revoke(artifactPreviewUrl);if(['image','binary_mask'].includes((next as any).type)){const blob=await SamplingGeometryAPI.sourcePreview(sessionId,name);setArtifactPreviewUrl(URL.createObjectURL(blob));}else setArtifactPreviewUrl(null);}catch(e:any){setError(e?.response?.data?.detail||e?.message||'Source inspect failed');}};
  const inspectInlineBlock=(block:any)=>{setArtifact({type:'data_block_set',count:1,blocks:[block]} as any);setArtifactPreviewUrl(null);setInspector({nodeId:'inline:block',port:'block',title:block.label});};
  const fftReconstruct=async(params:Record<string,any>)=>{if(!sessionId||!fftNodeId)return null;const blob=await SamplingGeometryAPI.fftReconstruction(sessionId,fftNodeId,params);return URL.createObjectURL(blob);};

  return { sessionId,workspace,setWorkspace,executionMode,setExecutionMode,inputFile,setInputFile,sourceBoardConfig,setSourceBoardConfig,sourceBoard,sourceUrls,imageServices,housingOperators,extractorOperator,spectralOperators,spatialUnits,spectralState,artifact,artifactPreviewUrl,inspector,setInspector,busy,error,setError,serviceName,setServiceName,editingService,buildBoard,addSpatialUnit,updateUnit,updateHousingParam,updateExtractorParam,removeUnit,toggleUnitVisible,toggleUnitExpose,setUnitExposeName,runNow,inspectUnit,addSpectral,selectSpectralNode,updateSpectralParameter,moveSpectral,removeSpectral,toggleSpectralExpose,setSpectralExposeName,fetchArtifact,deploy,inspectSource,inspectInlineBlock,fftReconstruct,channelPreview,services};
};
