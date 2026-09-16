import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Boxes,
  BrainCircuit,
  FlaskConical,
  Image as ImageIcon,
  Loader2,
  PackageCheck,
  Play,
  RefreshCw,
  Scale,
  ScanLine,
  Upload,
} from 'lucide-react';
import { LabServiceAPI, type LabServiceDefinition, type LabServiceRunManifest } from '../api/labServiceApi';
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
  { id: 'sampling', title: 'Sampling / Geometry LAB', subtitle: 'Contours, curves, profiles and spatial sampling.', icon: ScanLine, enabled: false },
  { id: 'representation', title: 'Representation LAB', subtitle: 'Vectors, matrices, tensors and feature representations.', icon: Boxes, enabled: false },
  { id: 'ai', title: 'AI LAB', subtitle: 'Model architecture, inference and training experiments.', icon: BrainCircuit, enabled: false },
  { id: 'rule', title: 'Comparison / Rule LAB', subtitle: 'Measurements, comparison, specs and decision primitives.', icon: Scale, enabled: false },
];

export const LabView = () => {
  const navigate = useNavigate();
  const [services, setServices] = useState<LabServiceDefinition[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState<string | null>(null);
  const [runnerFile, setRunnerFile] = useState<File | null>(null);
  const [runManifest, setRunManifest] = useState<LabServiceRunManifest | null>(null);
  const [outputUrls, setOutputUrls] = useState<Record<string, string>>({});
  const [loadingServices, setLoadingServices] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef<HTMLInputElement | null>(null);
  const outputUrlsRef = useRef<Record<string, string>>({});

  const selectedService = useMemo(
    () => services.find((service) => service.service_id === selectedServiceId) ?? null,
    [services, selectedServiceId],
  );

  const clearOutputUrls = () => {
    Object.values(outputUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
    outputUrlsRef.current = {};
    setOutputUrls({});
  };

  const loadServices = async () => {
    try {
      setLoadingServices(true);
      setError('');
      const result = await LabServiceAPI.list();
      setServices(result);
      setSelectedServiceId((current) => {
        if (current && result.some((item) => item.service_id === current)) return current;
        return result[0]?.service_id ?? null;
      });
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

  useEffect(() => {
    loadServices();
    return () => {
      Object.values(outputUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  useEffect(() => {
    setRunnerFile(null);
    setRunManifest(null);
    clearOutputUrls();
  }, [selectedServiceId]);

  const runSelectedService = async () => {
    if (!selectedService || !runnerFile) return;

    try {
      setRunning(true);
      setError('');
      clearOutputUrls();
      const manifest = await LabServiceAPI.runImage(
        selectedService.service_id,
        runnerFile,
        selectedService.version,
      );
      setRunManifest(manifest);

      const entries = await Promise.all(
        Object.keys(manifest.outputs).map(async (outputName) => {
          const blob = await LabServiceAPI.outputPreview(
            manifest.run_id,
            outputName,
            1400,
            90,
          );
          return [outputName, URL.createObjectURL(blob)] as const;
        }),
      );

      const next = Object.fromEntries(entries);
      outputUrlsRef.current = next;
      setOutputUrls(next);
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Lab Service manual run failed',
      );
    } finally {
      setRunning(false);
    }
  };

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
                LABs are editors. A deployed Lab Service is an immutable, callable processing snapshot with a stable input/output contract.
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
                    <div className="mt-5 flex items-center gap-2">
                      <h2 className="font-black text-base text-[#e8eaed]">{lab.title}</h2>
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
                  Click a service to inspect its contract and run the same callable runtime manually.
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
                No Lab Service has been deployed yet. Open Image Processing LAB, enable Lab Service mode, expose checkpoints, then deploy a snapshot.
              </div>
            ) : (
              <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-4 min-h-[480px]">
                <div className="space-y-2">
                  {services.map((service) => (
                    <button
                      key={service.service_id}
                      onClick={() => setSelectedServiceId(service.service_id)}
                      className={`w-full rounded-lg border p-4 text-left transition-colors ${
                        selectedServiceId === service.service_id
                          ? 'border-[#8ab4f8] bg-[#26364d]'
                          : 'border-[#3c4043] bg-[#292a2d] hover:border-[#5f6368] hover:bg-[#35363a]'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm font-black text-[#e8eaed]">{service.name}</span>
                        <span className="rounded bg-[#202124] px-2 py-0.5 text-[9px] font-bold text-[#81c995]">v{service.version}</span>
                      </div>
                      <div className="mt-1 text-[10px] text-[#9aa0a6]">{service.lab_type}</div>
                      <div className="mt-3 text-[9px] font-black tracking-wider text-[#80868b]">IN</div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {Object.entries(service.inputs).map(([name, port]) => (
                          <span key={name} className="rounded bg-[#202124] px-1.5 py-0.5 text-[9px] text-[#bdc1c6]">
                            {name}:{port.type}
                          </span>
                        ))}
                      </div>
                      <div className="mt-3 text-[9px] font-black tracking-wider text-[#80868b]">OUT</div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {Object.entries(service.outputs).map(([name, port]) => (
                          <span key={name} className="rounded bg-[#202124] px-1.5 py-0.5 text-[9px] text-[#8ab4f8]">
                            {name}:{port.type}
                          </span>
                        ))}
                      </div>
                    </button>
                  ))}
                </div>

                {selectedService && (
                  <div className="rounded-lg border border-[#3c4043] bg-[#292a2d] overflow-hidden flex flex-col min-w-0">
                    <div className="border-b border-[#3c4043] px-4 py-3 flex items-center gap-3">
                      <PackageCheck size={17} className="text-[#8ab4f8]" />
                      <div className="min-w-0">
                        <div className="truncate text-sm font-black">{selectedService.name}</div>
                        <div className="text-[10px] text-[#9aa0a6]">
                          Manual Runner · {selectedService.service_id}@v{selectedService.version}
                        </div>
                      </div>
                      <div className="ml-auto text-[10px] text-[#80868b]">
                        This UI calls the same LabServiceRuntime.run() contract future modules will use.
                      </div>
                    </div>

                    <div className="border-b border-[#3c4043] bg-[#242528] px-4 py-3 flex items-center gap-2">
                      <input
                        ref={fileRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(event: any) => {
                          const file = event.target.files?.[0] ?? null;
                          setRunnerFile(file);
                          setRunManifest(null);
                          clearOutputUrls();
                          event.currentTarget.value = '';
                        }}
                      />
                      <button
                        onClick={() => fileRef.current?.click()}
                        className="flex items-center gap-1.5 rounded border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-bold text-[#e8eaed] hover:bg-[#3c4043]"
                      >
                        <Upload size={13} className="text-[#8ab4f8]" />
                        Input Image
                      </button>
                      <span className="min-w-0 flex-1 truncate text-[10px] text-[#9aa0a6]">
                        {runnerFile?.name ?? 'No input selected'}
                      </span>
                      <button
                        onClick={runSelectedService}
                        disabled={!runnerFile || running}
                        className="flex items-center gap-1.5 rounded border border-[#8ab4f8] bg-[#174ea6] px-3 py-1.5 text-xs font-black text-[#d2e3fc] hover:bg-[#185abc] disabled:opacity-40"
                      >
                        {running ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
                        Run Service
                      </button>
                      {runManifest && (
                        <span className="rounded bg-[#202124] px-2 py-1 text-[10px] font-mono text-[#81c995]">
                          {runManifest.total_ms.toFixed(2)} ms
                        </span>
                      )}
                    </div>

                    <div className="flex-1 min-h-[360px] overflow-auto p-2 bg-[#171717]">
                      {!runManifest ? (
                        <div className="h-full min-h-[340px] flex items-center justify-center text-center text-sm text-[#80868b]">
                          Select an input image and run this deployed service snapshot.
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 2xl:grid-cols-2 gap-2">
                          {Object.entries(runManifest.outputs).map(([outputName, output]) => (
                            <div key={outputName} className="min-h-[300px] rounded border border-[#3c4043] overflow-hidden bg-[#202124] flex flex-col">
                              <div className="h-9 shrink-0 border-b border-[#3c4043] bg-[#292a2d] px-2 flex items-center gap-2">
                                <span className="text-xs font-bold text-[#e8eaed]">{outputName}</span>
                                <span className="rounded bg-[#202124] px-1.5 py-0.5 text-[9px] text-[#8ab4f8]">{output.type}</span>
                                {output.shape && (
                                  <span className="ml-auto font-mono text-[9px] text-[#80868b]">{output.shape.join('×')}</span>
                                )}
                              </div>
                              <div className="flex-1 min-h-[260px]">
                                {outputUrls[outputName] ? (
                                  <ZoomPanImageView
                                    src={outputUrls[outputName]}
                                    alt={outputName}
                                    resetKey={`${runManifest.run_id}:${outputName}`}
                                  />
                                ) : (
                                  <div className="h-full flex items-center justify-center text-xs text-[#80868b]">Loading preview...</div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
};
