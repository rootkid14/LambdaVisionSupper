import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Boxes,
  BrainCircuit,
  Eye,
  FlaskConical,
  Image as ImageIcon,
  Loader2,
  PackageCheck,
  Pencil,
  Play,
  RefreshCw,
  Scale,
  ScanLine,
  Upload,
  Trash2,
  X,
} from 'lucide-react';
import {
  LabServiceAPI,
  type LabServiceDefinition,
  type LabServiceRunManifest,
} from '../api/labServiceApi';
import { ZoomPanImageView } from '../components/VisionLabs/ImageProcessing/ZoomPanImageView';

const labs = [
  {
    id: 'image-processing',
    title: 'Image Processing LAB',
    subtitle: 'Raster transforms, filtering, thresholding, edge extraction and morphology.',
    icon: ImageIcon,
    enabled: true,
    route: '/labs/image-processing',
  },
  { id: 'contour-extractor', title: 'Contour Extractor LAB', subtitle: 'Memory-efficient candidate generation, contour cleanup, filtering and meaningful shape selection.', icon: ScanLine, enabled: true, route: '/labs/contour-extractor' },
  { id: 'sampling', title: 'Sampling LAB', subtitle: 'Spatial sampling units, Data Blocks, layout composition, Fourier and statistical descriptors.', icon: Boxes, enabled: true, route: '/labs/sampling-geometry' },
  { id: 'representation', title: 'Representation LAB', subtitle: 'Vectors, matrices, tensors and feature representations.', icon: Boxes, enabled: false },
  { id: 'ai', title: 'AI LAB', subtitle: 'Model architecture, inference and training experiments.', icon: BrainCircuit, enabled: false },
  { id: 'rule', title: 'Comparison / Rule LAB', subtitle: 'Measurements, comparison, specs and decision primitives.', icon: Scale, enabled: false },
];

interface OutputViewerState {
  service: LabServiceDefinition;
  run: LabServiceRunManifest;
  outputName: string;
  url: string;
}

