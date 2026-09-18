import { ArrowDown, ArrowUp, Boxes, Grid3X3, HelpCircle, Rows3 } from 'lucide-react';
import type { DataBlockArtifact, SamplingArtifact } from './types';

export const DataLayoutComposer = ({artifact,parameters,onParameter,onInspectBlock,onHelp}:{artifact?:SamplingArtifact|null;parameters:Record<string,any>;onParameter:(name:string,value:any)=>void;onInspectBlock:(block:DataBlockArtifact)=>void;onHelp:(topic:string)=>void}) => {
  const blocks=(artifact as any)?.type==='data_block_set' ? ((artifact as any).blocks??[]) as DataBlockArtifact[] : [];
  const customOrder=String(parameters.block_order??'').split(',').filter(Boolean);
  const ordered=[...blocks].sort((a,b)=>{const ai=customOrder.indexOf(a.block_id),bi=customOrder.indexOf(b.block_id);return (ai<0?9999:ai)-(bi<0?9999:bi);});
  const move=(index:number,delta:number)=>{const list=ordered.map((b)=>b.block_id);const target=index+delta;if(target<0||target>=list.length)return;[list[index],list[target]]=[list[target],list[index]];onParameter('order_mode','custom');onParameter('block_order',list.join(','));};
  return <div className="rounded border border-[#3c4043] bg-[#202124] p-2">
    <div className="flex items-center gap-2"><Boxes size={12} className="text-[#8ab4f8]"/><span className="text-[9px] font-black">DATA LAYOUT COMPOSER</span><button onClick={()=>onHelp('layout')} className="text-[#80868b]"><HelpCircle size={11}/></button><span className="ml-auto text-[8px] text-[#80868b]">{blocks.length} blocks</span></div>
    <div className="mt-2 flex items-center gap-1.5">
      <select value={parameters.layout_mode??'concatenate'} onChange={(e)=>onParameter('layout_mode',e.target.value)} className="rounded border border-[#5f6368] bg-[#292a2d] px-2 py-1 text-[8px]"><option value="concatenate">Vector · concatenate</option><option value="stack_rows">Matrix · stack rows</option><option value="stack_columns">Matrix · stack columns</option></select>
      <button onClick={()=>onParameter('order_mode','element_major')} className="rounded border border-[#3c4043] px-2 py-1 text-[8px]"><Rows3 size={9} className="inline mr-1"/>Element major</button>
      <button onClick={()=>onParameter('order_mode','channel_major')} className="rounded border border-[#3c4043] px-2 py-1 text-[8px]"><Grid3X3 size={9} className="inline mr-1"/>Channel major</button>
    </div>
    <div className="mt-2 flex flex-wrap gap-1.5">{ordered.length?ordered.map((block,index)=><div key={block.block_id} className="min-w-[150px] rounded border border-[#5f6368] bg-[#292a2d] p-1.5"><button onClick={()=>onInspectBlock(block)} className="block w-full text-left"><div className="truncate text-[8px] font-black text-[#d2e3fc]">{block.label}</div><div className="mt-0.5 text-[7px] text-[#9aa0a6]">{block.kind} · [{block.shape.join('×')}]</div></button><div className="mt-1 flex gap-1"><button onClick={()=>move(index,-1)} className="rounded bg-[#202124] p-0.5"><ArrowUp size={8}/></button><button onClick={()=>move(index,1)} className="rounded bg-[#202124] p-0.5"><ArrowDown size={8}/></button></div></div>):<div className="text-[8px] text-[#5f6368]">Run this Sampling Unit to see semantic Data Blocks here.</div>}</div>
  </div>;
};
