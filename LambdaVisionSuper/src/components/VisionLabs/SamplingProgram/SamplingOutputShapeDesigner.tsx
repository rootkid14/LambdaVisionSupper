import { useMemo, useState } from 'react';
import { Braces, Grid3X3, Loader2, Play, Rows3, X } from 'lucide-react';
import type { ProgramDataBlock, SamplingProgramDefinition, SamplingProgramRun } from './types';

const dim=(shape:number[])=>shape.reduce((a,b)=>a*Math.max(1,b),1);
const compact=(n:number)=>n.toLocaleString();

interface Group { label:string; d:number; channel?:string; kind?:string; start?:number; end?:number; }
const groupsFromBlocks=(blocks:ProgramDataBlock[]=[]):Group[]=>{
  const order:string[]=[];const map=new Map<string,Group>();
  blocks.forEach((b)=>{
    const key=(b.label||b.block_id).split(' · ').slice(0,2).join(' · ');
    const d=dim(b.shape);
    if(!map.has(key)){map.set(key,{label:key,d:0,channel:b.channel,kind:b.kind});order.push(key);}
    map.get(key)!.d+=d;
  });
  let cursor=0;
  return order.map((key)=>{const g=map.get(key)!;const out={...g,start:cursor,end:cursor+g.d-1};cursor+=g.d;return out;});
};

const SegmentedVector=({groups,total,title}:{groups:Group[];total:number;title:string})=>{
  const safe=Math.max(1,total);
  return <div className="rounded-lg border border-[#5f6368] bg-[#111] p-4">
    <div className="mb-2 flex items-end justify-between"><div><div className="text-[9px] font-black uppercase tracking-[.12em] text-[#8ab4f8]">{title}</div><div className="mt-1 font-mono text-xl font-black text-[#fdd663]">Vector [{compact(total)}]</div></div><div className="text-right font-mono text-[8px] text-[#80868b]">index 0 → {Math.max(0,total-1)}</div></div>
    <div className="flex h-24 w-full overflow-hidden rounded border border-[#3c4043] bg-[#202124]">
      {groups.length?groups.map((g,i)=>{
        const width=Math.max(3,(g.d/safe)*100);
        return <div key={`${g.label}-${i}`} title={`${g.label} · D=${g.d} · ${g.start}..${g.end}`} className="group relative flex min-w-[18px] items-center justify-center border-r border-[#5f6368] bg-[#303134] px-1 hover:bg-[#3c4043]" style={{width:`${width}%`}}>
          <div className="max-w-full -rotate-90 whitespace-nowrap text-[7px] font-black text-[#bdc1c6] group-hover:text-white">{g.label}</div>
        </div>;
      }):<div className="flex flex-1 items-center justify-center text-[9px] text-[#5f6368]">No sampled Data Blocks yet</div>}
    </div>
    <div className="mt-2 flex justify-between font-mono text-[7px] text-[#5f6368]"><span>0</span><span>{Math.floor(total/2)}</span><span>{Math.max(0,total-1)}</span></div>
  </div>;
};

const PatchRowMatrix=({run,groups,selected,onSelect}:{run:SamplingProgramRun;groups:Group[];selected:number;onSelect:(n:number)=>void})=>{
  const patches=run.local.patches;const totalD=run.manifest.features_per_patch||groups.reduce((n,g)=>n+g.d,0);const maxRows=Math.min(patches.length,24);
  return <div className="rounded-lg border border-[#5f6368] bg-[#111] p-4">
    <div className="mb-3 flex items-end justify-between"><div><div className="text-[9px] font-black uppercase tracking-[.12em] text-[#8ab4f8]">Final 2-D plane</div><div className="mt-1 font-mono text-xl font-black text-[#fdd663]">Matrix [{patches.length} × {compact(totalD)}]</div></div><div className="text-right text-[8px] text-[#80868b]">rows = patches<br/>columns = features</div></div>
    <div className="overflow-hidden rounded border border-[#3c4043]">
      <div className="flex h-7 border-b border-[#3c4043] bg-[#292a2d]"><div className="w-20 shrink-0 border-r border-[#3c4043] px-2 py-1 text-[7px] font-black text-[#9aa0a6]">PATCH</div><div className="flex min-w-0 flex-1">{groups.map((g,i)=><div key={i} className="min-w-[24px] border-r border-[#3c4043] px-1 py-1 text-center text-[6px] text-[#9aa0a6]" style={{flexGrow:Math.max(1,g.d),flexBasis:0}} title={`${g.label} D=${g.d}`}>{g.kind||g.label}</div>)}</div></div>
      <div className="max-h-[390px] overflow-y-auto">
        {Array.from({length:maxRows},(_,i)=><button key={i} onClick={()=>onSelect(i)} className={`flex h-8 w-full border-b border-[#292a2d] text-left ${selected===i?'bg-[#3c3520]':'bg-[#18191b] hover:bg-[#202124]'}`}><div className="w-20 shrink-0 border-r border-[#3c4043] px-2 py-2 font-mono text-[7px] text-[#bdc1c6]">P{i+1}</div><div className="flex min-w-0 flex-1">{groups.map((g,j)=><div key={j} className={`border-r border-[#303134] ${selected===i?'bg-[#5f5325]/35':'bg-[#303134]/60'}`} style={{flexGrow:Math.max(1,g.d),flexBasis:0}} title={`${g.label}: ${g.d} columns`}/>)}</div></button>)}
        {patches.length>maxRows?<div className="bg-[#18191b] py-2 text-center text-[7px] text-[#5f6368]">… {patches.length-maxRows} more patch rows</div>:null}
      </div>
    </div>
  </div>;
};

