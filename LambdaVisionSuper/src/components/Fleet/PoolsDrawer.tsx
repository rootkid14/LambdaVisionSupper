import { useEffect, useState } from 'react';
import { X, Server, Video, Database, Loader2, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { ServersTab, DevicesTab, ResourcesTab } from './PoolsDrawerTabs';
import { useFlowStore } from '../../Stores/FlowStore';

export const PoolsDrawer = () => {
  const navigate = useNavigate();
  
  const isDrawerOpen = useFleetStore(state => state.isPoolsDrawerOpen);
  const closeDrawer = useFleetStore(state => state.closePoolsDrawer);
  const selectedWorker = useFleetStore(state => state.selected_worker);
  const masterWorker = useFleetStore(state => state.master_worker);
  const fleetWorkers = useFleetStore(state => state.fleet_worker);

  const setWorkerEnvironment = useFlowStore(state => state.setWorkerEnvironment);
  const addNewServer = useFleetStore(state => state.addNewServer);
  const removeServer = useFleetStore(state => state.removeServer);
  const addDevice = useFleetStore(state => state.attachNewHttpDevice);
  const removeDevice = useFleetStore(state => state.removeHttpDevice);
  const uploadResource = useFleetStore(state => state.uploadResource);
  const downloadResource = useFleetStore(state => state.downloadResource);
  const removeResource = useFleetStore(state => state.removeResource);
  const deployGraph = useFleetStore(state => state.deployGraph);
  const undeployLogic = useFleetStore(state => state.undeployLogic);
  
  const isUploading = useFleetStore(state => state.isUploadingResource);
  const uploadProgress = useFleetStore(state => state.uploadProgress);

  const [showOverlay, setShowOverlay] = useState(false);
  const [slideIn, setSlideIn] = useState(false);
  const [activeTab, setActiveTab] = useState<'servers' | 'devices' | 'logic'>('servers');

  useEffect(() => {
    if (isDrawerOpen) {
      setShowOverlay(true); setTimeout(() => setSlideIn(true), 10); 
    } else {
      setSlideIn(false); setTimeout(() => setShowOverlay(false), 300);
    }
  }, [isDrawerOpen]);

  if (!showOverlay || !selectedWorker) return null;

  const isMasterNode = selectedWorker.selected_worker_id === 'master_gateway';
  const liveWorkerData = isMasterNode ? masterWorker : fleetWorkers.find(w => w.server_id === selectedWorker.selected_worker_id);

  const hardwareData = liveWorkerData?.hardware;
  const currentPing = liveWorkerData?.ping ?? 0;
  const isOnline = liveWorkerData?.alive ?? false;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end font-sans">
      {/* Backdrop */}
      <div className={`absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${slideIn ? 'opacity-100' : 'opacity-0'}`} onClick={closeDrawer}></div>

      {/* Drawer Panel */}
      <div className={`relative w-full max-w-[500px] bg-[#28292c] border-l border-[#3c4043] h-full shadow-[-20px_0_60px_rgba(0,0,0,0.5)] flex flex-col transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${slideIn ? 'translate-x-0' : 'translate-x-full'}`}>
        
        {isUploading && (
          <div className="absolute inset-0 bg-[#202124]/80 z-50 flex flex-col items-center justify-center backdrop-blur-md">
            <Loader2 className="animate-spin text-[#8ab4f8] mb-4" size={40} />
            <div className="text-[#e8eaed] font-bold text-lg">{uploadProgress}%</div>
            <div className="text-[#9aa0a6] text-xs mt-2 uppercase tracking-widest">Uploading Resource</div>
          </div>
        )}

        <div className="flex flex-col bg-[#303134] border-b border-[#3c4043] pb-4 z-10 shrink-0">
          <div className="flex items-center justify-between p-5 pb-4">
            <div>
              <h2 className="text-lg font-bold text-[#e8eaed] flex items-center gap-3 tracking-wide">
                Worker Configuration
                {isOnline ? (
                  <span className="text-[10px] bg-[#81c995]/10 text-[#81c995] px-2 py-1 rounded border border-[#81c995]/20 uppercase flex items-center gap-1 font-bold tracking-wider">
                    <Activity size={12} /> {isMasterNode ? '0ms (Local)' : `${currentPing}ms`}
                  </span>
                ) : (
                  <span className="text-[10px] bg-[#f28b82]/10 text-[#f28b82] px-2 py-1 rounded border border-[#f28b82]/20 uppercase tracking-wider font-bold">
                    Offline
                  </span>
                )}
              </h2>
              <p className="text-xs text-[#9aa0a6] mt-2 flex items-center gap-2">
                Target Node: 
                <span className="text-[#8ab4f8] font-mono bg-[#171717] px-2 py-0.5 rounded border border-[#3c4043]">
                  {selectedWorker.selected_worker_id}
                </span>
              </p>
            </div>
            <button onClick={closeDrawer} className="p-2 text-[#9aa0a6] hover:text-[#f28b82] hover:bg-[#3c4043] rounded-lg transition-colors border border-transparent hover:border-[#f28b82]/30"><X size={20} /></button>
          </div>
          
          <div className="flex mx-5 p-1 bg-[#171717] rounded-lg border border-[#3c4043]">
            <button onClick={() => setActiveTab('servers')} className={`flex-1 py-2 text-[10px] font-bold uppercase tracking-widest rounded flex items-center justify-center gap-2 transition-all ${activeTab === 'servers' ? 'bg-[#3c4043] text-[#8ab4f8]' : 'text-[#5f6368] hover:text-[#9aa0a6] hover:bg-[#202124]'}`}><Server size={14} /> System Bus</button>
            <button onClick={() => setActiveTab('devices')} className={`flex-1 py-2 text-[10px] font-bold uppercase tracking-widest rounded flex items-center justify-center gap-2 transition-all ${activeTab === 'devices' ? 'bg-[#3c4043] text-[#fcd663]' : 'text-[#5f6368] hover:text-[#9aa0a6] hover:bg-[#202124]'}`}><Video size={14} /> Device Bus</button>
            <button onClick={() => setActiveTab('logic')} className={`flex-1 py-2 text-[10px] font-bold uppercase tracking-widest rounded flex items-center justify-center gap-2 transition-all ${activeTab === 'logic' ? 'bg-[#3c4043] text-[#c58af9]' : 'text-[#5f6368] hover:text-[#9aa0a6] hover:bg-[#202124]'}`}><Database size={14} /> Logic & Resouce</button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 custom-scrollbar bg-[#202124]">
          {activeTab === 'servers' && <ServersTab servers={selectedWorker.localSevsInfo} onAdd={addNewServer} onRemove={removeServer} />}
          {activeTab === 'devices' && <DevicesTab devices={selectedWorker.DevsInfo} onAdd={addDevice} onRemove={(id) => removeDevice(id, "")} />}
          {activeTab === 'logic' && (
            <ResourcesTab 
              hardware={hardwareData} 
              resourceInfo={selectedWorker.ResourceInfo} 
              onUpload={uploadResource} 
              onDownload={downloadResource} 
              onRemove={removeResource}
              onDeploy={deployGraph}
              onToggleRam={useFleetStore.getState().toggleFileRamStatus}
              onUndeploy={undeployLogic}
              onNavigateLogic={() => { 
                setWorkerEnvironment(selectedWorker); 
                closeDrawer(); 
                navigate(`/fleet/${selectedWorker.selected_worker_id}/logic`); 
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};