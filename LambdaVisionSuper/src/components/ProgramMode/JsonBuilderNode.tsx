import { useState } from 'react';
import { NodeProps } from '@xyflow/react';
import { Plus, X, Check, Braces } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow';

export const JsonBuilderNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData } = useFlowStore();

  const [isAdding, setIsAdding] = useState(false);
  const [newPinLabel, setNewPinLabel] = useState('');
  const [newPinId, setNewPinId] = useState('');
  const [newPinType, setNewPinType] = useState('string');

  const handleLabelChange = (val: string) => {
    setNewPinLabel(val);
    const autoId = val.toLowerCase().trim().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
    setNewPinId(autoId);
  };

  const handleSavePin = () => {
    if (!newPinLabel || !newPinId) return;
    const newPin = { id: newPinId, label: newPinLabel, dataType: newPinType };
    updateNodeData(id, { inputs: [...(data.inputs || []), newPin] });
    
    setIsAdding(false);
    setNewPinLabel('');
    setNewPinId('');
    setNewPinType('string');
  };

  const handleRemovePin = (pinIdToRemove: string) => {
    updateNodeData(id, { inputs: data.inputs.filter((p: any) => p.id !== pinIdToRemove) });
  };

  const jsonOutput = data.outputs?.find((o: any) => o.id === 'json_data') || { id: 'json_data', label: 'JSON Object', dataType: 'json' };

  return (
    <BaseNodeShell
      isError={!!data.errorMessage} errorMessage={data.errorMessage} selected={selected}
      title={data.displayName} icon={<Braces size={16} />}
      headerColorClass="bg-amber-600" ringColorClass="ring-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.5)]"
    >
      {/* OUTPUT CỐ ĐỊNH (JSON DATA) */}
      <div className="border-b border-slate-300 pb-2 mb-2 bg-slate-300/50 rounded px-2 -mx-1">
        <PinRow {...jsonOutput} type="output" />
      </div>

      {data.inputs?.length > 0 && <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">JSON Keys (Inputs)</span>}

      {/* DANH SÁCH INPUTS */}
      {data.inputs?.map((input: any) => (
        <div key={input.id} className="bg-slate-100 px-1 rounded border border-transparent hover:border-slate-300 transition-colors mb-1 -mx-1">
          <PinRow {...input} type="input" onRemove={() => handleRemovePin(input.id)} extraLabel={<span className="text-[10px] text-slate-500 font-mono ml-2 py-0.5 px-1 bg-slate-200 rounded">"{input.id}"</span>} />
        </div>
      ))}

      {/* FORM THÊM KEY */}
      {isAdding ? (
        <div className="mt-2 p-2 bg-slate-300 rounded border border-slate-400 flex flex-col gap-2 shadow-inner">
          <input type="text" placeholder="Key Label" value={newPinLabel} onChange={(e) => handleLabelChange(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400" />
          <input type="text" placeholder="json_key" value={newPinId} onChange={(e) => setNewPinId(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400 font-mono text-amber-700" />
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
        <button onClick={() => setIsAdding(true)} className="mt-2 flex items-center justify-center gap-1 py-1.5 px-2 text-xs font-bold text-amber-700 bg-amber-100 hover:bg-amber-200 hover:text-amber-900 rounded transition-colors border border-amber-300 border-dashed">
          <Plus size={14} /> Add Key
        </button>
      )}
    </BaseNodeShell>
  );
};