const LabServiceCard = ({
  service,
  onEdit,
  onViewOutput,
  onError,
  onDelete,
}: {
  service: LabServiceDefinition;
  onEdit: () => void;
  onViewOutput: (
    service: LabServiceDefinition,
    run: LabServiceRunManifest,
    outputName: string,
  ) => Promise<void>;
  onError: (message: string) => void;
  onDelete: () => void;
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [runManifest, setRunManifest] = useState<LabServiceRunManifest | null>(null);
  const [running, setRunning] = useState(false);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const runService = async () => {
    if (!file) return;

    try {
      setRunning(true);
      onError('');
      const manifest = await LabServiceAPI.runImage(
        service.service_id,
        file,
        service.version,
      );
      setRunManifest(manifest);
    } catch (cause: any) {
      onError(
        cause?.response?.data?.detail
        || cause?.message
        || `Failed to run ${service.name}`,
      );
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    setRunManifest(null);
  }, [service.version]);

  return (
    <article className="rounded-lg border border-[#3c4043] bg-[#292a2d] overflow-hidden flex flex-col min-h-[260px]">
      <div className="px-4 py-3 border-b border-[#3c4043] flex items-start gap-3">
        <PackageCheck size={17} className="mt-0.5 shrink-0 text-[#8ab4f8]" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-black text-[#e8eaed]">
              {service.name}
            </h3>
            <span className="rounded bg-[#1e3828] px-2 py-0.5 text-[9px] font-black text-[#81c995]">
              v{service.version}
            </span>
          </div>
          <div className="mt-0.5 truncate font-mono text-[9px] text-[#80868b]">
            {service.service_id} · {service.lab_type}{service.workspace_type ? ` · ${service.workspace_type}` : ''}
          </div>
        </div>
        <button
          onClick={onEdit}
          className="flex shrink-0 items-center gap-1 rounded border border-[#5f6368] bg-[#35363a] px-2 py-1 text-[10px] font-bold text-[#bdc1c6] hover:border-[#8ab4f8] hover:text-white"
          title="Open this deployed service snapshot in its LAB for editing"
        >
          <Pencil size={11} />
          Edit
        </button>
        <button onClick={onDelete} className="flex shrink-0 items-center gap-1 rounded border border-[#5f6368] bg-[#35363a] px-2 py-1 text-[10px] font-bold text-[#f28b82] hover:border-[#f28b82]" title="Permanently delete this service and all stored versions"><Trash2 size={11}/>Remove</button>
      </div>

      <div className="px-4 pt-3 grid grid-cols-2 gap-3 text-[9px]">
        <div>
          <div className="font-black tracking-wider text-[#80868b]">INPUTS</div>
          <div className="mt-1 flex flex-wrap gap-1">
            {Object.entries(service.inputs).map(([name, port]) => (
              <span key={name} className="rounded bg-[#202124] px-1.5 py-0.5 text-[#bdc1c6]">
                {name}:{port.type}
              </span>
            ))}
          </div>
        </div>
        <div>
          <div className="font-black tracking-wider text-[#80868b]">OUTPUTS</div>
          <div className="mt-1 flex flex-wrap gap-1">
            {Object.entries(service.outputs).map(([name, port]) => (
              <span key={name} className="rounded bg-[#202124] px-1.5 py-0.5 text-[#8ab4f8]">
                {name}:{port.type}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-3 border-t border-[#3c4043] bg-[#242528] px-3 py-2">
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(event: any) => {
            const next = event.target.files?.[0] ?? null;
            setFile(next);
            setRunManifest(null);
            event.currentTarget.value = '';
          }}
        />

        <div className="flex items-center gap-2">
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-1 rounded border border-[#5f6368] bg-[#35363a] px-2 py-1.5 text-[10px] font-bold text-[#e8eaed] hover:bg-[#3c4043]"
          >
            <Upload size={11} className="text-[#8ab4f8]" />
            Upload
          </button>
          <span className="min-w-0 flex-1 truncate text-[9px] text-[#9aa0a6]">
            {file?.name ?? 'No test image'}
          </span>
          <button
            onClick={runService}
            disabled={!file || running}
            className="flex items-center gap-1 rounded border border-[#8ab4f8] bg-[#174ea6] px-2 py-1.5 text-[10px] font-black text-[#d2e3fc] hover:bg-[#185abc] disabled:opacity-40"
          >
            {running ? <Loader2 size={11} className="animate-spin" /> : <Play size={11} />}
            Run
          </button>
        </div>

        {runManifest && (
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="mr-1 rounded bg-[#202124] px-2 py-1 font-mono text-[9px] text-[#81c995]">
              {runManifest.total_ms.toFixed(2)} ms
            </span>
            {Object.entries(runManifest.outputs).map(([outputName, output]) => (
              <button
                key={outputName}
                onClick={() => onViewOutput(service, runManifest, outputName)}
                className="flex items-center gap-1 rounded border border-[#5f6368] bg-[#35363a] px-2 py-1 text-[9px] font-bold text-[#bdc1c6] hover:border-[#8ab4f8] hover:text-white"
                title={`${outputName} · ${output.type}${output.shape ? ` · ${output.shape.join('×')}` : ''}`}
              >
                <Eye size={10} className="text-[#8ab4f8]" />
                View {outputName}
              </button>
            ))}
          </div>
        )}
      </div>
    </article>
  );
};

export const LabView = () => {
  const navigate = useNavigate();
  const [services, setServices] = useState<LabServiceDefinition[]>([]);
  const [loadingServices, setLoadingServices] = useState(false);
  const [error, setError] = useState('');
  const [viewer, setViewer] = useState<OutputViewerState | null>(null);
  const viewerUrlRef = useRef<string | null>(null);

  const loadServices = async () => {
    try {
      setLoadingServices(true);
      setError('');
      setServices(await LabServiceAPI.list());
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Failed to load Lab Services',
      );
    } finally {
      setLoadingServices(false);
    }
  };

  const closeViewer = () => {
    if (viewerUrlRef.current) {
      URL.revokeObjectURL(viewerUrlRef.current);
      viewerUrlRef.current = null;
    }
    setViewer(null);
  };

  const viewOutput = async (
    service: LabServiceDefinition,
    run: LabServiceRunManifest,
    outputName: string,
  ) => {
    try {
      setError('');
      if (viewerUrlRef.current) {
        URL.revokeObjectURL(viewerUrlRef.current);
        viewerUrlRef.current = null;
      }
      const blob = await LabServiceAPI.outputPreview(
        run.run_id,
        outputName,
        2200,
        92,
      );
      const url = URL.createObjectURL(blob);
      viewerUrlRef.current = url;
      setViewer({ service, run, outputName, url });
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Failed to load Lab Service output preview',
      );
    }
  };

  const deleteService = async (service: LabServiceDefinition) => {
    if (!window.confirm(`Delete ${service.name} and all versions? This cannot be undone.`)) return;
    try {
      setError('');
      await LabServiceAPI.remove(service.service_id);
      await loadServices();
    } catch (cause: any) {
      setError(cause?.response?.data?.detail || cause?.message || 'Failed to delete Lab Service');
    }
  };

  useEffect(() => {
    loadServices();
    return () => {
      if (viewerUrlRef.current) {
        URL.revokeObjectURL(viewerUrlRef.current);
      }
    };
  }, []);

  const viewerOutput = viewer
    ? viewer.run.outputs[viewer.outputName]
    : null;

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#202124] text-[#e8eaed] flex flex-col">
      <header className="h-16 shrink-0 border-b border-[#3c4043] bg-[#292a2d] flex items-center px-4 gap-3">
        <button
          onClick={() => navigate('/')}
          className="w-9 h-9 rounded-md border border-[#5f6368] bg-[#35363a] flex items-center justify-center text-[#bdc1c6] hover:bg-[#3c4043] hover:text-white"
        >
          <ArrowLeft size={17} />
        </button>
        <div className="w-px h-8 bg-[#5f6368]" />
        <FlaskConical size={20} className="text-[#8ab4f8]" />
        <div>
          <div className="text-sm font-black tracking-[0.16em]">VISION LABS</div>
          <div className="text-[10px] text-[#9aa0a6]">Experimental workbenches and deployed Lab Services</div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-8 py-8 bg-[#202124]">
        <div className="max-w-7xl mx-auto space-y-10">
          <section>
            <div className="mb-6">
              <div className="text-xs font-black tracking-[0.24em] text-[#8ab4f8] uppercase">LAB Launcher</div>
              <h1 className="mt-2 text-3xl font-black text-[#e8eaed]">Choose an experimental environment</h1>
              <p className="mt-2 max-w-2xl text-sm text-[#9aa0a6]">
                LABs are editors. Deployed Lab Services are independent callable snapshots; multiple services can remain deployed at the same time.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {labs.map((lab) => {
                const Icon = lab.icon;
                return (
                  <button
                    key={lab.id}
                    disabled={!lab.enabled}
                    onClick={() => lab.enabled && lab.route && navigate(lab.route)}
                    className={`group min-h-[180px] rounded-lg border p-5 text-left transition-all ${
                      lab.enabled
                        ? 'border-[#5f6368] bg-[#292a2d] hover:-translate-y-0.5 hover:border-[#8ab4f8] hover:bg-[#35363a] hover:shadow-xl'
                        : 'border-[#3c4043] bg-[#292a2d] opacity-50 cursor-not-allowed'
                    }`}
                  >
                    <div className={`w-11 h-11 rounded-md flex items-center justify-center ${lab.enabled ? 'bg-[#3c4043] text-[#8ab4f8]' : 'bg-[#35363a] text-[#80868b]'}`}>
                      <Icon size={22} />
                    </div>
                    <div className="mt-4 flex items-center gap-2">
                      <h2 className="text-base font-black text-[#e8eaed]">{lab.title}</h2>
                      {!lab.enabled && <span className="rounded bg-[#3c4043] px-2 py-0.5 text-[9px] font-bold text-[#9aa0a6]">COMING SOON</span>}
                    </div>
                    <p className="mt-2 text-xs leading-5 text-[#9aa0a6]">{lab.subtitle}</p>
                  </button>
                );
              })}
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-end justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs font-black tracking-[0.24em] text-[#8ab4f8] uppercase">
                  <PackageCheck size={15} />
                  Deployed Lab Services
                </div>
                <p className="mt-2 text-sm text-[#9aa0a6]">
                  Every card is an independent deployed service. Upload a test image directly on the card; outputs open only when you press View.
                </p>
              </div>
              <button
                onClick={loadServices}
                disabled={loadingServices}
                className="flex items-center gap-1.5 rounded border border-[#5f6368] bg-[#292a2d] px-3 py-1.5 text-xs font-bold text-[#bdc1c6] hover:bg-[#35363a] disabled:opacity-40"
              >
                <RefreshCw size={13} className={loadingServices ? 'animate-spin' : ''} />
                Refresh
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded border border-[#f28b82]/40 bg-[#5f2120] px-3 py-2 text-xs text-[#f28b82]">
                {error}
              </div>
            )}

            {services.length === 0 ? (
              <div className="rounded-lg border border-dashed border-[#5f6368] bg-[#292a2d] p-8 text-center text-sm text-[#9aa0a6]">
                No Lab Service has been deployed yet. Open a LAB, expose typed checkpoints, then deploy a reusable service.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {services.map((service) => (
                  <LabServiceCard
                    key={`${service.service_id}:${service.version}`}
                    service={service}
                    onEdit={() => navigate(service.lab_type === 'contour_extractor' ? `/labs/contour-extractor?editService=${encodeURIComponent(service.service_id)}` : service.lab_type === 'sampling_geometry' ? `/labs/sampling-geometry?editService=${encodeURIComponent(service.service_id)}` : `/labs/image-processing?editService=${encodeURIComponent(service.service_id)}`)}
                    onViewOutput={viewOutput}
                    onError={setError}
                    onDelete={() => void deleteService(service)}
                  />
                ))}
              </div>
            )}
          </section>
        </div>
      </main>

      {viewer && viewerOutput && (
        <div className="fixed inset-0 z-[100] bg-black/80 p-4 md:p-8 flex items-center justify-center">
          <div className="w-full h-full max-w-[1800px] max-h-[1100px] rounded-lg border border-[#5f6368] bg-[#202124] overflow-hidden flex flex-col shadow-2xl">
            <div className="h-12 shrink-0 border-b border-[#3c4043] bg-[#292a2d] px-3 flex items-center gap-3">
              <Eye size={15} className="text-[#8ab4f8]" />
              <div className="min-w-0">
                <div className="truncate text-xs font-black">
                  {viewer.service.name} · {viewer.outputName}
                </div>
                <div className="text-[9px] text-[#9aa0a6]">
                  {viewerOutput.type}
                  {viewerOutput.shape ? ` · ${viewerOutput.shape.join('×')}` : ''}
                  {` · service v${viewer.run.service_version}`}
                </div>
              </div>
              <button
                onClick={closeViewer}
                className="ml-auto rounded p-1.5 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"
                title="Close viewer"
              >
                <X size={16} />
              </button>
            </div>
            <div className="flex-1 min-h-0 bg-[#171717]">
              <ZoomPanImageView
                src={viewer.url}
                alt={`${viewer.service.name} ${viewer.outputName}`}
                resetKey={`${viewer.run.run_id}:${viewer.outputName}`}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
