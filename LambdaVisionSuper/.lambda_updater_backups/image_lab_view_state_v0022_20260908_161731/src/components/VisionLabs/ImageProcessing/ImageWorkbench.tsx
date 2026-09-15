import { useRef, useState, type CSSProperties } from 'react';
import {
  Columns2,
  ImagePlus,
  LayoutGrid,
  Loader2,
  Play,
  Plus,
  RotateCcw,
  Square,
  X,
} from 'lucide-react';
import type {
  ViewerPane,
  ViewerSource,
} from './types';
import { ZoomPanImageView } from './ZoomPanImageView';

interface Props {
  sourceLoaded: boolean;
  imageName?: string;
  viewerPanes: ViewerPane[];
  sources: ViewerSource[];
  previewUrls: Record<string, string>;
  busy: boolean;
  onUpload: (file: File) => void;
  onViewerSourceChange: (
    viewerId: string,
    key: string,
  ) => void;
  onAddViewer: () => void;
  onRemoveViewer: (viewerId: string) => void;
  onSetViewerPreset: (count: number) => void;
  onRun: () => void;
}

const clamp = (
  value: number,
  min: number,
  max: number,
) => Math.min(
  max,
  Math.max(min, value),
);

const defaultPaneStyle = (
  count: number,
): CSSProperties => {
  if (count <= 1) {
    return {
      flex: '1 1 100%',
      height: '100%',
    };
  }

  if (count <= 2) {
    return {
      flex: '1 1 calc(50% - 4px)',
      height: '100%',
    };
  }

  if (count <= 4) {
    return {
      flex: '1 1 calc(50% - 4px)',
      height: 'calc(50% - 4px)',
    };
  }

  return {
    flex: '1 1 360px',
    height: 340,
  };
};

