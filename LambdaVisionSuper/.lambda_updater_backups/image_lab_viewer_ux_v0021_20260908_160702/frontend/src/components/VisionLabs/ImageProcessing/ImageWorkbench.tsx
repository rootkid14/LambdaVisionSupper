import { useRef } from 'react';
import { Columns2, ImagePlus, LayoutGrid, Loader2, Play, Square } from 'lucide-react';
import type { ViewerCount, ViewerSource } from './types';
import { ZoomPanImageView } from './ZoomPanImageView';

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
    <main className="min-w-0 flex-1 flex flex-col bg-[#202124]">
      <div className="h-12 border-b border-[#3c4043] bg-[#292a2d] flex items-center justify-between px-3 gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-2 rounded-md border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-semibold text-[#e8eaed] hover:bg-[#3c4043]"
          >
            <ImagePlus size={14} className="text-[#8ab4f8]" /> Load Image
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
          <span className="truncate text-[10px] text-[#9aa0a6]">{imageName || 'No image loaded'}</span>
        </div>

        <div className="flex items-center gap-1 rounded-md border border-[#3c4043] bg-[#202124] p-1">
          <button onClick={() => onViewerCountChange(1)} title="1 viewer" className={`p-1.5 rounded ${viewerCount === 1 ? 'bg-[#3c4043] text-[#8ab4f8]' : 'text-[#9aa0a6] hover:bg-[#35363a] hover:text-white'}`}><Square size={14} /></button>
          <button onClick={() => onViewerCountChange(2)} title="2 viewers" className={`p-1.5 rounded ${viewerCount === 2 ? 'bg-[#3c4043] text-[#8ab4f8]' : 'text-[#9aa0a6] hover:bg-[#35363a] hover:text-white'}`}><Columns2 size={14} /></button>
          <button onClick={() => onViewerCountChange(4)} title="4 viewers" className={`p-1.5 rounded ${viewerCount === 4 ? 'bg-[#3c4043] text-[#8ab4f8]' : 'text-[#9aa0a6] hover:bg-[#35363a] hover:text-white'}`}><LayoutGrid size={14} /></button>
        </div>

        <button
          onClick={onRun}
          disabled={!sourceLoaded || busy}
          className="flex items-center gap-2 rounded-md border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-semibold text-[#e8eaed] hover:bg-[#3c4043] disabled:opacity-40"
        >
          {busy ? <Loader2 size={14} className="animate-spin text-[#8ab4f8]" /> : <Play size={14} className="text-[#8ab4f8]" />}
          Run
        </button>
      </div>

      <div className={`flex-1 min-h-0 grid ${viewGridClass(viewerCount)} gap-px bg-[#5f6368] p-px`}>
        {Array.from({ length: viewerCount }).map((_, index) => {
          const selectedKey = viewerKeys[index] ?? sources[0]?.key ?? 'source:image';
          const selected = sources.find((source) => source.key === selectedKey) ?? sources[0];
          const url = selected ? previewUrls[selected.key] : undefined;
          return (
            <section key={index} className="relative min-h-0 min-w-0 bg-[#171717] flex flex-col overflow-hidden">
              <div className="h-9 border-b border-[#3c4043] bg-[#292a2d] flex items-center px-2 gap-2">
                <span className="text-[9px] font-black tracking-widest text-[#9aa0a6]">VIEW {index + 1}</span>
                <select
                  value={selectedKey}
                  onChange={(event: any) => onViewerSourceChange(index, event.target.value)}
                  className="min-w-0 flex-1 rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[10px] text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
                >
                  {sources.map((source) => (
                    <option key={source.key} value={source.key}>{source.label}</option>
                  ))}
                </select>
                {selected?.dataType && <span className="rounded bg-[#202124] px-1.5 py-0.5 text-[9px] text-[#9aa0a6]">{selected.dataType}</span>}
              </div>

              <div className="relative flex-1 min-h-0 overflow-hidden">
                {url ? (
                  <ZoomPanImageView src={url} alt={selected?.label ?? 'Image LAB preview'} />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center text-center text-[#9aa0a6]">
                    <div>
                      <ImagePlus size={34} className="mx-auto mb-2 opacity-40" />
                      <div className="text-xs">{sourceLoaded ? 'Preview not generated yet' : 'Load an image to start experimenting'}</div>
                    </div>
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
