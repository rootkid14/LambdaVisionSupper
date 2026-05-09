import React, { useState, useRef } from 'react';
import { 
  Trash2, Activity, Plus, Check, HardDrive, Upload, Cpu, 
  Play, Square, FileJson, Workflow, Blocks, Download, Zap, ZapOff , Search, Edit3, CloudUpload
} from 'lucide-react';
import { LocalServerInfo, DeviceInfo, ResourceType } from "../../Stores/FleetDashboardStores";
import { MiniProgressBar } from '../../Commons/MiniProgressBar';

// ==========================================
// CÁC COMPONENT THẺ (CARDS) ĐỂ TÁI SỬ DỤNG
// ==========================================

const ServerCard = ({ srv, onRemove }: { srv: LocalServerInfo, onRemove: (id: string) => void }) => (
  <div className="group flex flex-col p-3 bg-[#28292c] rounded-xl border border-[#3c4043] hover:border-[#8ab4f8] transition-colors shadow-sm relative overflow-hidden">
    <button onClick={() => onRemove(srv.id)} className="absolute top-2 right-2 text-[#5f6368] hover:text-[#f28b82] p-1.5 rounded-lg hover:bg-[#f28b82]/10 transition-all opacity-0 group-hover:opacity-100 bg-[#28292c]"><Trash2 size={16} /></button>
    <div className="flex items-center gap-2 mb-2 pr-8">
      <span className="text-sm font-bold text-[#e8eaed] truncate">{srv.id}</span>
      {srv.status === 'online' 
        ? <span className="bg-[#81c995]/10 text-[#81c995] px-2 py-[2px] rounded uppercase text-[9px] font-bold tracking-wider flex items-center gap-1 border border-[#81c995]/20"><Activity size={10}/> ONLINE {srv.ping}ms</span> 
        : <span className="bg-[#f28b82]/10 text-[#f28b82] px-2 py-[2px] rounded uppercase text-[9px] font-bold tracking-wider border border-[#f28b82]/20">TIMEOUT</span>}
    </div>
    <div className="text-xs text-[#8ab4f8] font-mono bg-[#171717] px-2 py-1 rounded inline-flex self-start border border-[#3c4043]">{srv.host}</div>
  </div>
);

const DeviceCard = ({ dev, onRemove }: { dev: DeviceInfo, onRemove: (id: string) => void }) => (
  <div className="group flex flex-col p-3 bg-[#28292c] rounded-xl border border-[#3c4043] hover:border-[#fcd663] transition-colors shadow-sm relative overflow-hidden">
    <button onClick={() => onRemove(dev.host)} className="absolute top-2 right-2 text-[#5f6368] hover:text-[#f28b82] p-1.5 rounded-lg hover:bg-[#f28b82]/10 transition-all opacity-0 group-hover:opacity-100 bg-[#28292c]"><Trash2 size={16} /></button>
    <div className="flex items-center gap-2 mb-2 pr-8">
      <span className="text-sm font-bold text-[#e8eaed] truncate">{dev.host}</span>
      {dev.alive 
        ? <span className="bg-[#81c995]/10 text-[#81c995] px-2 py-[2px] rounded uppercase text-[9px] font-bold tracking-wider border border-[#81c995]/20">STREAMING</span> 
        : <span className="bg-[#fcd663]/10 text-[#fcd663] px-2 py-[2px] rounded uppercase text-[9px] font-bold tracking-wider border border-[#fcd663]/20">OFFLINE</span>}
    </div>
    <div className="flex items-center gap-3">
      <span className="text-xs text-[#9aa0a6] font-mono">{dev.host}</span>
    </div>
  </div>
);

