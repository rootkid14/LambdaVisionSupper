import { Activity, Eye, Image as ImageIcon, Waves } from 'lucide-react';
import { useState } from 'react';
import type { SamplingArtifact, SamplingWorkspace } from './types';
import { ArtifactDataView } from './SamplingVisuals';
import { SamplingCanvas } from './SamplingCanvas';

const Sparkline = ({ values, label }: { values: number[]; label: string }) => {
  const max = Math.max(...values, 1e-12);
  const points = values.map((value,index)=>`${(index/Math.max(1,values.length-1))*100},${36-(value/max)*32}`).join(' ');
  return <div className="rounded border border-[#3c4043] bg-[#202124] p-2"><div className="mb-1 text-[8px] font-black uppercase text-[#80868b]">{label}</div><svg viewBox="0 0 100 38" className="h-20 w-full"><polyline points={points} fill="none" stroke="#8ab4f8" strokeWidth="1.4" vectorEffect="non-scaling-stroke"/></svg></div>;
};

export const SamplingWorkbench = ({
  workspace,
  sourceUrl,
  artifact,
  artifactPreviewUrl,
  masterContours,
}: {
  workspace: SamplingWorkspace;
  sourceUrl: string | null;
  artifact: SamplingArtifact | null;
  artifactPreviewUrl: string | null;
  masterContours: SamplingArtifact | null;
}) => {
  const [mode, setMode] = useState<'visual'|'data'>('visual');
  const spectrum = artifact?.type === 'spectrum_2d' ? artifact as any : null;
  const geometryMission = 'Find the meaningful shapes inside the contour mess: inspect → filter → rank → clean.';
  const spatialMission = 'WHERE is the housing; HOW is the extractor. Every produced number keeps an explicit schema.';
  const spectralMission = 'Represent pixels/contours as interpretable distributions and frequency-domain data.';

  return <div className="flex min-w-0 flex-1 flex-col bg-[#171717]">
    <div className="flex h-12 shrink-0 items-center gap-2 border-b border-[#3c4043] bg-[#292a2d] px-3">
      <div className="mr-auto min-w-0"><div className="text-[10px] font-black tracking-[0.14em] text-[#8ab4f8]">{workspace==='geometry'?'GEOMETRY · CONTOUR DISCOVERY':workspace==='spatial'?'SPATIAL · HOUSING + EXTRACTION':'SPECTRAL / STATISTICS · DATA REPRESENTATION'}</div><div className="truncate text-[8px] text-[#80868b]">{workspace==='geometry'?geometryMission:workspace==='spatial'?spatialMission:spectralMission}</div></div>
      <button onClick={()=>setMode('visual')} className={`flex items-center gap-1 rounded px-2 py-1 text-[9px] font-bold ${mode==='visual'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#9aa0a6]'}`}><Eye size={11}/>Visual</button>
      <button onClick={()=>setMode('data')} className={`flex items-center gap-1 rounded px-2 py-1 text-[9px] font-bold ${mode==='data'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#9aa0a6]'}`}><Activity size={11}/>Data</button>
    </div>

    <div className="relative min-h-0 flex-1">
      {mode==='data' ? <ArtifactDataView artifact={artifact}/>
        : workspace==='spectral' && spectrum && artifactPreviewUrl ? (
          <div className="grid h-full grid-cols-[minmax(0,1.3fr)_minmax(320px,.7fr)] gap-px bg-[#3c4043]">
            <div className="grid min-h-0 grid-rows-2 gap-px bg-[#3c4043]">
              <div className="relative min-h-0 bg-[#171717]"><div className="absolute left-2 top-2 z-10 rounded bg-[#202124]/90 px-2 py-1 text-[8px] font-black text-[#bdc1c6]"><ImageIcon size={9} className="mr-1 inline"/>SOURCE</div><SamplingCanvas sourceUrl={sourceUrl} artifact={null}/></div>
              <div className="relative flex min-h-0 items-center justify-center overflow-hidden bg-black"><div className="absolute left-2 top-2 z-10 rounded bg-[#202124]/90 px-2 py-1 text-[8px] font-black text-[#bdc1c6]"><Waves size={9} className="mr-1 inline"/>FFT ENERGY MAP</div><img src={artifactPreviewUrl} className="max-h-full max-w-full object-contain" alt="Fourier spectrum"/></div>
            </div>
            <div className="min-h-0 overflow-y-auto bg-[#202124] p-2"><Sparkline values={spectrum.metadata?.radial_energy ?? []} label="Radial energy · low → high frequency"/><div className="h-2"/><Sparkline values={spectrum.metadata?.angular_energy ?? []} label="Angular energy · 0 → 180°"/><div className="mt-2 rounded border border-[#3c4043] bg-[#292a2d] p-3 text-[9px] text-[#bdc1c6]"><div className="font-black uppercase text-[#8ab4f8]">Spectrum summary</div><div className="mt-2">Channel <b>{spectrum.channel}</b></div><div>Window <b>{spectrum.window}</b></div><div>Dominant radial band <b>{spectrum.metadata?.dominant_radial_band}</b></div><div>Dominant orientation <b>{Number(spectrum.metadata?.dominant_angle_deg ?? 0).toFixed(1)}°</b></div></div></div>
          </div>
        ) : <SamplingCanvas sourceUrl={sourceUrl} artifact={artifact} masterContours={workspace==='geometry'?masterContours:null}/>
      }
    </div>
  </div>;
};
