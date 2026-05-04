// components/Nodes/ObjectNodeUI.tsx
import { useState, useRef, useEffect } from 'react';
import { NodeProps } from '@xyflow/react';
import { Box, Code2 } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { BaseNodeShell } from './BaseNodeShell';
import { PinRow } from './PinRow';
import { SmartDropdown } from './SmartDropdown';

export const ObjectNodeUI = ({ id, data, selected, positionAbsoluteX, positionAbsoluteY }: NodeProps<any>) => {
  const { updateNodeData, addNode, nodeCatalogueMap } = useFlowStore();
  
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Xử lý sự kiện click ra ngoài để đóng menu +f
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Xử lý thay đổi cấu hình Node
  const handleConfigChange = (fieldId: string, value: any) => {
    updateNodeData(id, { [fieldId]: value });
  };

  // Logic sinh Node Method (Function)
  const handleSpawnFunction = (funcClass: string) => {
    const template = nodeCatalogueMap[funcClass];
    if (!template) return;
    
    addNode({
      id: `${template.class}-${Date.now()}`,
      type: template.type,
      position: { x: (positionAbsoluteX ?? 0) + 250, y: (positionAbsoluteY ?? 0) + 50 },
      data: { ...template, className: template.class, displayName: template.label }
    });
    
    setIsMenuOpen(false);
  };

  // Nút +f và dropdown menu
  const HeaderRight = data.functions?.length > 0 && (
    <div className="relative" ref={menuRef}>
      <button 
        onClick={() => setIsMenuOpen(!isMenuOpen)} 
        className="flex items-center justify-center gap-1 bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-bold px-1.5 py-0.5 rounded shadow-sm border border-indigo-400 transition-colors"
        title="Add Object Method"
      >
        <Code2 size={12} /> <span className="mb-px">+f</span>
      </button>
      
      {isMenuOpen && (
        <div className="absolute right-0 top-full mt-1 w-48 bg-slate-800 border border-slate-600 rounded-md shadow-2xl z-50 overflow-hidden">
          <div className="px-2 py-1 bg-slate-900 border-b border-slate-700 text-[10px] text-slate-400 uppercase font-bold tracking-wider">
            Available Methods
          </div>
          <div className="max-h-48 overflow-y-auto custom-scrollbar">
            {data.functions.map((fn: string) => (
              <button 
                key={fn} 
                onClick={() => handleSpawnFunction(fn)} 
                className="w-full text-left px-3 py-2 text-xs text-slate-200 hover:bg-indigo-600 hover:text-white transition-colors"
              >
                {fn.replace('Node', '')}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <BaseNodeShell
      isError={!!data.errorMessage} 
      errorMessage={data.errorMessage} 
      selected={selected}
      title={data.displayName} 
      icon={<Box size={16} className="text-indigo-200" />}
      headerColorClass="bg-indigo-700" 
      ringColorClass="ring-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.5)]"
      headerRight={HeaderRight}
    >
      {/* KHU VỰC CONFIG FIELDS */}
      {data.config_fields && data.config_fields.length > 0 && (
        <div className="flex flex-col gap-2 p-3 pb-1 border-b border-slate-300/50 bg-slate-200/50 -mx-3 mb-2">
          {data.config_fields.map((field: any) => {
            const fieldKey = field.name || field.id; // Hỗ trợ cả property name mới và id cũ
            
            return (
              <div key={fieldKey} className="flex flex-col gap-1">
                <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                  {field.label || fieldKey}
                </label>
                
                {field.type === 'text' && (
                  <input 
                    type="text" 
                    className="nodrag text-xs p-1 rounded border border-slate-400 w-full" 
                    value={data[fieldKey] ?? field.default ?? ''} 
                    onChange={(e) => handleConfigChange(fieldKey, e.target.value)} 
                  />
                )}
                
                {field.type === 'select' && (
                  <select 
                    className="nodrag text-xs p-1 rounded border border-slate-400 w-full bg-white" 
                    value={data[fieldKey] ?? field.default ?? ''} 
                    onChange={(e) => handleConfigChange(fieldKey, e.target.value)}
                  >
                    {field.options?.map((opt: string) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                )}
                
                {['server_pool_dropdown', 'device_pool_dropdown', 'active_logic_dropdown'].includes(field.type) && (
                  <SmartDropdown 
                    type={field.type} 
                    id={fieldKey} 
                    value={data[fieldKey]} 
                    onChange={(val) => handleConfigChange(fieldKey, val)} 
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* DANH SÁCH INPUTS */}
      {data.inputs?.map((input: any) => (
        <PinRow key={input.id} {...input} type="input" />
      ))}

      {/* DANH SÁCH OUTPUTS */}
      {data.outputs?.map((output: any) => (
        <PinRow key={output.id} {...output} type="output" />
      ))}
    </BaseNodeShell>
  );
};