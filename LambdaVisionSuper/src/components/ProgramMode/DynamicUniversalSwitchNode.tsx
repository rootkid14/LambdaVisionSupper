// src/components/ProgramMode/DynamicSwitchNode.tsx
import { useState, useEffect } from 'react';
import { NodeProps, useUpdateNodeInternals } from '@xyflow/react';
import { Plus, X, Trash2 } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow';
import { SmartDropdown } from './SmartDropdown';

export const DynamicSwitchNode = ({ id, data, selected }: NodeProps<any>) => {
  const { updateNodeData } = useFlowStore();

  const updateNodeInternals = useUpdateNodeInternals();
  
  const [isAdding, setIsAdding] = useState(false);
  const [newCaseVal, setNewCaseVal] = useState('');

  const isError = !!data.errorMessage;
  const cases: any[] = data.cases || [];

  useEffect(() => {
    updateNodeInternals(id);
  }, [data.outputs?.length, id, updateNodeInternals]);

  // Hàm thay đổi cấu hình dropdown (kiểu so sánh: String, Number, Boolean)
  const handleConfigChange = (fieldId: string, value: any) => {
    updateNodeData(id, { [fieldId]: value });
  };

  // Hàm thêm Case mới
  const handleAddCase = () => {
    if (newCaseVal.trim() === '') return;
    
    const newCases = [...cases, newCaseVal];
    rebuildOutputs(newCases);
    setNewCaseVal('');
    setIsAdding(false);
  };

  // Hàm xóa Case
  const handleDeleteCase = (indexToRemove: number) => {
    const newCases = cases.filter((_, idx) => idx !== indexToRemove);
    rebuildOutputs(newCases);
    // Lưu ý: React Flow tự động ngắt các sợi dây nếu Handle ID không còn tồn tại!
  };

  // Hàm tự động tính toán lại danh sách cổng (Outputs) dựa trên mảng Cases
  const rebuildOutputs = (currentCases: any[]) => {
    const newOutputs = currentCases.map((c, index) => ({
      id: `out_case_${index}`, // BẮT BUỘC DÙNG INDEX ĐỂ PYTHON KHÔNG LỖI CÚ PHÁP
      label: `Case: ${c}`,
      dataType: 'execute'
    }));
    
    // Luôn luôn chèn chân Default ở cuối cùng
    newOutputs.push({
      id: 'out_default',
      label: 'Default',
      dataType: 'execute'
    });

    // Cập nhật vào Store
    updateNodeData(id, { cases: currentCases, outputs: newOutputs });
  };

  return (
    <BaseNodeShell
      isError={isError} errorMessage={data.errorMessage} selected={selected}
      title={data.displayName || data.className}
      headerColorClass="bg-red-700"
      ringColorClass="ring-red-500 shadow-[0_0_15px_rgba(220,38,38,0.5)]"
    >
      {/* 1. RENDER DROP-DOWN CẤU HÌNH (Kiểu so sánh) */}
      {data.config_fields && data.config_fields.length > 0 && (
        <div className="p-2 border-b border-slate-300 bg-slate-100 flex flex-col gap-2">
          
          {/* SỬA Ở ĐÂY: Thêm .filter() để loại bỏ timeout_limit */}
          {data.config_fields
            .filter((field: any) => field.id !== 'timeout_limit') 
            .map((field: any) => (
             <div key={field.id} className="flex flex-col gap-1">
               <span className="text-[10px] font-bold text-slate-500 uppercase">{field.label}</span>
               <select 
                 className="nodrag text-xs p-1 rounded border border-slate-400 w-full" 
                 value={data[field.id] || field.default || ''} 
                 onChange={(e) => handleConfigChange(field.id, e.target.value)}
               >
                 {field.options?.map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
               </select>
             </div>
          ))}
          
        </div>
      )}

      {/* 2. RENDER PINS (Input + Output) */}
      {data.inputs?.map((pin: any) => <PinRow key={pin.id} {...pin} type="input" />)}
      {data.outputs?.map((pin: any, idx: number) => (
        <div key={pin.id} className="relative group">
           <PinRow {...pin} type="output" />
           {/* Hiển thị nút xóa cạnh các Handle Case (Không cho xóa handle Default) */}
           {pin.id !== 'out_default' && (
              <button 
                onClick={() => handleDeleteCase(idx)}
                className="absolute right-24 top-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 size={12}/>
              </button>
           )}
        </div>
      ))}

      {/* 3. KHU VỰC THÊM CASE MỚI */}
      <div className="p-2 bg-slate-100 border-t border-slate-300 rounded-b-md">
        {isAdding ? (
          <div className="flex flex-col gap-1">
            <input 
              type="text" 
              placeholder="Nhập giá trị Case..." 
              value={newCaseVal} 
              onChange={e => setNewCaseVal(e.target.value)} 
              className="nodrag text-xs p-1 rounded border border-slate-400 w-full"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleAddCase()}
            />
            <div className="flex justify-end gap-2 mt-1">
              <button onClick={() => setIsAdding(false)} className="p-1 text-red-600 hover:bg-red-100 rounded"><X size={14}/></button>
              <button onClick={handleAddCase} className="p-1 text-green-700 hover:bg-green-200 rounded font-bold"><Plus size={14}/></button>
            </div>
          </div>
        ) : (
          <button 
            onClick={() => setIsAdding(true)} 
            className="w-full flex items-center justify-center gap-1 py-1 px-2 text-xs font-bold text-slate-600 bg-slate-300 hover:bg-slate-400 rounded transition-colors"
          >
            <Plus size={12}/> Add Case
          </button>
        )}
      </div>
    </BaseNodeShell>
  );
};