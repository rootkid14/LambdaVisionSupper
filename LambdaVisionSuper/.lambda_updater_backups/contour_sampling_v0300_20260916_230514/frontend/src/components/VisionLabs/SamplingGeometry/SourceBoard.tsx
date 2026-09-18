import { Eye, ImagePlus, Route, Upload } from 'lucide-react';
import type { LabServiceDefinition } from '../../../api/labServiceApi';
import type { SourceBoardConfig, SourceBoardManifest } from './types';

const outputOptions = (service: LabServiceDefinition | undefined, allowed: string[]) =>
  Object.entries(service?.outputs ?? {}).filter(([, output]) => allowed.includes(output.type));

export const SourceBoard = ({
  file,
  onFile,
  config,
  onConfig,
  services,
  manifest,
  busy,
  onBuild,
  onInspect,
}: {
  file: File | null;
  onFile: (file: File | null) => void;
  config: SourceBoardConfig;
  onConfig: (config: SourceBoardConfig) => void;
  services: LabServiceDefinition[];
  manifest: SourceBoardManifest | null;
  busy: boolean;
  onBuild: () => void;
  onInspect: (sourceName: string) => void;
}) => {
  const imageService = services.find((service) => service.service_id === config.image_service.service_id);
  const geometryService = services.find((service) => service.service_id === config.geometry_service.service_id);
  const imageOutputs = outputOptions(imageService, ['image']);
  const geometryOutputs = outputOptions(geometryService, ['image', 'binary_mask']);

  const updatePin = (kind: 'image_service' | 'geometry_service', patch: Record<string, any>) => {
    onConfig({ ...config, [kind]: { ...config[kind], ...patch } });
  };

  return (
    <section className="border-t border-[#3c4043] bg-[#202124] px-3 py-2">
      <div className="grid grid-cols-[220px_minmax(0,1fr)_minmax(0,1fr)_auto] items-stretch gap-2">
        <label className="flex min-w-0 cursor-pointer flex-col justify-center rounded border border-[#3c4043] bg-[#292a2d] px-3 py-2 hover:border-[#5f6368]">
          <span className="flex items-center gap-2 text-[9px] font-black uppercase tracking-wider text-[#8ab4f8]"><Upload size={11}/>Input Image</span>
          <span className="mt-1 truncate text-[10px] text-[#e8eaed]">{file?.name ?? 'Choose one image for all workspaces'}</span>
          <input type="file" accept="image/*" className="hidden" onChange={(event) => onFile(event.target.files?.[0] ?? null)} />
        </label>

        <div className="rounded border border-[#3c4043] bg-[#292a2d] p-2">
          <div className="mb-1 flex items-center gap-2 text-[9px] font-black uppercase tracking-wider text-[#81c995]"><Route size={11}/>Image Processing Service</div>
          <div className="grid grid-cols-2 gap-1.5">
            <select
              value={config.image_service.service_id}
              onChange={(event) => {
                const serviceId = event.target.value;
                const service = services.find((item) => item.service_id === serviceId);
                const first = outputOptions(service, ['image'])[0]?.[0] ?? '';
                updatePin('image_service', { service_id: serviceId, output_name: first, version: null });
              }}
              className="min-w-0 rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px] text-[#e8eaed]"
            >
              <option value="">Blank → raw image</option>
              {services.map((service) => <option key={service.service_id} value={service.service_id}>{service.name} · v{service.version}</option>)}
            </select>
            <select value={config.image_service.output_name} onChange={(event) => updatePin('image_service', { output_name: event.target.value })} disabled={!imageService} className="min-w-0 rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px] text-[#e8eaed] disabled:opacity-40">
              <option value="">Image output…</option>
              {imageOutputs.map(([name, output]) => <option key={name} value={name}>{name}:{output.type}</option>)}
            </select>
          </div>
          <div className="mt-1 text-[8px] text-[#80868b]">Produces <b>inspected_image</b> for Spatial and Spectral workspaces.</div>
        </div>

        <div className="rounded border border-[#3c4043] bg-[#292a2d] p-2">
          <div className="mb-1 flex items-center gap-2 text-[9px] font-black uppercase tracking-wider text-[#fdd663]"><Route size={11}/>Contour Source Service</div>
          <div className="grid grid-cols-2 gap-1.5">
            <select
              value={config.geometry_service.service_id}
              onChange={(event) => {
                const serviceId = event.target.value;
                const service = services.find((item) => item.service_id === serviceId);
                const first = outputOptions(service, ['image', 'binary_mask'])[0]?.[0] ?? '';
                updatePin('geometry_service', { service_id: serviceId, output_name: first, version: null });
              }}
              className="min-w-0 rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px] text-[#e8eaed]"
            >
              <option value="">Blank → Canny(raw image)</option>
              {services.map((service) => <option key={service.service_id} value={service.service_id}>{service.name} · v{service.version}</option>)}
            </select>
            <select value={config.geometry_service.output_name} onChange={(event) => updatePin('geometry_service', { output_name: event.target.value })} disabled={!geometryService} className="min-w-0 rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px] text-[#e8eaed] disabled:opacity-40">
              <option value="">Raster/mask output…</option>
              {geometryOutputs.map(([name, output]) => <option key={name} value={name}>{name}:{output.type}</option>)}
            </select>
          </div>
          <div className="mt-1 grid grid-cols-3 gap-1">
            <label className="text-[8px] text-[#9aa0a6]">Canny low<input type="number" value={config.canny_low} onChange={(e)=>onConfig({...config,canny_low:Number(e.target.value)})} className="mt-0.5 w-full rounded border border-[#5f6368] bg-[#202124] px-1 py-0.5 text-[9px] text-[#e8eaed]"/></label>
            <label className="text-[8px] text-[#9aa0a6]">Canny high<input type="number" value={config.canny_high} onChange={(e)=>onConfig({...config,canny_high:Number(e.target.value)})} className="mt-0.5 w-full rounded border border-[#5f6368] bg-[#202124] px-1 py-0.5 text-[9px] text-[#e8eaed]"/></label>
            <label className="text-[8px] text-[#9aa0a6]">Blur<input type="number" min={1} step={2} value={config.blur_kernel} onChange={(e)=>onConfig({...config,blur_kernel:Number(e.target.value)})} className="mt-0.5 w-full rounded border border-[#5f6368] bg-[#202124] px-1 py-0.5 text-[9px] text-[#e8eaed]"/></label>
          </div>
        </div>

        <button onClick={onBuild} disabled={!file || busy} className="flex min-w-[120px] items-center justify-center gap-2 rounded border border-[#8ab4f8] bg-[#174ea6] px-3 text-[9px] font-black text-[#d2e3fc] disabled:opacity-35"><ImagePlus size={13}/>{manifest ? 'Rebuild Sources' : 'Build Sources'}</button>
      </div>

      <div className="mt-2 flex min-h-[30px] items-center gap-1.5 overflow-x-auto rounded border border-[#3c4043] bg-[#171717] p-1.5">
        <span className="mr-1 shrink-0 text-[8px] font-black uppercase tracking-wider text-[#80868b]">Exposed source data</span>
        {(manifest?.entries ?? []).map((entry) => (
          <button key={entry.name} onClick={() => onInspect(entry.name)} title={entry.origin} className="flex shrink-0 items-center gap-1.5 rounded border border-[#3c4043] bg-[#292a2d] px-2 py-1 text-[8px] text-[#bdc1c6] hover:border-[#8ab4f8]">
            <Eye size={9} className="text-[#8ab4f8]"/><b>{entry.name}</b><span className="text-[#80868b]">{entry.type}</span>
            {entry.name === 'master_contours' && manifest?.geometry_contour_count !== undefined ? <span className="rounded bg-[#3c4043] px-1 font-mono text-[#fdd663]">{manifest.geometry_contour_count}</span> : null}
          </button>
        ))}
        {!manifest ? <span className="text-[8px] text-[#5f6368]">Build once; the same source board remains active while switching tabs.</span> : null}
      </div>
    </section>
  );
};
