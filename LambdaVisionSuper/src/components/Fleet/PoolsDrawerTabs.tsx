import React, { useState, useRef } from 'react';
import { 
  Trash2, Activity, Plus, Check, HardDrive, Upload, Cpu, 
  Play, Square, FileJson, Workflow, Blocks, Download, Zap, ZapOff 
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

const ResourceCard = ({ 
  id, size, inRam, type, icon: Icon, onDownload, onRemove, actionBtn 
}: { 
  id: string, size: number, inRam?: boolean, type: ResourceType, 
  icon: any, onDownload: (id: string, type: ResourceType) => void, onRemove: (id: string, type: ResourceType) => void, actionBtn?: React.ReactNode 
}) => {
  const formatBytes = (bytes: number) => bytes > 1048576 ? (bytes / 1048576).toFixed(2) + ' MB' : (bytes / 1024).toFixed(2) + ' KB';

  return (
    <div className="flex flex-col p-3 bg-[#28292c] rounded-xl border border-[#3c4043] hover:border-[#8ab4f8]/50 transition-colors group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex flex-col gap-1 pr-4">
          <span className="text-sm font-bold text-[#e8eaed] flex items-center gap-2 truncate">
            <Icon size={16} className="text-[#8ab4f8] shrink-0"/> 
            <span className="truncate">{id}</span>
          </span>
          <span className="text-xs text-[#9aa0a6] font-mono">{formatBytes(size)}</span>
        </div>
        {inRam !== undefined && (
          inRam 
            ? <span className="shrink-0 bg-[#81c995]/10 text-[#81c995] border border-[#81c995]/20 px-2 py-1 rounded-md uppercase text-[9px] font-extrabold flex items-center gap-1"><Play size={10}/> IN RAM</span> 
            : <span className="shrink-0 bg-[#171717] text-[#9aa0a6] border border-[#3c4043] px-2 py-1 rounded-md uppercase text-[9px] font-extrabold flex items-center gap-1"><HardDrive size={10}/> DISK</span>
        )}
      </div>
      <div className="flex items-center justify-between pt-3 border-t border-[#3c4043]">
        <div className="flex gap-2">
          <button onClick={() => onDownload(id, type)} className="flex items-center gap-1.5 text-xs font-bold text-[#9aa0a6] hover:text-[#8ab4f8] bg-[#202124] hover:bg-[#303134] px-3 py-1.5 rounded-lg transition-colors border border-[#3c4043]"><Download size={14}/> Tải về</button>
          {actionBtn}
        </div>
        {/* NÚT XÓA TÀI NGUYÊN */}
        <button onClick={() => onRemove(id, type)} className="text-[#5f6368] hover:text-[#f28b82] p-1.5 rounded-lg hover:bg-[#f28b82]/10 transition-all opacity-50 group-hover:opacity-100">
          <Trash2 size={16}/>
        </button>
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

export const ResourcesTab = ({ 
  hardware, 
  resourceInfo, 
  onUpload, 
  onDownload, 
  onRemove, 
  onDeploy, 
  onUndeploy, 
  onNavigateLogic,
  onToggleRam
}: any) => {
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadTargetType, setUploadTargetType] = useState<ResourceType | null>(null);

  const handleTriggerUpload = (type: ResourceType) => {
    setUploadTargetType(type);
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && uploadTargetType) {
      await onUpload(e.target.files[0], uploadTargetType);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setUploadTargetType(null);
    }
  };

  // --- XỬ LÝ MAPPING DỮ LIỆU ---
  const filesObj = resourceInfo?.files || {};
  const pluginsArray = resourceInfo?.plugins || [];
  
  // 1. Files/Models vẫn là Object {filename: {size, inram}}
  const models = Object.entries(filesObj).map(([id, info]: any) => ({ id, size: info.size, inRam: info.inram }));
  
  // 2. CẬP NHẬT: Graphs bây giờ là Array [{name, size}] từ BE trả về
  const graphs = resourceInfo?.graphs || [];
  
  // 3. MỚI: Danh sách Logic Objects đang chạy trên RAM
  const activeLogics = resourceInfo?.active_logics || [];

  return (
    <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-right-4 duration-300 pb-10">
      <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />

      {/* 1. NODE PERFORMANCE */}
      <div>
        <h3 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest mb-3 flex items-center gap-2"><Activity size={14}/> Node Performance</h3>
        <div className="p-4 bg-[#28292c] rounded-xl border border-[#3c4043] flex flex-col gap-4 shadow-sm">
          <MiniProgressBar label="CPU Core" percent={hardware?.cpu_percent ?? 0} colorClass={(hardware?.cpu_percent ?? 0) > 80 ? 'bg-[#fcd663]' : 'bg-[#8ab4f8]'} />
          <MiniProgressBar label="RAM System" percent={hardware?.ram_percent ?? 0} colorClass={(hardware?.ram_percent ?? 0) > 80 ? 'bg-[#f28b82]' : 'bg-[#81c995]'} extraText={`${hardware?.ram_used_mb ?? 0}MB / ${hardware?.ram_total_mb ?? 0}MB`} />
        </div>
      </div>

      {/* 2. MỚI: ACTIVE LOGIC OBJECTS (Các thực thể đang chạy) */}
      <div>
        <h3 className="text-xs font-bold text-[#81c995] uppercase tracking-widest mb-4 flex items-center gap-2">
          <Zap size={14}/> Active Logic Objects
        </h3>
        <div className="flex flex-col gap-3">
          {activeLogics.map((logic: any) => (
            <div key={logic.name} className="flex flex-col p-3 bg-[#81c995]/5 border border-[#81c995]/20 rounded-xl group transition-all hover:border-[#81c995]/50">
              <div className="flex items-start justify-between">
                <div className="flex flex-col gap-1 overflow-hidden">
                  <span className="text-sm font-bold text-[#81c995] truncate flex items-center gap-2">
                    <Cpu size={14}/> {logic.name}
                  </span>
                  <span className="text-[10px] text-[#9aa0a6] font-mono bg-[#171717] px-2 py-0.5 rounded self-start border border-[#3c4043]">
                    Source: {logic.graph_file}.json
                  </span>
                </div>
                {/* NÚT UNDEPLOY */}
                <button 
                  onClick={() => onUndeploy(logic.name)}
                  className="p-2 text-[#f28b82] hover:bg-[#f28b82]/10 rounded-lg transition-colors"
                  title="Undeploy from RAM"
                >
                  <ZapOff size={18}/>
                </button>
              </div>
            </div>
          ))}
          {activeLogics.length === 0 && (
            <div className="text-[11px] text-[#5f6368] italic text-center py-4 border border-dashed border-[#3c4043] rounded-xl bg-[#171717]">
              Không có Logic Object nào đang chạy
            </div>
          )}
        </div>
      </div>

      {/* 3. LOGIC GRAPHS (Files trên đĩa) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest flex items-center gap-2"><Workflow size={14}/> Logic Graphs</h3>
          <div className="flex gap-2">
            <button onClick={() => handleTriggerUpload('graph')} className="flex items-center gap-1.5 px-3 py-1.5 bg-[#303134] hover:bg-[#3c4043] text-[#e8eaed] text-[10px] font-bold uppercase rounded-lg border border-[#3c4043] transition-colors"><Upload size={14}/> Upload</button>
            <button onClick={onNavigateLogic} className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8ab4f8] hover:bg-[#aecbfa] text-[#202124] text-[10px] font-bold uppercase rounded-lg shadow-md transition-colors"><Plus size={14}/> Create</button>
          </div>
        </div>
        <div className="flex flex-col gap-3">
          {graphs.map((g: any) => (
            <ResourceCard 
              key={g.name} id={g.name} size={g.size} type="graph" 
              icon={FileJson} onDownload={onDownload} onRemove={onRemove}
              // NÚT DEPLOY ĐỂ BIẾN FILE THÀNH OBJECT TRÊN RAM
              actionBtn={
                <button 
                  onClick={() => onDeploy(g.name.replace('.json', ''))} 
                  className="flex items-center gap-1.5 text-xs font-bold text-[#81c995] hover:text-[#a8dab5] bg-[#81c995]/10 px-3 py-1.5 rounded-lg transition-colors border border-[#81c995]/20"
                >
                  <Zap size={14}/> DEPLOY
                </button>
              }
            />
          ))}
          {graphs.length === 0 && <div className="text-xs text-[#5f6368] italic text-center p-4 border border-dashed border-[#3c4043] rounded-xl bg-[#171717]">No Graph File</div>}
        </div>
      </div>

      {/* 4. AI MODELS & FILES */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest flex items-center gap-2"><HardDrive size={14}/> AI Models & Files</h3>
          <button onClick={() => handleTriggerUpload('file')} className="flex items-center gap-1.5 px-3 py-1.5 bg-[#303134] hover:bg-[#3c4043] text-[#e8eaed] text-[10px] font-bold uppercase rounded-lg border border-[#3c4043] transition-colors"><Upload size={14}/> Upload</button>
        </div>
        <div className="flex flex-col gap-3">
          {models.map(m => (
            <ResourceCard 
              key={m.id} id={m.id} size={m.size} inRam={m.inRam} type="file" 
              icon={Cpu} onDownload={onDownload} onRemove={onRemove}
              actionBtn={
                // NÚT BẤM THÔNG MINH: ĐỔI TRẠNG THÁI VÀ GỌI HÀM
                <button 
                  onClick={() => onToggleRam(m.id, m.inRam)} 
                  className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors border ${
                    m.inRam 
                      ? 'text-[#f28b82] hover:text-[#f6aea9] bg-[#f28b82]/10 hover:bg-[#f28b82]/20 border-[#f28b82]/20' // Đang trong RAM -> Nút Unload màu Đỏ
                      : 'text-[#8ab4f8] hover:text-[#aecbfa] bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 border-[#8ab4f8]/20' // Đang trên Disk -> Nút Load màu Xanh
                  }`}
                  title={m.inRam ? "Unload from Memory" : "Load into Memory"}
                >
                  {m.inRam ? <Square size={14}/> : <Play size={14}/>} 
                  {m.inRam ? 'UNLOAD RAM' : 'LOAD TO RAM'}
                </button>
              }
            />
          ))}
        </div>
      </div>

      {/* 5. PLUGINS */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest flex items-center gap-2"><Blocks size={14}/> External Plugins</h3>
          <button onClick={() => handleTriggerUpload('plugin')} className="flex items-center gap-1.5 px-3 py-1.5 bg-[#303134] hover:bg-[#3c4043] text-[#e8eaed] text-[10px] font-bold uppercase rounded-lg border border-[#3c4043] transition-colors"><Upload size={14}/> Upload .py</button>
        </div>
        <div className="flex flex-col gap-3">
          {pluginsArray.map((p: any) => (
            <ResourceCard key={p.name} id={p.name} size={p.size} type="plugin" icon={Blocks} onDownload={onDownload} onRemove={onRemove} />
          ))}
        </div>
      </div>

    </div>
  );
};