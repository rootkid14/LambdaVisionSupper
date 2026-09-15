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
    subtitle: 'Raster transforms, filtering, thresholding and morphology.',
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
    <div className="h-screen w-screen overflow-hidden bg-[#050812] text-slate-100 flex flex-col">
      <header className="h-16 shrink-0 border-b border-slate-800 bg-slate-950/90 flex items-center px-4 gap-3">
        <button onClick={() => navigate('/')} className="w-9 h-9 rounded-lg border border-slate-700 bg-slate-900 flex items-center justify-center text-slate-400 hover:text-white hover:border-cyan-500/50">
          <ArrowLeft size={17} />
        </button>
        <div className="w-px h-8 bg-slate-800" />
        <FlaskConical size={20} className="text-fuchsia-400" />
        <div>
          <div className="text-sm font-black tracking-[0.18em]">VISION LABS</div>
          <div className="text-[10px] text-slate-500">Experimental workhorses for Lambda Vision</div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-8 py-10">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="text-xs font-black tracking-[0.28em] text-fuchsia-400 uppercase">LAB Launcher</div>
            <h1 className="mt-2 text-3xl font-black text-white">Choose an experimental environment</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-500">Each LAB is optimized around its native data and workflow. Pipelines can later be reused inside Vision Stations.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {labs.map((lab) => {
              const Icon = lab.icon;
              return (
                <button
                  key={lab.id}
                  disabled={!lab.enabled}
                  onClick={() => lab.enabled && lab.route && navigate(lab.route)}
                  className={`group min-h-[190px] rounded-2xl border p-5 text-left transition-all ${
                    lab.enabled
                      ? 'border-fuchsia-500/30 bg-fuchsia-500/[0.06] hover:-translate-y-1 hover:border-fuchsia-400/60 hover:bg-fuchsia-500/[0.10] hover:shadow-[0_0_40px_rgba(217,70,239,0.12)]'
                      : 'border-slate-800 bg-slate-900/30 opacity-55 cursor-not-allowed'
                  }`}
                >
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${lab.enabled ? 'bg-fuchsia-500/15 text-fuchsia-300' : 'bg-slate-800 text-slate-600'}`}>
                    <Icon size={22} />
                  </div>
                  <div className="mt-5 flex items-center gap-2">
                    <h2 className="font-black text-base text-slate-100">{lab.title}</h2>
                    {!lab.enabled && <span className="rounded bg-slate-800 px-2 py-0.5 text-[9px] font-bold text-slate-500">COMING SOON</span>}
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{lab.subtitle}</p>
                </button>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
};
