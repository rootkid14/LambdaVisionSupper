import { Activity, ArrowDown, ArrowUp, Bug, ChevronDown, ChevronRight, Layers3, Plus, SlidersHorizontal, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import type { LabServiceDefinition } from '../../api/labServiceApi';
import type { BenchmarkStep, MasterRoi, ScopePipelineConfig, WorkingServiceBinding } from '../../api/visionAppApi';
import { ScopeEditorModal } from './ScopeEditorModal';

type Phase='filter'|'logic';
type Props={
  services:LabServiceDefinition[];
  rois:MasterRoi[];
  globalScope:ScopePipelineConfig;
  stationScopes:Record<string,ScopePipelineConfig>;
  stationExecution:'sequential'|'parallel';
  benchmarks:BenchmarkStep[];
  debugCount:number;
  onGlobal:(s:ScopePipelineConfig)=>void;
  onStations:(s:Record<string,ScopePipelineConfig>)=>void;
  onExecution:(v:'sequential'|'parallel')=>void;
  onSelectStation?:(id:string)=>void;
  onOpenDebug:()=>void;
  onPreviewDebug:(scopeId:string)=>Promise<void>;
};

const empty=():ScopePipelineConfig=>({
  enable_filter:true,
  filter_services:[],
  enable_logic:true,
  logic_services:[],
  enable_decision:false,
  decision:{script:"if logic_ok:\n    result = 'OK'\nelse:\n    result = 'NG'\n"},
});
const makeBinding=(serviceId:string,index:number):WorkingServiceBinding=>({
  binding_id:`bind_${Date.now()}_${Math.random().toString(36).slice(2,7)}`,
  service_id:serviceId,
  version:null,
  enabled:true,
  label:'',
  alias:`logic_${index+1}`,
});

export const WorkingModulePanel=({services,rois,globalScope,stationScopes,stationExecution,benchmarks,debugCount,onGlobal,onStations,onExecution,onSelectStation,onOpenDebug,onPreviewDebug}:Props)=>{
  const [tab,setTab]=useState<'operation'|'benchmark'>('operation');
  const [scopeId,setScopeId]=useState('global');
  const [editor,setEditor]=useState<{phase:Phase;scopeName:string}|null>(null);
  const [open,setOpen]=useState<Record<Phase,boolean>>({filter:true,logic:true});
  const [quickChoice,setQuickChoice]=useState<Record<Phase,string>>({filter:'',logic:''});

  useEffect(()=>{if(scopeId!=='global'&&!rois.some(r=>r.roi_id===scopeId))setScopeId('global');},[rois,scopeId]);
  const roi=rois.find(r=>r.roi_id===scopeId);
  const scope=scopeId==='global'?globalScope:(stationScopes[scopeId]??empty());
  const scopeName=scopeId==='global'?'Global Scope':(roi?.name??'ROI Scope');
  const update=(next:ScopePipelineConfig)=>scopeId==='global'?onGlobal({...next,enable_decision:false}):onStations({...stationScopes,[scopeId]:{...next,enable_decision:false}});

  const candidates=useMemo(()=>({
    filter:services.filter(s=>s.lab_type==='image_processing'),
    logic:services.filter(s=>s.lab_type!=='image_processing'),
  }),[services]);
  const listFor=(phase:Phase)=>phase==='filter'?scope.filter_services:scope.logic_services;
  const setList=(phase:Phase,next:WorkingServiceBinding[])=>update(phase==='filter'?{...scope,filter_services:next}:{...scope,logic_services:next});
  const patchBinding=(phase:Phase,index:number,patch:Partial<WorkingServiceBinding>)=>{const next=[...listFor(phase)];next[index]={...next[index],...patch};setList(phase,next);};
  const moveBinding=(phase:Phase,index:number,delta:number)=>{const next=[...listFor(phase)];const j=index+delta;if(j<0||j>=next.length)return;[next[index],next[j]]=[next[j],next[index]];setList(phase,next);};
  const addQuick=(phase:Phase)=>{const id=quickChoice[phase];if(!id)return;const list=listFor(phase);setList(phase,[...list,makeBinding(id,list.length)]);setQuickChoice(v=>({...v,[phase]:''}));};

  const phasePanel=(phase:Phase)=>{
    const isFilter=phase==='filter';
    const enabled=isFilter?scope.enable_filter:scope.enable_logic;
    const list=listFor(phase);
    const active=list.filter(x=>x.enabled).length;
    const title=isFilter?'Filter & Processing':'Logic Services';
    return <div className="overflow-hidden rounded-lg border border-[#3c4043] bg-[#202124]">
      <div className="flex items-center gap-2 p-2.5">
        <button className="text-[#9aa0a6]" onClick={()=>setOpen(v=>({...v,[phase]:!v[phase]}))}>{open[phase]?<ChevronDown size={12}/>:<ChevronRight size={12}/>}</button>
        <label className="flex items-center gap-2"><input type="checkbox" checked={enabled} onChange={e=>update(isFilter?{...scope,enable_filter:e.target.checked}:{...scope,enable_logic:e.target.checked})}/><b>{title}</b></label>
        <span className="ml-auto rounded bg-[#35363a] px-2 py-1 text-[7px] text-[#9aa0a6]">{active}/{list.length} active</span>
      </div>
      {open[phase]?<div className="border-t border-[#3c4043] p-2.5">
        <div className="mb-2 text-[7px] leading-4 text-[#80868b]">{isFilter?'Sequential Image Processing services. Output of the final filter becomes the source for ROI location and downstream Logic.':'Information extraction services such as Contour Extractor and Sampling. Their exposed outputs are reserved for the future IDE / glue layer.'}</div>
        <div className="space-y-1.5">
          {list.length?list.map((binding,index)=>{const svc=services.find(s=>s.service_id===binding.service_id);return <div key={binding.binding_id} className="rounded border border-[#3c4043] bg-[#242528] p-2">
            <div className="flex items-center gap-1.5">
              <input type="checkbox" checked={binding.enabled} onChange={e=>patchBinding(phase,index,{enabled:e.target.checked})}/>
              <div className="min-w-0 flex-1"><div className="truncate font-bold">{svc?.name??binding.service_id}</div><div className="truncate text-[6px] text-[#80868b]">{svc?.lab_type??'service'} · {binding.service_id}</div></div>
              <button className="cv-mini-icon" onClick={()=>moveBinding(phase,index,-1)} title="Move up"><ArrowUp size={9}/></button>
              <button className="cv-mini-icon" onClick={()=>moveBinding(phase,index,1)} title="Move down"><ArrowDown size={9}/></button>
              <button className="cv-mini-icon text-[#f28b82]" onClick={()=>setList(phase,list.filter((_,i)=>i!==index))} title="Remove"><Trash2 size={9}/></button>
            </div>
            {!isFilter?<label className="mt-1.5 block text-[7px] text-[#9aa0a6]">Output alias<input className="cv-field !mt-1" value={binding.alias} onChange={e=>patchBinding(phase,index,{alias:e.target.value})}/></label>:null}
          </div>}):<div className="rounded border border-dashed border-[#3c4043] p-3 text-center text-[7px] text-[#80868b]">No {isFilter?'filter':'logic'} service yet.</div>}
        </div>
        <div className="mt-2 flex gap-1.5"><select className="cv-field !mt-0 min-w-0 flex-1" value={quickChoice[phase]} onChange={e=>setQuickChoice(v=>({...v,[phase]:e.target.value}))}><option value="">Add {isFilter?'Image Processing':'Logic'} service…</option>{candidates[phase].map(s=><option key={s.service_id} value={s.service_id}>{s.name}</option>)}</select><button className="cv-btn shrink-0" disabled={!quickChoice[phase]} onClick={()=>addQuick(phase)}><Plus size={10}/>Add</button></div>
        <div className="mt-2 grid grid-cols-2 gap-1.5"><button className="cv-btn" onClick={()=>setEditor({phase,scopeName})}><SlidersHorizontal size={10}/>Open Stack Workspace</button>{isFilter?<button className="cv-btn border-[#c58af9] text-[#c58af9]" onClick={()=>void onPreviewDebug(scopeId)}><Bug size={10}/>Debug Filter Stack</button>:<button className="cv-btn" disabled title="Logic debug is available after Run Test"><Bug size={10}/>Debug after Run</button>}</div>
      </div>:null}
    </div>;
  };

  return <div className="flex h-full flex-col text-[9px]">
    <div className="grid grid-cols-2 border-b border-[#3c4043]"><button className={`py-2 font-black ${tab==='operation'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#80868b]'}`} onClick={()=>setTab('operation')}>OPERATION</button><button className={`py-2 font-black ${tab==='benchmark'?'bg-[#3c4043] text-[#fdd663]':'text-[#80868b]'}`} onClick={()=>setTab('benchmark')}>BENCHMARK</button></div>
    {tab==='operation'?<div className="min-h-0 flex-1 overflow-y-auto p-3">
      <div className="mb-3 rounded-lg border border-[#5f6368] bg-[#242528] p-3"><div className="mb-2 flex items-center gap-2 font-black text-[#c58af9]"><Layers3 size={12}/>SCOPE</div><select className="cv-field" value={scopeId} onChange={e=>{setScopeId(e.target.value);if(e.target.value!=='global')onSelectStation?.(e.target.value)}}><option value="global">Global Scope · whole image · runs first</option>{rois.map(r=><option key={r.roi_id} value={r.roi_id}>{r.name} · ROI station</option>)}</select><div className="mt-2 text-[7px] leading-4 text-[#80868b]">{scopeId==='global'?'Global output feeds ROI finding and every station.':'This station receives its crop from the Global-filtered image.'}</div></div>
      {scopeId==='global'?<div className="mb-3 flex items-center justify-between rounded border border-[#3c4043] bg-[#242528] p-2"><span>ROI station execution</span><select className="cv-field !mt-0 !w-[140px]" value={stationExecution} onChange={e=>onExecution(e.target.value as any)}><option value="sequential">Sequential</option><option value="parallel">Parallel</option></select></div>:null}
      <div className="mb-2"><div className="text-[11px] font-black">{scopeName}</div><div className="mt-1 text-[7px] text-[#80868b]">{scopeId==='global'?'Whole-image production stack':'Selected ROI production stack'}</div></div>
      <div className="space-y-2">{phasePanel('filter')}{phasePanel('logic')}</div>
      <button disabled={!debugCount} onClick={onOpenDebug} className="cv-btn mt-3 w-full border-[#c58af9] text-[#c58af9]"><Bug size={11}/>Open Last Run Debug Workspace · {debugCount} artifact(s)</button>
    </div>:<div className="min-h-0 flex-1 overflow-y-auto p-3"><div className="mb-3 rounded border border-[#3c4043] bg-[#242528] p-2 text-[8px] text-[#9aa0a6]"><Activity size={11} className="mr-1 inline"/>Runtime per Filter, ROI locator, Logic and total cycle.</div>{benchmarks.length?benchmarks.map((b,i)=><div key={`${b.scope}-${b.phase}-${i}`} className="mb-2 rounded border border-[#3c4043] bg-[#242528] p-2"><div className="flex"><b className="flex-1">{b.scope} · {b.name}</b><span className="text-[#fdd663]">{b.elapsed_ms.toFixed(2)} ms</span></div><div className="mt-1 text-[7px] text-[#80868b]">{b.phase} · {b.detail}</div></div>):<div className="p-6 text-center text-[#80868b]">Run Test to collect benchmark data.</div>}</div>}
    {editor?<ScopeEditorModal open phase={editor.phase} scopeName={editor.scopeName} scope={scope} services={services} onChange={update} onClose={()=>setEditor(null)} onDebugPreview={editor.phase==='filter'?async()=>{setEditor(null);await onPreviewDebug(scopeId);}:undefined}/>:null}
  </div>;
};
