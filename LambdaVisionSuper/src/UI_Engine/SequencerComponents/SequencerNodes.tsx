import React from 'react';
import { Handle, Position, useUpdateNodeInternals } from '@xyflow/react';
import { Clock, FileText, Braces, Plus, X, Settings2, Wifi, Radio, TerminalSquare, Database } from 'lucide-react';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { BaseNode } from './BaseNode';
// ==========================================
// SHARED HELPER COMPONENTS
// ==========================================

const IdentityBadge = ({ name }: { name?: string }) => {
  if (!name) return null;
  return (
    <div className="absolute -top-3 right-2 bg-[#4fd1c5]/20 text-[#4fd1c5] px-1.5 py-0.5 rounded text-[8px] font-mono border border-[#4fd1c5]/30 z-50 shadow-sm backdrop-blur-sm whitespace-nowrap pointer-events-none">
      ID: {name}
    </div>
  );
};

const inferType = (value: any): string => {
  if (value === null || value === undefined) return 'any';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  if (Array.isArray(value)) return 'array';
  if (typeof value === 'object') return 'json';
  return 'string';
};

const CustomHandle = ({ type, position, id, colorClass }: any) => (
  <Handle
    type={type}
    position={position}
    id={id}
    className={`!w-4 !h-4 !border-[3px] !border-[#202124] ${colorClass} ${
      position === Position.Left ? '!-left-3' : '!-right-3'
    } transition-transform hover:scale-125`}
  />
);

const TagSelector = ({ value, onChange, placeholder, filterType }: any) => {
  const tags = useTagDb(state => state.tags);
  const globalTags = Object.keys(tags);
  
  const options = filterType 
    ? globalTags.filter(t => inferType(tags[t]) === filterType || filterType === 'any')
    : globalTags;

  return (
    <select 
      value={value || ''} 
      onChange={onChange} 
      className="nodrag w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-[10px] p-1.5 rounded outline-none focus:border-[#8ab4f8] cursor-pointer"
    >
      <option value="">{placeholder || 'Select Tag...'}</option>
      {options.map(t => <option key={t} value={t}>{t}</option>)}
    </select>
  );
};

const TextInput = ({ value, onChange, placeholder, type = "text" }: any) => (
  <input 
    type={type} 
    value={value || ''} 
    onChange={onChange} 
    placeholder={placeholder} 
    className="nodrag w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs p-1.5 rounded outline-none focus:border-[#8ab4f8] font-mono" 
  />
);

// ==========================================
// 1. PROCESS NODE
// ==========================================
export const ProcessNode = ({ id, data, selected }: any) => {
  const config = data?.sequencer_data?.config || {};
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-56 bg-[#202124] rounded-lg border-2 flex flex-col cursor-pointer ${selected ? 'border-[#8ab4f8] shadow-[0_0_20px_rgba(138,180,248,0.15)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="p-2 border-b border-[#3c4043] bg-[#28292c] rounded-t-md flex justify-between items-center">
        <span className="text-[#8ab4f8] font-bold text-[10px] uppercase tracking-wider">
            {config.node_title || 'Process'} 
        </span>
      </div>
      <div className="p-3 flex flex-col gap-2">
        <span className="text-[9px] text-[#9aa0a6]">Target: <b className="text-[#e8eaed]">{config.logic_object_info?.logic_object_id || 'Not configured'}</b></span>
        <button 
          onClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }} 
          className="w-full py-2 bg-[#8ab4f8]/10 border border-[#8ab4f8]/30 text-[#8ab4f8] font-bold text-[10px] rounded hover:bg-[#8ab4f8]/20 transition-colors flex justify-center items-center gap-2"
        >
          <Settings2 size={12} /> CONFIGURE NODE
        </button>
      </div>
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#8ab4f8]" />
    </div>
  );
};

