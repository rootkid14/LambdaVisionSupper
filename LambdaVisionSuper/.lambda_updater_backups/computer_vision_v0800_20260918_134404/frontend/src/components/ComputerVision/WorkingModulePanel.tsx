import { useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import type { LabServiceDefinition } from '../../api/labServiceApi';
import type { MasterRoi, WorkingServiceBinding } from '../../api/visionAppApi';

type Props={
  services:LabServiceDefinition[];
  rois:MasterRoi[];
  globalBindings:WorkingServiceBinding[];
  stationBindings:Record<string,WorkingServiceBinding[]>;
  onGlobal:(next:WorkingServiceBinding[])=>void;
  onStations:(next:Record<string,WorkingServiceBinding[]>)=>void;
  onSelectStation?:(id:string)=>void;
};

const makeBinding=(serviceId:string):WorkingServiceBinding=>({binding_id:`bind_${Date.now()}_${Math.random().toString(36).slice(2,6)}`,service_id:serviceId,version:null,enabled:true,label:'',decision:{mode:'service_success',output_name:'',value_path:'',threshold:0}});

const BindingCard=({binding,services,onChange,onRemove}:{binding:WorkingServiceBinding;services:LabServiceDefinition[];onChange:(b:WorkingServiceBinding)=>void;onRemove:()=>void})=>{
 const service=services.find(s=>s.service_id===binding.service_id);const patch=(p:Partial<WorkingServiceBinding>)=>onChange({...binding,...p});const patchRule=(p:any)=>patch({decision:{...binding.decision,...p}});
 return <div className="rounded-lg border border-[#3c4043] bg-[#242528] p-2"><div className="flex items-center gap-2"><input type="checkbox" checked={binding.enabled} onChange={e=>patch({enabled:e.target.checked})}/><b className="min-w-0 flex-1 truncate text-[9px]">{service?.name??binding.service_id}</b><span className="rounded bg-[#35363a] px-1 text-[7px] text-[#8ab4f8]">{service?.lab_type}</span><button onClick={onRemove} className="text-[#f28b82]"><Trash2 size={11}/></button></div><div className="mt-2 grid grid-cols-2 gap-2"><label>Decision<select value={binding.decision.mode} onChange={e=>patchRule({mode:e.target.value})} className="cv-field"><option value="service_success">Service succeeds</option><option value="scalar_gt">Scalar &gt;</option><option value="scalar_gte">Scalar ≥</option><option value="scalar_lt">Scalar &lt;</option><option value="scalar_lte">Scalar ≤</option><option value="scalar_eq">Scalar =</option></select></label>{binding.decision.mode!=='service_success'?<><label>Output<select value={binding.decision.output_name} onChange={e=>patchRule({output_name:e.target.value})} className="cv-field"><option value="">First output</option>{Object.keys(service?.outputs??{}).map(name=><option key={name} value={name}>{name}</option>)}</select></label><label>Value path<input value={binding.decision.value_path} onChange={e=>patchRule({value_path:e.target.value})} placeholder="optional" className="cv-field"/></label><label>Threshold<input type="number" step="any" value={binding.decision.threshold} onChange={e=>patchRule({threshold:Number(e.target.value)})} className="cv-field"/></label></>:null}</div></div>;
};

export const WorkingModulePanel=({services,rois,globalBindings,stationBindings,onGlobal,onStations,onSelectStation}:Props)=>{
 const [tab,setTab]=useState<'global'|'local'>('global');const [stationId,setStationId]=useState(rois[0]?.roi_id??'');const [addService,setAddService]=useState('');
 const station=rois.find(r=>r.roi_id===stationId)??rois[0]??null;const current=station?stationBindings[station.roi_id]??[]:[];
 const add=(local:boolean)=>{if(!addService)return;const b=makeBinding(addService);if(local&&station){onStations({...stationBindings,[station.roi_id]:[...current,b]});}else onGlobal([...globalBindings,b]);setAddService('');};
 const cards=tab==='global'?globalBindings:current;
 const update=(index:number,b:WorkingServiceBinding)=>{if(tab==='global'){const next=[...globalBindings];next[index]=b;onGlobal(next);}else if(station){const next=[...current];next[index]=b;onStations({...stationBindings,[station.roi_id]:next});}};
 const remove=(index:number)=>{if(tab==='global')onGlobal(globalBindings.filter((_,i)=>i!==index));else if(station)onStations({...stationBindings,[station.roi_id]:current.filter((_,i)=>i!==index)});};
 return <div className="flex h-full flex-col text-[9px]"><div className="grid grid-cols-2 border-b border-[#3c4043]"><button onClick={()=>setTab('global')} className={`py-2 font-black ${tab==='global'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#80868b]'}`}>GLOBAL · WHOLE IMAGE</button><button onClick={()=>setTab('local')} className={`py-2 font-black ${tab==='local'?'bg-[#3c4043] text-[#81c995]':'text-[#80868b]'}`}>LOCAL · ROI STATIONS</button></div><div className="min-h-0 flex-1 overflow-y-auto p-3">
  {tab==='global'?<div className="mb-3 rounded border border-[#3c4043] bg-[#242528] p-2 text-[8px] text-[#9aa0a6]">Global services receive the full test image. Use Image Processing, Contour Extractor, Sampling or future AI services as independent working stages.</div>:<><label>Station<select value={station?.roi_id??''} onChange={e=>{setStationId(e.target.value);onSelectStation?.(e.target.value);}} className="cv-field mb-3">{rois.map(r=><option key={r.roi_id} value={r.roi_id}>{r.name}</option>)}</select></label><div className="mb-3 rounded border border-[#3c4043] bg-[#242528] p-2 text-[8px] text-[#9aa0a6]">Each ROI is a station. Services receive the located/cropped station image. Station OK requires ROI location and every enabled decision rule to pass.</div></>}
  <div className="flex gap-2"><select value={addService} onChange={e=>setAddService(e.target.value)} className="cv-field flex-1"><option value="">Choose Lab Service…</option>{services.map(s=><option key={s.service_id} value={s.service_id}>{s.name} · {s.lab_type}</option>)}</select><button onClick={()=>add(tab==='local')} disabled={!addService||(tab==='local'&&!station)} className="cv-btn"><Plus size={11}/>Add</button></div><div className="mt-3 space-y-2">{cards.map((b,i)=><BindingCard key={b.binding_id} binding={b} services={services} onChange={next=>update(i,next)} onRemove={()=>remove(i)}/>)}</div>
 </div></div>;
};
