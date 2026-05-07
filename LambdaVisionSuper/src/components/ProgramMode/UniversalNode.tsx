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

  return (
    <BaseNodeShell
      isError={isError} errorMessage={data.errorMessage} selected={selected}
      title={data.displayName || data.className}
      // SỬA DÒNG NÀY: Lấy data.color từ Backend thay vì hardcode
      headerColorClass={data.color || "bg-slate-600"}
      ringColorClass="ring-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
    >
      {/* Config Fields (Đã được dọn dẹp logic lọc mảng) */}
      {(() => {
        const validFields = data.config_fields?.filter((f: any) => f.id !== 'timeout_limit') || [];
        if (validFields.length === 0) return null;

        return (
          <div className="p-2 border-b border-slate-300 bg-slate-100 flex flex-col gap-2">
            {validFields.map((field: any) => (
              <div key={field.id} className="flex flex-col gap-1">
                 <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{field.label || field.id}</label>
                 
                 {field.type === 'text' && (
                   <input type="text" className="nodrag text-xs p-1 rounded border border-slate-400 w-full" value={data[field.id] || field.default || ''} onChange={(e) => handleConfigChange(field.id, e.target.value)} />
                 )}
                 {field.type === 'select' && (
                   <select className="nodrag text-xs p-1 rounded border border-slate-400 w-full" value={data[field.id] || field.default || ''} onChange={(e) => handleConfigChange(field.id, e.target.value)}>
                     {field.options?.map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
                   </select>
                 )}
                 {field.type === 'number' && (
                    <input type="number" step="any" className="nodrag text-xs p-1 rounded border border-slate-400 w-full" value={data[field.id] ?? field.default ?? ''} 
                           onChange={(e) => {
                               const rawValue = e.target.value;
                               handleConfigChange(field.id, rawValue === '' ? '' : Number(rawValue));
                           }} />
                  )}
                 {['server_pool_dropdown', 'device_pool_dropdown', 'active_logic_dropdown'].includes(field.type) && (
                   <SmartDropdown type={field.type} id={field.id} value={data[field.id]} onChange={(val) => handleConfigChange(field.id, val)} />
                 )}
              </div>
            ))}
          </div>
        );
      })()}

      {/* Pins */}
      {data.inputs?.map((pin: any) => <PinRow key={pin.id} {...pin} type="input" />)}
      {data.outputs?.map((pin: any) => <PinRow key={pin.id} {...pin} type="output" />)}
    </BaseNodeShell>
  );
};