// ==========================================
// 2. SWITCH NODE
// ==========================================
export const SwitchNode = ({ id, data, selected }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const updateNodeInternals = useUpdateNodeInternals();
  const config = data?.sequencer_data?.config || {};
  const switchType = config.switch_type || 'string'; 
  const cases = config.cases || [{ value: 'Value 1' }];

  const updateCases = (newCases: any[]) => {
    setFieldValue(id, 'cases', newCases);
    setTimeout(() => updateNodeInternals(id), 50); 
  };

  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-64 bg-[#28292c] rounded-lg border-2 pb-2 cursor-pointer ${selected ? 'border-[#fcd663] shadow-[0_0_15px_rgba(252,214,99,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="p-2 border-b border-[#3c4043] bg-[#202124] rounded-t-md flex flex-col gap-1.5">
        <span className="text-[9px] font-bold text-[#9aa0a6] uppercase tracking-wider">Condition Tag</span>
        <TagSelector value={config.tag_id} onChange={(e: any) => setFieldValue(id, 'tag_id', e.target.value)} />
        <div className="flex gap-2 items-center mt-1 border-t border-[#3c4043] pt-2">
           <span className="text-[9px] font-bold text-[#5f6368] uppercase">Data Type:</span>
           <select value={switchType} onChange={(e) => {
               const newType = e.target.value;
               setFieldValue(id, 'switch_type', newType);
               const resetCases = cases.map(() => ({ value: newType === 'boolean' ? 'true' : newType === 'number' ? '0' : '' }));
               updateCases(resetCases);
           }} className="nodrag flex-1 bg-[#171717] border border-[#3c4043] text-[#fcd663] text-[10px] p-1 rounded outline-none cursor-pointer">
             <option value="string">String</option><option value="number">Number</option><option value="boolean">Boolean</option>
           </select>
        </div>
      </div>
      <div className="flex flex-col gap-1 p-2">
        {cases.map((c: any, i: number) => (
          <div key={i} className="relative flex items-center gap-1.5">
             {switchType === 'boolean' ? (
                <select value={c.value} onChange={(e) => { const nc = [...cases]; nc[i].value = e.target.value; updateCases(nc); }} className="nodrag flex-1 bg-[#171717] border border-[#3c4043] text-[#fcd663] text-[10px] p-1.5 rounded outline-none cursor-pointer">
                  <option value="true">True</option><option value="false">False</option>
                </select>
             ) : (
                <input type={switchType === 'number' ? 'number' : 'text'} value={c.value} onChange={(e) => { const nc = [...cases]; nc[i].value = e.target.value; updateCases(nc); }} className="nodrag flex-1 bg-[#171717] border border-[#3c4043] text-[#fcd663] text-[10px] p-1.5 rounded outline-none min-w-0" placeholder={`Case ${i+1}`} />
             )}
             <button onClick={() => updateCases(cases.filter((_: any, idx: number) => idx !== i))} className="text-[#5f6368] hover:text-[#f28b82] shrink-0 p-1"><X size={14}/></button>
             <CustomHandle type="source" position={Position.Right} id={`case-${i}`} colorClass="!bg-[#fcd663]" />
          </div>
        ))}
      </div>
      <div className="px-2">
        <button onClick={() => updateCases([...cases, { value: switchType==='boolean'?'true':'' }])} className="w-full py-1 border border-dashed border-[#5f6368] text-[#9aa0a6] rounded text-[10px] font-bold hover:border-[#fcd663] hover:text-[#fcd663] transition-colors flex items-center justify-center gap-1">
          <Plus size={12}/> ADD CASE
        </button>
      </div>
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
    </div>
  );
};

// ==========================================
// 3. COMPUTE NODE
// ==========================================
export const ComputeNode = ({ id, data, selected }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const config = data?.sequencer_data?.config || {};
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-48 bg-[#28292c] rounded-lg border-2 p-3 flex flex-col gap-2 cursor-pointer ${selected ? 'border-[#81c995] shadow-[0_0_15px_rgba(129,201,149,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <span className="text-[10px] font-bold text-[#81c995] uppercase text-center mb-1 tracking-widest">Compute</span>
      <TagSelector value={config.tag_id_a} onChange={(e: any) => setFieldValue(id, 'tag_id_a', e.target.value)} placeholder="Tag A" />
      <select value={config.operand} onChange={(e) => setFieldValue(id, 'operand', e.target.value)} className="nodrag bg-[#202124] border border-[#3c4043] text-[#81c995] font-bold text-center text-sm py-1 rounded outline-none w-1/2 self-center cursor-pointer">
        <option value="+">+</option><option value="-">-</option><option value="*">*</option><option value="/">/</option>
        <option value=">">&gt;</option><option value="<">&lt;</option><option value="==">==</option><option value=">=">&gt;=</option><option value="<=">&lt;=</option>
      </select>
      <TagSelector value={config.tag_id_b} onChange={(e: any) => setFieldValue(id, 'tag_id_b', e.target.value)} placeholder="Tag B" />
      <div className="w-full h-px bg-[#3c4043] my-1"></div>
      <TagSelector value={config.target_tag_id} onChange={(e: any) => setFieldValue(id, 'target_tag_id', e.target.value)} placeholder="Result Tag" />
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#81c995]" />
    </div>
  );
};

