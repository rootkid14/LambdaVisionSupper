import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, Search, Trash2, UploadCloud, FolderOpen, 
  Database, Cpu, Blocks, Play, Square, Zap, ZapOff, Activity, HardDrive, Save, ChevronDown, Edit3, Plus, Workflow
} from 'lucide-react';

import { FleetAPI } from '../../api/fleetApi';
import { NodeAPI } from '../../api/nodeApi';
import { useFleetStore } from '../../Stores/FleetDashboardStores'; 
import { useFlowStore } from '../../Stores/FlowStore'; 

interface FileManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'projects' | 'graphs' | 'models' | 'plugins';
  mode?: 'load' | 'save' | 'manage'; 
  onFileSelect?: (filename: string, fileContent?: any) => void;
  onSaveAs?: (filename: string) => void;
}

export function FileManagerModal({ isOpen, onClose, defaultTab = 'projects', onFileSelect, onSaveAs }: FileManagerModalProps) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [searchQuery, setSearchQuery] = useState('');
  const [saveName, setSaveName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const [targetNode, setTargetNode] = useState<string>('master_gateway');
  
  const masterWorker = useFleetStore(state => state.master_worker);
  const fleetWorkers = useFleetStore(state => state.fleet_worker);

  const [localResources, setLocalResources] = useState<any>({ projects: [], graphs: [], files: {}, plugins: [], active_logics: [] });
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) fetchResources();
  }, [isOpen, activeTab, targetNode]); 

  // ==========================================
  // 1. DATA FETCHING 
  // ==========================================
  const fetchResources = async () => {
    setIsLoading(true);
    try {
      let data;
      if (targetNode === 'master_gateway') {
        data = await FleetAPI.getMasterLocalResource();
      } else {
        data = await FleetAPI.proxy_getWorkerLocalResource(targetNode);
      }
      setLocalResources(data);
    } catch (error) {
      console.error(`Error fetching resources from ${targetNode}:`, error);
      setLocalResources({ projects: [], graphs: [], files: {}, plugins: [], active_logics: [] });
    } finally {
      setIsLoading(false);
    }
  };

  const getFileTypeString = (tab: string) => {
      if (tab === 'models') return 'file';
      if (tab === 'graphs') return 'graph';
      if (tab === 'plugins') return 'plugin';
      return 'projects';
  }

  // ==========================================
  // 2. HANDLERS
  // ==========================================

  const handleCreateLogic = async () => {
    const workerEnv: any = {
        selected_worker_id: targetNode,
        localSevsInfo: [],
        DevsInfo: [],
        ResourceInfo: localResources
    };

    useFlowStore.getState().setWorkerEnvironment(workerEnv);
    useFlowStore.getState().loadGraphfromFile({ nodes: [], edges: [] });
    useFlowStore.getState().setEditingRemoteGraphName('');
    await useFlowStore.getState().loadNodeCatalogue();
    onClose();
    navigate(`/fleet/${targetNode}/logic`);
  };

  const handleEditGraph = async (filename: string) => {
    setIsLoading(true);
    try {
        const workerEnv: any = {
            selected_worker_id: targetNode,
            localSevsInfo: [],
            DevsInfo: [],
            ResourceInfo: localResources
        };
        
        useFlowStore.getState().setWorkerEnvironment(workerEnv);
        
        // ĐÃ SỬA LỖI MISMATCH Ở ĐÂY: Dùng 'graph' thay vì 'graphs'
        const content = targetNode === 'master_gateway'
            ? await FleetAPI.master_getFileContent(filename, 'graph')
            : await FleetAPI.proxy_getFileContent(targetNode, filename, 'graph');
        
        await useFlowStore.getState().loadNodeCatalogue();
        useFlowStore.getState().loadGraphfromFile(content);
        useFlowStore.getState().setEditingRemoteGraphName(filename);
        
        onClose();
        navigate(`/fleet/${targetNode}/logic`);
    } catch (err: any) {
        alert("Failed to sync graph data: " + (err.response?.data?.detail || err.message));
    } finally {
        setIsLoading(false);
    }
  };

  const handleDeployGraph = async (filename: string) => {
    setIsLoading(true);
    try {
      if (targetNode === 'master_gateway') {
          await NodeAPI.master_deploy_graph_to_ram(filename.replace('.json', ''));
      } else {
          await NodeAPI.proxy_deploy_graph_to_ram(targetNode, filename.replace('.json', ''));
      }
      await fetchResources();
    } catch (error: any) {
      alert("Deploy failed: " + (error.response?.data?.detail || error.message));
      setIsLoading(false);
    }
  };

  const handleUndeployLogic = async (logicId: string) => {
    setIsLoading(true);
    try {
      if (targetNode === 'master_gateway') {
          await NodeAPI.master_undeploy_graph_from_ram(logicId);
      } else {
          await NodeAPI.proxy_undeploy_graph_from_ram(targetNode, logicId);
      }
      await fetchResources();
    } catch (error: any) {
      alert("Undeploy failed: " + (error.response?.data?.detail || error.message));
      setIsLoading(false);
    }
  };

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setIsLoading(true);
      try {
        let targetType = getFileTypeString(activeTab);
        if (targetNode === 'master_gateway') {
            await FleetAPI.master_uploadFile(e.target.files[0], targetType);
        } else {
            await FleetAPI.proxy_uploadFile(targetNode, e.target.files[0], targetType);
        }
        await fetchResources();
      } catch (error: any) {
        alert(`Upload to ${targetNode} failed: ` + (error.response?.data?.detail || error.message));
      }
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename} from [${targetNode}]?`)) return;
    try {
      const fileType = getFileTypeString(activeTab) as any;
      if (targetNode === 'master_gateway') {
          await FleetAPI.master_removeResource(filename, fileType);
      } else {
          await FleetAPI.proxy_removeResource(targetNode, filename, fileType);
      }
      fetchResources(); 
    } catch (error) {
      console.error("Error deleting file:", error);
    }
  };

  const handleToggleRam = async (filename: string, isCurrentlyInRam: boolean) => {
    setIsLoading(true);
    try {
      if (isCurrentlyInRam) {
          targetNode === 'master_gateway' 
            ? await FleetAPI.master_unloadFileFromRam(filename) 
            : await FleetAPI.proxy_unloadFileFromRam(targetNode, filename);
      } else {
          targetNode === 'master_gateway' 
            ? await FleetAPI.master_loadFileToRam(filename) 
            : await FleetAPI.proxy_loadFileToRam(targetNode, filename);
      }
      await fetchResources();
    } catch (error: any) {
      alert("RAM operation failed: " + (error.response?.data?.detail || error.message));
      setIsLoading(false);
    }
  };

  const handleLoadProject = async (filename: string) => {
    if (onFileSelect && activeTab === 'projects') {
      setIsLoading(true);
      try {
        const data = targetNode === 'master_gateway'
            ? await FleetAPI.master_getFileContent(filename, 'projects')
            : await FleetAPI.proxy_getFileContent(targetNode, filename, 'projects');
        onFileSelect(filename, data);
      } catch (error) {
        alert(`Cannot read Project file from ${targetNode}!`);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const formatBytes = (bytes: number) => bytes > 1048576 ? (bytes / 1048576).toFixed(2) + ' MB' : (bytes / 1024).toFixed(2) + ' KB';

  if (!isOpen) return null;

  // ==========================================
  // 3. RENDER DATA
  // ==========================================
  let items: any[] = [];
  if (activeTab === 'projects') items = localResources.projects?.map((name: string) => ({ id: name, name })) || [];
  if (activeTab === 'graphs') items = localResources.graphs || [];
  if (activeTab === 'models') items = Object.entries(localResources.files || {}).map(([id, info]: any) => ({ id, name: id, ...info }));
  if (activeTab === 'plugins') items = localResources.plugins || [];

  const filteredItems = items.filter((item: any) => item.name.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-6 font-sans">
      <input type="file" ref={fileInputRef} onChange={handleUploadFile} className="hidden" />
      
      <div className="bg-[#1e1e1e] w-full max-w-6xl h-[85vh] rounded-2xl shadow-2xl border border-[#3c4043] flex overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* SIDEBAR */}
        <div className="w-64 bg-[#252526] border-r border-[#3c4043] flex flex-col shrink-0">
          <div className="p-5 border-b border-[#3c4043] flex flex-col gap-3 bg-[#202124]">
            <h2 className="text-[#e8eaed] font-extrabold text-sm tracking-widest flex items-center gap-2">
              <Database size={18} className="text-[#8ab4f8]" /> ASSET MANAGER
            </h2>
            
            <div className="flex flex-col gap-1">
                <label className="text-[9px] font-bold uppercase tracking-widest text-[#5f6368]">Target Node</label>
                <div className="relative">
                    <select 
                        value={targetNode} 
                        onChange={(e) => setTargetNode(e.target.value)}
                        className="w-full bg-[#171717] border border-[#3c4043] text-[#8ab4f8] text-xs font-bold rounded-lg pl-3 pr-8 py-2 outline-none focus:border-[#8ab4f8] appearance-none cursor-pointer shadow-inner hover:bg-[#28292c] transition-colors"
                    >
                        <option value="master_gateway">Master Gateway (Local)</option>
                        {fleetWorkers.map(w => (
                            <option key={w.server_id} value={w.server_id}>
                                Worker: {w.server_id} {w.alive ? '' : '(Offline)'}
                            </option>
                        ))}
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[#5f6368]">
                        <ChevronDown size={14} />
                    </div>
                </div>
            </div>
          </div>
          
          <div className="flex flex-col gap-1 p-3">
            <SidebarBtn active={activeTab === 'projects'} icon={<FolderOpen size={16}/>} label="Projects" count={localResources.projects?.length} color="#8ab4f8" onClick={() => setActiveTab('projects')} />
            <div className="h-px bg-[#3c4043] my-2 mx-2"></div>
            <SidebarBtn active={activeTab === 'graphs'} icon={<Workflow size={16}/>} label="Logic Graphs" count={localResources.graphs?.length} color="#81c995" onClick={() => setActiveTab('graphs')} />
            <SidebarBtn active={activeTab === 'models'} icon={<Cpu size={16}/>} label="AI Models / Files" count={Object.keys(localResources.files || {}).length} color="#fcd663" onClick={() => setActiveTab('models')} />
            <SidebarBtn active={activeTab === 'plugins'} icon={<Blocks size={16}/>} label="Python Plugins" count={localResources.plugins?.length} color="#c58af9" onClick={() => setActiveTab('plugins')} />
          </div>
        </div>

        {/* MAIN CONTENT AREA */}
        <div className="flex-1 flex flex-col bg-[#1e1e1e]">
          
          {/* Top Bar */}
          <div className="h-16 border-b border-[#3c4043] flex items-center justify-between px-6 bg-[#252526]">
            
            <div className="flex-1 max-w-sm relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5f6368]" />
              <input 
                type="text" placeholder={`Search in ${activeTab}...`} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#171717] border border-[#3c4043] rounded-lg pl-9 pr-4 py-1.5 text-sm text-[#e8eaed] focus:border-[#8ab4f8] outline-none transition"
              />
            </div>

            <div className="flex items-center gap-3">
              {activeTab === 'projects' && (
                <div className="flex items-center gap-2 bg-[#171717] p-1 border border-[#3c4043] rounded-lg">
                  <input type="text" placeholder="New Project Name..." value={saveName} onChange={(e) => setSaveName(e.target.value)} className="bg-transparent px-3 py-1 text-sm text-[#e8eaed] focus:outline-none w-48 font-mono"/>
                  <button onClick={() => { onSaveAs?.(saveName); setSaveName(''); }} disabled={!saveName} className="bg-[#81c995] hover:bg-[#a8dab5] disabled:opacity-50 text-[#202124] px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition"><Save size={14}/> SAVE UI STATE</button>
                </div>
              )}

              {activeTab === 'graphs' ? (
                <div className="flex items-center gap-2">
                    <button onClick={() => fileInputRef.current?.click()} className="bg-[#3c4043] hover:bg-[#5f6368] text-[#e8eaed] px-3 py-1.5 rounded-lg text-sm font-bold flex items-center gap-2 transition">
                        <UploadCloud size={16}/> Upload
                    </button>
                    <button onClick={handleCreateLogic} className="bg-[#81c995] hover:bg-[#a8dab5] text-[#202124] px-3 py-1.5 rounded-lg text-sm font-bold flex items-center gap-2 transition shadow-md">
                        <Plus size={16} className="stroke-[3]"/> CREATE GRAPH
                    </button>
                </div>
              ) : activeTab !== 'projects' ? (
                <button onClick={() => fileInputRef.current?.click()} className="bg-[#3c4043] hover:bg-[#5f6368] text-[#e8eaed] px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition">
                  <UploadCloud size={16}/> Upload {activeTab}
                </button>
              ) : null}

              <div className="w-px h-6 bg-[#3c4043] mx-2"></div>
              <button onClick={onClose} className="p-2 text-[#9aa0a6] hover:text-[#f28b82] hover:bg-[#3c4043] rounded-lg transition"><X size={20}/></button>
            </div>
          </div>

          {/* Table Container */}
          <div className="flex-1 overflow-y-auto custom-scrollbar relative">
            {isLoading && (
               <div className="absolute inset-0 bg-[#1e1e1e]/80 z-20 flex items-center justify-center backdrop-blur-sm">
                  <div className="text-[#8ab4f8] animate-pulse font-mono flex items-center gap-2"><Activity size={18}/> SYNCING WITH {targetNode.toUpperCase()}...</div>
               </div>
            )}
            
            {filteredItems.length === 0 && !isLoading ? (
                <div className="flex h-full flex-col items-center justify-center text-[#5f6368] gap-3">
                    <Database size={48} className="opacity-20"/>
                    <p className="font-mono text-sm uppercase">Empty</p>
                </div>
            ) : (
                <table className="w-full text-left border-collapse">
                    <thead className="bg-[#28292c] sticky top-0 z-10 shadow-md">
                        <tr>
                            <th className="py-3 px-6 text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest border-b border-[#3c4043]">Name</th>
                            <th className="py-3 px-6 text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest border-b border-[#3c4043]">Size</th>
                            <th className="py-3 px-6 text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest border-b border-[#3c4043]">System Status</th>
                            <th className="py-3 px-6 text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest border-b border-[#3c4043] text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredItems.map((item, idx) => {
                            const activeLogicInstances = localResources.active_logics?.filter((l: any) => l.graph_file === item.name.replace('.json', '')) || [];
                            
                            return (
                                <tr key={idx} className="hover:bg-[#252526] border-b border-[#3c4043]/50 transition-colors group">
                                    <td className="py-3 px-6">
                                        <div className="flex items-center gap-3">
                                            <div className={`p-1.5 rounded ${activeTab === 'projects' ? 'text-[#8ab4f8]' : activeTab === 'graphs' ? 'text-[#81c995]' : activeTab === 'models' ? 'text-[#fcd663]' : 'text-[#c58af9]'}`}>
                                                {activeTab === 'projects' ? <FolderOpen size={16}/> : activeTab === 'graphs' ? <Workflow size={16}/> : activeTab === 'models' ? <Cpu size={16}/> : <Blocks size={16}/>}
                                            </div>
                                            <span className="text-sm font-bold text-[#e8eaed] font-mono">{item.name}</span>
                                        </div>
                                    </td>

                                    <td className="py-3 px-6 text-xs text-[#9aa0a6] font-mono">
                                        {item.size ? formatBytes(item.size) : '--'}
                                    </td>

                                    <td className="py-3 px-6">
                                        <div className="flex gap-2 flex-wrap">
                                            {activeTab === 'graphs' && activeLogicInstances.map((instance: any) => (
                                                <div key={instance.name} className="bg-[#81c995]/10 text-[#81c995] pl-2 pr-1 py-0.5 rounded text-[9px] font-bold tracking-widest flex items-center gap-1.5 border border-[#81c995]/30 w-fit" title={`Logic ID: ${instance.name}`}>
                                                    <Activity size={10} className="shrink-0"/> 
                                                    <span className="truncate max-w-[100px]">{instance.name}</span>
                                                    <button onClick={() => handleUndeployLogic(instance.name)} className="p-0.5 hover:bg-[#f28b82]/20 hover:text-[#f28b82] rounded transition-colors text-[#81c995]" title="Stop (Undeploy) this Logic">
                                                        <ZapOff size={10}/>
                                                    </button>
                                                </div>
                                            ))}
                                            
                                            {activeTab === 'models' && item.inram !== undefined && (
                                                <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-widest flex items-center gap-1 border w-fit ${item.inram ? 'bg-[#fcd663]/10 text-[#fcd663] border-[#fcd663]/30' : 'bg-[#171717] text-[#5f6368] border-[#3c4043]'}`}>
                                                    {item.inram ? <Zap size={10}/> : <HardDrive size={10}/>} {item.inram ? 'IN RAM' : 'ON DISK'}
                                                </span>
                                            )}
                                        </div>
                                    </td>

                                    <td className="py-3 px-6">
                                        <div className="flex items-center justify-end gap-2 opacity-30 group-hover:opacity-100 transition-opacity">
                                            
                                            {activeTab === 'projects' && (
                                                <button onClick={() => handleLoadProject(item.name)} className="px-3 py-1 bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 text-[#8ab4f8] text-[10px] font-bold uppercase rounded border border-[#8ab4f8]/30 flex items-center gap-1 transition-colors"><FolderOpen size={12}/> OPEN</button>
                                            )}

                                            {activeTab === 'graphs' && (
                                                <>
                                                    <button onClick={() => handleEditGraph(item.name)} className="px-3 py-1 bg-[#fcd663]/10 hover:bg-[#fcd663]/20 text-[#fcd663] text-[10px] font-bold uppercase rounded border border-[#fcd663]/30 flex items-center gap-1 transition-colors"><Edit3 size={12}/> EDIT</button>
                                                    <button onClick={() => handleDeployGraph(item.name)} className="px-3 py-1 bg-[#81c995]/10 hover:bg-[#81c995]/20 text-[#81c995] text-[10px] font-bold uppercase rounded border border-[#81c995]/30 flex items-center gap-1 transition-colors" title="Deploy a new instance from this graph"><Zap size={12}/> DEPLOY</button>
                                                </>
                                            )}

                                            {activeTab === 'models' && item.inram !== undefined && (
                                                item.inram
                                                ? <button onClick={() => handleToggleRam(item.name, true)} className="px-3 py-1 bg-[#f28b82]/10 hover:bg-[#f28b82]/20 text-[#f28b82] text-[10px] font-bold uppercase rounded border border-[#f28b82]/30 flex items-center gap-1 transition-colors"><Square size={12}/> UNLOAD</button>
                                                : <button onClick={() => handleToggleRam(item.name, false)} className="px-3 py-1 bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 text-[#8ab4f8] text-[10px] font-bold uppercase rounded border border-[#8ab4f8]/30 flex items-center gap-1 transition-colors"><Play size={12}/> LOAD TO RAM</button>
                                            )}

                                            <div className="w-px h-4 bg-[#3c4043] mx-1"></div>
                                            
                                            <button onClick={() => handleDelete(item.name)} className="p-1.5 bg-[#171717] hover:bg-[#f28b82]/20 text-[#5f6368] hover:text-[#f28b82] rounded transition-colors" title="Delete File">
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const SidebarBtn = ({ active, icon, label, count, color, onClick }: any) => (
  <button 
    onClick={onClick}
    className={`flex items-center justify-between w-full p-3 rounded-xl transition-all ${active ? 'bg-[#171717] shadow-inner border border-[#3c4043]' : 'hover:bg-[#202124] border border-transparent'}`}
  >
    <div className="flex items-center gap-3">
      <div className={`${active ? '' : 'text-[#9aa0a6]'}`} style={{ color: active ? color : undefined }}>{icon}</div>
      <span className={`text-sm font-bold ${active ? 'text-[#e8eaed]' : 'text-[#9aa0a6]'}`}>{label}</span>
    </div>
    {count !== undefined && (
      <span className="text-[10px] font-mono bg-[#303134] text-[#9aa0a6] px-2 py-0.5 rounded-full">{count}</span>
    )}
  </button>
);