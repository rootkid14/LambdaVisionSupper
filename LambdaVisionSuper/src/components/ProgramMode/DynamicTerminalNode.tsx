import { useState } from 'react';
import { NodeProps } from '@xyflow/react';
import { Plus, X, Check, ArrowRightLeft } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow';

export const DynamicTerminalNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData } = useFlowStore();

  const [isAdding, setIsAdding] = useState(false);
  const [newPinLabel, setNewPinLabel] = useState('');
  const [newPinId, setNewPinId] = useState('');
  const [newPinType, setNewPinType] = useState('number');

  const isReceiver = data.className === 'ReceivePayloadNode'; // Đẻ ra Output
  const isSender = data.className === 'SendResponseNode';     // Đẻ ra Input

  const handleLabelChange = (val: string) => {
    setNewPinLabel(val);
    const autoId = val.toLowerCase().trim().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
    setNewPinId(autoId);
  };

  const handleSavePin = () => {
    if (!newPinLabel || !newPinId) return;
    const newPin = { id: newPinId, label: newPinLabel, dataType: newPinType };

    if (isReceiver) {
      updateNodeData(id, { outputs: [...(data.outputs || []), newPin] });
    } else if (isSender) {
      updateNodeData(id, { inputs: [...(data.inputs || []), newPin] });
    }

    setIsAdding(false);
    setNewPinLabel('');
    setNewPinId('');
    setNewPinType('number');
  };

  const handleRemovePin = (pinIdToRemove: string, type: 'input' | 'output') => {
    if (type === 'input') {
      updateNodeData(id, { inputs: data.inputs.filter((p: any) => p.id !== pinIdToRemove) });
    } else {
      updateNodeData(id, { outputs: data.outputs.filter((p: any) => p.id !== pinIdToRemove) });
    }
  };

  return (
    <BaseNodeShell
      isError={!!data.errorMessage} errorMessage={data.errorMessage} selected={selected}
      title={data.displayName}
      icon={<ArrowRightLeft size={16} />}
      headerColorClass={isReceiver ? 'bg-purple-700' : 'bg-rose-700'}
      ringColorClass="ring-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]"
    >
      {/* DANH SÁCH INPUTS (Cho SendResponseNode) */}
      {data.inputs?.map((input: any) => (
        <PinRow key={input.id} {...input} type="input" onRemove={(pinId) => handleRemovePin(pinId, 'input')} extraLabel={<span className="text-[10px] text-slate-400 font-mono ml-1">({input.id})</span>} />
      ))}

      {/* DANH SÁCH OUTPUTS (Cho ReceivePayloadNode) */}
      {data.outputs?.map((output: any) => (
        <PinRow key={output.id} {...output} type="output" onRemove={(pinId) => handleRemovePin(pinId, 'output')} extraLabel={<span className="text-[10px] text-slate-400 font-mono mr-1">({output.id})</span>} />
      ))}

      {/* FORM THÊM PIN */}
      {isAdding ? (
        <div className="mt-2 p-2 bg-slate-300 rounded border border-slate-400 flex flex-col gap-2 shadow-inner">
          <input type="text" placeholder="Label" value={newPinLabel} onChange={(e) => handleLabelChange(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400" />
          <input type="text" placeholder="pin_id" value={newPinId} onChange={(e) => setNewPinId(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400 font-mono text-blue-700" />
          <select value={newPinType} onChange={(e) => setNewPinType(e.target.value)} className="nodrag text-xs p-1 rounded border border-slate-400">
            <option value="number">Number</option>
            <option value="string">String</option>
            <option value="boolean">Boolean</option>
            <option value="numpy_array">Numpy Array</option>
            <option value="tensor">Tensor</option>
            <option value="dict">Dictionary</option>
            <option value="list">List</option>
            <option value="json">JSON Object</option>
            <option value="base64">Base64</option>
            <option value="object_ref">Object Ref</option>
            <option value="any">Any</option>
          </select>
          <div className="flex justify-end gap-2 mt-1">
            <button onClick={() => setIsAdding(false)} className="p-1 text-red-600 hover:bg-red-100 rounded"><X size={14}/></button>
            <button onClick={handleSavePin} className="p-1 text-green-700 hover:bg-green-200 rounded font-bold"><Check size={14}/></button>
          </div>
        </div>
      ) : (
        <button onClick={() => setIsAdding(true)} className="mt-2 flex items-center justify-center gap-1 py-1 px-2 text-xs font-bold text-slate-600 bg-slate-300 hover:bg-slate-400 hover:text-slate-800 rounded transition-colors border border-slate-400 border-dashed">
          <Plus size={14} /> Add {isReceiver ? 'Output' : 'Input'}
        </button>
      )}
    </BaseNodeShell>
  );
};