const PatchColumnMatrix=({run,groups,selected,onSelect}:{run:SamplingProgramRun;groups:Group[];selected:number;onSelect:(n:number)=>void})=>{
  const patches=run.local.patches;const totalD=run.manifest.features_per_patch||groups.reduce((n,g)=>n+g.d,0);const maxCols=Math.min(patches.length,24);
  return <div className="rounded-lg border border-[#5f6368] bg-[#111] p-4">
    <div className="mb-3 flex items-end justify-between"><div><div className="text-[9px] font-black uppercase tracking-[.12em] text-[#8ab4f8]">Final 2-D plane</div><div className="mt-1 font-mono text-xl font-black text-[#fdd663]">Matrix [{compact(totalD)} × {patches.length}]</div></div><div className="text-right text-[8px] text-[#80868b]">rows = features<br/>columns = patches</div></div>
    <div className="overflow-x-auto rounded border border-[#3c4043] bg-[#18191b] p-2">
      <div className="flex min-w-[520px] pl-28">{Array.from({length:maxCols},(_,i)=><button key={i} onClick={()=>onSelect(i)} className={`h-7 min-w-[28px] flex-1 border-r border-[#3c4043] text-[6px] font-black ${selected===i?'bg-[#5f5325] text-[#fdd663]':'bg-[#292a2d] text-[#80868b]'}`}>P{i+1}</button>)}</div>
      {groups.map((g,i)=><div key={i} className="flex min-w-[520px] border-t border-[#292a2d]"><div className="flex w-28 shrink-0 items-center justify-between border-r border-[#3c4043] px-2 py-2"><span className="truncate text-[7px] text-[#bdc1c6]">{g.label}</span><span className="font-mono text-[6px] text-[#8ab4f8]">D={g.d}</span></div><div className="flex min-h-[34px] flex-1">{Array.from({length:maxCols},(_,j)=><button key={j} onClick={()=>onSelect(j)} className={`min-w-[28px] flex-1 border-r border-[#303134] ${selected===j?'bg-[#5f5325]/40':'bg-[#303134]/55 hover:bg-[#3c4043]'}`} title={`${g.label} × Patch ${j+1}`}/>)}</div></div>)}
      {patches.length>maxCols?<div className="py-2 pl-28 text-center text-[7px] text-[#5f6368]">… {patches.length-maxCols} more patch columns</div>:null}
    </div>
  </div>;
};

