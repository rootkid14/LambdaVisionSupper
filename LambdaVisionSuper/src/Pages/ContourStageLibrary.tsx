import { CircleHelp, Plus } from 'lucide-react';
import type { ContourStageManifest } from '../api/contourExtractorApi';

export const ContourStageLibrary = ({stages,onAdd,onGuide}:{stages:ContourStageManifest[];onAdd:(stage:ContourStageManifest)=>void;onGuide:(stage:ContourStageManifest)=>void}) => {
  const groups=Array.from(new Set(stages.map((s)=>s.category)));
  return <aside className="w-[300px] shrink-0 overflow-y-auto border-r border-[#3c4043] bg-[#202124] p-3">
    <div className="text-[10px] font-black tracking-[.14em] text-[#81c995]">CONTOUR TOOL LIBRARY</div>
    <div className="mt-1 text-[8px] leading-4 text-[#80868b]">Build a filtering / shape-discovery strategy. Every stage consumes contour IDs and keeps the geometry single-copy in memory.</div>
    {groups.map((group)=><section key={group} className="mt-4"><div className="mb-1 text-[8px] font-black uppercase tracking-wider text-[#9aa0a6]">{group}</div><div className="space-y-2">{stages.filter((s)=>s.category===group).map((stage)=><div key={stage.kind} className="rounded-lg border border-[#3c4043] bg-[#292a2d] p-2.5 hover:border-[#5f6368]"><div className="flex items-start gap-2"><div className="min-w-0 flex-1"><div className="text-[10px] font-black text-[#e8eaed]">{stage.label}</div><div className="mt-1 text-[8px] leading-4 text-[#9aa0a6]">{stage.description}</div></div><button onClick={()=>onGuide(stage)} className="rounded p-1 text-[#8ab4f8] hover:bg-[#3c4043]" title="How this stage works"><CircleHelp size={12}/></button></div><button onClick={()=>onAdd(stage)} className="mt-2 flex w-full items-center justify-center gap-1 rounded border border-[#5f6368] bg-[#202124] py-1 text-[8px] font-black text-[#d2e3fc] hover:border-[#81c995]"><Plus size={9}/>Add to filter pipeline</button></div>)}</div></section>)}
  </aside>;
};
