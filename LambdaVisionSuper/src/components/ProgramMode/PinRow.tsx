// components/Nodes/PinRow.tsx
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Trash2 } from 'lucide-react';
import { getPinColor } from '../../utils/FlowUtils';

interface PinRowProps {
  id: string;
  label: string;
  dataType: string;
  type: 'input' | 'output';
  optional?: boolean;
  onRemove?: (id: string) => void;
  extraLabel?: React.ReactNode;
}

export const PinRow = ({ id, label, dataType, type, optional, onRemove, extraLabel }: PinRowProps) => {
  const isInput = type === 'input';
  
  return (
    <div className={`relative flex items-center h-6 group ${isInput ? 'justify-start' : 'justify-end'}`}>
      {/* Nút xóa (Hiển thị khi hover, nếu có onRemove) */}
      {!isInput && onRemove && (
         <button onClick={() => onRemove(id)} className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity absolute left-0 z-10">
           <Trash2 size={14} />
         </button>
      )}

      {isInput && <Handle type="target" position={Position.Left} id={id} className={`!w-4 !h-4 !border-2 !-left-[21px] ${getPinColor(dataType)}`} />}
      
      <div className="flex items-center mx-1">
        <span className={`text-sm font-semibold ${optional ? 'text-slate-500 italic' : 'text-slate-700'}`}>
          {label}
        </span>
        {extraLabel}
      </div>

      {!isInput && <Handle type="source" position={Position.Right} id={id} className={`!w-4 !h-4 !border-2 !-right-[21px] ${getPinColor(dataType)}`} />}
      
      {isInput && onRemove && (
         <button onClick={() => onRemove(id)} className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-opacity absolute right-0 z-10">
           <Trash2 size={14} />
         </button>
      )}
    </div>
  );
};