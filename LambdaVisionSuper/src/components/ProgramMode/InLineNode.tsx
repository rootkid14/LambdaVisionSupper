// components/Nodes/InlineNode.tsx
import { NodeProps, Handle, Position } from '@xyflow/react';
import { useFlowStore } from '../../Stores/FlowStore';
import { getPinColor } from '../../utils/FlowUtils'; 

export const InlineNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData } = useFlowStore();

  const handleInlineChange = (e: any) => {
    // Chỉ quan tâm checkbox hoặc lấy thẳng text
    const val = data.inlineInputType === 'checkbox' ? e.target.checked : e.target.value;
    updateNodeData(id, { inlineValue: val });
  };

  return (
    <div className={`
      relative flex items-center min-w-[120px] h-8 bg-slate-800 rounded-full pr-1 pl-3 transition-all
      ${selected ? 'ring-2 ring-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]' : 'border border-slate-600 shadow-md'}
    `}>
      <div className="text-[10px] font-bold text-slate-300 uppercase tracking-wider mr-2 whitespace-nowrap">
        {data.displayName || data.className}
      </div>

      <div className="flex-1 flex justify-end">
        {data.inlineInputType === 'checkbox' ? (
          <input 
            type="checkbox" 
            checked={!!data.inlineValue} 
            onChange={handleInlineChange} 
            className="nodrag w-4 h-4 cursor-pointer accent-blue-500 mr-2" 
          />
        ) : (
          <input
            // Ép thành text để dập tắt sự can thiệp của trình duyệt
            type="text" 
            inputMode={data.inlineInputType === 'number' ? "decimal" : undefined}
            value={data.inlineValue ?? ''} 
            onChange={handleInlineChange}
            placeholder="..."
            className="nodrag w-16 bg-slate-900/50 text-white text-xs font-mono px-2 py-1 rounded-full border border-slate-700 focus:border-blue-400 focus:outline-none text-right"
          />
        )}
      </div>

      {data.outputs?.map((pin: any) => (
        <Handle 
          key={pin.id} 
          type="source" 
          position={Position.Right} 
          id={pin.id} 
          className={`!w-3 !h-3 !border-2 !-right-1.5 ${getPinColor(pin.dataType)}`} 
        />
      ))}
    </div>
  );
};