// ==========================================
// 4. AND / OR NODES
// ==========================================
const LogicGateNode = ({ id, data, selected, typeLabel, colorClass }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const config = data?.sequencer_data?.config || {};
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-40 bg-[#28292c] rounded-lg border-2 p-3 flex flex-col gap-2 cursor-pointer ${selected ? `border-[${colorClass}] shadow-[0_0_15px_rgba(252,214,99,0.2)]` : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className={`text-center font-bold text-[${colorClass}] text-sm tracking-widest bg-[#202124] rounded py-1 border border-[#3c4043]`}>{typeLabel}</div>
      <TagSelector value={config.tag_id_a} onChange={(e: any) => setFieldValue(id, 'tag_id_a', e.target.value)} placeholder="Condition A" />
      <TagSelector value={config.tag_id_b} onChange={(e: any) => setFieldValue(id, 'tag_id_b', e.target.value)} placeholder="Condition B" />
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass={`!bg-[${colorClass}]`} />
    </div>
  );
};
export const AndNode = (props: any) => <LogicGateNode {...props} typeLabel="AND" colorClass="#fcd663" />;
export const OrNode = (props: any) => <LogicGateNode {...props} typeLabel="OR" colorClass="#fcd663" />;

// ==========================================
// 5. DELAY NODE
// ==========================================
export const DelayNode = ({ id, data, selected }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const config = data?.sequencer_data?.config || {};
  const isDynamic = config.is_dynamic || false;
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-40 bg-[#28292c] rounded-lg border-2 p-3 flex flex-col items-center gap-2 cursor-pointer ${selected ? 'border-[#9aa0a6] shadow-[0_0_10px_rgba(154,160,166,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="flex justify-between items-center w-full">
         <span className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest">Delay</span>
         <button onClick={(e) => { e.stopPropagation(); setFieldValue(id, 'is_dynamic', !isDynamic); }} className="text-[8px] bg-[#3c4043] text-[#e8eaed] px-1.5 py-0.5 rounded">
            {isDynamic ? 'USE TAG' : 'USE CONST'}
         </button>
      </div>
      <Clock size={24} className="text-[#9aa0a6]" />
      <div className="w-full mt-1">
        {isDynamic ? (
            <TagSelector filterType="number" value={config.delay_tag_id} onChange={(e: any) => setFieldValue(id, 'delay_tag_id', e.target.value)} placeholder="Secs from Tag..." />
        ) : (
            <div className="flex items-center gap-2">
                <span className="text-[#9aa0a6] font-bold font-mono text-[10px]">sec:</span>
                <input type="number" step="0.1" min="0" value={config.delay_duration || 0} onChange={(e) => setFieldValue(id, 'delay_duration', Number(e.target.value))} className="nodrag w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs p-1.5 rounded outline-none text-center" />
            </div>
        )}
      </div>
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#9aa0a6]" />
    </div>
  );
};

