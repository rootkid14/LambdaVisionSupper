import { useMemo, useState, useRef, useEffect } from 'react';
import { NodeProps, Handle, Position, useReactFlow } from '@xyflow/react';
import { Share2, Zap, Crosshair, MapPin } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { getPinColor } from '../../utils/FlowUtils';

export const TeleportNodeUI = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData, nodes } = useFlowStore();
  
  // Hook xịn sò của React Flow để điều khiển Camera
  const { setCenter } = useReactFlow(); 
  
  const [showNav, setShowNav] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isEntry = data.className === 'PortalInNode'; 
  const channelName = data.channel_name !== undefined ? data.channel_name : (isEntry ? 'Channel_A' : '');

  // 1. Quét danh sách các Channel đang có (Dành cho Portal Out lấy list chọn)
  const availableChannels = useMemo(() => {
    const channels = new Set<string>();
    nodes.forEach(n => {
      if (n.data.className === 'PortalInNode') {
        const name = n.data.channel_name || (n.data.config_fields as any)?.find((f:any) => f.id === 'channel_name')?.default;
        if (name) channels.add(name);
      }
    });
    return Array.from(channels);
  }, [nodes]);

  // 2. TÌM CÁC NODE LIÊN KẾT (Để làm menu dịch chuyển)
  const connectedNodes = useMemo(() => {
    if (!channelName) return [];
    return nodes.filter(n => {
      // Đọc channel name của node đang xét một cách an toàn
      const nChannel = n.data.channel_name !== undefined ? n.data.channel_name : (n.data.className === 'PortalInNode' ? 'Channel_A' : '');
      
      if (isEntry) {
        // Nếu mình là Điểm Vào -> Tìm các Điểm Đáp có cùng tên kênh
        return n.data.className === 'PortalOutNode' && nChannel === channelName;
      } else {
        // Nếu mình là Điểm Đáp -> Tìm các Điểm Vào có cùng tên kênh
        return n.data.className === 'PortalInNode' && nChannel === channelName;
      }
    });
  }, [nodes, isEntry, channelName]);

  // 3. HÀM FLY CAMERA ĐẾN NODE ĐÍCH
  const flyToNode = (targetNode: any) => {
    // Lấy tọa độ x, y và cộng thêm một nửa width/height để căn chính giữa tâm Node
    const x = targetNode.position.x + (targetNode.measured?.width || 128) / 2;
    const y = targetNode.position.y + (targetNode.measured?.height || 96) / 2;
    
    // Ra lệnh cho Camera bay đến vị trí đó với hiệu ứng animation 800ms
    setCenter(x, y, { zoom: 1.2, duration: 800 });
    setShowNav(false); // Đóng menu
  };

  // Click ra ngoài để đóng menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowNav(false);
      }
    };
    if (showNav) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showNav]);

  return (
    <div className="relative w-32 h-24 flex items-center justify-center font-sans">
      
      {/* ========================================================== */}
      {/* NÚT NAVIGATOR ĐỊNH VỊ (Tròn, bên phải Jump, bên trái Land) */}
      {/* ========================================================== */}
      {channelName && connectedNodes.length > 0 && (
        <div 
           ref={menuRef}
           className={`absolute top-1/2 -translate-y-1/2 z-50 ${isEntry ? '-right-6' : '-left-6'}`}
        >
          <button 
            onClick={() => setShowNav(!showNav)}
            title={isEntry ? "Xem các điểm đáp (Land)" : "Xem các điểm nhảy (Jump)"}
            className={`
              w-6 h-6 flex items-center justify-center rounded-full border border-slate-500 shadow-lg transition-all
              ${showNav ? 'bg-amber-500 text-white border-amber-300' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'}
            `}
          >
            <Crosshair size={12} className={showNav ? "animate-spin" : ""} />
            
            {/* Chấm đỏ nhỏ báo hiệu số lượng kết nối */}
            <span className="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-red-500 text-[7px] font-bold text-white shadow-sm border border-slate-900">
              {connectedNodes.length}
            </span>
          </button>

          {/* DROPDOWN MENU CHỌN TỌA ĐỘ */}
          {showNav && (
            <div className={`absolute top-full mt-2 w-36 bg-slate-900/95 backdrop-blur-md border border-slate-600 rounded-lg shadow-xl overflow-hidden py-1 animate-in fade-in zoom-in duration-200 ${isEntry ? 'right-0' : 'left-0'}`}>
              <div className="px-2 py-1 border-b border-slate-700 mb-1">
                <span className="text-[9px] font-black uppercase text-slate-400 tracking-wider">
                  {isEntry ? 'Connected Lands' : 'Connected Jumps'}
                </span>
              </div>
              <div className="max-h-32 overflow-y-auto custom-scrollbar">
                {connectedNodes.map((n, idx) => (
                  <button 
                    key={n.id}
                    onClick={() => flyToNode(n)}
                    className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-slate-700 text-left transition-colors group"
                  >
                    <MapPin size={10} className="text-amber-500 group-hover:scale-125 transition-transform" />
                    <div className="flex flex-col">
                      <span className="text-[10px] font-bold text-slate-200">
                        {isEntry ? `Land Point #${idx + 1}` : `Jump Point #${idx + 1}`}
                      </span>
                      <span className="text-[8px] text-slate-500 font-mono">
                        [X: {Math.round(n.position.x)}, Y: {Math.round(n.position.y)}]
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================== */}
      {/* UI CŨ CỦA TELEPORT NODE */}
      {/* ========================================================== */}
      
      {/* LÕI TRONG */}
      <div className={`
        absolute w-16 h-16 rounded-xl transition-all rotate-45
        ${isEntry ? 'bg-cyan-600 border-cyan-400' : 'bg-indigo-700 border-indigo-400'}
        ${selected ? 'ring-4 ring-white shadow-[0_0_30px_rgba(34,211,238,0.8)]' : 'border-2 shadow-xl'}
      `}></div>

      {/* Icon & Text */}
      <div className="relative z-10 flex flex-col items-center gap-0.5 pointer-events-none">
        <div className="text-white drop-shadow-md">
          {isEntry ? <Zap size={22} fill="currentColor" /> : <Share2 size={22} />}
        </div>
        <div className="text-[9px] font-black text-white uppercase tracking-tighter">
            {isEntry ? 'Jump' : 'Land'}
        </div>
      </div>

      {/* Cấu hình Channel */}
      <div className="absolute -bottom-8 w-full flex justify-center">
        {isEntry ? (
          <input 
            className="nodrag w-24 text-[10px] font-bold bg-slate-900 text-cyan-300 border border-cyan-500 rounded px-1 py-1 text-center focus:outline-none focus:ring-1 focus:ring-cyan-300 shadow-md"
            value={channelName}
            onChange={(e) => updateNodeData(id, { channel_name: e.target.value })}
            placeholder="Channel ID..."
          />
        ) : (
          <select 
            className={`nodrag w-24 text-[10px] font-bold bg-slate-900 rounded px-1 py-1 text-center focus:outline-none focus:ring-1 transition-colors cursor-pointer shadow-md
              ${channelName === '' 
                ? 'border border-red-500 text-red-400 focus:ring-red-400 animate-pulse' 
                : 'border border-indigo-500 text-indigo-300 focus:ring-indigo-300'       
              }`}
            value={channelName}
            onChange={(e) => updateNodeData(id, { channel_name: e.target.value })}
          >
            <option value="" disabled>-- Select --</option>
            {availableChannels.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        )}
      </div>

      {/* KHU VỰC CHÂN CẮM (PINS) */}
      {isEntry && data.inputs && (
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-center gap-5 -ml-3">
          {data.inputs.map((pin: any) => (
            <div key={pin.id} className="relative flex items-center group">
              <Handle 
                type="target" 
                position={Position.Left} 
                id={pin.id} 
                className={`!relative !left-0 !transform-none !w-4 !h-4 !border-2 ${getPinColor(pin.dataType)}`}
              />
              <span className="absolute left-6 text-[8px] font-black tracking-widest text-slate-300 bg-slate-800 border border-slate-600 px-1.5 py-0.5 rounded opacity-80 shadow-md pointer-events-none">
                {pin.dataType === 'execute' ? 'EXEC' : 'DATA'}
              </span>
            </div>
          ))}
        </div>
      )}

      {!isEntry && data.outputs && (
        <div className="absolute right-0 top-0 bottom-0 flex flex-col justify-center gap-5 -mr-3">
          {data.outputs.map((pin: any) => (
            <div key={pin.id} className="relative flex items-center justify-end group">
              <span className="absolute right-6 text-[8px] font-black tracking-widest text-slate-300 bg-slate-800 border border-slate-600 px-1.5 py-0.5 rounded opacity-80 shadow-md pointer-events-none">
                {pin.dataType === 'execute' ? 'EXEC' : 'DATA'}
              </span>
              <Handle 
                type="source" 
                position={Position.Right} 
                id={pin.id} 
                className={`!relative !right-0 !transform-none !w-4 !h-4 !border-2 ${getPinColor(pin.dataType)}`}
              />
            </div>
          ))}
        </div>
      )}

    </div>
  );
};