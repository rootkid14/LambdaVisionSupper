import { Server, Trash2, Video, Workflow, Activity } from 'lucide-react';
import { WorkerInfoCard } from "../../Stores/FleetDashboardStores";
import { MiniProgressBar } from '../../Commons/MiniProgressBar';

interface MasterGatewayCardProps {
  masterData: WorkerInfoCard | null;
  onManage: () => void;
}

export const MasterGatewayCard = ({ masterData, onManage }: MasterGatewayCardProps) => {
  if (!masterData) return null;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3 pl-1 border-b border-[#3c4043] pb-2">
        <h2 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest">Gateway / Master Node</h2>
      </div>
      
      <div className="bg-[#28292c] border-2 border-[#3c4043] rounded-xl p-0 shadow-lg flex flex-col overflow-hidden relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-[#8ab4f8]"></div>
        <div className="p-5 flex flex-col md:flex-row items-center justify-between gap-6 ml-2">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-[#8ab4f8]/10 rounded-lg border border-[#8ab4f8]/20"><Server size={28} className="text-[#8ab4f8]" /></div>
            <div>
              <div className="text-lg font-bold text-[#e8eaed] tracking-wider">MASTER GATEWAY</div>
              <div className="text-xs text-[#8ab4f8] font-mono bg-[#171717] px-2 py-0.5 rounded border border-[#3c4043] mt-1.5 inline-block">{masterData.host}</div>
            </div>
          </div>
          <div className="flex-1 max-w-md flex gap-6 w-full px-6 md:border-l border-[#3c4043]">
            <MiniProgressBar label="CPU Core" percent={masterData.hardware?.cpu_percent ?? 0} colorClass="bg-[#8ab4f8]" />
            <MiniProgressBar label="RAM System" percent={masterData.hardware?.ram_percent ?? 0} colorClass="bg-[#8ab4f8]" />
          </div>
        </div>
        
        <button 
          onClick={onManage}
          className="w-full flex items-center justify-center gap-2 p-3 bg-[#202124] hover:bg-[#8ab4f8]/10 text-[#9aa0a6] hover:text-[#8ab4f8] transition-colors border-t border-[#3c4043] cursor-pointer group"
        >
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] group-hover:tracking-[0.3em] transition-all">Manage Master Node</span>
        </button>
      </div>
    </div>
  );
};

interface WorkerCardProps {
  worker: WorkerInfoCard;
  onRemove: (id: string) => void;
  onManage: () => void;
}

export const WorkerCard = ({ worker, onRemove, onManage }: WorkerCardProps) => {
  const isOnline = worker.alive;
  
  return (
    <div className={`flex flex-col bg-[#28292c] rounded-xl border-2 transition-all duration-200 hover:-translate-y-1 overflow-hidden relative group ${isOnline ? 'border-[#3c4043] hover:border-[#8ab4f8]/50 hover:shadow-[0_10px_30px_rgba(138,180,248,0.1)]' : 'border-[#f28b82]/30 bg-[#f28b82]/5'}`}>
      <button onClick={() => onRemove(worker.server_id)} className="absolute top-4 right-4 text-[#5f6368] hover:text-[#f28b82] opacity-0 group-hover:opacity-100 transition-opacity bg-[#202124] hover:bg-[#f28b82]/10 p-1.5 rounded-md z-10 border border-[#3c4043] hover:border-[#f28b82]/30">
        <Trash2 size={16} />
      </button>
      
      <div className="p-5 border-b border-[#3c4043] flex justify-between items-start bg-[#202124]">
        <div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full shadow-[0_0_8px_currentColor] ${isOnline ? 'bg-[#81c995] text-[#81c995]' : 'bg-[#f28b82] text-[#f28b82]'}`}></div>
            <h3 className="font-bold text-[#e8eaed] text-base pr-8 tracking-wider">{worker.server_id}</h3>
          </div>
          <div className="text-[11px] text-[#9aa0a6] font-mono mt-2 bg-[#171717] px-2 py-0.5 rounded border border-[#3c4043] inline-block">{worker.host}</div>
        </div>
        {isOnline ? (
          <span className="text-[10px] font-bold bg-[#8ab4f8]/10 text-[#8ab4f8] px-2 py-1 rounded border border-[#8ab4f8]/20 flex items-center gap-1">
            <Activity size={12} /> {worker.ping}ms
          </span>
        ) : (
          <span className="text-[10px] font-bold bg-[#f28b82]/10 text-[#f28b82] px-2 py-1 rounded border border-[#f28b82]/20 uppercase">
            Offline
          </span>
        )}
      </div>
      
      <div className="p-5 flex flex-col gap-5 flex-1">
        {isOnline ? (
          <>
            <div className="grid grid-cols-2 gap-6">
              <MiniProgressBar label="CPU" percent={worker.hardware?.cpu_percent ?? 0} colorClass={(worker.hardware?.cpu_percent ?? 0) > 80 ? 'bg-[#fcd663]' : 'bg-[#8ab4f8]'} />
              <MiniProgressBar label="RAM" percent={worker.hardware?.ram_percent ?? 0} colorClass="bg-[#8ab4f8]" />
            </div>
            <div className="flex gap-4 text-[11px] text-[#9aa0a6] font-bold uppercase mt-2 bg-[#171717] rounded-lg p-3 border border-[#3c4043]">
              <div className="flex items-center gap-2 w-1/2"><Video size={14} className="text-[#fcd663]"/> {worker.device_list?.length ?? 0} Cameras</div>
              <div className="w-px h-full bg-[#3c4043]"></div>
              <div className="flex items-center gap-2"><Workflow size={14} className="text-[#c58af9]"/> {worker.logic_obj_count ?? 0} Graphs</div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-[#5f6368] text-sm py-4 italic">
            <Server size={32} className="opacity-20 mb-2" />
            <span>Connection lost to worker...</span>
          </div>
        )}
      </div>
      
      <button 
        disabled={!isOnline} 
        onClick={onManage} 
        className="w-full flex items-center justify-center gap-2 p-3 bg-[#202124] hover:bg-[#8ab4f8]/10 text-[#5f6368] hover:text-[#8ab4f8] transition-colors border-t border-[#3c4043] disabled:opacity-50 group"
      >
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] group-hover:tracking-[0.3em] transition-all">Manage Config</span>
      </button>
    </div>
  );
};