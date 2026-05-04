import { useEffect } from 'react';
import { Network, Plus, Home, Loader2, Activity, RefreshCcw, PlugZap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { useFleetStore } from '../Stores/FleetDashboardStores';
import { FleetAPI } from '../api/fleetApi';
import { MasterGatewayCard, WorkerCard } from '../components/Fleet/FleetCards';
import { AddWorkerModal, SwitchMasterModal, ErrorModal } from '../components/Fleet/FleetModals';
import { PoolsDrawer } from '../components/Fleet/PoolsDrawer';

export const FleetDashboard = () => {
  const navigate = useNavigate();

  // === ZUSTAND STORE HOOKS ===
  const gateway = useFleetStore(state => state.gateway);
  const masterWorker = useFleetStore(state => state.master_worker);
  const fleetWorkers = useFleetStore(state => state.fleet_worker);
  
  const isLoading = useFleetStore(state => state.isLoading);
  const setGatewayandLoadFleet = useFleetStore(state => state.setGatewayandLoadFleet);
  
  const isSwitchMasterOpen = useFleetStore(state => state.isSwitchMasterOpen);
  const openSwitchMaster = useFleetStore(state => state.openSwitchMaster);
  const closeSwitchMaster = useFleetStore(state => state.closeSwitchMaster);
  
  const isAddNewServerUIOpen = useFleetStore(state => state.isAddNewServerUIOpen);
  const isErrorModalOpen = useFleetStore(state => state.isErrorModalOpen);
  const errorMessage = useFleetStore(state => state.errorMessage);
  
  const openPoolsDrawer = useFleetStore(state => state.openPoolsDrawer);
  const silentRefreshFleet = useFleetStore(state => state.silentRefreshFleet);

  useEffect(() => {
    if (gateway) {
      setGatewayandLoadFleet(gateway);
    } else {
      openSwitchMaster();
    }
  }, [gateway, setGatewayandLoadFleet, openSwitchMaster]);

  const handleAddWorker = async (id: string, host: string) => {
    try {
      const resp = await FleetAPI.master_addLocalWorker({ server_id: id, host });
      if (resp.success) {
        useFleetStore.setState({ isAddNewServerUIOpen: false });
        if(gateway) setGatewayandLoadFleet(gateway);
      } else {
        useFleetStore.setState({ errorMessage: resp.message || "Add failed", isErrorModalOpen: true });
      }
    } catch (err: any) {
      useFleetStore.setState({ errorMessage: err.message, isErrorModalOpen: true });
    }
  };

  useEffect(() => {
    if(!gateway || isSwitchMasterOpen) return;
    const intervalId = setInterval(() => { silentRefreshFleet(); }, 3000)
    return () => clearInterval(intervalId);
  }, [gateway, isSwitchMasterOpen, silentRefreshFleet])

  const handleRemoveWorker = async (id: string) => {
    if(!window.confirm(`Gỡ Worker [${id}] khỏi Bus hệ thống?`)) return;
    try {
      await FleetAPI.master_removeLocalServer(id);
      if(gateway) setGatewayandLoadFleet(gateway);
    } catch (err: any) {
      useFleetStore.setState({ errorMessage: err.message, isErrorModalOpen: true });
    }
  };

  return (
    <div className="min-h-screen bg-[#202124] p-6 font-sans text-[#e8eaed] overflow-y-auto selection:bg-[#8ab4f8]/30">
      
      {/* HEADER PAGE */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <button 
            onClick={() => navigate('/')} 
            className="group flex items-center gap-2 px-4 py-2.5 bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 text-[#8ab4f8] rounded-xl transition-all border border-[#8ab4f8]/20 shadow-[0_0_15px_rgba(138,180,248,0.1)]"
          >
            <Home size={22} className="group-hover:-translate-y-0.5 transition-transform" />
            <span className="font-bold tracking-wide uppercase text-sm">Home</span>
          </button>
          
          <div className="h-8 w-px bg-[#3c4043]"></div>
          
          <div>
            <h1 className="text-2xl font-bold text-[#e8eaed] tracking-wider flex items-center gap-2">
              <Network size={24} className="text-[#8ab4f8]" /> Fleet Command Center
            </h1>
            <p className="text-[#9aa0a6] text-sm mt-1">Command Center</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* SECONDARY ACTION: REFRESH */}
          <button 
            onClick={() => setGatewayandLoadFleet(gateway!)} 
            className="group flex items-center gap-2 px-4 py-2 bg-[#28292c] hover:bg-[#303134] text-[#9aa0a6] hover:text-[#e8eaed] rounded-lg border border-[#3c4043] hover:border-[#5f6368] transition-all text-xs font-bold uppercase tracking-wider shadow-sm"
          >
            <RefreshCcw size={14} className="group-hover:rotate-180 transition-transform duration-500" /> 
            Refresh
          </button>

          {/* NEW: SWITCH MASTER ACTION */}
          <button 
            onClick={openSwitchMaster} 
            className="flex items-center gap-2 px-4 py-2 bg-[#202124] hover:bg-[#28292c] text-[#8ab4f8] rounded-lg border border-[#8ab4f8]/30 hover:border-[#8ab4f8] transition-all text-xs font-bold uppercase tracking-wider shadow-sm hover:shadow-[0_0_15px_rgba(138,180,248,0.15)]"
          >
            <PlugZap size={14} /> 
            Switch Master
          </button>

          {/* PRIMARY ACTION: ADD WORKER (MỚI: Có Gradient và Shadow mượt hơn) */}
          <button 
            onClick={() => useFleetStore.setState({ isAddNewServerUIOpen: true })} 
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#8ab4f8] to-[#669df6] hover:from-[#aecbfa] hover:to-[#8ab4f8] text-[#171717] rounded-lg border border-[#aecbfa]/50 transition-all shadow-[0_0_15px_rgba(138,180,248,0.3)] hover:shadow-[0_0_25px_rgba(138,180,248,0.5)] text-xs font-bold uppercase tracking-wider hover:-translate-y-0.5"
          >
            <Plus size={16} className="stroke-[2.5]" /> 
            Add Worker
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-[#8ab4f8]">
           <Loader2 size={40} className="animate-spin" />
        </div>
      ) : (
        <>
          {/* TẦNG 1: MASTER SERVER */}
          <MasterGatewayCard 
            masterData={masterWorker} 
            onManage={() => openPoolsDrawer('master_gateway')} 
          />

          {/* TẦNG 2: WORKER FLEET */}
          <div className="mt-8">
            <h2 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest mb-4 pl-1 flex items-center justify-between border-b border-[#3c4043] pb-2">
              <span>AI Worker Nodes ({fleetWorkers.length})</span>
              <span className="flex items-center gap-1.5 text-[#81c995] bg-[#81c995]/10 px-2 py-1 rounded border border-[#81c995]/20"><Activity size={12}/> Live Syncing</span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pt-2">
              {fleetWorkers.map((worker) => (
                <WorkerCard 
                  key={worker.server_id} 
                  worker={worker} 
                  onRemove={handleRemoveWorker} 
                  onManage={() => openPoolsDrawer(worker.server_id)} 
                />
              ))}
            </div>
          </div>
        </>
      )}

      {/* MODALS & DRAWER */}
      {isAddNewServerUIOpen && <AddWorkerModal onClose={() => useFleetStore.setState({ isAddNewServerUIOpen: false })} onSubmit={handleAddWorker} />}
      {isSwitchMasterOpen && (
          <SwitchMasterModal 
            currentHost={gateway} 
            onClose={() => { 
                if (!gateway) navigate('/'); // Chưa có host thì back về trang chủ (Launcher)
                else closeSwitchMaster();    // Có host rồi thì chỉ đóng modal
            }} 
            onSwitch={(host) => { setGatewayandLoadFleet(host); closeSwitchMaster(); }} 
          />
      )}
      {isErrorModalOpen && <ErrorModal message={errorMessage} onClose={() => useFleetStore.setState({ isErrorModalOpen: false, errorMessage: '' })} />}
      <PoolsDrawer />
    </div>
  );
};