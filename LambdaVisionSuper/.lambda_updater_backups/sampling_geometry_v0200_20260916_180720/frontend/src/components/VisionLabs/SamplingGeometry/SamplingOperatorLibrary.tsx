import { useMemo, useState } from 'react';
import { CircleHelp, Plus, Search } from 'lucide-react';
import type { SamplingOperatorManifest } from './types';
import { SamplingGuideModal } from './SamplingGuideModal';

export const SamplingOperatorLibrary = ({ operators, onAdd, canAppend }: { operators: SamplingOperatorManifest[]; onAdd: (operator: SamplingOperatorManifest) => void; canAppend: (operator: SamplingOperatorManifest) => { ok: boolean; reason?: string } }) => {
  const [query, setQuery] = useState('');
  const [guide, setGuide] = useState<SamplingOperatorManifest | null>(null);
  const grouped = useMemo(() => {
    const map = new Map<string, SamplingOperatorManifest[]>();
    const q = query.trim().toLowerCase();
    operators.filter((op) => !q || `${op.label} ${op.category} ${op.description ?? ''}`.toLowerCase().includes(q)).forEach((op) => map.set(op.category, [...(map.get(op.category) ?? []), op]));
    return [...map.entries()];
  }, [operators, query]);
  return <>
    <aside className="flex w-[300px] min-w-[260px] flex-col overflow-hidden border-r border-[#3c4043] bg-[#202124]">
      <div className="border-b border-[#3c4043] bg-[#292a2d] p-3"><div className="mb-2 text-[11px] font-black tracking-[0.18em] text-[#e8eaed]">TOOLS</div><div className="relative"><Search size={14} className="absolute left-2.5 top-2.5 text-[#9aa0a6]"/><input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search sampling tools..." className="w-full rounded border border-[#5f6368] bg-[#202124] py-2 pl-8 pr-2 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"/></div></div>
      <div className="flex-1 overflow-y-auto p-2">{grouped.map(([category, items]) => <div key={category} className="mb-2 overflow-hidden rounded border border-[#3c4043] bg-[#292a2d]"><div className="border-b border-[#3c4043] px-2.5 py-1.5 text-[9px] font-black uppercase tracking-wider text-[#9aa0a6]">{category}</div>{items.map((operator)=>{const compatibility=canAppend(operator);return <div key={operator.id} className="border-b border-[#3c4043] p-2.5 last:border-b-0 hover:bg-[#35363a]"><div className="flex gap-2"><div className="min-w-0 flex-1"><div className="truncate text-[11px] font-bold text-[#e8eaed]">{operator.label}</div><div className="mt-0.5 line-clamp-2 text-[9px] leading-4 text-[#9aa0a6]">{operator.description}</div></div><button onClick={()=>setGuide(operator)} className="flex h-7 w-7 items-center justify-center rounded border border-[#5f6368] bg-[#202124] text-[#8ab4f8] hover:border-[#8ab4f8]" title="Guide"><CircleHelp size={14}/></button><button disabled={!compatibility.ok} onClick={()=>compatibility.ok&&onAdd(operator)} className="flex h-7 w-7 items-center justify-center rounded border border-[#5f6368] bg-[#202124] text-[#8ab4f8] disabled:cursor-not-allowed disabled:opacity-25" title={compatibility.reason ?? 'Add'}><Plus size={14}/></button></div>{!compatibility.ok&&compatibility.reason?<div className="mt-1 text-[8px] text-[#80868b]">{compatibility.reason}</div>:null}</div>;})}</div>)}</div>
    </aside>
    {guide ? <SamplingGuideModal operator={guide} onClose={()=>setGuide(null)} /> : null}
  </>;
};
