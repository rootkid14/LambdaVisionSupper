import React from 'react';
import { NodeProps, useReactFlow } from '@xyflow/react'; 
import { SmartDropdown } from './SmartDropdown';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow'; // BƯỚC 1: IMPORT PINROW CHUẨN

export type DataType = 'boolean' | 'number' | 'string' | 'numpy_array' | 'tensor' | 'any' | "object_ref" | "json" | "dict" | "list" | "base64";

export interface PinData {
  id: string;
  label: string;
  dataType: DataType;
  optional?: boolean;
}

export interface ConfigField {
  id: string;
  label: string;
  type: string;
  default?: any;
  options?: string[];
}

export interface UniversalNodeData {
  className: string; 
  nodeType: string;
  displayName: string;
  inputs: PinData[];
  outputs: PinData[];
  errorMessage?: string; 
  inlineInputType?: 'text' | 'number' | 'checkbox'; 
  inlineValue?: string | number | boolean;       
  config_fields?: ConfigField[];
  [key: string]: any;
}

// BƯỚC 2: ĐÃ XÓA BỎ HOÀN TOÀN HÀM getPinColor CŨ GÂY XUNG ĐỘT Ở ĐÂY!

export const UniversalNode = ({ id, data, selected }: NodeProps<any>) => {
  const isError = !!data.errorMessage;
  const { updateNodeData } = useReactFlow();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val: any = e.target.value;
    if (data.inlineInputType === 'number') val = Number(val);
    if (data.inlineInputType === 'checkbox') val = e.target.checked;
    updateNodeData(id, { inlineValue: val });
  };

  const handleConfigChange = (fieldId: string, value: any) => {
    updateNodeData(id, { [fieldId]: value });
  };

  const nodeColor = data.color || 'bg-slate-600'; 

  return (
    <BaseNodeShell
      isError={isError} 
      errorMessage={data.errorMessage} 
      selected={selected}
      title={data.displayName || data.className}
      headerColorClass={nodeColor}
      ringColorClass="ring-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
    >
      {/* Inline Inputs */}
      {data.inlineInputType && (
        <div className="mb-2">
          {data.inlineInputType === 'checkbox' ? (
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={!!data.inlineValue} onChange={handleInputChange} className="nodrag w-4 h-4" />
              <span className="text-xs text-slate-600">True</span>
            </label>
          ) : (
            <input
              type={data.inlineInputType}
              value={data.inlineValue ?? ''}
              onChange={handleInputChange}
              className="nodrag w-full bg-slate-100 text-slate-800 text-sm font-mono px-2 py-1.5 rounded border border-slate-400 focus:outline-none"
            />
          )}
        </div>
      )}

      {/* Config Fields */}
      {data.config_fields && data.config_fields.length > 0 && (
        <div className="flex flex-col gap-2 p-3 pb-1 border-b border-slate-300/50 bg-slate-200/50 -mx-3 mb-2">
          {data.config_fields.map((field: ConfigField) => (
            <div key={field.id} className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{field.label}</label>
              {field.type === 'text' && (
                <input
                  type="text"
                  className="nodrag text-xs p-1 rounded border border-slate-400 w-full"
                  value={data[field.id] || field.default || ''}
                  onChange={(e) => handleConfigChange(field.id, e.target.value)}
                />
              )}
              {field.type === 'select' && field.options && (
                <select
                  className="nodrag text-xs p-1 rounded border border-slate-400 w-full"
                  value={data[field.id] || field.default || ''}
                  onChange={(e) => handleConfigChange(field.id, e.target.value)}
                >
                  {field.options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                </select>
              )}
              {['server_pool_dropdown', 'device_pool_dropdown', 'active_logic_dropdown'].includes(field.type) && (
                <SmartDropdown
                  type={field.type}
                  id={field.id}
                  value={data[field.id]}
                  onChange={(val) => handleConfigChange(field.id, val)}
                />
              )}
              {field.type === 'number' && (
                <input
                  type="number"
                  step="any"
                  className="nodrag text-xs p-1 rounded border border-slate-400 w-full"
                  value={data[field.id] ?? field.default ?? ''}
                  onChange={(e) => {
                      const rawValue = e.target.value;
                      handleConfigChange(field.id, rawValue === '' ? '' : Number(rawValue));
                  }}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* BƯỚC 3: SỬ DỤNG COMPONENT PINROW CHUẨN */}
      {data.inputs?.map((pin: PinData) => (
         <PinRow key={pin.id} {...pin} type="input" />
      ))}
      {data.outputs?.map((pin: PinData) => (
         <PinRow key={pin.id} {...pin} type="output" />
      ))}
    </BaseNodeShell>
  );
};