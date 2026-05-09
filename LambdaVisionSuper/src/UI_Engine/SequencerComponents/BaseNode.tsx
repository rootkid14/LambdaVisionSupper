// src/Sequencer/BaseNode.tsx
import React from 'react';
import { Handle, Position } from '@xyflow/react';

interface BaseNodeProps {
  id: string;
  selected?: boolean;
  data: any;
  title: string;
  icon: React.ReactNode;
  headerColor: string;
  children?: React.ReactNode;
  inputs?: number;
  outputs?: number;
}

export const BaseNode = ({ selected, title, icon, headerColor, children, inputs = 1, outputs = 1 }: BaseNodeProps) => {
  return (
    <div className={`
      min-w-[180px] bg-[#606060] rounded-md border transition-all duration-200
      ${selected ? 'border-blue-500 ring-2 ring-blue-500/20 shadow-lg' : 'border-slate-300 shadow-sm'}
      hover:shadow-md
    `}>
      {/* Input Handles */}
      {Array.from({ length: inputs }).map((_, i) => (
        <Handle 
          key={`in-${i}`} type="target" position={Position.Left} id={`in-${i}`}
          className="w-2.5 h-2.5 bg-slate-400 border-white"
          style={{ top: `${(i + 1) * (100 / (inputs + 1))}%` }}
        />
      ))}

      {/* Header */}
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-t-[5px] text-white ${headerColor}`}>
        <span className="opacity-90">{icon}</span>
        <span className="text-[11px] font-bold uppercase tracking-tight truncate">{title}</span>
      </div>

      {/* Body */}
      <div className="p-3 text-slate-700">
        {children}
      </div>

      {/* Output Handles */}
      {Array.from({ length: outputs }).map((_, i) => (
        <Handle 
          key={`out-${i}`} type="source" position={Position.Right} id={`out-${i}`}
          className="w-2.5 h-2.5 bg-blue-500 border-white"
          style={{ top: `${(i + 1) * (100 / (outputs + 1))}%` }}
        />
      ))}
    </div>
  );
};