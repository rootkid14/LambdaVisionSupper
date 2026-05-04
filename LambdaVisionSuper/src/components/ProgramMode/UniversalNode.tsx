// components/Nodes/UniversalNode.tsx
import { NodeProps } from '@xyflow/react';
import { useFlowStore } from '../../Stores/FlowStore';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow';
import { SmartDropdown } from './SmartDropdown';

export const UniversalNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData } = useFlowStore();
  const isError = !!data.errorMessage;

  const handleConfigChange = (fieldId: string, value: any) => updateNodeData(id, { [fieldId]: value });
  const handleInlineChange = (e: any) => {
    let val = e.target.value;
    if (data.inlineInputType === 'number') {
        val = val === '' ? '' : Number(val);
      }
    if (data.inlineInputType === 'checkbox') val = e.target.checked;
    updateNodeData(id, { inlineValue: val });
  };

  return (
    <BaseNodeShell
      isError={isError} errorMessage={data.errorMessage} selected={selected}
      title={data.displayName || data.className}
      headerColorClass="bg-slate-600"
      ringColorClass="ring-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
    >
      {/* Inline Input (Type 2) */}
      {data.inlineInputType && (
        <div className="mb-2">
          {data.inlineInputType === 'checkbox' ? (
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={!!data.inlineValue} onChange={handleInlineChange} className="nodrag w-4 h-4" />
              <span className="text-xs text-slate-600">True</span>
            </label>
          ) : (
            <input
              type={data.inlineInputType} value={data.inlineValue ?? ''} onChange={handleInlineChange}
              className="nodrag w-full bg-slate-100 text-slate-800 text-sm font-mono px-2 py-1.5 rounded border border-slate-400 focus:outline-none"
            />
          )}
        </div>
      )}

      {/* Config Fields */}
      {data.config_fields?.length > 0 && (
        <div className="flex flex-col gap-2 p-3 pb-1 border-b border-slate-300/50 bg-slate-200/50 -mx-3 mb-2">
          {data.config_fields.map((field: any) => (
             <div key={field.name} className="flex flex-col gap-1">
               <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{field.label || field.name}</label>
               {field.type === 'text' && (
                 <input type="text" className="nodrag text-xs p-1 rounded border border-slate-400 w-full" value={data[field.name] || field.default || ''} onChange={(e) => handleConfigChange(field.name, e.target.value)} />
               )}
               {field.type === 'select' && (
                 <select className="nodrag text-xs p-1 rounded border border-slate-400 w-full" value={data[field.name] || field.default || ''} onChange={(e) => handleConfigChange(field.name, e.target.value)}>
                   {field.options?.map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
                 </select>
               )}
               {['server_pool_dropdown', 'device_pool_dropdown', 'active_logic_dropdown'].includes(field.type) && (
                 <SmartDropdown type={field.type} id={field.name} value={data[field.name]} onChange={(val) => handleConfigChange(field.name, val)} />
               )}
             </div>
          ))}
        </div>
      )}

      {/* Pins */}
      {data.inputs?.map((pin: any) => <PinRow key={pin.id} {...pin} type="input" />)}
      {data.outputs?.map((pin: any) => <PinRow key={pin.id} {...pin} type="output" />)}
    </BaseNodeShell>
  );
};