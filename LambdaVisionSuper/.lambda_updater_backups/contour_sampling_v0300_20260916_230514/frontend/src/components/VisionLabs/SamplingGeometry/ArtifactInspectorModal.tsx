import { useMemo, useState } from 'react';
import { Activity, ListTree, X } from 'lucide-react';
import type { SamplingArtifact } from './types';
import { SamplingCanvas } from './SamplingCanvas';
import { ArtifactDataView } from './SamplingVisuals';

const MiniSeries = ({ values, label }: { values: number[]; label: string }) => {
  const points = useMemo(() => {
    if (!values.length) return '';
    const max = Math.max(...values, 1e-12);
    return values.map((value, index) => `${(index / Math.max(1, values.length - 1)) * 100},${40 - (value / max) * 36}`).join(' ');
  }, [values]);
  return <div className="rounded border border-[#3c4043] bg-[#171717] p-2"><div className="mb-1 text-[9px] font-black uppercase tracking-wider text-[#9aa0a6]">{label}</div><svg viewBox="0 0 100 42" className="h-20 w-full"><polyline points={points} fill="none" stroke="#8ab4f8" strokeWidth="1.5" vectorEffect="non-scaling-stroke"/></svg></div>;
};

export const ArtifactInspectorModal = ({
  title,
  artifact,
  previewUrl,
  sourceUrl,
  masterContours,
  onClose,
}: {
  title: string;
  artifact: SamplingArtifact | null;
  previewUrl: string | null;
  sourceUrl: string | null;
  masterContours?: SamplingArtifact | null;
  onClose: () => void;
}) => {
  const [selectedContourId, setSelectedContourId] = useState<number | null>(null);
  const [tab, setTab] = useState<'visual'|'data'>('visual');
  const contour = artifact?.type === 'contour_set' ? artifact as any : null;
  const spectrum = artifact?.type === 'spectrum_2d' ? artifact as any : null;
  const housing = artifact?.type === 'sampling_housing' ? artifact as any : null;
  const selectedMetric = contour?.metrics?.find((metric: any) => Number(metric.id) === selectedContourId);

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center bg-black/80 p-4">
      <div className="flex h-[90vh] w-[95vw] max-w-[1750px] flex-col overflow-hidden rounded-xl border border-[#5f6368] bg-[#202124] shadow-2xl">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-[#3c4043] bg-[#292a2d] px-4">
          <ListTree size={16} className="text-[#8ab4f8]"/>
          <div className="min-w-0 flex-1"><div className="text-[9px] font-black uppercase tracking-[0.18em] text-[#8ab4f8]">Universal Artifact Inspector</div><div className="truncate text-sm font-bold text-[#e8eaed]">{title} <span className="font-mono text-[10px] font-normal text-[#9aa0a6]">· {(artifact as any)?.type ?? 'none'}</span></div></div>
          <div className="flex rounded border border-[#3c4043] bg-[#202124] p-0.5"><button onClick={()=>setTab('visual')} className={`rounded px-2 py-1 text-[9px] font-bold ${tab==='visual'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#9aa0a6]'}`}>Visual</button><button onClick={()=>setTab('data')} className={`rounded px-2 py-1 text-[9px] font-bold ${tab==='data'?'bg-[#3c4043] text-[#8ab4f8]':'text-[#9aa0a6]'}`}>Data</button></div>
          <button onClick={onClose} className="rounded p-2 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"><X size={17}/></button>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-[330px_minmax(0,1fr)]">
          <aside className="overflow-y-auto border-r border-[#3c4043] bg-[#292a2d] p-3">
            {contour ? <>
              <div className="rounded border border-[#3c4043] bg-[#202124] p-3"><div className="text-[9px] font-black uppercase text-[#8ab4f8]">Contour population</div><div className="mt-1 text-3xl font-black text-[#e8eaed]">{contour.count ?? contour.contours?.length ?? 0}</div><div className="text-[8px] text-[#80868b]">Click a row or click the contour directly on the image.</div></div>
              <div className="mt-2 max-h-[48vh] overflow-y-auto rounded border border-[#3c4043]">
                {(contour.metrics ?? []).map((metric: any) => <button key={metric.id} onClick={()=>setSelectedContourId(Number(metric.id))} className={`grid w-full grid-cols-[44px_1fr_1fr] gap-1 border-b border-[#3c4043] px-2 py-1.5 text-left text-[9px] last:border-b-0 ${selectedContourId===Number(metric.id)?'bg-[#4a3d16] text-[#fdd663]':'bg-[#202124] text-[#bdc1c6] hover:bg-[#303134]'}`}><b>#{metric.id}</b><span>A {metric.area_px2.toFixed(1)}</span><span>L {metric.perimeter_px.toFixed(1)}</span></button>)}
              </div>
              {selectedMetric ? <div className="mt-2 rounded border border-[#fdd663]/40 bg-[#4a3d16] p-2 font-mono text-[9px] text-[#e8d58a]"><div>ID {selectedMetric.id}</div><div>points {selectedMetric.point_count}</div><div>area {selectedMetric.area_px2.toFixed(3)} px²</div><div>perimeter {selectedMetric.perimeter_px.toFixed(3)} px</div><div>aspect {selectedMetric.aspect_ratio.toFixed(4)}</div><div>circularity {selectedMetric.circularity.toFixed(4)}</div><div>solidity {selectedMetric.solidity.toFixed(4)}</div><div>centroid {selectedMetric.centroid.map((v:number)=>v.toFixed(1)).join(', ')}</div></div> : null}
            </> : null}

            {artifact?.type === 'polyline' ? <div className="space-y-2 rounded border border-[#3c4043] bg-[#202124] p-3 text-[10px] text-[#bdc1c6]"><div className="text-[9px] font-black uppercase text-[#8ab4f8]">Curve summary</div><div>Points <b>{(artifact as any).point_count ?? (artifact as any).points?.length}</b></div><div>Arc length <b>{Number((artifact as any).arc_length_px ?? 0).toFixed(3)} px</b></div><pre className="whitespace-pre-wrap text-[8px] text-[#80868b]">{JSON.stringify((artifact as any).metadata ?? {}, null, 2)}</pre></div> : null}

            {housing ? <div className="space-y-2 rounded border border-[#3c4043] bg-[#202124] p-3 text-[10px] text-[#bdc1c6]"><div className="text-[9px] font-black uppercase text-[#8ab4f8]">Sampling housing</div><div>Kind <b>{housing.kind}</b></div><div>Elements <b>{housing.element_count}</b></div><div className="max-h-[45vh] overflow-y-auto font-mono text-[8px]">{(housing.elements ?? []).map((element:any)=><div key={element.id} className="border-t border-[#3c4043] py-1">{element.id} · {element.kind}</div>)}</div></div> : null}

            {artifact?.type === 'feature_vector' ? <div className="rounded border border-[#3c4043] bg-[#202124] p-3"><div className="text-[9px] font-black uppercase text-[#8ab4f8]">Vector schema</div><div className="mt-1 text-2xl font-black text-[#e8eaed]">{(artifact as any).dimension ?? (artifact as any).values?.length}D</div><div className="mt-2 max-h-[55vh] overflow-y-auto">{((artifact as any).names ?? []).map((name:string,index:number)=><div key={`${index}:${name}`} className="grid grid-cols-[36px_1fr_80px] gap-1 border-t border-[#3c4043] py-1 font-mono text-[8px]"><span className="text-[#80868b]">{index}</span><span className="truncate text-[#bdc1c6]" title={name}>{name}</span><span className="text-right text-[#8ab4f8]">{Number((artifact as any).values?.[index] ?? 0).toPrecision(5)}</span></div>)}</div></div> : null}

            {spectrum ? <div className="space-y-2"><div className="rounded border border-[#3c4043] bg-[#202124] p-3 text-[9px] text-[#bdc1c6]"><div className="font-black uppercase text-[#8ab4f8]">Spectrum diagnostics</div><div className="mt-2">Map {spectrum.shape?.join('×')}</div><div>Channel {spectrum.channel}</div><div>Window {spectrum.window}</div><div>Dominant radial band <b>{spectrum.metadata?.dominant_radial_band}</b></div><div>Dominant angle <b>{Number(spectrum.metadata?.dominant_angle_deg ?? 0).toFixed(1)}°</b></div></div><MiniSeries values={spectrum.metadata?.radial_energy ?? []} label="Radial energy · low → high frequency"/><MiniSeries values={spectrum.metadata?.angular_energy ?? []} label="Angular energy · 0 → 180°"/></div> : null}

            {!contour && artifact?.type !== 'polyline' && !housing && artifact?.type !== 'feature_vector' && !spectrum ? <div className="rounded border border-[#3c4043] bg-[#202124] p-3 text-[9px] text-[#9aa0a6]">This artifact uses the generic typed data inspector. New operators that reuse an existing artifact type automatically inherit its inspector.</div> : null}
          </aside>

          <main className="min-w-0 bg-[#171717]">
            {tab === 'data' ? <ArtifactDataView artifact={artifact}/>
              : spectrum && previewUrl ? <div className="grid h-full grid-rows-[minmax(0,1fr)_180px]"><div className="flex min-h-0 items-center justify-center overflow-hidden bg-black"><img src={previewUrl} alt="Spectrum" className="max-h-full max-w-full object-contain"/></div><div className="grid grid-cols-2 gap-2 border-t border-[#3c4043] p-2"><MiniSeries values={spectrum.metadata?.radial_energy ?? []} label="Radial energy"/><MiniSeries values={spectrum.metadata?.angular_energy ?? []} label="Angular energy"/></div></div>
              : <SamplingCanvas sourceUrl={sourceUrl} artifact={artifact} masterContours={masterContours} selectedContourId={selectedContourId} onSelectContour={setSelectedContourId}/>
            }
          </main>
        </div>
      </div>
    </div>
  );
};
