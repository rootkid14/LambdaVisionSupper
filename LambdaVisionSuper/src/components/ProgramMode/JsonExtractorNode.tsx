import { useState } from 'react';
import { NodeProps } from '@xyflow/react';
import { Plus, X, Check, FileJson } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow';

export const JsonExtractorNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData } = useFlowStore();

  const [isAdding, setIsAdding] = useState(false);
  const [newPinLabel, setNewPinLabel] = useState('');
  const [newPinId, setNewPinId] = useState(''); // Đây là JSON Path (VD: user.id)
  const [newPinType, setNewPinType] = useState('string');

  const handleSavePin = () => {
    if (!newPinLabel || !newPinId) return;
    const newPin = { id: newPinId, label: newPinLabel, dataType: newPinType };
    updateNodeData(id, { outputs: [...(data.outputs || []), newPin] });
    
    setIsAdding(false);
    setNewPinLabel('');
    setNewPinId('');
    setNewPinType('string');
  };

  const handleRemovePin = (pinIdToRemove: string) => {
    updateNodeData(id, { outputs: data.outputs.filter((p: any) => p.id !== pinIdToRemove) });
  };

  const handleConfigChange = (fieldId: string, value: any) => updateNodeData(id, { [fieldId]: value });

  return (
    <BaseNodeShell
      isError={!!data.errorMessage} errorMessage={data.errorMessage} selected={selected} minW="min-w-[280px]"
      title={data.displayName} icon={<FileJson size={16} />}
      headerColorClass="bg-fuchsia-600" ringColorClass="ring-fuchsia-500 shadow-[0_0_15px_rgba(217,70,239,0.5)]"
    >
      {/* CONFIG FIELDS (Missing key handling...) */}
      {data.config_fields?.length > 0 && (
        <div className="flex flex-col gap-2 pb-2 mb-1 border-b border-slate-300/50">
          {data.config_fields.map((field: any) => (
            <div key={field.name || field.id} className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{field.label}</label>
              {field.type === 'select' && (
                <select className="nodrag text-xs p-1 rounded border border-slate-400 w-full bg-white" value={data[field.name || field.id] || field.default || ''} onChange={(e) => handleConfigChange(field.name || field.id, e.target.value)}>
                  {field.options?.map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
                </select>
              )}
            </div>
          ))}
        </div>
      )}
      
      {/* INPUT CỐ ĐỊNH */}
      <div className="border-b border-slate-300 pb-2 mb-2 bg-slate-300/50 rounded px-2 -mx-1">
        {data.inputs?.map((input: any) => <PinRow key={input.id} {...input} type="input" />)}
      </div>

      {data.outputs?.length > 0 && <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider text-right">Extracted Paths</span>}

      {/* DANH SÁCH OUTPUTS */}
      {data.outputs?.map((output: any) => (
        <div key={output.id} className="bg-slate-100 px-1 rounded border border-transparent hover:border-slate-300 transition-colors mb-1 -mx-1">
           <PinRow {...output} type="output" onRemove={() => handleRemovePin(output.id)} extraLabel={<span className="text-[10px] text-fuchsia-700 font-mono mr-2 py-0.5 px-1 bg-fuchsia-100 border border-fuchsia-200 rounded truncate max-w-[120px]" title={output.id}>{output.id}</span>}/>
        </div>
      ))}

      {/* FORM THÊM PATH */}
      {isAdding ? (
        <div className="mt-2 p-2 bg-slate-300 rounded border border-slate-400 flex flex-col gap-2 shadow-inner">
          <input type="text" placeholder="Label" value={newPinLabel} onChange={(e) => setNewPinLabel(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400" />
          <input type="text" placeholder="Path (Ex: data.sensor.temp)" value={newPinId} onChange={(e) => setNewPinId(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400 font-mono text-fuchsia-700" />
          <select value={newPinType} onChange={(e) => setNewPinType(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400">
            <option value="number">Number</option>
            <option value="string">String</option>
            <option value="boolean">Boolean</option>
            <option value="json">JSON Object</option>
            <option value="any">Any</option>
          </select>
          <div className="flex justify-end gap-2 mt-1">
            <button onClick={() => setIsAdding(false)} className="p-1 text-red-600 hover:bg-red-100 rounded"><X size={14}/></button>
            <button onClick={handleSavePin} className="p-1 text-green-700 hover:bg-green-200 rounded font-bold"><Check size={14}/></button>
          </div>
        </div>
      ) : (
        <button onClick={() => setIsAdding(true)} className="mt-2 flex items-center justify-center gap-1 py-1.5 px-2 text-xs font-bold text-fuchsia-700 bg-fuchsia-100 hover:bg-fuchsia-200 hover:text-fuchsia-900 rounded transition-colors border border-fuchsia-300 border-dashed">
          <Plus size={14} /> Add Extract Path
        </button>
      )}
    </BaseNodeShell>
  );
};