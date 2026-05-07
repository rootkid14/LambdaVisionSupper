import { useMemo, useEffect } from 'react';
import { NodeProps, Handle, Position } from '@xyflow/react';
import { Database, ChevronDown } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { getPinColor } from '../../utils/FlowUtils'; 

export const MemoryReadNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData, nodes } = useFlowStore();

  // 1. Quét toàn bộ Graph để gom các biến từ khối Write
  const availableVars = useMemo(() => {
    const vars = new Set<string>();
    nodes.forEach(n => {
      if (n.data.className === 'InternalMemoryWrite' && n.data.inputs) {
        (n.data.inputs as any).forEach((pin: any) => {
          if (pin.dataType !== 'execute' && pin.label) {
            vars.add(pin.label);
          }
        });
      }
    });
    return Array.from(vars);
  }, [nodes]);

  const selectedVar = data.selectedVar || '';

  // 2. Tự động cập nhật chân Output "value" dựa trên biến đã chọn
  useEffect(() => {
    const targetLabel = selectedVar || 'Select a Variable';
    if (!data.outputs || data.outputs.length === 0 || data.outputs[0].label !== targetLabel) {
      updateNodeData(id, {
        outputs: [{
          id: 'value',
          label: targetLabel,
          dataType: 'any'
        }]
      });
    }
  }, [selectedVar, id, updateNodeData, data.outputs]);

  return (
    <div className={`
      relative flex items-center h-12 min-w-[200px] max-w-[400px] bg-slate-800 rounded-lg p-1.5 transition-all
      ${selected ? 'ring-2 ring-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.6)]' : 'border border-slate-600 shadow-md hover:border-purple-500/80'}
    `}>
      
      {/* 1. KHỐI NHÃN (BADGE) "GET" */}
      <div className="flex flex-none items-center justify-center bg-purple-600 text-white text-[10px] font-black uppercase tracking-wider px-3 h-full rounded-md shadow-sm gap-2">
        <Database size={14} />
        GET
      </div>

      {/* 2. DROPDOWN TỰ CO GIÃN (Flexible Width) */}
      <div className="relative flex-1 ml-2 mr-6 overflow-hidden">
         <select
            className="nodrag w-full bg-slate-900 text-purple-200 text-xs font-bold px-3 py-1.5 rounded border border-slate-600 focus:border-purple-400 focus:outline-none appearance-none cursor-pointer shadow-inner truncate"
            value={selectedVar}
            onChange={(e) => updateNodeData(id, { selectedVar: e.target.value })}
            title={selectedVar || "Chọn biến để đọc"}
          >
            <option value="" disabled className="text-slate-500">Select Variable...</option>
            {availableVars.map(v => (
              <option key={v} value={v} className="bg-slate-800 text-white">{v}</option>
            ))}
          </select>
          {/* Mũi tên chỉ hướng */}
          <ChevronDown size={14} className="text-purple-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>

      {/* 3. LỖ CẮM OUTPUT */}
      {data.outputs?.map((pin: any) => (
        <Handle
          key={pin.id}
          type="source"
          position={Position.Right}
          id={pin.id}
          className={`!w-4 !h-4 !border-2 !-right-2.5 ${getPinColor(pin.dataType)}`}
        />
      ))}
    </div>
  );
};