// ==========================================
// 6. TAG OVERWRITE (BY VALUE)
// ==========================================
export const TagOverValNode = ({ id, data, selected }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const tags = useTagDb(s => s.tags);
  const config = data?.sequencer_data?.config || {};
  const targetTagType = config.target_tag_id ? inferType(tags[config.target_tag_id]) : 'string';

  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-44 bg-[#28292c] rounded-lg border-2 p-3 flex flex-col gap-2 cursor-pointer ${selected ? 'border-[#8ab4f8] shadow-[0_0_15px_rgba(138,180,248,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="flex items-center justify-center gap-2 text-[#8ab4f8] font-bold text-[10px] uppercase border-b border-[#3c4043] pb-2 mb-1">
        <FileText size={14}/> OVERWRITE (VAL)
      </div>
      <TagSelector value={config.target_tag_id} onChange={(e: any) => setFieldValue(id, 'target_tag_id', e.target.value)} placeholder="Target Tag" />
      {targetTagType === 'boolean' ? (
        <select value={String(config.ovwr_value)} onChange={(e) => setFieldValue(id, 'ovwr_value', e.target.value === 'true')} className="nodrag w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs p-1.5 rounded outline-none cursor-pointer">
          <option value="true">True</option><option value="false">False</option>
        </select>
      ) : targetTagType === 'number' ? (
        <input type="number" value={config.ovwr_value || 0} onChange={(e: any) => setFieldValue(id, 'ovwr_value', Number(e.target.value))} className="nodrag w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs p-1.5 rounded outline-none font-mono" />
      ) : (
        <TextInput value={config.ovwr_value} onChange={(e: any) => setFieldValue(id, 'ovwr_value', e.target.value)} placeholder="New Value..." />
      )}
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#8ab4f8]" />
    </div>
  );
};

// ==========================================
// 7. TAG OVERWRITE (BY TAG)
// ==========================================
export const TagOverTagNode = ({ id, data, selected }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const tags = useTagDb(s => s.tags);
  const config = data?.sequencer_data?.config || {};
  const sourceTagType = config.source_tag_id ? inferType(tags[config.source_tag_id]) : 'any';

  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-44 bg-[#28292c] rounded-lg border-2 p-3 flex flex-col gap-2 cursor-pointer ${selected ? 'border-[#8ab4f8] shadow-[0_0_15px_rgba(138,180,248,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="flex items-center justify-center gap-2 text-[#8ab4f8] font-bold text-[10px] uppercase border-b border-[#3c4043] pb-2 mb-1">
        <FileText size={14}/> OVERWRITE (TAG)
      </div>
      <TagSelector value={config.source_tag_id} onChange={(e: any) => setFieldValue(id, 'source_tag_id', e.target.value)} placeholder="Source Tag" />
      <div className="w-full flex justify-center"><span className="text-[#5f6368] text-[10px]">▼</span></div>
      <TagSelector filterType={sourceTagType} value={config.target_tag_id} onChange={(e: any) => setFieldValue(id, 'target_tag_id', e.target.value)} placeholder={`Target Tag (${sourceTagType})`} />
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#8ab4f8]" />
    </div>
  );
};

// ==========================================
// 8. EXTRACT JSON NODE
// ==========================================
export const ExtractJsonNode = ({ id, data, selected }: any) => {
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-48 bg-[#202124] rounded-lg border-2 flex flex-col cursor-pointer ${selected ? 'border-[#f28b82] shadow-[0_0_15px_rgba(242,139,130,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="p-2 border-b border-[#3c4043] bg-[#28292c] rounded-t-md flex items-center justify-center gap-2 text-[#f28b82]">
        <Braces size={14}/> <span className="font-bold text-[10px] uppercase tracking-wider">Extract JSON</span>
      </div>
      <div className="p-3">
        <button onClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }} className="w-full py-1.5 bg-[#f28b82]/10 border border-[#f28b82]/30 text-[#f28b82] font-bold text-[10px] rounded hover:bg-[#f28b82]/20 transition-colors">
          <Settings2 size={12} className="inline mr-1"/> CONFIGURE
        </button>
      </div>
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#f28b82]" />
    </div>
  );
};

// ==========================================
// 8B. BUILD JSON NODE
// ==========================================
export const BuildJsonNode = ({ id, data, selected }: any) => {
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-48 bg-[#202124] rounded-lg border-2 flex flex-col cursor-pointer ${selected ? 'border-[#81c995] shadow-[0_0_15px_rgba(129,201,149,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="p-2 border-b border-[#3c4043] bg-[#28292c] rounded-t-md flex items-center justify-center gap-2 text-[#81c995]">
        <Braces size={14}/> <span className="font-bold text-[10px] uppercase tracking-wider">Build JSON</span>
      </div>
      <div className="p-3">
        <button onClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }} className="w-full py-1.5 bg-[#81c995]/10 border border-[#81c995]/30 text-[#81c995] font-bold text-[10px] rounded hover:bg-[#81c995]/20 transition-colors">
          <Settings2 size={12} className="inline mr-1"/> CONFIGURE
        </button>
      </div>
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#81c995]" />
    </div>
  );
};

