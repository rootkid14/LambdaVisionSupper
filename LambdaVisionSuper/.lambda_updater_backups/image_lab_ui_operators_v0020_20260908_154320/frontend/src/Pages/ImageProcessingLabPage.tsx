import { useNavigate } from 'react-router-dom';
import { ArrowLeft, FlaskConical, Wifi, AlertTriangle, Gauge } from 'lucide-react';
import { OperatorLibrary } from '../components/VisionLabs/ImageProcessing/OperatorLibrary';
import { ProcessingStack } from '../components/VisionLabs/ImageProcessing/ProcessingStack';
import { ImageWorkbench } from '../components/VisionLabs/ImageProcessing/ImageWorkbench';
import { useImageLabController } from '../components/VisionLabs/ImageProcessing/useImageLabController';

export const ImageProcessingLabPage = () => {
  const navigate = useNavigate();
  const lab = useImageLabController();

  const totalTiming = Object.values(lab.timings).reduce((sum, value) => sum + Number(value || 0), 0);

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#050812] text-slate-100 flex flex-col">
      <header className="h-14 shrink-0 border-b border-slate-800 bg-slate-950/95 flex items-center px-3 gap-3">
        <button onClick={() => navigate('/labs')} className="w-8 h-8 rounded-lg border border-slate-700 bg-slate-900 flex items-center justify-center text-slate-400 hover:text-white hover:border-cyan-500/50">
          <ArrowLeft size={16} />
        </button>
        <div className="w-px h-7 bg-slate-800" />
        <FlaskConical size={18} className="text-cyan-400" />
        <div className="min-w-0">
          <div className="text-xs font-black tracking-[0.16em]">IMAGE PROCESSING LAB</div>
          <div className="text-[9px] text-slate-500">Interactive raster processing workbench</div>
        </div>

        <div className="ml-auto flex items-center gap-2 text-[10px] text-slate-500">
          <span className="flex items-center gap-1 rounded-md border border-slate-800 bg-slate-900 px-2 py-1">
            <Wifi size={11} className={lab.sessionId ? 'text-emerald-400' : 'text-amber-400'} />
            {lab.status}
          </span>
          <span className="flex items-center gap-1 rounded-md border border-slate-800 bg-slate-900 px-2 py-1">
            <Gauge size={11} className="text-cyan-400" />
            {totalTiming.toFixed(2)} ms
          </span>
        </div>
      </header>

      {lab.error && (
        <div className="shrink-0 border-b border-rose-500/30 bg-rose-500/10 px-4 py-2 flex items-center gap-2 text-xs text-rose-300">
          <AlertTriangle size={14} />
          <span className="flex-1">{lab.error}</span>
          <button onClick={() => lab.setError('')} className="text-[10px] font-bold hover:text-white">DISMISS</button>
        </div>
      )}

      <div className="flex-1 min-h-0 flex overflow-hidden">
        <OperatorLibrary operators={lab.operators} onAdd={lab.addOperator} canAppend={lab.canAppend} />
        <ImageWorkbench
          sourceLoaded={lab.sourceLoaded}
          imageName={lab.imageName}
          viewerCount={lab.viewerCount}
          viewerKeys={lab.viewerKeys}
          sources={lab.availableSources}
          previewUrls={lab.previewUrls}
          busy={lab.busy}
          onUpload={lab.uploadImage}
          onViewerCountChange={lab.setViewerCount}
          onViewerSourceChange={lab.setViewerSource}
          onRun={lab.runNow}
        />
        <ProcessingStack
          stack={lab.stack}
          manifests={lab.manifests}
          onToggleExpanded={lab.toggleExpanded}
          onDelete={lab.deleteOperator}
          onToggleEnabled={lab.toggleEnabled}
          onReset={lab.resetOperator}
          onReorder={lab.reorderOperator}
          onParameterChange={lab.changeParameter}
        />
      </div>
    </div>
  );
};
