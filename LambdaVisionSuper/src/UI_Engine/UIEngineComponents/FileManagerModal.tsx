import React, { useState, useEffect, useRef } from 'react';
import { 
  X, Search, Trash2, UploadCloud, FolderOpen, 
  Database, Cpu, Blocks, Play, Square, Zap, ZapOff, Activity, Workflow, HardDrive, Save, Download
} from 'lucide-react';
import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { FleetAPI } from '../../api/fleetApi';

interface FileManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'projects' | 'graphs' | 'models' | 'plugins';
  mode?: 'load' | 'save' | 'manage'; 
  onFileSelect?: (filename: string, fileContent?: any) => void;
  onSaveAs?: (filename: string) => void;
}

export function FileManagerModal({ isOpen, onClose, defaultTab = 'projects', onFileSelect, onSaveAs }: FileManagerModalProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [searchQuery, setSearchQuery] = useState('');
  const [saveName, setSaveName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localResources, setLocalResources] = useState<any>({ projects: [], graphs: [], files: {}, plugins: [], active_logics: [] });
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const deployGraph = useFleetStore(state => state.deployGraph);
  const undeployLogic = useFleetStore(state => state.undeployLogic);
  const toggleFileRamStatus = useFleetStore(state => state.toggleFileRamStatus);
  const uploadResourceToNode = useFleetStore(state => state.uploadResource);

  useEffect(() => {
    if (isOpen) fetchResources();
  }, [isOpen, activeTab]);

  const fetchResources = async () => {
    setIsLoading(true);
    try {
      const data = await FleetAPI.getMasterLocalResource();
      setLocalResources(data);
    } catch (error) {
      console.error(`Lỗi tải danh sách tài nguyên:`, error);
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

  const handleDelete = async (filename: string) => {
    if (!confirm(`Xóa file ${filename}? Hành động này không thể hoàn tác.`)) return;
    try {
      const fileType = getFileTypeString(activeTab) as any;
      await FleetAPI.master_removeResource(filename, fileType);
      fetchResources(); 
    } catch (error) {
      console.error("Lỗi xóa file:", error);
    }
  };

  const handleLoadProject = async (filename: string) => {
    if (onFileSelect && activeTab === 'projects') {
      setIsLoading(true);
      try {
        const data = await FleetAPI.master_getFileContent(filename, 'projects');
        onFileSelect(filename, data);
      } catch (error) {
        console.error("Lỗi đọc Project:", error);
        alert("Không thể đọc file Project này!");
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

  // Xử lý dữ liệu cho Table
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
          <div className="p-5 border-b border-[#3c4043]">
            <h2 className="text-[#e8eaed] font-extrabold text-sm tracking-widest flex items-center gap-2">
              <Database size={18} className="text-[#8ab4f8]" /> ASSET MANAGER
            </h2>
            <p className="text-[#9aa0a6] text-[10px] font-mono mt-1">Target: Master Node</p>
          </div>
          
          <div className="flex flex-col gap-1 p-3">
            <SidebarBtn active={activeTab === 'projects'} icon={<FolderOpen size={16}/>} label="Projects" count={localResources.projects?.length} color="#8ab4f8" onClick={() => setActiveTab('projects')} />
            <div className="h-px bg-[#3c4043] my-2 mx-2"></div>
            <SidebarBtn active={activeTab === 'graphs'} icon={<Workflow size={16}/>} label="Logic Graphs" count={localResources.graphs?.length} color="#81c995" onClick={() => setActiveTab('graphs')} />
            <SidebarBtn active={activeTab === 'models'} icon={<Cpu size={16}/>} label="AI Models / Files" count={Object.keys(localResources.files || {}).length} color="#fcd663" onClick={() => setActiveTab('models')} />
            <SidebarBtn active={activeTab === 'plugins'} icon={<Blocks size={16}/>} label="Python Plugins" count={localResources.plugins?.length} color="#c58af9" onClick={() => setActiveTab('plugins')} />
          </div>
        </div>

        {/* NỘI DUNG CHÍNH (TABLE AREA) */}
        <div className="flex-1 flex flex-col bg-[#1e1e1e]">
          
          {/* Top Bar - Công cụ theo từng Tab */}
          <div className="h-16 border-b border-[#3c4043] flex items-center justify-between px-6 bg-[#252526]">
            
            {/* Thanh Tìm kiếm */}
            <div className="flex-1 max-w-sm relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5f6368]" />
              <input 
                type="text" placeholder={`Search ${activeTab}...`} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#171717] border border-[#3c4043] rounded-lg pl-9 pr-4 py-1.5 text-sm text-[#e8eaed] focus:border-[#8ab4f8] outline-none transition"
              />
            </div>

            <div className="flex items-center gap-3">
              {/* Toolbar cho Tab Projects (Tích hợp Save) */}
              {activeTab === 'projects' && (
                <div className="flex items-center gap-2 bg-[#171717] p-1 border border-[#3c4043] rounded-lg">
                  <input type="text" placeholder="Tên Project mới..." value={saveName} onChange={(e) => setSaveName(e.target.value)} className="bg-transparent px-3 py-1 text-sm text-[#e8eaed] focus:outline-none w-48 font-mono"/>
                  <button onClick={() => { onSaveAs?.(saveName); setSaveName(''); }} disabled={!saveName} className="bg-[#81c995] hover:bg-[#a8dab5] disabled:opacity-50 text-[#202124] px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition"><Save size={14}/> LƯU LÊN MÁY CHỦ</button>
                </div>
              )}

              {/* Nút Upload cho các Tab Tài nguyên khác */}
              {activeTab !== 'projects' && (
                <button onClick={() => fileInputRef.current?.click()} className="bg-[#3c4043] hover:bg-[#5f6368] text-[#e8eaed] px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition">
                  <UploadCloud size={16}/> Upload {activeTab}
                </button>
              )}

              <div className="w-px h-6 bg-[#3c4043] mx-2"></div>
              <button onClick={onClose} className="p-2 text-[#9aa0a6] hover:text-[#f28b82] hover:bg-[#3c4043] rounded-lg transition"><X size={20}/></button>
            </div>
          </div>

          {/* Table Container */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {isLoading ? (
                <div className="flex h-full items-center justify-center text-[#8ab4f8] animate-pulse font-mono">ĐANG ĐỒNG BỘ DỮ LIỆU...</div>
            ) : filteredItems.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-[#5f6368] gap-3">
                    <Database size={48} className="opacity-20"/>
                    <p className="font-mono text-sm uppercase">Trống</p>
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
                            const isDeployed = activeTab === 'graphs' && localResources.active_logics?.some((l: any) => l.graph_file === item.name.replace('.json', ''));
                            
                            return (
                                <tr key={idx} className="hover:bg-[#252526] border-b border-[#3c4043]/50 transition-colors group">
                                    {/* CỘT TÊN FILE */}
                                    <td className="py-3 px-6">
                                        <div className="flex items-center gap-3">
                                            <div className={`p-1.5 rounded ${activeTab === 'projects' ? 'text-[#8ab4f8]' : activeTab === 'graphs' ? 'text-[#81c995]' : activeTab === 'models' ? 'text-[#fcd663]' : 'text-[#c58af9]'}`}>
                                                {activeTab === 'projects' ? <FolderOpen size={16}/> : activeTab === 'graphs' ? <Workflow size={16}/> : activeTab === 'models' ? <Cpu size={16}/> : <Blocks size={16}/>}
                                            </div>
                                            <span className="text-sm font-bold text-[#e8eaed] font-mono">{item.name}</span>
                                        </div>
                                    </td>

                                    {/* CỘT SIZE */}
                                    <td className="py-3 px-6 text-xs text-[#9aa0a6] font-mono">
                                        {item.size ? formatBytes(item.size) : '--'}
                                    </td>

                                    {/* CỘT TRẠNG THÁI (STATUS) */}
                                    <td className="py-3 px-6">
                                        <div className="flex gap-2">
                                            {isDeployed && <span className="bg-[#81c995]/10 text-[#81c995] px-2 py-0.5 rounded text-[9px] font-bold tracking-widest flex items-center gap-1 border border-[#81c995]/30 w-fit"><Activity size={10}/> RUNNING</span>}
                                            {activeTab === 'models' && item.inRam !== undefined && (
                                                <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-widest flex items-center gap-1 border w-fit ${item.inRam ? 'bg-[#fcd663]/10 text-[#fcd663] border-[#fcd663]/30' : 'bg-[#171717] text-[#5f6368] border-[#3c4043]'}`}>
                                                    {item.inRam ? <Zap size={10}/> : <HardDrive size={10}/>} {item.inRam ? 'IN RAM' : 'ON DISK'}
                                                </span>
                                            )}
                                        </div>
                                    </td>

                                    {/* CỘT HÀNH ĐỘNG (ACTIONS) */}
                                    <td className="py-3 px-6">
                                        <div className="flex items-center justify-end gap-2 opacity-30 group-hover:opacity-100 transition-opacity">
                                            
                                            {/* Action cho Project */}
                                            {activeTab === 'projects' && (
                                                <button onClick={() => handleLoadProject(item.name)} className="px-3 py-1 bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 text-[#8ab4f8] text-[10px] font-bold uppercase rounded border border-[#8ab4f8]/30 flex items-center gap-1 transition-colors"><FolderOpen size={12}/> MỞ PROJECT</button>
                                            )}

                                            {/* Action cho Logic Graph */}
                                            {activeTab === 'graphs' && (
                                                isDeployed 
                                                ? <button onClick={() => { undeployLogic(localResources.active_logics.find((l:any) => l.graph_file === item.name.replace('.json', '')).name); setTimeout(fetchResources, 500); }} className="px-3 py-1 bg-[#f28b82]/10 hover:bg-[#f28b82]/20 text-[#f28b82] text-[10px] font-bold uppercase rounded border border-[#f28b82]/30 flex items-center gap-1 transition-colors"><ZapOff size={12}/> UNDEPLOY</button>
                                                : <button onClick={() => { deployGraph(item.name.replace('.json', '')); setTimeout(fetchResources, 500); }} className="px-3 py-1 bg-[#81c995]/10 hover:bg-[#81c995]/20 text-[#81c995] text-[10px] font-bold uppercase rounded border border-[#81c995]/30 flex items-center gap-1 transition-colors"><Zap size={12}/> DEPLOY</button>
                                            )}

                                            {/* Action cho Models (RAM/Disk) */}
                                            {activeTab === 'models' && item.inRam !== undefined && (
                                                item.inRam
                                                ? <button onClick={() => { toggleFileRamStatus(item.name, true); setTimeout(fetchResources, 500); }} className="px-3 py-1 bg-[#f28b82]/10 hover:bg-[#f28b82]/20 text-[#f28b82] text-[10px] font-bold uppercase rounded border border-[#f28b82]/30 flex items-center gap-1 transition-colors"><Square size={12}/> GIẢI PHÓNG</button>
                                                : <button onClick={() => { toggleFileRamStatus(item.name, false); setTimeout(fetchResources, 500); }} className="px-3 py-1 bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 text-[#8ab4f8] text-[10px] font-bold uppercase rounded border border-[#8ab4f8]/30 flex items-center gap-1 transition-colors"><Play size={12}/> NẠP LÊN RAM</button>
                                            )}

                                            <div className="w-px h-4 bg-[#3c4043] mx-1"></div>
                                            
                                            <button onClick={() => handleDelete(item.name)} className="p-1.5 bg-[#171717] hover:bg-[#f28b82]/20 text-[#5f6368] hover:text-[#f28b82] rounded transition-colors" title="Delete">
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