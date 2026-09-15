import { useCallback, useEffect, useRef, useState } from 'react';
import { Maximize2, Minus, Move, Plus, RotateCcw } from 'lucide-react';

interface Props {
  src?: string;
  alt: string;
}

type Pan = { x: number; y: number };

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

export const ZoomPanImageView = ({ src, alt }: Props) => {
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 });
  const dragRef = useRef<{ pointerId: number; x: number; y: number; start: Pan } | null>(null);

  const resetView = useCallback(() => {
    setScale(1);
    setPan({ x: 0, y: 0 });
  }, []);

  useEffect(() => {
    resetView();
  }, [src, resetView]);

  const zoomBy = useCallback((factor: number) => {
    setScale((current) => clamp(current * factor, 0.2, 12));
  }, []);

  if (!src) return null;

  return (
    <div
      className="relative h-full w-full overflow-hidden bg-[#171717] select-none"
      onWheel={(event) => {
        event.preventDefault();
        zoomBy(event.deltaY < 0 ? 1.12 : 1 / 1.12);
      }}
      onDoubleClick={resetView}
      onPointerDown={(event) => {
        if (event.button !== 0) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        dragRef.current = {
          pointerId: event.pointerId,
          x: event.clientX,
          y: event.clientY,
          start: pan,
        };
      }}
      onPointerMove={(event) => {
        const drag = dragRef.current;
        if (!drag || drag.pointerId !== event.pointerId) return;
        setPan({
          x: drag.start.x + (event.clientX - drag.x),
          y: drag.start.y + (event.clientY - drag.y),
        });
      }}
      onPointerUp={(event) => {
        if (dragRef.current?.pointerId === event.pointerId) dragRef.current = null;
      }}
      onPointerCancel={() => {
        dragRef.current = null;
      }}
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <img
          src={src}
          alt={alt}
          draggable={false}
          className="max-h-full max-w-full object-contain pointer-events-none"
          style={{
            transform: `translate3d(${pan.x}px, ${pan.y}px, 0) scale(${scale})`,
            transformOrigin: 'center center',
            willChange: 'transform',
          }}
        />
      </div>

      <div className="absolute left-2 top-2 z-10 flex items-center gap-1 rounded-md border border-[#5f6368] bg-[#292a2d]/95 p-1 shadow-lg">
        <button
          onClick={() => zoomBy(1 / 1.18)}
          title="Zoom out"
          className="rounded p-1.5 text-[#bdc1c6] hover:bg-[#3c4043] hover:text-white"
        >
          <Minus size={13} />
        </button>
        <span className="min-w-[48px] text-center font-mono text-[10px] text-[#bdc1c6]">
          {Math.round(scale * 100)}%
        </span>
        <button
          onClick={() => zoomBy(1.18)}
          title="Zoom in"
          className="rounded p-1.5 text-[#bdc1c6] hover:bg-[#3c4043] hover:text-white"
        >
          <Plus size={13} />
        </button>
        <div className="mx-0.5 h-4 w-px bg-[#5f6368]" />
        <button
          onClick={resetView}
          title="Fit / reset view"
          className="rounded p-1.5 text-[#bdc1c6] hover:bg-[#3c4043] hover:text-white"
        >
          <Maximize2 size={13} />
        </button>
      </div>

      <div className="absolute bottom-2 left-2 z-10 flex items-center gap-1.5 rounded bg-black/55 px-2 py-1 text-[9px] text-[#9aa0a6]">
        <Move size={11} />
        Drag to pan · Wheel to zoom · Double click to fit
      </div>

      {(scale !== 1 || pan.x !== 0 || pan.y !== 0) && (
        <button
          onClick={resetView}
          title="Reset"
          className="absolute right-2 top-2 z-10 rounded-md border border-[#5f6368] bg-[#292a2d]/95 p-1.5 text-[#bdc1c6] hover:bg-[#3c4043] hover:text-white"
        >
          <RotateCcw size={13} />
        </button>
      )}
    </div>
  );
};
