import React, { useState, useEffect, useRef } from 'react';
import { 
  X, Search, FileJson, Trash2, UploadCloud, FolderOpen, 
  Database, Cpu, Blocks, Play, Square, Zap, ZapOff, Activity, Workflow, HardDrive
} from 'lucide-react';
import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { axiosClient, api_version } from '../../api/axiosClient';

interface FileManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'projects' | 'graphs' | 'models' | 'plugins';
  mode: 'load' | 'save' | 'manage'; 
  onFileSelect?: (filename: string, fileContent?: any) => void;
  onSaveAs?: (filename: string) => void;
}

export function FileManagerModal({ isOpen, onClose, defaultTab = 'projects', mode, onFileSelect, onSaveAs }: FileManagerModalProps) {
  // --- STATES ---
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [searchQuery, setSearchQuery] = useState('');
  const [saveName, setSaveName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localResources, setLocalResources] = useState<any>({ projects: [], graphs: [], files: {}, plugins: [], active_logics: [] });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- ACTIONS TỪ FLEET STORE ---
  const deployGraph = useFleetStore(state => state.deployGraph);
  const undeployLogic = useFleetStore(state => state.undeployLogic);
  const toggleFileRamStatus = useFleetStore(state => state.toggleFileRamStatus);
  const uploadResourceToNode = useFleetStore(state => state.uploadResource);

  // Fetch dữ liệu mỗi khi mở Modal hoặc đổi Tab
  useEffect(() => {
    if (isOpen) {
      if (mode === 'load' || mode === 'save') setActiveTab('projects');
      fetchResources();
    }
  }, [isOpen, mode]);

  const fetchResources = async () => {
    setIsLoading(true);
    try {
      // ĐÃ SỬA API: Thêm prefix api_version/infra
      const res = await axiosClient.get(`${api_version}/infra/resources/status`);
      setLocalResources(res.data);
    } catch (error) {
      console.error(`Lỗi tải danh sách tài nguyên:`, error);
    } finally {
      setIsLoading(false);
    }
  };

  // --- HANDLERS ---
  const getFileTypeString = (tab: string) => {
      // Map đúng từ tab name sang keyword mà Backend xử lý
      if (tab === 'models') return 'file';
      if (tab === 'graphs') return 'graph';
      if (tab === 'plugins') return 'plugin';
      return 'projects';
  }

  const handleDelete = async (filename: string) => {
    if (!confirm(`Xóa file ${filename}? Hành động này không thể hoàn tác.`)) return;
    try {
      const fileType = getFileTypeString(activeTab);
      // ĐÃ SỬA API: Thêm prefix
      await axiosClient.delete(`${api_version}/infra/resources/delete/${fileType}/${filename}`);
      fetchResources(); 
    } catch (error) {
      console.error("Lỗi xóa file:", error);
    }
  };

  const handleAction = async (filename: string) => {
    if (mode === 'load' && onFileSelect && activeTab === 'projects') {
      setIsLoading(true);
      try {
        // ĐÃ SỬA API: Đọc Project từ Disk
        const res = await axiosClient.get(`${api_version}/infra/resources/files/projects/${filename}/content`);
        onFileSelect(filename, res.data);
      } catch (error) {
        console.error("Lỗi đọc Project:", error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      let targetType: any = getFileTypeString(activeTab);
      await uploadResourceToNode(e.target.files[0], targetType);
      fetchResources(); 
    }
  };

  const formatBytes = (bytes: number) => bytes > 1048576 ? (bytes / 1048576).toFixed(2) + ' MB' : (bytes / 1024).toFixed(2) + ' KB';

  if (!isOpen) return null;

  const renderContent = () => {
    let items: any[] = [];
    
    if (activeTab === 'projects') items = localResources.projects || [];
    if (activeTab === 'graphs') items = localResources.graphs || [];
    if (activeTab === 'models') items = Object.entries(localResources.files || {}).map(([id, info]: any) => ({ id, ...info }));
    if (activeTab === 'plugins') items = localResources.plugins || [];

    const filteredItems = items.filter((item: any) => {
      const name = typeof item === 'string' ? item : item.name || item.id;
      return name.toLowerCase().includes(searchQuery.toLowerCase());
    });

    if (isLoading) return <div className="flex-1 flex items-center justify-center text-[#8ab4f8] animate-pulse font-mono">ĐANG ĐỒNG BỘ DỮ LIỆU...</div>;
    
    if (filteredItems.length === 0) return (
      <div className="flex-1 flex flex-col items-center justify-center text-[#5f6368] gap-3">
        <Database size={48} className="opacity-20"/>
        <p className="font-mono text-sm uppercase">Không có dữ liệu trong mục này</p>
      </div>
    );

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 auto-rows-max p-1">
        {filteredItems.map((item: any, idx: number) => {
          const name = typeof item === 'string' ? item : item.name || item.id;
          const size = item.size ? formatBytes(item.size) : '--';
          const inRam = item.inram;

          const isDeployed = activeTab === 'graphs' && localResources.active_logics?.some((l: any) => l.graph_file === name.replace('.json', ''));

          return (
            <div key={idx} onClick={() => (mode === 'load' && activeTab === 'projects') && handleAction(name)}
                 className={`group relative bg-[#202124] border ${activeTab === 'projects' && mode === 'load' ? 'hover:border-[#8ab4f8] cursor-pointer' : 'border-[#3c4043]'} rounded-xl p-4 flex flex-col gap-3 transition-all hover:shadow-lg overflow-hidden`}>
              
              <div className="flex items-start justify-between">
                <div className={`p-2.5 rounded-lg ${
                  activeTab === 'projects' ? 'bg-[#8ab4f8]/10 text-[#8ab4f8]' : 
                  activeTab === 'graphs' ? 'bg-[#81c995]/10 text-[#81c995]' : 
                  activeTab === 'models' ? 'bg-[#fcd663]/10 text-[#fcd663]' : 'bg-[#c58af9]/10 text-[#c58af9]'
                }`}>
                  {activeTab === 'projects' ? <FolderOpen size={20}/> : activeTab === 'graphs' ? <Workflow size={20}/> : activeTab === 'models' ? <Cpu size={20}/> : <Blocks size={20}/>}
                </div>

                <div className="flex gap-1">
                  {isDeployed && <span className="bg-[#81c995]/20 text-[#81c995] px-2 py-0.5 rounded text-[9px] font-bold tracking-widest flex items-center gap-1 border border-[#81c995]/30"><Activity size={10}/> DEPLOYED</span>}
                  {activeTab === 'models' && inRam !== undefined && (
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-widest flex items-center gap-1 border ${inRam ? 'bg-[#fcd663]/20 text-[#fcd663] border-[#fcd663]/30' : 'bg-[#3c4043] text-[#9aa0a6] border-transparent'}`}>
                      {inRam ? <Zap size={10}/> : <HardDrive size={10}/>} {inRam ? 'IN RAM' : 'DISK'}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold text-[#e8eaed] truncate" title={name}>{name}</h3>
                {activeTab !== 'projects' && <p className="text-[10px] text-[#5f6368] font-mono mt-1">Size: {size}</p>}
              </div>

              <div className="flex items-center gap-2 mt-2 pt-3 border-t border-[#3c4043] opacity-0 group-hover:opacity-100 transition-opacity">
                
                {activeTab === 'graphs' && (
                  isDeployed 
                  ? <button onClick={(e) => { e.stopPropagation(); undeployLogic(localResources.active_logics.find((l:any) => l.graph_file === name.replace('.json', '')).name); setTimeout(fetchResources, 500); }} className="flex-1 py-1.5 bg-[#f28b82]/10 hover:bg-[#f28b82]/20 text-[#f28b82] text-[10px] font-bold uppercase rounded border border-[#f28b82]/30 flex justify-center items-center gap-1 transition-colors"><ZapOff size={12}/> Stop</button>
                  : <button onClick={(e) => { e.stopPropagation(); deployGraph(name.replace('.json', '')); setTimeout(fetchResources, 500); }} className="flex-1 py-1.5 bg-[#81c995]/10 hover:bg-[#81c995]/20 text-[#81c995] text-[10px] font-bold uppercase rounded border border-[#81c995]/30 flex justify-center items-center gap-1 transition-colors"><Zap size={12}/> Deploy</button>
                )}

                {activeTab === 'models' && (
                  inRam
                  ? <button onClick={(e) => { e.stopPropagation(); toggleFileRamStatus(name, true); setTimeout(fetchResources, 500); }} className="flex-1 py-1.5 bg-[#f28b82]/10 hover:bg-[#f28b82]/20 text-[#f28b82] text-[10px] font-bold uppercase rounded border border-[#f28b82]/30 flex justify-center items-center gap-1 transition-colors"><Square size={12}/> Unload</button>
                  : <button onClick={(e) => { e.stopPropagation(); toggleFileRamStatus(name, false); setTimeout(fetchResources, 500); }} className="flex-1 py-1.5 bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 text-[#8ab4f8] text-[10px] font-bold uppercase rounded border border-[#8ab4f8]/30 flex justify-center items-center gap-1 transition-colors"><Play size={12}/> Load RAM</button>
                )}

                <button 
                  onClick={(e) => { e.stopPropagation(); handleDelete(name); }}
                  className="p-1.5 bg-[#28292c] hover:bg-[#f28b82]/20 text-[#5f6368] hover:text-[#f28b82] rounded transition-colors" title="Delete">
                  <Trash2 size={14} />
                </button>
              </div>

            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-6 font-sans">
      <input type="file" ref={fileInputRef} onChange={handleUploadFile} className="hidden" />
      
      <div className="bg-[#1e1e1e] w-full max-w-6xl h-[85vh] rounded-2xl shadow-2xl border border-[#3c4043] flex overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* SIDEBAR BÊN TRÁI */}
        <div className="w-64 bg-[#252526] border-r border-[#3c4043] flex flex-col shrink-0">
          <div className="p-5 border-b border-[#3c4043]">
            <h2 className="text-[#e8eaed] font-extrabold text-sm tracking-widest flex items-center gap-2">
              <Database size={18} className="text-[#8ab4f8]" /> ASSET MANAGER
            </h2>
            <p className="text-[#9aa0a6] text-[10px] font-mono mt-1">Target: Master Node</p>
          </div>
          
          <div className="flex flex-col gap-1 p-3">
            <SidebarBtn active={activeTab === 'projects'} icon={<FolderOpen size={16}/>} label="Projects" count={localResources.projects?.length} color="#8ab4f8" onClick={() => setActiveTab('projects')} />
            
            {mode === 'manage' && (
              <>
                <div className="h-px bg-[#3c4043] my-2 mx-2"></div>
                <SidebarBtn active={activeTab === 'graphs'} icon={<Workflow size={16}/>} label="Logic Graphs" count={localResources.graphs?.length} color="#81c995" onClick={() => setActiveTab('graphs')} />
                <SidebarBtn active={activeTab === 'models'} icon={<Cpu size={16}/>} label="AI Models & Assets" count={Object.keys(localResources.files || {}).length} color="#fcd663" onClick={() => setActiveTab('models')} />
                <SidebarBtn active={activeTab === 'plugins'} icon={<Blocks size={16}/>} label="Plugins (Python)" count={localResources.plugins?.length} color="#c58af9" onClick={() => setActiveTab('plugins')} />
              </>
            )}
          </div>
        </div>

        {/* NỘI DUNG BÊN PHẢI */}
        <div className="flex-1 flex flex-col bg-[#1e1e1e]">
          
          {/* Top Bar */}
          <div className="h-16 border-b border-[#3c4043] flex items-center justify-between px-6 bg-[#252526]">
            
            <div className="flex-1 max-w-md relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5f6368]" />
              <input 
                type="text" placeholder={`Search in ${activeTab}...`} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#171717] border border-[#3c4043] rounded-lg pl-9 pr-4 py-2 text-sm text-[#e8eaed] focus:border-[#8ab4f8] outline-none transition"
              />
            </div>

            <div className="flex items-center gap-3">
              {/* Nút Save As nếu đang ở Mode Save */}
              {mode === 'save' && activeTab === 'projects' && (
                <div className="flex items-center gap-2">
                  <input type="text" placeholder="Project Name..." value={saveName} onChange={(e) => setSaveName(e.target.value)} className="bg-[#171717] border border-[#3c4043] rounded-lg px-3 py-2 text-sm text-[#e8eaed] focus:border-[#81c995] outline-none w-48"/>
                  <button onClick={() => onSaveAs?.(saveName)} disabled={!saveName} className="bg-[#81c995] hover:bg-[#a8dab5] disabled:opacity-50 text-[#202124] px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition"><UploadCloud size={16}/> Save to Server</button>
                </div>
              )}

              {/* Nút Upload Tài Nguyên */}
              {mode === 'manage' && activeTab !== 'projects' && (
                <button onClick={() => fileInputRef.current?.click()} className="bg-[#3c4043] hover:bg-[#5f6368] text-[#e8eaed] px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition">
                  <UploadCloud size={16}/> Upload {activeTab}
                </button>
              )}

              <div className="w-px h-6 bg-[#3c4043] mx-2"></div>
              <button onClick={onClose} className="p-2 text-[#9aa0a6] hover:text-[#f28b82] hover:bg-[#3c4043] rounded-lg transition"><X size={20}/></button>
            </div>
          </div>

          <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
            {renderContent()}
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