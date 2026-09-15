import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Image as ImageIcon,
  ScanLine,
  Boxes,
  BrainCircuit,
  Scale,
  FlaskConical,
} from 'lucide-react';

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
          <div className="text-[10px] text-[#9aa0a6]">Experimental workbenches for Lambda Vision</div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-8 py-10 bg-[#202124]">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="text-xs font-black tracking-[0.24em] text-[#8ab4f8] uppercase">LAB Launcher</div>
            <h1 className="mt-2 text-3xl font-black text-[#e8eaed]">Choose an experimental environment</h1>
            <p className="mt-2 max-w-2xl text-sm text-[#9aa0a6]">
              Each LAB is optimized around its native data and workflow. Pipelines can later be reused inside Vision Stations.
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
                  className={`group min-h-[190px] rounded-lg border p-5 text-left transition-all ${
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
        </div>
      </main>
    </div>
  );
};
