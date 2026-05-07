// components/Nodes/FlowControlNode.tsx
import { NodeProps, Handle, Position } from '@xyflow/react';
import { GitMerge, GitFork } from 'lucide-react';
import { getPinColor } from '../../utils/FlowUtils';

export const FlowControlNode = ({ data, selected }: NodeProps<any>) => {
  const isJoin = data.className === 'JoinNode';

  // Cấu hình giao diện và màu sắc riêng biệt cho từng loại
  const styleConfig = isJoin ? {
    ring: 'ring-teal-400 shadow-[0_0_25px_rgba(45,212,191,0.6)]',
    border: 'border-teal-600',
    iconColor: 'text-teal-400',
    labelColor: 'text-teal-200',
    Icon: GitMerge,
  } : {
    ring: 'ring-amber-500 shadow-[0_0_25px_rgba(245,158,11,0.6)]',
    border: 'border-amber-600',
    iconColor: 'text-amber-500',
    labelColor: 'text-amber-200',
    Icon: GitFork,
  };

  const { Icon } = styleConfig;

  return (
    <div className={`
      relative flex flex-col items-center justify-center w-16 min-h-[100px] py-5 bg-slate-900 rounded-full transition-all
      ${selected ? `ring-2 ${styleConfig.ring}` : `border-2 ${styleConfig.border} shadow-xl`}
    `}>
      {/* Icon lớn và nổi bật hơn */}
      <div className={`${styleConfig.iconColor} mb-2`}>
        <Icon size={24} strokeWidth={2.5} />
      </div>
      
      {/* Label */}
      <div className={`text-[10px] font-black tracking-widest uppercase ${styleConfig.labelColor}`}>
        {data.displayName || data.className.replace('Node', '')}
      </div>

      {/* Render toàn bộ chân Input (bên trái) */}
      {data.inputs?.map((pin: any, idx: number) => (
        <Handle 
          key={pin.id} 
          type="target" 
          position={Position.Left} 
          id={pin.id} 
          style={{ top: `${(idx + 1) * (100 / (data.inputs.length + 1))}%` }}
          className={`!w-4 !h-4 !border-2 !-left-2.5 ${getPinColor(pin.dataType)}`} 
        />
      ))}

      {/* Render toàn bộ chân Output (bên phải) */}
      {data.outputs?.map((pin: any, idx: number) => (
        <Handle 
          key={pin.id} 
          type="source" 
          position={Position.Right} 
          id={pin.id} 
          style={{ top: `${(idx + 1) * (100 / (data.outputs.length + 1))}%` }}
          className={`!w-4 !h-4 !border-2 !-right-2.5 ${getPinColor(pin.dataType)}`} 
        />
      ))}
    </div>
  );
};