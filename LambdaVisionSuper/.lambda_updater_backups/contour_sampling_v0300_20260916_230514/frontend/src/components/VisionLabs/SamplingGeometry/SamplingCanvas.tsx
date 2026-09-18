import { useEffect, useMemo, useRef, useState } from 'react';
import { Maximize2, Minus, Plus, RotateCcw } from 'lucide-react';
import type { SamplingArtifact } from './types';

const artifactGeometry = (artifact: SamplingArtifact | null): any => {
  if (!artifact) return null;
  if ((artifact as any).type === 'sampling_housing') return (artifact as any).geometry;
  if ((artifact as any).type === 'profile_set' || (artifact as any).type === 'feature_matrix') return (artifact as any).geometry;
  return null;
};

export const SamplingCanvas = ({
  sourceUrl,
  artifact,
  masterContours,
  selectedContourId,
  onSelectContour,
}: {
  sourceUrl: string | null;
  artifact: SamplingArtifact | null;
  masterContours?: SamplingArtifact | null;
  selectedContourId?: number | null;
  onSelectContour?: (id: number) => void;
}) => {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [imageSize, setImageSize] = useState({ w: 1, h: 1 });
  const [fitScale, setFitScale] = useState(1);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragRef = useRef<{ x: number; y: number; px: number; py: number } | null>(null);

  const reset = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  useEffect(() => {
    const recompute = () => {
      const host = hostRef.current;
      if (!host || imageSize.w <= 1 || imageSize.h <= 1) return;
      const rect = host.getBoundingClientRect();
      const scale = Math.min((rect.width - 24) / imageSize.w, (rect.height - 24) / imageSize.h);
      setFitScale(Math.max(0.01, scale));
    };
    recompute();
    const observer = new ResizeObserver(recompute);
    if (hostRef.current) observer.observe(hostRef.current);
    return () => observer.disconnect();
  }, [imageSize.w, imageSize.h]);

  useEffect(() => { reset(); }, [sourceUrl]);

  const contourArtifact = artifact?.type === 'contour_set' ? artifact as any : null;
  const master = masterContours?.type === 'contour_set' ? masterContours as any : null;
  const resultIds = useMemo(() => new Set<number>((contourArtifact?.contour_ids ?? []).map(Number)), [contourArtifact]);
  const geometry = artifactGeometry(artifact);

  const overlay = (
    <svg viewBox={`0 0 ${imageSize.w} ${imageSize.h}`} className="absolute inset-0 h-full w-full overflow-visible">
      {master?.contours?.map((contour: number[][], index: number) => {
        const id = Number(master.contour_ids?.[index] ?? index);
        const isKept = resultIds.has(id);
        const selected = selectedContourId === id;
        return (
          <polyline
            key={`master:${id}`}
            points={contour.map((point) => `${point[0]},${point[1]}`).join(' ')}
            fill="none"
            stroke={selected ? '#fdd663' : isKept ? '#81c995' : '#80868b'}
            strokeOpacity={selected ? 1 : isKept ? 0.95 : 0.18}
            strokeWidth={selected ? 4 : isKept ? 2 : 1}
            vectorEffect="non-scaling-stroke"
            pointerEvents="stroke"
            onClick={(event) => { event.stopPropagation(); onSelectContour?.(id); }}
            className="cursor-crosshair"
          />
        );
      })}

      {!master && contourArtifact?.contours?.map((contour: number[][], index: number) => {
        const id = Number(contourArtifact.contour_ids?.[index] ?? index);
        const selected = selectedContourId === id;
        return <polyline key={id} points={contour.map((point) => `${point[0]},${point[1]}`).join(' ')} fill="none" stroke={selected ? '#fdd663' : '#81c995'} strokeWidth={selected ? 4 : 2} vectorEffect="non-scaling-stroke" pointerEvents="stroke" onClick={(event)=>{event.stopPropagation();onSelectContour?.(id);}} className="cursor-crosshair"/>;
      })}

      {artifact?.type === 'polyline' ? (
        <polyline points={(artifact as any).points.map((point: number[]) => `${point[0]},${point[1]}`).join(' ')} fill="none" stroke="#fdd663" strokeWidth="3" vectorEffect="non-scaling-stroke" />
      ) : null}

      {geometry?.kind === 'rays' ? (geometry.rays ?? []).map((ray: number[], index: number) => (
        <line key={index} x1={ray[0] * imageSize.w} y1={ray[1] * imageSize.h} x2={ray[2] * imageSize.w} y2={ray[3] * imageSize.h} stroke={index % 2 ? '#81c995' : '#8ab4f8'} strokeWidth="2" vectorEffect="non-scaling-stroke" />
      )) : null}
      {geometry?.kind === 'rings' ? (geometry.radii ?? []).map((radius: number, index: number) => {
        const scale = Math.min(imageSize.w, imageSize.h);
        return <circle key={index} cx={(geometry.center?.[0] ?? 0.5) * imageSize.w} cy={(geometry.center?.[1] ?? 0.5) * imageSize.h} r={radius * scale} fill="none" stroke="#8ab4f8" strokeWidth="2" vectorEffect="non-scaling-stroke"/>;
      }) : null}
      {geometry?.kind === 'boxes' ? (geometry.boxes ?? []).map((box: number[], index: number) => (
        <rect key={index} x={box[0] * imageSize.w} y={box[1] * imageSize.h} width={(box[2]-box[0])*imageSize.w} height={(box[3]-box[1])*imageSize.h} fill="none" stroke="#8ab4f8" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      )) : null}
    </svg>
  );

  return (
    <div
      ref={hostRef}
      className="relative h-full w-full overflow-hidden bg-[#111] select-none"
      onWheel={(event) => {
        event.preventDefault();
        const factor = event.deltaY < 0 ? 1.12 : 0.89;
        setZoom((value) => Math.min(20, Math.max(0.08, value * factor)));
      }}
      onMouseDown={(event) => { if (event.button === 0) dragRef.current = { x: event.clientX, y: event.clientY, px: pan.x, py: pan.y }; }}
      onMouseMove={(event) => {
        const drag = dragRef.current;
        if (!drag) return;
        setPan({ x: drag.px + event.clientX - drag.x, y: drag.py + event.clientY - drag.y });
      }}
      onMouseUp={() => { dragRef.current = null; }}
      onMouseLeave={() => { dragRef.current = null; }}
      onDoubleClick={reset}
    >
      {sourceUrl ? (
        <div
          className="absolute left-1/2 top-1/2 origin-center"
          style={{
            width: imageSize.w,
            height: imageSize.h,
            transform: `translate(-50%, -50%) translate(${pan.x}px, ${pan.y}px) scale(${fitScale * zoom})`,
          }}
        >
          <img
            src={sourceUrl}
            alt="Sampling source"
            draggable={false}
            className="absolute inset-0 h-full w-full"
            onLoad={(event) => {
              const image = event.currentTarget;
              setImageSize({ w: Math.max(1, image.naturalWidth), h: Math.max(1, image.naturalHeight) });
            }}
          />
          {overlay}
        </div>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-sm text-[#5f6368]">Build the shared Source Board first.</div>
      )}

      <div className="absolute right-3 top-3 flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124]/90 p-1 shadow-lg">
        <button onClick={() => setZoom((value)=>Math.max(0.08,value/1.2))} className="rounded p-1 text-[#bdc1c6] hover:bg-[#3c4043]"><Minus size={12}/></button>
        <span className="min-w-[54px] text-center font-mono text-[9px] text-[#8ab4f8]">{Math.round(zoom * 100)}%</span>
        <button onClick={() => setZoom((value)=>Math.min(20,value*1.2))} className="rounded p-1 text-[#bdc1c6] hover:bg-[#3c4043]"><Plus size={12}/></button>
        <button onClick={reset} className="rounded p-1 text-[#bdc1c6] hover:bg-[#3c4043]" title="Fit/reset"><RotateCcw size={12}/></button>
        <Maximize2 size={11} className="mx-1 text-[#5f6368]"/>
      </div>
      <div className="absolute bottom-2 left-2 rounded bg-[#202124]/85 px-2 py-1 text-[8px] text-[#80868b]">Wheel zoom · drag pan · double-click fit</div>
    </div>
  );
};
