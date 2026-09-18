import { BarChart3, CircleDot, Crosshair, Plus, ScanLine, Sigma } from 'lucide-react';
import type { SamplingDomain, SamplingMethodCatalogItem } from './types';

const iconFor=(kind:string)=>kind==='histogram'?BarChart3:kind==='statistics'?Sigma:kind==='rays'?ScanLine:kind==='cross'?Crosshair:CircleDot;

export const SamplingMethodLibrary=({domain,catalog,onAdd}:{domain:SamplingDomain;catalog:SamplingMethodCatalogItem[];onAdd:(item:SamplingMethodCatalogItem)=>void;})=>{
 const grouped=Object.entries(catalog.reduce<Record<string,SamplingMethodCatalogItem[]>>((acc,item)=>{(acc[item.family]??=[]).push(item);return acc;},{}));
 return <aside className="w-[250px] shrink-0 overflow-y-auto border-r border-[#3c4043] bg-[#242528] p-3">
  <div className="mb-3"><div className="text-[10px] font-black tracking-[.14em]">{domain==='global'?'GLOBAL METHODS':'LOCAL METHODS'}</div><div className="mt-1 text-[8px] leading-4 text-[#80868b]">{domain==='global'?'Measure the whole inspected image as one domain.':'The same recipe is applied independently to every patch.'}</div></div>
  {grouped.map(([family,items])=><div key={family} className="mb-4"><div className="mb-1 text-[8px] font-black uppercase tracking-[.12em] text-[#8ab4f8]">{family}</div>{items.map((item)=>{const Icon=iconFor(item.kind);return <button key={item.kind} onClick={()=>onAdd(item)} className="mb-1 flex w-full items-start gap-2 rounded border border-[#3c4043] bg-[#202124] p-2 text-left hover:border-[#8ab4f8]"><Icon size={14} className="mt-0.5 shrink-0 text-[#81c995]"/><span className="min-w-0 flex-1"><span className="block text-[9px] font-black text-[#e8eaed]">{item.label}</span><span className="mt-0.5 block text-[8px] leading-3 text-[#80868b]">{item.description}</span></span><Plus size={12} className="mt-1 shrink-0 text-[#8ab4f8]"/></button>;})}</div>)}
  <div className="rounded border border-[#3c4043] bg-[#202124] p-2 text-[8px] leading-4 text-[#80868b]"><b className="text-[#bdc1c6]">Hierarchy</b><br/>Domain → placement → sampling shape → channel → measure → output shape.</div>
 </aside>;
};