export const SamplingOutputShapeDesigner=({program,run,onChange,onFormulate,formulating,dirty,onClose}:{program:SamplingProgramDefinition;run:SamplingProgramRun|null;onChange:(patch:Partial<SamplingProgramDefinition['output_shape']>)=>void;onFormulate:()=>void;formulating:boolean;dirty:boolean;onClose:()=>void;})=>{
  const [tab,setTab]=useState<'global'|'local'>('local');const [patchIndex,setPatchIndex]=useState(0);
  const globalGroups=useMemo(()=>groupsFromBlocks(run?.global_blocks.blocks??[]),[run]);
  const patchBlocks=run?.local.patches[Math.min(patchIndex,Math.max(0,(run?.local.patches.length??1)-1))]?.blocks??[];
  const patchGroups=useMemo(()=>groupsFromBlocks(patchBlocks),[patchBlocks]);
  const patchD=run?.manifest.features_per_patch??patchGroups.reduce((n,g)=>n+g.d,0);
  const patchCount=run?.local.patches.length??program.local_domain.grid.rows*program.local_domain.grid.cols;
  const localVectorTotal=patchD*patchCount;
  const localGroups:Group[]=program.output_shape.local_vector_order==='patch_major'
    ?Array.from({length:Math.min(patchCount,64)},(_,i)=>({label:`Patch ${i+1}`,d:patchD,start:i*patchD,end:(i+1)*patchD-1}))
    :patchGroups.map((g)=>({label:g.label,d:g.d*patchCount}));

  return <div className="fixed inset-0 z-[90] flex flex-col bg-[#111]/95 text-[#e8eaed]">
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-[#3c4043] bg-[#202124] px-4"><Braces size={18} className="text-[#81c995]"/><div><div className="text-xs font-black tracking-[.14em]">OUTPUT FORMULATION WORKSPACE</div><div className="text-[8px] text-[#80868b]">Cached Data Blocks → final Vector or 2-D Matrix. Tensor depth is intentionally deferred to Representation LAB.</div></div><div className="ml-auto flex items-center gap-2"><div className={`rounded border px-2 py-1 text-[8px] ${dirty?'border-[#fdd663] bg-[#3c3520] text-[#fdd663]':'border-[#3c4043] text-[#81c995]'}`}>{dirty?'FORMULATION CHANGED':'FORMULATED'}</div><button onClick={onFormulate} disabled={!run||formulating||!dirty} className="flex items-center gap-1 rounded border border-[#81c995] bg-[#1e3828] px-3 py-1.5 text-[9px] font-black text-[#81c995] disabled:opacity-35">{formulating?<Loader2 size={11} className="animate-spin"/>:<Play size={11}/>}Formulate</button><button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded border border-[#5f6368] bg-[#303134]"><X size={14}/></button></div></header>

    <div className="flex h-11 shrink-0 items-center gap-1 border-b border-[#3c4043] bg-[#18191b] px-4"><button onClick={()=>setTab('global')} className={`rounded px-3 py-1.5 text-[9px] font-black ${tab==='global'?'bg-[#174ea6] text-white':'text-[#9aa0a6]'}`}>GLOBAL VECTOR</button><button onClick={()=>setTab('local')} className={`rounded px-3 py-1.5 text-[9px] font-black ${tab==='local'?'bg-[#174ea6] text-white':'text-[#9aa0a6]'}`}>LOCAL OUTPUT</button><div className="ml-auto text-[8px] text-[#80868b]">Changing formulation never re-runs image sampling.</div></div>

    <div className="flex min-h-0 flex-1">
      <aside className="w-[300px] shrink-0 overflow-y-auto border-r border-[#3c4043] bg-[#202124] p-4">
        <div className="text-[9px] font-black uppercase tracking-[.12em] text-[#9aa0a6]">Formulation</div>
        {tab==='global'?<div className="mt-3 rounded border border-[#3c4043] bg-[#111] p-3"><div className="flex items-center gap-2"><Braces size={14} className="text-[#8ab4f8]"/><b className="text-[9px]">Global = Vector only</b></div><p className="mt-2 text-[8px] leading-4 text-[#80868b]">All Global Data Blocks concatenate in method/block order. Depth/channel stacking is not a Sampling responsibility.</p></div>:<>
          <div className="mt-3 grid grid-cols-2 gap-2"><button onClick={()=>onChange({local_layout:'vector'})} className={`rounded border p-3 text-left ${program.output_shape.local_layout==='vector'?'border-[#8ab4f8] bg-[#174ea6]/25':'border-[#3c4043] bg-[#111]'}`}><Braces size={14}/><div className="mt-2 text-[9px] font-black">Vector</div><div className="text-[7px] text-[#80868b]">[N]</div></button><button onClick={()=>onChange({local_layout:'matrix'})} className={`rounded border p-3 text-left ${program.output_shape.local_layout==='matrix'?'border-[#8ab4f8] bg-[#174ea6]/25':'border-[#3c4043] bg-[#111]'}`}><Grid3X3 size={14}/><div className="mt-2 text-[9px] font-black">Matrix</div><div className="text-[7px] text-[#80868b]">[R × C]</div></button></div>
          {program.output_shape.local_layout==='vector'?<div className="mt-3 rounded border border-[#3c4043] bg-[#111] p-3"><div className="mb-2 text-[8px] font-black">Vector ordering</div>{(['patch_major','feature_major'] as const).map((v)=><label key={v} className="mb-2 flex items-center gap-2 text-[8px]"><input type="radio" checked={program.output_shape.local_vector_order===v} onChange={()=>onChange({local_vector_order:v})}/><span>{v==='patch_major'?'Patch-major: P1 then P2…':'Feature-major: same feature across patches first'}</span></label>)}</div>:<div className="mt-3 rounded border border-[#3c4043] bg-[#111] p-3"><div className="mb-2 text-[8px] font-black">Matrix axes</div>{(['patch_rows','patch_columns'] as const).map((v)=><label key={v} className="mb-2 flex items-center gap-2 text-[8px]"><input type="radio" checked={program.output_shape.local_matrix_axis===v} onChange={()=>onChange({local_matrix_axis:v})}/><span>{v==='patch_rows'?'Rows = patches · Columns = features':'Rows = features · Columns = patches'}</span></label>)}</div>}
        </>}
        <div className="mt-5 text-[9px] font-black uppercase tracking-[.12em] text-[#9aa0a6]">Service outputs</div>
        {([['include_global','Global vector'],['include_local','Local formulated output'],['include_combined','Combined flat vector']] as const).map(([key,label])=><label key={key} className="mt-2 flex items-center gap-2 rounded border border-[#3c4043] bg-[#111] p-2 text-[8px]"><input type="checkbox" checked={program.output_shape[key]} onChange={(e)=>onChange({[key]:e.target.checked} as any)}/><span>{label}</span></label>)}
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto p-5">
        {!run?<div className="flex h-full min-h-[420px] items-center justify-center rounded-lg border border-dashed border-[#5f6368] text-center"><div><div className="text-sm font-black text-[#9aa0a6]">Run Program once to materialize Data Blocks</div><div className="mt-2 text-[9px] text-[#5f6368]">After that, this workspace can re-formulate them without sampling the image again.</div></div></div>:tab==='global'?<SegmentedVector groups={globalGroups} total={run.global_data.shape[0]??0} title="Global final shape"/>:<>
          {program.output_shape.local_layout==='vector'?<SegmentedVector groups={localGroups} total={localVectorTotal} title={program.output_shape.local_vector_order==='patch_major'?'Local patch-major vector':'Local feature-major vector'}/>:program.output_shape.local_matrix_axis==='patch_rows'?<PatchRowMatrix run={run} groups={patchGroups} selected={patchIndex} onSelect={setPatchIndex}/>:<PatchColumnMatrix run={run} groups={patchGroups} selected={patchIndex} onSelect={setPatchIndex}/>}          
          <div className="mt-5 rounded-lg border border-[#3c4043] bg-[#18191b] p-4"><div className="flex items-center justify-between"><div><div className="text-[9px] font-black uppercase tracking-[.12em] text-[#9aa0a6]">Selected patch anatomy</div><div className="mt-1 text-[8px] text-[#80868b]">Patch {patchIndex+1} · D={compact(patchD)}</div></div><Rows3 size={16} className="text-[#8ab4f8]"/></div><div className="mt-3 flex min-h-[82px] overflow-hidden rounded border border-[#3c4043] bg-[#111]">{patchGroups.length?patchGroups.map((g,i)=><div key={i} className="flex min-w-[90px] flex-1 flex-col justify-center border-r border-[#3c4043] p-2" style={{flexGrow:Math.max(1,g.d)}} title={`${g.label} · ${g.d} dimensions`}><div className="truncate text-[7px] font-black">{g.label}</div><div className="mt-1 font-mono text-[10px] text-[#81c995]">D={g.d}</div><div className="text-[6px] text-[#5f6368]">{g.channel?.toUpperCase()} · {g.kind}</div></div>):<div className="flex flex-1 items-center justify-center text-[8px] text-[#5f6368]">No local Data Blocks</div>}</div></div>
        </>}
      </main>

      <aside className="w-[260px] shrink-0 overflow-y-auto border-l border-[#3c4043] bg-[#202124] p-4"><div className="text-[9px] font-black uppercase tracking-[.12em] text-[#9aa0a6]">Current final shape</div>{run?<div className="mt-3 rounded border border-[#3c4043] bg-[#111] p-3"><div className="text-[8px] text-[#80868b]">Global</div><div className="font-mono text-lg font-black text-[#fdd663]">[{run.global_data.shape.join(' × ')}]</div><div className="mt-3 text-[8px] text-[#80868b]">Local</div><div className="font-mono text-lg font-black text-[#fdd663]">[{run.local_data.shape.join(' × ')}]</div><div className="mt-1 text-[7px] text-[#80868b]">{run.local_data.metadata?.rows_semantic&&run.local_data.metadata?.columns_semantic?`${run.local_data.metadata.rows_semantic} × ${run.local_data.metadata.columns_semantic}`:`${run.local_data.metadata?.representation??run.local_data.layout}`}</div><div className="mt-3 text-[8px] text-[#80868b]">Features / patch</div><div className="font-mono text-base font-black text-[#81c995]">{compact(run.manifest.features_per_patch??0)}</div></div>:null}<div className="mt-4 rounded border border-[#3c4043] bg-[#111] p-3 text-[8px] leading-4 text-[#80868b]"><b className="text-[#bdc1c6]">Boundary</b><br/>Sampling formulates one numeric vector or plane. Representation LAB will later align multiple Sampling services and stack/merge them into model tensors.</div></aside>
    </div>
  </div>;
};
