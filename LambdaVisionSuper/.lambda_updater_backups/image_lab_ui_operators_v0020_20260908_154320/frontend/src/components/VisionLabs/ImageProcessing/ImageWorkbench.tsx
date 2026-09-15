import { useRef } from 'react';
import { ImagePlus, LayoutGrid, Columns2, Square, Play, Loader2 } from 'lucide-react';
import type { ViewerCount, ViewerSource } from './types';

interface Props {
  sourceLoaded: boolean;
  imageName?: string;
  viewerCount: ViewerCount;
  viewerKeys: string[];
  sources: ViewerSource[];
  previewUrls: Record<string, string>;
  busy: boolean;
  onUpload: (file: File) => void;
  onViewerCountChange: (count: ViewerCount) => void;
  onViewerSourceChange: (index: number, key: string) => void;
  onRun: () => void;
}

const viewGridClass = (count: ViewerCount) => {
  if (count === 1) return 'grid-cols-1 grid-rows-1';
  if (count === 2) return 'grid-cols-2 grid-rows-1';
  return 'grid-cols-2 grid-rows-2';
};

export const ImageWorkbench = ({
  sourceLoaded,
  imageName,
  viewerCount,
  viewerKeys,
  sources,
  previewUrls,
  busy,
  onUpload,
  onViewerCountChange,
  onViewerSourceChange,
  onRun,
}: Props) => {
  const fileRef = useRef<HTMLInputElement | null>(null);

  return (
    <main className="min-w-0 flex-1 flex flex-col bg-slate-950">
      <div className="h-12 border-b border-slate-800 bg-slate-900/70 flex items-center justify-between px-3 gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-bold text-cyan-300 hover:bg-cyan-500/20"
          >
            <ImagePlus size={14} /> Load Image
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event: any) => {
              const file = event.target.files?.[0];
              if (file) onUpload(file);
              event.currentTarget.value = '';
            }}
          />
          <span className="truncate text-[10px] text-slate-500">{imageName || 'No image loaded'}</span>
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950 p-1">
          <button onClick={() => onViewerCountChange(1)} title="1 viewer" className={`p-1.5 rounded ${viewerCount === 1 ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-200'}`}><Square size={14} /></button>
          <button onClick={() => onViewerCountChange(2)} title="2 viewers" className={`p-1.5 rounded ${viewerCount === 2 ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-200'}`}><Columns2 size={14} /></button>
          <button onClick={() => onViewerCountChange(4)} title="4 viewers" className={`p-1.5 rounded ${viewerCount === 4 ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-200'}`}><LayoutGrid size={14} /></button>
        </div>

        <button
          onClick={onRun}
          disabled={!sourceLoaded || busy}
          className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-40"
        >
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          Run
        </button>
      </div>

      <div className={`flex-1 min-h-0 grid ${viewGridClass(viewerCount)} gap-px bg-slate-800 p-px`}>
        {Array.from({ length: viewerCount }).map((_, index) => {
          const selectedKey = viewerKeys[index] ?? sources[0]?.key ?? 'source:image';
          const selected = sources.find((source) => source.key === selectedKey) ?? sources[0];
          const url = selected ? previewUrls[selected.key] : undefined;
          return (
            <section key={index} className="relative min-h-0 min-w-0 bg-[#060a12] flex flex-col overflow-hidden">
              <div className="h-9 border-b border-slate-800 bg-slate-950/90 flex items-center px-2 gap-2">
                <span className="text-[9px] font-black tracking-widest text-slate-600">VIEW {index + 1}</span>
                <select
                  value={selectedKey}
                  onChange={(event: any) => onViewerSourceChange(index, event.target.value)}
                  className="min-w-0 flex-1 rounded-md border border-slate-800 bg-slate-900 px-2 py-1 text-[10px] text-slate-300 outline-none focus:border-cyan-500"
                >
                  {sources.map((source) => (
                    <option key={source.key} value={source.key}>{source.label}</option>
                  ))}
                </select>
                {selected?.dataType && <span className="rounded bg-slate-900 px-1.5 py-0.5 text-[9px] text-slate-600">{selected.dataType}</span>}
              </div>

              <div className="relative flex-1 min-h-0 flex items-center justify-center overflow-hidden p-2">
                {url ? (
                  <img
                    src={url}
                    alt={selected?.label ?? 'Image LAB preview'}
                    draggable={false}
                    className="max-w-full max-h-full object-contain select-none shadow-[0_0_30px_rgba(0,0,0,0.35)]"
                  />
                ) : (
                  <div className="text-center text-slate-600">
                    <ImagePlus size={34} className="mx-auto mb-2 opacity-40" />
                    <div className="text-xs">{sourceLoaded ? 'Preview not generated yet' : 'Load an image to start experimenting'}</div>
                  </div>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </main>
  );
};
