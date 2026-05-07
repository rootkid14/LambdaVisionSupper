import { useMemo } from 'react';
import { NodeProps, Handle, Position } from '@xyflow/react';
import { Share2, Zap } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { getPinColor } from '../../utils/FlowUtils';

export const TeleportNodeUI = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData, nodes } = useFlowStore();
  
  const isEntry = data.className === 'PortalInNode'; // Điểm vào (Jump)
  const channelName = data.channel_name || 'Channel_A';

  // Quét danh sách các Channel đang có từ các điểm Vào (Dành cho Portal Out)
  const availableChannels = useMemo(() => {
    const channels = new Set<string>();
    nodes.forEach(n => {
      if (n.data.className === 'PortalInNode') {
        const name = n.data.channel_name || 
                     (n.data.config_fields as any)?.find((f:any) => f.id === 'channel_name')?.default;
        if (name) channels.add(name);
      }
    });
    return Array.from(channels);
  }, [nodes]);

  return (
    // KHUNG NGOÀI: Nằm thẳng (Không xoay), chứa form và Handles để hitbox chuẩn 100%
    <div className="relative w-32 h-24 flex items-center justify-center font-sans">
      
      {/* LÕI TRONG: Hình thoi trang trí (Chỉ mang tính chất hiển thị) */}
      <div className={`
        absolute w-16 h-16 rounded-xl transition-all rotate-45
        ${isEntry ? 'bg-cyan-600 border-cyan-400' : 'bg-indigo-700 border-indigo-400'}
        ${selected ? 'ring-4 ring-white shadow-[0_0_30px_rgba(34,211,238,0.8)]' : 'border-2 shadow-xl'}
      `}></div>

      {/* Icon & Text (Nằm thẳng, đè lên hình thoi) */}
      <div className="relative z-10 flex flex-col items-center gap-0.5 pointer-events-none">
        <div className="text-white drop-shadow-md">
          {isEntry ? <Zap size={22} fill="currentColor" /> : <Share2 size={22} />}
        </div>
        <div className="text-[9px] font-black text-white uppercase tracking-tighter">
            {isEntry ? 'Jump' : 'Land'}
        </div>
      </div>

      {/* Cấu hình Channel (Đẩy xuống dưới cùng) */}
      <div className="absolute -bottom-8 w-full flex justify-center">
        {isEntry ? (
          <input 
            className="nodrag w-24 text-[10px] font-bold bg-slate-900 text-cyan-300 border border-cyan-500 rounded px-1 py-1 text-center focus:outline-none focus:ring-1 focus:ring-cyan-300"
            value={channelName}
            onChange={(e) => updateNodeData(id, { channel_name: e.target.value })}
            placeholder="Channel ID..."
          />
        ) : (
          <select 
            className="nodrag w-24 text-[10px] font-bold bg-slate-900 text-indigo-300 border border-indigo-500 rounded px-1 py-1 text-center focus:outline-none focus:ring-1 focus:ring-indigo-300"
            value={channelName}
            onChange={(e) => updateNodeData(id, { channel_name: e.target.value })}
          >
            <option value="" disabled>-- Select --</option>
            {availableChannels.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        )}
      </div>

      {/* ========================================================== */}
      {/* KHU VỰC CHÂN CẮM (PINS) - TÁCH BIỆT, CÓ NHÃN DỄ NHÌN NHẤT */}
      {/* ========================================================== */}
      
      {isEntry && data.inputs && (
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-center gap-5 -ml-3">
          {data.inputs.map((pin: any) => (
            <div key={pin.id} className="relative flex items-center group">
              {/* Dùng !relative và !transform-none để đè lại CSS absolute mặc định của React Flow */}
              <Handle 
                type="target" 
                position={Position.Left} 
                id={pin.id} 
                className={`!relative !left-0 !transform-none !w-4 !h-4 !border-2 ${getPinColor(pin.dataType)}`}
              />
              {/* Nhãn báo hiệu loại chân cắm */}
              <span className="absolute left-6 text-[8px] font-black tracking-widest text-slate-300 bg-slate-800 border border-slate-600 px-1.5 py-0.5 rounded opacity-80 shadow-md">
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
              <span className="absolute right-6 text-[8px] font-black tracking-widest text-slate-300 bg-slate-800 border border-slate-600 px-1.5 py-0.5 rounded opacity-80 shadow-md">
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