const ResourceCard = ({ id, size, inRam, type, icon: Icon, onDownload, onRemove, actionBtn }: any) => {
  const formatBytes = (bytes: number) => bytes > 1048576 ? (bytes / 1048576).toFixed(2) + ' MB' : (bytes / 1024).toFixed(2) + ' KB';

  return (
    <div className="flex flex-col p-2.5 bg-[#171717] rounded-lg border border-[#3c4043] hover:border-[#8ab4f8]/50 transition-colors group">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-[#e8eaed] flex items-center gap-1.5 truncate">
          <Icon size={14} className="text-[#8ab4f8] shrink-0"/> 
          <span className="truncate">{id}</span>
        </span>
        <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#5f6368] font-mono">{formatBytes(size)}</span>
            {inRam !== undefined && (
              inRam 
                ? <span className="bg-[#81c995]/10 text-[#81c995] border border-[#81c995]/20 px-1.5 py-0.5 rounded uppercase text-[9px] font-extrabold tracking-widest"><Play size={10} className="inline mr-0.5 -mt-0.5"/> IN RAM</span> 
                : <span className="bg-[#202124] text-[#9aa0a6] border border-[#3c4043] px-1.5 py-0.5 rounded uppercase text-[9px] font-extrabold tracking-widest"><HardDrive size={10} className="inline mr-0.5 -mt-0.5"/> DISK</span>
            )}
        </div>
      </div>
      <div className="flex items-center justify-between pt-2 border-t border-[#3c4043]">
        <div className="flex gap-1.5">
          <button onClick={() => onDownload(id, type)} className="flex items-center gap-1 text-[10px] font-bold text-[#9aa0a6] hover:text-[#8ab4f8] bg-[#202124] hover:bg-[#303134] px-2 py-1 rounded transition-colors border border-[#3c4043]"><Download size={12}/> Download</button>
          {actionBtn}
        </div>
        <button onClick={() => onRemove(id, type)} className="text-[#5f6368] hover:text-[#f28b82] p-1 rounded hover:bg-[#f28b82]/10 transition-all opacity-30 group-hover:opacity-100"><Trash2 size={14}/></button>
      </div>
    </div>
  );
};


// ==========================================
// CÁC TABS CHÍNH
// ==========================================

export const ServersTab = ({ servers, onAdd, onRemove }: { servers: LocalServerInfo[], onAdd: (id: string, host: string) => void, onRemove: (id: string) => void }) => {
  const [isAdding, setIsAdding] = useState(false);
  const [id, setId] = useState('');
  const [host, setHost] = useState('');

  return (
    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="flex items-center justify-between"><span className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest">APIManualRoutingBus</span><span className="bg-[#8ab4f8]/10 text-[#8ab4f8] px-2 py-0.5 rounded text-[10px] font-bold border border-[#8ab4f8]/20">{servers.length} Nodes</span></div>
      <div className="flex flex-col gap-3">
        {servers.map(srv => <ServerCard key={srv.id} srv={srv} onRemove={onRemove} />)}
        
        {isAdding ? (
          <div className="p-4 bg-[#28292c] rounded-xl border border-[#8ab4f8]/50 flex flex-col gap-3 shadow-lg">
            <input type="text" placeholder="Server ID (e.g., worker_2)" value={id} onChange={e => setId(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm rounded-lg px-3 py-2.5 focus:border-[#8ab4f8] outline-none" />
            <input type="text" placeholder="Host (e.g., 192.168.1.10:8000)" value={host} onChange={e => setHost(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm rounded-lg px-3 py-2.5 focus:border-[#8ab4f8] outline-none font-mono" />
            <div className="flex justify-end gap-2 mt-2">
              <button onClick={() => setIsAdding(false)} className="px-4 py-2 text-xs font-bold text-[#9aa0a6] hover:text-[#e8eaed] bg-[#3c4043] hover:bg-[#5f6368] rounded-lg transition-colors">Cancel</button>
              <button onClick={() => { onAdd(id, host); setIsAdding(false); setId(''); setHost(''); }} className="flex items-center gap-1.5 px-4 py-2 bg-[#8ab4f8] hover:bg-[#aecbfa] text-[#202124] text-xs font-bold rounded-lg"><Check size={14} /> Add to Bus</button>
            </div>
          </div>
        ) : (
          <button onClick={() => setIsAdding(true)} className="w-full py-3.5 bg-[#202124] hover:bg-[#303134] text-[#8ab4f8] text-xs font-bold uppercase rounded-xl border border-dashed border-[#3c4043] hover:border-[#8ab4f8] transition-colors flex items-center justify-center gap-2"><Plus size={16} /> Register Server</button>
        )}
      </div>
    </div>
  );
};

export const DevicesTab = ({ devices, onAdd, onRemove }: { devices: DeviceInfo[], onAdd: (id: string, host: string) => void, onRemove: (id: string) => void }) => {
  const [isAdding, setIsAdding] = useState(false);
  const [id, setId] = useState('');
  const [host, setHost] = useState('');

  return (
    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="flex items-center justify-between"><span className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest">Hardware Endpoints</span><span className="bg-[#81c995]/10 text-[#81c995] px-2 py-0.5 rounded text-[10px] font-bold border border-[#81c995]/20">{devices.length} Devices</span></div>
      <div className="flex flex-col gap-3">
        {devices.map((dev, idx) => <DeviceCard key={`${dev.host}-${idx}`} dev={dev} onRemove={onRemove} />)}
        
        {isAdding ? (
          <div className="p-4 bg-[#28292c] rounded-xl border border-[#81c995]/50 flex flex-col gap-3 shadow-lg">
            <input type="text" placeholder="Device ID (Name)" value={id} onChange={e => setId(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm rounded-lg px-3 py-2.5 focus:border-[#81c995] outline-none" />
            <input type="text" placeholder="Endpoint URL / IP" value={host} onChange={e => setHost(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm rounded-lg px-3 py-2.5 focus:border-[#81c995] outline-none font-mono" />
            <div className="flex justify-end gap-2 mt-2">
              <button onClick={() => setIsAdding(false)} className="px-4 py-2 text-xs font-bold text-[#9aa0a6] hover:text-[#e8eaed] bg-[#3c4043] hover:bg-[#5f6368] rounded-lg transition-colors">Cancel</button>
              <button onClick={() => { onAdd(id, host); setIsAdding(false); setId(''); setHost(''); }} className="flex items-center gap-1.5 px-4 py-2 bg-[#81c995] hover:bg-[#a8dab5] text-[#202124] text-xs font-bold rounded-lg"><Check size={14} /> Add Device</button>
            </div>
          </div>
        ) : (
          <button onClick={() => setIsAdding(true)} className="w-full py-3.5 bg-[#202124] hover:bg-[#303134] text-[#81c995] text-xs font-bold uppercase rounded-xl border border-dashed border-[#3c4043] hover:border-[#81c995] transition-colors flex items-center justify-center gap-2"><Plus size={16} /> Add Device Endpoint</button>
        )}
      </div>
    </div>
  );
};

export const ResourcesTab = ({ hardware, resourceInfo, onUpload, onDownload, onRemove, onDeploy, onUndeploy, onNavigateLogic, onToggleRam, onEditGraph }: any) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadTargetType, setUploadTargetType] = useState<ResourceType | null>(null);
  const [subTab, setSubTab] = useState<'logics' | 'files' | 'plugins'>('logics');
  const [searchQuery, setSearchQuery] = useState('');

  const handleTriggerUpload = (type: ResourceType) => { setUploadTargetType(type); fileInputRef.current?.click(); };
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && uploadTargetType) {
      await onUpload(e.target.files[0], uploadTargetType);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setUploadTargetType(null);
    }
  };

  const filesObj = resourceInfo?.files || {};
  const activeLogics = resourceInfo?.active_logics || [];
  const models = Object.entries(filesObj).map(([id, info]: any) => ({ id, size: info.size, inRam: info.inram })).filter(m => m.id.toLowerCase().includes(searchQuery.toLowerCase()));
  const graphs = (resourceInfo?.graphs || []).filter((g:any) => g.name.toLowerCase().includes(searchQuery.toLowerCase()));
  const plugins = (resourceInfo?.plugins || []).filter((p:any) => p.name.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="flex flex-col gap-5 animate-in fade-in slide-in-from-right-4 duration-300 pb-10">
      <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />

      {/* 1. NODE PERFORMANCE */}
      <div className="p-3 bg-[#171717] rounded-xl border border-[#3c4043] flex flex-col gap-3 shadow-sm">
        <MiniProgressBar label="CPU Core" percent={hardware?.cpu_percent ?? 0} colorClass={(hardware?.cpu_percent ?? 0) > 80 ? 'bg-[#fcd663]' : 'bg-[#8ab4f8]'} />
        <MiniProgressBar label="RAM System" percent={hardware?.ram_percent ?? 0} colorClass={(hardware?.ram_percent ?? 0) > 80 ? 'bg-[#f28b82]' : 'bg-[#81c995]'} extraText={`${hardware?.ram_used_mb ?? 0}MB / ${hardware?.ram_total_mb ?? 0}MB`} />
      </div>

      {/* 2. THANH CÔNG CỤ: SUBTABS & SEARCH */}
      <div className="flex flex-col gap-3 sticky top-0 bg-[#202124] z-10 py-1">
        <div className="flex bg-[#171717] p-1 rounded-lg border border-[#3c4043]">
          <button onClick={() => setSubTab('logics')} className={`flex-1 py-1.5 text-[10px] font-bold uppercase rounded transition-colors ${subTab === 'logics' ? 'bg-[#3c4043] text-[#81c995]' : 'text-[#9aa0a6] hover:text-[#e8eaed]'}`}>Logics</button>
          <button onClick={() => setSubTab('files')} className={`flex-1 py-1.5 text-[10px] font-bold uppercase rounded transition-colors ${subTab === 'files' ? 'bg-[#3c4043] text-[#8ab4f8]' : 'text-[#9aa0a6] hover:text-[#e8eaed]'}`}>Models / Files</button>
          <button onClick={() => setSubTab('plugins')} className={`flex-1 py-1.5 text-[10px] font-bold uppercase rounded transition-colors ${subTab === 'plugins' ? 'bg-[#3c4043] text-[#fcd663]' : 'text-[#9aa0a6] hover:text-[#e8eaed]'}`}>Plugins</button>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#5f6368]"/>
          <input type="text" placeholder="Search resources..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs rounded-lg pl-9 pr-3 py-2 outline-none focus:border-[#8ab4f8] transition-colors" />
        </div>
      </div>

      {/* 3. NỘI DUNG SUBTAB */}
      <div className="flex flex-col gap-3">
        {subTab === 'logics' && (
          <>
            {/* Active Logics Section */}
            {activeLogics.length > 0 && (
              <div className="mb-2">
                <h4 className="text-[10px] font-bold text-[#81c995] uppercase tracking-widest mb-2 flex items-center gap-1.5"><Zap size={12}/> Running Logics</h4>
                <div className="flex flex-col gap-2">
                  {activeLogics.map((logic: any) => (
                    <div key={logic.name} className="flex justify-between items-center p-2.5 bg-[#81c995]/5 border border-[#81c995]/30 rounded-lg">
                      <div className="flex flex-col overflow-hidden">
                        <span className="text-xs font-bold text-[#81c995] truncate">{logic.name}</span>
                        <span className="text-[9px] text-[#9aa0a6] font-mono mt-0.5">Src: {logic.graph_file}.json</span>
                      </div>
                      <button onClick={() => onUndeploy(logic.name)} className="p-1.5 text-[#f28b82] hover:bg-[#f28b82]/10 rounded transition-colors"><ZapOff size={16}/></button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Logic Graphs Section */}
            <div className="flex items-center justify-between mb-1 mt-2">
              <h4 className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest"><Workflow size={12} className="inline mr-1 -mt-0.5"/> Graph Files</h4>
              <div className="flex gap-1.5">
                <button onClick={() => handleTriggerUpload('graph')} className="px-2 py-1 bg-[#303134] hover:bg-[#3c4043] text-[#e8eaed] text-[9px] font-bold uppercase rounded border border-[#3c4043]"><Upload size={10} className="inline mr-1 -mt-0.5"/> Upload</button>
                <button onClick={onNavigateLogic} className="px-2 py-1 bg-[#81c995] hover:bg-[#a8dab5] text-[#202124] text-[9px] font-bold uppercase rounded shadow-md"><Plus size={10} className="inline mr-1 -mt-0.5"/> Create</button>
              </div>
            </div>
            {graphs.map((g: any) => (
              <ResourceCard key={g.name} id={g.name} size={g.size} type="graph" icon={FileJson} onDownload={onDownload} onRemove={onRemove} actionBtn={
                  <>
                    <button onClick={() => onEditGraph(g.name)} className="flex items-center gap-1 text-[10px] font-bold text-[#fcd663] hover:text-[#fde293] bg-[#fcd663]/10 px-2 py-1 rounded transition-colors border border-[#fcd663]/20"><Edit3 size={12}/> Edit</button>
                    <button onClick={() => onDeploy(g.name.replace('.json', ''))} className="flex items-center gap-1 text-[10px] font-bold text-[#81c995] hover:text-[#a8dab5] bg-[#81c995]/10 px-2 py-1 rounded transition-colors border border-[#81c995]/20"><Zap size={12}/> Deploy</button>
                  </>
              } />
            ))}
          </>
        )}

        {subTab === 'files' && (
          <>
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest"><HardDrive size={12} className="inline mr-1 -mt-0.5"/> Models & Assets</h4>
              <button onClick={() => handleTriggerUpload('file')} className="px-2 py-1 bg-[#303134] hover:bg-[#3c4043] text-[#e8eaed] text-[9px] font-bold uppercase rounded border border-[#3c4043]"><Upload size={10} className="inline mr-1 -mt-0.5"/> Upload</button>
            </div>
            {models.map(m => (
              <ResourceCard key={m.id} id={m.id} size={m.size} inRam={m.inRam} type="file" icon={Cpu} onDownload={onDownload} onRemove={onRemove} actionBtn={
                  <button onClick={() => onToggleRam(m.id, m.inRam)} className={`flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded transition-colors border ${m.inRam ? 'text-[#f28b82] hover:text-[#f6aea9] bg-[#f28b82]/10 border-[#f28b82]/20' : 'text-[#8ab4f8] hover:text-[#aecbfa] bg-[#8ab4f8]/10 border-[#8ab4f8]/20'}`}>
                    {m.inRam ? <Square size={10}/> : <Play size={10}/>} {m.inRam ? 'UNLOAD' : 'LOAD'}
                  </button>
              }/>
            ))}
          </>
        )}

        {subTab === 'plugins' && (
          <>
             <div className="flex items-center justify-between mb-1">
              <h4 className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest"><Blocks size={12} className="inline mr-1 -mt-0.5"/> Python Scripts</h4>
              <button onClick={() => handleTriggerUpload('plugin')} className="px-2 py-1 bg-[#303134] hover:bg-[#3c4043] text-[#e8eaed] text-[9px] font-bold uppercase rounded border border-[#3c4043]"><Upload size={10} className="inline mr-1 -mt-0.5"/> Upload</button>
            </div>
            {plugins.map((p: any) => <ResourceCard key={p.name} id={p.name} size={p.size} type="plugin" icon={Blocks} onDownload={onDownload} onRemove={onRemove} />)}
          </>
        )}
      </div>
    </div>
  );
};