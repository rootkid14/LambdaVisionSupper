import { useState, useEffect } from 'react';
import { NodeProps, useUpdateNodeInternals } from '@xyflow/react';
import { Plus, X, Trash2 } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow';

// Dùng hàm sinh ID ngẫu nhiên để tránh trùng lặp Pin ID
const generateShortId = () => Math.random().toString(36).substring(2, 9);

export const DynamicMemoryNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData } = useFlowStore();
  const updateNodeInternals = useUpdateNodeInternals();

  const [isAdding, setIsAdding] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');

  const isError = !!data.errorMessage;
  const isWriteNode = data.className === 'InternalMemoryWrite';

  // Lấy danh sách pin hiện tại dựa vào loại Node
  const memoryPins = isWriteNode ? (data.inputs || []) : (data.outputs || []);

  useEffect(() => {
    updateNodeInternals(id);
  }, [memoryPins.length, id, updateNodeInternals]);

  // Hàm thêm Biến mới
  const handleAddVariable = () => {
    if (newKeyName.trim() === '') return;

    const newPin = {
      id: `mem_pin_${generateShortId()}`, // ID ngẫu nhiên cho Pydantic Schema
      label: newKeyName.trim(),           // Label chính là tên biến người dùng muốn lưu
      dataType: 'any'
    };

    if (isWriteNode) {
      updateNodeData(id, { inputs: [...memoryPins, newPin] });
    } else {
      updateNodeData(id, { outputs: [...memoryPins, newPin] });
    }

    setNewKeyName('');
    setIsAdding(false);
  };

  // Hàm xóa Biến
  const handleDeleteVariable = (pinIdToRemove: string) => {
    const newPins = memoryPins.filter((p: any) => p.id !== pinIdToRemove);
    if (isWriteNode) {
      updateNodeData(id, { inputs: newPins });
    } else {
      updateNodeData(id, { outputs: newPins });
    }
  };

  return (
    <BaseNodeShell
      isError={isError} errorMessage={data.errorMessage} selected={selected}
      title={data.displayName || data.className}
      headerColorClass={isWriteNode ? "bg-red-600" : "bg-purple-500"}
      ringColorClass={isWriteNode ? "ring-red-500" : "ring-purple-500"}
    >
      {/* 1. RENDER PINS (Có nút thùng rác bên cạnh các Pin động) */}
      {data.inputs?.map((pin: any) => (
        <div key={pin.id} className="relative group">
          <PinRow {...pin} type="input" />
          {/* Nút xóa chỉ hiện trên các pin động, không xóa chân execute */}
          {pin.dataType !== 'execute' && isWriteNode && (
            <button onClick={() => handleDeleteVariable(pin.id)}
                    className="absolute right-24 top-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100">
              <Trash2 size={12}/>
            </button>
          )}
        </div>
      ))}

      {data.outputs?.map((pin: any) => (
        <div key={pin.id} className="relative group">
          <PinRow {...pin} type="output" />
          {pin.dataType !== 'execute' && !isWriteNode && (
            <button onClick={() => handleDeleteVariable(pin.id)}
                    className="absolute right-24 top-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100">
              <Trash2 size={12}/>
            </button>
          )}
        </div>
      ))}

      {/* 2. KHU VỰC THÊM BIẾN MỚI */}
      <div className="p-2 bg-slate-100 border-t border-slate-300 rounded-b-md mt-2">
        {isAdding ? (
          <div className="flex flex-col gap-1">
            <input 
              type="text" 
              placeholder="Nhập tên biến (Key)..." 
              value={newKeyName} 
              onChange={e => setNewKeyName(e.target.value)} 
              className="nodrag text-xs p-1 rounded border border-slate-400 w-full"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleAddVariable()}
            />
            <div className="flex justify-end gap-2 mt-1">
              <button onClick={() => setIsAdding(false)} className="p-1 text-red-600 hover:bg-red-100 rounded"><X size={14}/></button>
              <button onClick={handleAddVariable} className="p-1 text-green-700 hover:bg-green-200 rounded font-bold"><Plus size={14}/></button>
            </div>
          </div>
        ) : (
          <button 
            onClick={() => setIsAdding(true)} 
            className="w-full flex items-center justify-center gap-1 py-1 px-2 text-xs font-bold text-slate-600 bg-slate-300 hover:bg-slate-400 rounded transition-colors"
          >
            <Plus size={12}/> Add Variable
          </button>
        )}
      </div>
    </BaseNodeShell>
  );
};