// ==========================================
// 9. START NODE
// ==========================================
export const StartNode = ({ id, data, selected }: any) => (
  <div 
    className={`relative w-32 h-14 bg-[#202124] rounded-[50px] border-2 flex items-center justify-between px-4 cursor-pointer ${selected ? 'border-[#81c995] shadow-[0_0_15px_rgba(129,201,149,0.3)]' : 'border-[#5f6368] hover:border-[#81c995]/50'}`} 
    onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
  >
    <IdentityBadge name={data.name} />
    <div className="flex flex-col justify-center">
        <span className="text-[#81c995] font-bold text-xs tracking-widest uppercase">Start</span>
        {Object.keys(data?.sequencer_data?.config?.on_begin_map || {}).length > 0 && (
           <span className="text-[8px] text-[#5f6368] mt-0.5">Has Init Data</span>
        )}
    </div>
    <button onClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }} className="text-[#9aa0a6] hover:text-[#81c995] transition-colors p-1" title="Configure Initial Values">
        <Settings2 size={14} />
    </button>
    <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#81c995]" />
  </div>
);

// ==========================================
// 9B. END NODE
// ==========================================
export const EndNode = ({ id, data, selected }: any) => (
  <div 
    className={`relative w-32 h-14 bg-[#202124] rounded-[50px] border-2 flex items-center justify-between px-4 cursor-pointer ${selected ? 'border-[#f28b82] shadow-[0_0_15px_rgba(242,139,130,0.3)]' : 'border-[#5f6368] hover:border-[#f28b82]/50'}`} 
    onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
  >
    <IdentityBadge name={data.name} />
    <div className="flex flex-col justify-center">
        <span className="text-[#f28b82] font-bold text-xs tracking-widest uppercase">End</span>
        {Object.keys(data?.sequencer_data?.config?.on_end_map || {}).length > 0 && (
           <span className="text-[8px] text-[#5f6368] mt-0.5">Has Cleanup Data</span>
        )}
    </div>
    <button onClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }} className="text-[#9aa0a6] hover:text-[#f28b82] transition-colors p-1" title="Configure Cleanup Values">
        <Settings2 size={14} />
    </button>
    <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
  </div>
);

// ==========================================
// 10. SCRIPT NODE
// ==========================================
export const ScriptNode = ({ id, data, selected }: any) => {
    const titleName = data.name || "JS SCRIPT";
    return (
        <BaseNode 
            id={id} 
            data={data} 
            selected={selected} 
            title={titleName} 
            icon={<TerminalSquare size={14}/>} 
            headerColor="bg-[#202020]"
            onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        >
            <IdentityBadge name={data.name} />
            <div className="p-3">
                <button 
                    onClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }} 
                    className="w-full py-1.5 bg-white/80 border border-[#4fd1c5]/30 text-[#0c1a18] font-bold text-[10px] rounded hover:bg-[#4fd1c5]/20 transition-colors"
                >
                    <Settings2 size={12} className="inline mr-1"/> EDIT SCRIPT
                </button>
            </div>
            <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
            <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#e8eaed]" />
        </BaseNode>
    );
};

// ==========================================
// 11. SPLIT NODE
// ==========================================
export const SplitNode = ({ id, data, selected }: any) => (
  <div 
    onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
    className={`relative w-3 h-24 bg-[#c58af9] rounded-full flex items-center justify-center cursor-pointer ${selected ? 'ring-2 ring-[#c58af9]/50 shadow-[0_0_15px_rgba(197,138,249,0.5)]' : ''}`}
  >
    <IdentityBadge name={data.name} />
    <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
    <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#c58af9]" />
  </div>
);

