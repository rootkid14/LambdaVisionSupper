import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  FlaskConical,
  Gauge,
  Wifi,
} from 'lucide-react';
import { OperatorLibrary } from '../components/VisionLabs/ImageProcessing/OperatorLibrary';
import { ProcessingStack } from '../components/VisionLabs/ImageProcessing/ProcessingStack';
import { ImageWorkbench } from '../components/VisionLabs/ImageProcessing/ImageWorkbench';
import { useImageLabController } from '../components/VisionLabs/ImageProcessing/useImageLabController';

export const ImageProcessingLabPage = () => {
  const navigate = useNavigate();
  const lab = useImageLabController();

  const totalTiming =
    Object.values(
      lab.timings,
    ).reduce(
      (sum, value) => (
        sum
        + Number(value || 0)
      ),
      0,
    );

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#202124] text-[#e8eaed] flex flex-col">
      <header className="h-14 shrink-0 border-b border-[#3c4043] bg-[#292a2d] flex items-center px-3 gap-3 shadow-sm">
        <button
          onClick={() => navigate('/labs')}
          className="w-8 h-8 rounded-md border border-[#5f6368] bg-[#35363a] flex items-center justify-center text-[#bdc1c6] hover:bg-[#3c4043] hover:text-white"
        >
          <ArrowLeft size={16} />
        </button>

        <div className="w-px h-7 bg-[#5f6368]" />

        <FlaskConical
          size={18}
          className="text-[#8ab4f8]"
        />

        <div className="min-w-0">
          <div className="text-xs font-black tracking-[0.14em] text-[#e8eaed]">
            IMAGE PROCESSING LAB
          </div>

          <div className="text-[9px] text-[#9aa0a6]">
            Interactive raster processing workbench
          </div>
        </div>

        <div className="ml-auto flex items-center gap-2 text-[10px] text-[#9aa0a6]">
          <span className="flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124] px-2 py-1">
            <Wifi
              size={11}
              className={
                lab.sessionId
                  ? 'text-[#81c995]'
                  : 'text-[#fdd663]'
              }
            />
            {lab.status}
          </span>

          <span className="flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124] px-2 py-1">
            <Gauge
              size={11}
              className="text-[#8ab4f8]"
            />
            {totalTiming.toFixed(2)} ms
          </span>
        </div>
      </header>

      {
        lab.error
        && (
          <div className="shrink-0 border-b border-[#f28b82]/40 bg-[#5f2120] px-4 py-2 flex items-center gap-2 text-xs text-[#f28b82]">
            <AlertTriangle size={14} />

            <span className="flex-1">
              {lab.error}
            </span>

            <button
              onClick={() => {
                lab.setError('');
              }}
              className="text-[10px] font-bold hover:text-white"
            >
              DISMISS
            </button>
          </div>
        )
      }

      <div className="flex-1 min-h-0 flex overflow-hidden">
        <OperatorLibrary
          operators={lab.operators}
          onAdd={lab.addOperator}
          canAppend={lab.canAppend}
        />

        <ImageWorkbench
          sourceLoaded={lab.sourceLoaded}
          imageName={lab.imageName}
          viewerPanes={lab.viewerPanes}
          sources={lab.availableSources}
          previewUrls={lab.previewUrls}
          busy={lab.busy}
          onUpload={lab.uploadImage}
          onViewerSourceChange={lab.setViewerSource}
          onAddViewer={lab.addViewer}
          onRemoveViewer={lab.removeViewer}
          onSetViewerPreset={lab.setViewerPreset}
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