const ResizableViewerPane = ({
  pane,
  index,
  paneCount,
  sources,
  previewUrls,
  sourceLoaded,
  onSourceChange,
  onRemove,
}: {
  pane: ViewerPane;
  index: number;
  paneCount: number;
  sources: ViewerSource[];
  previewUrls: Record<string, string>;
  sourceLoaded: boolean;
  onSourceChange: (key: string) => void;
  onRemove: () => void;
}) => {
  const paneRef = useRef<HTMLElement | null>(null);
  const resizeRef = useRef<{
    pointerId: number;
    x: number;
    y: number;
    width: number;
    height: number;
  } | null>(null);

  const [size, setSize] = useState<{
    width: number;
    height: number;
  } | null>(null);

  const selected = sources.find(
    (source) => source.key === pane.sourceKey,
  )
    ?? sources.find(
      (source) => source.key === 'latest',
    )
    ?? sources[0];

  const url = selected
    ? previewUrls[selected.key]
    : undefined;

  return (
    <section
      ref={paneRef}
      className="relative min-h-[220px] min-w-[280px] bg-[#171717] flex flex-col overflow-hidden border border-[#3c4043]"
      style={
        size
          ? {
              flex: '0 0 auto',
              width: size.width,
              height: size.height,
            }
          : defaultPaneStyle(paneCount)
      }
    >
      <div className="h-9 shrink-0 border-b border-[#3c4043] bg-[#292a2d] flex items-center px-2 gap-2">
        <span className="text-[9px] font-black tracking-widest text-[#9aa0a6]">
          VIEW {index + 1}
        </span>

        <select
          value={selected?.key ?? 'latest'}
          onChange={(event: any) => {
            onSourceChange(event.target.value);
          }}
          className="min-w-0 flex-1 rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[10px] text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
        >
          {sources.map((source) => (
            <option
              key={source.key}
              value={source.key}
            >
              {source.label}
            </option>
          ))}
        </select>

        {selected?.dataType && (
          <span className="rounded bg-[#202124] px-1.5 py-0.5 text-[9px] text-[#9aa0a6]">
            {selected.dataType}
          </span>
        )}

        {size && (
          <button
            onClick={() => setSize(null)}
            title="Reset pane size"
            className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"
          >
            <RotateCcw size={12} />
          </button>
        )}

        {paneCount > 1 && (
          <button
            onClick={onRemove}
            title="Remove view"
            className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-[#f28b82]"
          >
            <X size={13} />
          </button>
        )}
      </div>

      <div className="relative flex-1 min-h-0 overflow-hidden">
        {url ? (
          <ZoomPanImageView
            src={url}
            alt={
              selected?.label
              ?? 'Image LAB preview'
            }
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-center text-[#9aa0a6]">
            <div>
              <ImagePlus
                size={34}
                className="mx-auto mb-2 opacity-40"
              />
              <div className="text-xs">
                {
                  sourceLoaded
                    ? 'Preview not generated yet'
                    : 'Load an image to start experimenting'
                }
              </div>
            </div>
          </div>
        )}
      </div>

      <div
        role="separator"
        aria-label="Resize viewer"
        title="Drag to resize this view"
        className="absolute bottom-0 right-0 z-30 h-5 w-5 cursor-nwse-resize"
        onPointerDown={(event) => {
          event.preventDefault();
          event.stopPropagation();

          const element = paneRef.current;
          if (!element) return;

          const rect = element.getBoundingClientRect();

          event.currentTarget.setPointerCapture(
            event.pointerId,
          );

          resizeRef.current = {
            pointerId: event.pointerId,
            x: event.clientX,
            y: event.clientY,
            width: rect.width,
            height: rect.height,
          };
        }}
        onPointerMove={(event) => {
          const resize = resizeRef.current;

          if (
            !resize
            || resize.pointerId !== event.pointerId
          ) {
            return;
          }

          const maxWidth = Math.max(
            320,
            (
              paneRef.current
                ?.parentElement
                ?.clientWidth
              ?? 1800
            ) - 8,
          );

          const maxHeight = Math.max(
            260,
            (
              paneRef.current
                ?.parentElement
                ?.clientHeight
              ?? 1200
            ) - 8,
          );

          setSize({
            width: clamp(
              resize.width
                + event.clientX
                - resize.x,
              280,
              maxWidth,
            ),
            height: clamp(
              resize.height
                + event.clientY
                - resize.y,
              220,
              maxHeight,
            ),
          });
        }}
        onPointerUp={(event) => {
          if (
            resizeRef.current?.pointerId
            === event.pointerId
          ) {
            resizeRef.current = null;
          }
        }}
        onPointerCancel={() => {
          resizeRef.current = null;
        }}
      >
        <div className="absolute bottom-1 right-1 h-2.5 w-2.5 border-b-2 border-r-2 border-[#9aa0a6]" />
      </div>
    </section>
  );
};

export const ImageWorkbench = ({
  sourceLoaded,
  imageName,
  viewerPanes,
  sources,
  previewUrls,
  busy,
  onUpload,
  onViewerSourceChange,
  onAddViewer,
  onRemoveViewer,
  onSetViewerPreset,
  onRun,
}: Props) => {
  const fileRef = useRef<HTMLInputElement | null>(null);

  return (
    <main className="min-w-0 flex-1 flex flex-col bg-[#202124]">
      <div className="h-12 shrink-0 border-b border-[#3c4043] bg-[#292a2d] flex items-center justify-between px-3 gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <button
            onClick={() => {
              fileRef.current?.click();
            }}
            className="flex items-center gap-2 rounded-md border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-semibold text-[#e8eaed] hover:bg-[#3c4043]"
          >
            <ImagePlus
              size={14}
              className="text-[#8ab4f8]"
            />
            Load Image
          </button>

          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event: any) => {
              const file =
                event.target.files?.[0];

              if (file) {
                onUpload(file);
              }

              event.currentTarget.value = '';
            }}
          />

          <span className="truncate text-[10px] text-[#9aa0a6]">
            {
              imageName
              || 'No image loaded'
            }
          </span>
        </div>

        <div className="flex items-center gap-1 rounded-md border border-[#3c4043] bg-[#202124] p-1">
          <button
            onClick={() => {
              onSetViewerPreset(1);
            }}
            title="1 view preset"
            className="p-1.5 rounded text-[#9aa0a6] hover:bg-[#35363a] hover:text-[#8ab4f8]"
          >
            <Square size={14} />
          </button>

          <button
            onClick={() => {
              onSetViewerPreset(2);
            }}
            title="2 view preset"
            className="p-1.5 rounded text-[#9aa0a6] hover:bg-[#35363a] hover:text-[#8ab4f8]"
          >
            <Columns2 size={14} />
          </button>

          <button
            onClick={() => {
              onSetViewerPreset(4);
            }}
            title="4 view preset"
            className="p-1.5 rounded text-[#9aa0a6] hover:bg-[#35363a] hover:text-[#8ab4f8]"
          >
            <LayoutGrid size={14} />
          </button>

          <div className="mx-0.5 h-4 w-px bg-[#5f6368]" />

          <button
            onClick={onAddViewer}
            title="Add another independent viewer"
            className="flex items-center gap-1 rounded px-2 py-1.5 text-[10px] font-bold text-[#bdc1c6] hover:bg-[#35363a] hover:text-[#8ab4f8]"
          >
            <Plus size={13} />
            View
          </button>

          <span className="px-1 text-[9px] text-[#80868b]">
            {viewerPanes.length} open
          </span>
        </div>

        <button
          onClick={onRun}
          disabled={
            !sourceLoaded
            || busy
          }
          className="flex items-center gap-2 rounded-md border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-semibold text-[#e8eaed] hover:bg-[#3c4043] disabled:opacity-40"
        >
          {
            busy
              ? (
                  <Loader2
                    size={14}
                    className="animate-spin text-[#8ab4f8]"
                  />
                )
              : (
                  <Play
                    size={14}
                    className="text-[#8ab4f8]"
                  />
                )
          }
          Run
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-auto bg-[#171717] p-1">
        <div className="min-h-full min-w-full flex flex-wrap content-start items-stretch gap-1">
          {viewerPanes.map((pane, index) => (
            <ResizableViewerPane
              key={pane.id}
              pane={pane}
              index={index}
              paneCount={viewerPanes.length}
              sources={sources}
              previewUrls={previewUrls}
              sourceLoaded={sourceLoaded}
              onSourceChange={(key) => {
                onViewerSourceChange(
                  pane.id,
                  key,
                );
              }}
              onRemove={() => {
                onRemoveViewer(pane.id);
              }}
            />
          ))}
        </div>
      </div>
    </main>
  );
};
