import { useMemo, useState } from 'react';
import { Activity, Grid3X3, Image as ImageIcon, Table2 } from 'lucide-react';
import type { SamplingArtifact, SamplingWorkspace } from './types';
import { ArtifactDataView } from './SamplingVisuals';

const Overlay = ({ artifact }: { artifact: SamplingArtifact | null }) => {
  if (!artifact) return null;
  const type = (artifact as any).type;
  if (type === 'contour_set') {
    const h=(artifact as any).source_shape?.[0]||1; const w=(artifact as any).source_shape?.[1]||1;
    return <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">{((artifact as any).contours??[]).map((contour:number[][],i:number)=><polyline key={i} points={contour.map((p)=>`${p[0]/w},${p[1]/h}`).join(' ')} fill="none" stroke="#81c995" strokeWidth="0.003" vectorEffect="non-scaling-stroke"/>)}</svg>;
  }
  if (type === 'polyline') {
    const shape=(artifact as any).source_shape; const h=shape?.[0]||1; const w=shape?.[1]||1;
    return <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full"><polyline points={((artifact as any).points??[]).map((p:number[])=>`${p[0]/w},${p[1]/h}`).join(' ')} fill="none" stroke="#fdd663" strokeWidth="0.004" vectorEffect="non-scaling-stroke"/></svg>;
  }
  const geometry=(artifact as any).geometry;
  if (!geometry) return null;
  if (geometry.kind==='rays') return <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">{(geometry.rays??[]).map((ray:number[],i:number)=><line key={i} x1={ray[0]} y1={ray[1]} x2={ray[2]} y2={ray[3]} stroke={i%2?'#81c995':'#8ab4f8'} strokeWidth="0.004" vectorEffect="non-scaling-stroke"/>)}</svg>;
  if (geometry.kind==='rings') return <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">{(geometry.radii??[]).map((r:number,i:number)=><ellipse key={i} cx={geometry.center?.[0]??0.5} cy={geometry.center?.[1]??0.5} rx={r} ry={r} fill="none" stroke="#8ab4f8" strokeWidth="0.003" vectorEffect="non-scaling-stroke"/>)}</svg>;
  if (geometry.kind==='boxes') return <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">{(geometry.boxes??[]).map((box:number[],i:number)=><rect key={i} x={box[0]} y={box[1]} width={box[2]-box[0]} height={box[3]-box[1]} fill="none" stroke="#8ab4f8" strokeWidth="0.0025" vectorEffect="non-scaling-stroke"/>)}</svg>;
  if (geometry.kind==='polyline') { const shape=geometry.source_shape; const h=shape?.[0]||1; const w=shape?.[1]||1; return <svg viewBox="0 0 1 1" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full"><polyline points={(geometry.points??[]).map((p:number[])=>`${p[0]/w},${p[1]/h}`).join(' ')} fill="none" stroke="#fdd663" strokeWidth="0.003"/></svg>; }
  return null;
};

export const SamplingWorkbench = ({ workspace, sourceUrl, artifact, artifactPreviewUrl }: { workspace: SamplingWorkspace; sourceUrl: string | null; artifact: SamplingArtifact | null; artifactPreviewUrl: string | null }) => {
  const defaultMode = workspace==='spectral' ? 'data' : 'spatial';
  const [mode,setMode]=useState<'spatial'|'data'>('spatial');
  const effective = useMemo(()=>workspace==='spectral'&&artifact?.type==='spectrum_2d'?'spatial':mode,[workspace,artifact,mode]);
  return <div className="flex min-w-0 flex-1 flex-col bg-[#171717]">
    <div className="flex h-11 shrink-0 items-center gap-2 border-b border-[#3c4043] bg-[#292a2d] px-3"><div className="mr-auto"><div className="text-[10px] font-black tracking-[0.14em] text-[#8ab4f8]">{workspace==='geometry'?'GEOMETRY WORKBENCH':workspace==='spatial'?'SAMPLING PATTERN WORKBENCH':'SPECTRAL / STATISTICS WORKBENCH'}</div><div className="text-[9px] text-[#80868b]">{workspace==='geometry'?'Blob/curve structure and measurements':workspace==='spatial'?'Visual sampling patterns on the real image':'Fourier map, distributions and descriptors'}</div></div><button onClick={()=>setMode('spatial')} className={`flex items-center gap-1 rounded px-2 py-1 text-[9px] font-bold ${effective==='spatial'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#9aa0a6]'}`}><ImageIcon size={11}/>{workspace==='spectral'?'Spectrum / Source':'Spatial'}</button><button onClick={()=>setMode('data')} className={`flex items-center gap-1 rounded px-2 py-1 text-[9px] font-bold ${effective==='data'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#9aa0a6]'}`}><Activity size={11}/>{workspace==='geometry'?'Data / Profile':workspace==='spatial'?'Profiles / Features':'Descriptor'}</button></div>
    <div className="relative min-h-0 flex-1">
      {effective==='data'?<ArtifactDataView artifact={artifact}/>:artifact?.type==='spectrum_2d'&&artifactPreviewUrl?<img src={artifactPreviewUrl} className="h-full w-full object-contain" alt="Fourier spectrum"/>:sourceUrl?<div className="absolute inset-0"><img src={sourceUrl} className="h-full w-full object-fill" alt="Sampling source"/><Overlay artifact={artifact}/></div>:<div className="flex h-full items-center justify-center text-center text-sm text-[#80868b]">Load an input source, add operators, then Run.</div>}
    </div>
  </div>;
};