// ==========================================
// 12. JOIN NODE
// ==========================================
export const JoinNode = ({ id, data, selected }: any) => (
  <div 
    onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
    className={`relative h-3 w-24 bg-[#c58af9] rounded-full flex items-center justify-center cursor-pointer ${selected ? 'ring-2 ring-[#c58af9]/50 shadow-[0_0_15px_rgba(197,138,249,0.5)]' : ''}`}
  >
    <IdentityBadge name={data.name} />
    <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
    <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#c58af9]" />
  </div>
);

// ==========================================
// 13. PORTAL IN
// ==========================================
export const PortalInNode = ({ id, data, selected }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const config = data?.sequencer_data?.config || {};
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-32 bg-[#202124] rounded-full border-2 flex items-center p-1.5 cursor-pointer ${selected ? 'border-[#c58af9] shadow-[0_0_15px_rgba(197,138,249,0.3)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <div className="bg-[#c58af9]/20 p-1.5 rounded-full mr-2">
        <Wifi size={14} className="text-[#c58af9]" />
      </div>
      <input 
        type="text" value={config.channel_name || ''} 
        onChange={(e) => setFieldValue(id, 'channel_name', e.target.value)} 
        placeholder="Channel..." 
        className="nodrag flex-1 bg-transparent text-[#e8eaed] text-[10px] font-bold outline-none uppercase min-w-0" 
      />
    </div>
  );
};

// ==========================================
// 14. PORTAL OUT
// ==========================================
export const PortalOutNode = ({ id, data, selected }: any) => {
  const setFieldValue = useSequencerStore(s => s.setFieldValue);
  const config = data?.sequencer_data?.config || {};
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-32 bg-[#202124] rounded-full border-2 flex items-center p-1.5 cursor-pointer ${selected ? 'border-[#fcd663] shadow-[0_0_15px_rgba(252,214,99,0.3)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="bg-[#fcd663]/20 p-1.5 rounded-full mr-2">
        <Radio size={14} className="text-[#fcd663]" />
      </div>
      <input 
        type="text" value={config.channel_name || ''} 
        onChange={(e) => setFieldValue(id, 'channel_name', e.target.value)} 
        placeholder="Channel..." 
        className="nodrag flex-1 bg-transparent text-[#e8eaed] text-[10px] font-bold outline-none uppercase min-w-0" 
      />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#fcd663]" />
    </div>
  );
};

// ==========================================
// 15. WRITE DB
// ==========================================
export const WriteDbNode = ({ id, data, selected }: any) => {
  return (
    <div 
        onDoubleClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }}
        className={`relative w-48 bg-[#202124] rounded-lg border-2 flex flex-col cursor-pointer ${selected ? 'border-[#e580ff] shadow-[0_0_15px_rgba(229,128,255,0.2)]' : 'border-[#5f6368]'}`}
    >
      <IdentityBadge name={data.name} />
      <div className="p-2 border-b border-[#3c4043] bg-[#28292c] rounded-t-md flex items-center justify-center gap-2 text-[#e580ff]">
        <Database size={14}/> <span className="font-bold text-[10px] uppercase tracking-wider">Write DB</span>
      </div>
      <div className="p-3">
        <button onClick={(e) => { e.stopPropagation(); data.onEdit?.(id); }} className="w-full py-1.5 bg-[#e580ff]/10 border border-[#e580ff]/30 text-[#e580ff] font-bold text-[10px] rounded hover:bg-[#e580ff]/20 transition-colors">
          <Settings2 size={12} className="inline mr-1"/> CONFIGURE
        </button>
      </div>
      <CustomHandle type="target" position={Position.Left} colorClass="!bg-[#e8eaed]" />
      <CustomHandle type="source" position={Position.Right} colorClass="!bg-[#e580ff]" />
    </div>
  );
};

// ==========================================
// EXPORT NODE TYPES REGISTRY
// ==========================================
export const nodeTypes = {
  start: StartNode,
  end: EndNode,
  proc: ProcessNode,
  split: SplitNode,
  join: JoinNode,
  switch: SwitchNode,
  comp: ComputeNode,
  and: AndNode,
  or: OrNode,
  delay: DelayNode,
  tov: TagOverValNode,
  tot: TagOverTagNode,
  exjson: ExtractJsonNode,
  buildjson: BuildJsonNode,
  script: ScriptNode,
  writedb: WriteDbNode,
  portal_in: PortalInNode,
  portal_out: PortalOutNode,
};