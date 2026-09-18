import { ArrowDown, ArrowUp, Eye, Share2, Trash2 } from 'lucide-react';
import type { SamplingArtifact, SamplingParameterManifest, SamplingStackItem, SourceBoardEntry } from './types';

const ParameterControl = ({ name, spec, value, onChange }: { name: string; spec: SamplingParameterManifest; value: any; onChange: (value: any) => void }) => {
  const label = spec.label || name.replaceAll('_', ' ');
  if (spec.type === 'boolean') return <div className="grid grid-cols-[1fr_auto] items-center gap-2"><div className="text-[9px] text-[#bdc1c6]">{label}</div><button onClick={()=>onChange(!Boolean(value))} className={`rounded px-2 py-1 text-[9px] font-bold ${value?'bg-[#174ea6] text-[#d2e3fc]':'bg-[#202124] text-[#9aa0a6]'}`}>{value?'ON':'OFF'}</button></div>;
  if (spec.type === 'enum') { const choices=spec.choices??[]; let index=choices.findIndex((choice)=>Object.is(choice,value)); if(index<0) index=choices.findIndex((choice)=>String(choice)===String(value)); return <div><div className="mb-1 text-[9px] text-[#bdc1c6]">{label}</div><select value={Math.max(0,index)} onChange={(e)=>onChange(choices[Number(e.target.value)])} className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[10px] text-[#e8eaed]">{choices.map((choice,i)=><option key={`${i}:${String(choice)}`} value={i}>{String(choice)}</option>)}</select></div>; }
  if (spec.type === 'integer' || spec.type === 'float') { const min=spec.min??0; const max=spec.max??(spec.type==='integer'?255:1); const step=spec.odd?2:spec.type==='integer'?1:Math.max(0.001,(Number(max)-Number(min))/200); return <div><div className="mb-1 flex items-center justify-between text-[9px] text-[#bdc1c6]"><span>{label}</span><span className="font-mono text-[#8ab4f8]">{String(value)}</span></div><div className="grid grid-cols-[1fr_70px] gap-2"><input type="range" min={min??undefined} max={max??undefined} step={step} value={Number(value)} onChange={(e)=>onChange(Number(e.target.value))} className="accent-[#8ab4f8]"/><input type="number" min={min??undefined} max={max??undefined} step={step} value={Number(value)} onChange={(e)=>onChange(Number(e.target.value))} className="rounded border border-[#5f6368] bg-[#202124] px-1 py-0.5 text-[9px] text-[#e8eaed]"/></div>{spec.description?<div className="mt-1 text-[8px] leading-3 text-[#80868b]">{spec.description}</div>:null}</div>; }
  return null;
};

export const SamplingStack = ({
  stack,
  selectedNodeId,
  selectedPort,
  timings,
  sourceEntries,
  inspectedArtifact,
  onSelect,
  onInspect,
  onParameter,
  onReferenceBinding,
  onMove,
  onRemove,
  onToggleExpose,
  onExposeName,
}: {
  stack: SamplingStackItem[];
  selectedNodeId: string | null;
  selectedPort: string | null;
  timings: Record<string, number>;
  sourceEntries: SourceBoardEntry[];
  inspectedArtifact: SamplingArtifact | null;
  onSelect: (id: string, port?: string) => void;
  onInspect: (id: string, port: string) => void;
  onParameter: (id: string, name: string, value: any) => void;
  onReferenceBinding: (id: string, port: string, sourceName: string) => void;
  onMove: (id: string, delta: number) => void;
  onRemove: (id: string) => void;
  onToggleExpose: (id: string, port: string) => void;
  onExposeName: (id: string, port: string, name: string) => void;
}) => (
  <aside className="flex w-[390px] min-w-[330px] flex-col overflow-hidden border-l border-[#3c4043] bg-[#202124]">
    <div className="border-b border-[#3c4043] bg-[#292a2d] px-3 py-2"><div className="text-[11px] font-black tracking-[0.18em] text-[#e8eaed]">PIPELINE STACK</div><div className="text-[9px] text-[#80868b]">Every output is inspectable; Expose is only for the public service contract.</div></div>
    <div className="flex-1 overflow-y-auto p-2">
      {stack.length===0?<div className="rounded border border-dashed border-[#5f6368] p-5 text-center text-xs text-[#80868b]">Add an operator from the left panel.</div>:stack.map((item,index)=>{
        const outputs = Object.entries(item.operator.outputs);
        const referenceInputs = Object.entries(item.operator.inputs).slice(1);
        const isSelected = selectedNodeId === item.id;
        const count = isSelected && inspectedArtifact?.type === 'contour_set' ? ((inspectedArtifact as any).count ?? (inspectedArtifact as any).contours?.length) : null;
        return <div key={item.id} onClick={()=>onSelect(item.id)} className={`mb-2 rounded border p-2.5 ${isSelected?'border-[#8ab4f8] bg-[#303134]':'border-[#3c4043] bg-[#292a2d]'}`}>
          <div className="flex items-start gap-2">
            <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded bg-[#3c4043] text-[9px] font-black text-[#8ab4f8]">{index+1}</div>
            <div className="min-w-0 flex-1"><div className="truncate text-[11px] font-bold text-[#e8eaed]">{item.operator.label}</div><div className="font-mono text-[8px] text-[#80868b]">{Object.values(item.operator.inputs)[0]?.type} → {outputs.map(([port,spec])=>`${port}:${spec.type}`).join(' · ')}{timings[item.id]!==undefined?` · ${timings[item.id].toFixed(2)} ms`:''}</div>{count!==null?<div className="mt-1 inline-flex rounded bg-[#1e3828] px-1.5 py-0.5 text-[8px] font-black text-[#81c995]">{count} contours</div>:null}</div>
            <div className="flex gap-1"><button onClick={(e)=>{e.stopPropagation();onMove(item.id,-1)}} className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043]"><ArrowUp size={11}/></button><button onClick={(e)=>{e.stopPropagation();onMove(item.id,1)}} className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043]"><ArrowDown size={11}/></button><button onClick={(e)=>{e.stopPropagation();onRemove(item.id)}} className="rounded p-1 text-[#9aa0a6] hover:bg-[#5f2120] hover:text-[#f28b82]"><Trash2 size={11}/></button></div>
          </div>

          {referenceInputs.length ? <div className="mt-2 rounded border border-[#3c4043] bg-[#202124] p-2" onClick={(e)=>e.stopPropagation()}><div className="mb-1 text-[8px] font-black uppercase tracking-wider text-[#fdd663]">Reference bindings</div>{referenceInputs.map(([port,spec])=>{const compatible=sourceEntries.filter((entry)=>entry.type===spec.type);return <label key={port} className="mt-1 grid grid-cols-[95px_1fr] items-center gap-2 text-[8px] text-[#9aa0a6]"><span>{port}:{spec.type}</span><select value={item.referenceBindings[port]??''} onChange={(e)=>onReferenceBinding(item.id,port,e.target.value)} className="min-w-0 rounded border border-[#5f6368] bg-[#292a2d] px-1 py-1 text-[9px] text-[#e8eaed]"><option value="">Unbound</option>{compatible.map((entry)=><option key={entry.name} value={entry.name}>{entry.name}</option>)}</select></label>;})}</div>:null}

          <div className="mt-2 space-y-2" onClick={(e)=>e.stopPropagation()}>{Object.entries(item.operator.parameters).map(([name,spec])=><ParameterControl key={name} name={name} spec={spec} value={item.parameters[name]} onChange={(value)=>onParameter(item.id,name,value)}/>)}</div>

          <div className="mt-2 space-y-1 border-t border-[#3c4043] pt-2" onClick={(e)=>e.stopPropagation()}>
            <div className="text-[8px] font-black uppercase tracking-wider text-[#80868b]">Typed outputs</div>
            {outputs.map(([port,spec])=>{const alias=item.exposedOutputs[port]??'';const active=isSelected&&selectedPort===port;return <div key={port} className={`rounded border p-1.5 ${active?'border-[#8ab4f8]/70 bg-[#26354d]':'border-[#3c4043] bg-[#202124]'}`}><div className="flex items-center gap-1.5"><span className="min-w-0 flex-1 truncate font-mono text-[8px] text-[#bdc1c6]">{port}:{spec.type}</span><button onClick={()=>onInspect(item.id,port)} className="flex items-center gap-1 rounded border border-[#5f6368] px-1.5 py-0.5 text-[8px] font-bold text-[#8ab4f8] hover:border-[#8ab4f8]"><Eye size={9}/>Inspect</button><button onClick={()=>onToggleExpose(item.id,port)} className={`flex items-center gap-1 rounded border px-1.5 py-0.5 text-[8px] font-bold ${alias?'border-[#81c995] bg-[#1e3828] text-[#81c995]':'border-[#5f6368] text-[#9aa0a6]'}`}><Share2 size={9}/>{alias?'Exposed':'Expose'}</button></div>{alias?<input value={alias} onChange={(e)=>onExposeName(item.id,port,e.target.value)} className="mt-1 w-full rounded border border-[#5f6368] bg-[#292a2d] px-2 py-1 font-mono text-[8px] text-[#e8eaed]"/>:null}</div>;})}
          </div>
        </div>;
      })}
    </div>
  </aside>
);
