import React, { useState, useEffect } from 'react';
import { useUIEngine } from '../UIEngineStores/InspectionStore';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { 
    Settings, Trash2, Box, Type, Circle, Edit2, Maximize, Layout, 
    Monitor, Unlink, KeyIcon, MousePointer2, 
    List, Sliders, CheckSquare , ArrowRight, ArrowLeft
} from 'lucide-react';
import { COLOR_PALETTE } from "../../utils/ColorConst";
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/themes/prism-tomorrow.css';
import { TerminalSquare } from 'lucide-react';


interface UIScriptEditorModalProps {
    isOpen: boolean;
    title: string;
    initialScript: string;
    initialInAliases: Record<string, string>;
    initialOutAliases: Record<string, string>;
    globalTags: string[];
    onClose: () => void;
    onSave: (finalCode: string, inAliases: Record<string, string>, outAliases: Record<string, string>) => void;
}

export const UIScriptEditorModal = ({ isOpen, title, initialScript, initialInAliases, initialOutAliases, globalTags, onClose, onSave }: UIScriptEditorModalProps) => {
    const [code, setCode] = useState("");
    
    // State quản lý Aliases
    const [inList, setInList] = useState<{name: string, tag: string}[]>([]);
    const [outList, setOutList] = useState<{name: string, tag: string}[]>([]);

    useEffect(() => {
        if (isOpen) {
            setCode(initialScript || "");
            setInList(Object.entries(initialInAliases || {}).map(([k, v]) => ({ name: k, tag: v })));
            setOutList(Object.entries(initialOutAliases || {}).map(([k, v]) => ({ name: k, tag: v })));
        }
    }, [isOpen, initialScript, initialInAliases, initialOutAliases]);

    if (!isOpen) return null;

    // Helper functions cho Aliases
    const addVar = (type: 'in' | 'out') => {
        if (type === 'in') setInList([...inList, { name: '', tag: '' }]);
        else setOutList([...outList, { name: '', tag: '' }]);
    };

    const removeVar = (type: 'in' | 'out', idx: number) => {
        if (type === 'in') setInList(inList.filter((_, i) => i !== idx));
        else setOutList(outList.filter((_, i) => i !== idx));
    };

    const updateVar = (type: 'in' | 'out', idx: number, field: 'name'|'tag', val: string) => {
        const list = type === 'in' ? [...inList] : [...outList];
        // Ràng buộc tên biến hợp lệ trong JS
        list[idx][field] = field === 'name' ? val.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '') : val;
        if (type === 'in') setInList(list);
        else setOutList(list);
    };

    const handleSave = () => {
        const finalIn: Record<string, string> = {};
        const finalOut: Record<string, string> = {};
        inList.forEach(item => { if (item.name && item.tag) finalIn[item.name] = item.tag; });
        outList.forEach(item => { if (item.name && item.tag) finalOut[item.name] = item.tag; });
        
        onSave(code, finalIn, finalOut);
    };

    return (
        <div className="fixed inset-0 z-[150] bg-black/70 backdrop-blur-sm flex items-center justify-center font-sans">
            <div className="bg-[#28292c] border border-[#3c4043] rounded-xl shadow-2xl w-[1000px] h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                
                {/* Header */}
                <div className="bg-[#303134] px-4 py-3 border-b border-[#3c4043] flex justify-between items-center shrink-0">
                    <div className="flex items-center gap-2 text-[#4fd1c5]">
                        <TerminalSquare size={16} />
                        <h3 className="font-bold text-sm tracking-wide">
                            UI Script Editor — {title}
                        </h3>
                    </div>
                    <button onClick={onClose} className="p-1.5 hover:bg-[#3c4043] rounded-md text-[#9aa0a6] hover:text-[#f28b82] transition-colors">✕</button>
                </div>
                
                {/* Vùng Content 2 Cột */}
                <div className="flex-1 flex overflow-hidden">
                    
                    {/* CỘT TRÁI: QUẢN LÝ ALIAS */}
                    <div className="w-[360px] bg-[#202124] border-r border-[#3c4043] flex flex-col overflow-y-auto custom-scrollbar shrink-0">
                        {/* INPUTS */}
                        <div className="p-4 border-b border-[#3c4043]">
                            <div className="flex items-center justify-between mb-3">
                                <label className="text-xs font-bold text-[#4fd1c5] uppercase flex items-center gap-2">
                                    <ArrowRight size={14} /> [ IN ] Read Tags
                                </label>
                                <button onClick={() => addVar('in')} className="text-[#4fd1c5] hover:bg-[#4fd1c5]/20 px-2 py-1 rounded transition-colors text-[10px] font-bold">+ ADD</button>
                            </div>
                            <div className="flex flex-col gap-2">
                                {inList.map((al, idx) => (
                                    <div key={idx} className="flex gap-1.5 items-center">
                                        <span className="text-[#9aa0a6] font-mono text-[10px]">IN.</span>
                                        <input type="text" value={al.name} onChange={(e) => updateVar('in', idx, 'name', e.target.value)} className="w-20 bg-[#171717] border border-[#3c4043] text-[#4fd1c5] text-xs p-1.5 rounded font-mono outline-none" placeholder="var" />
                                        <span className="text-[#5f6368] text-xs">⟵</span>
                                        <select value={al.tag} onChange={(e) => updateVar('in', idx, 'tag', e.target.value)} className="flex-1 bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-[10px] p-1.5 rounded outline-none cursor-pointer min-w-0">
                                            <option value="">Tag...</option>
                                            {globalTags.map(t => <option key={t} value={t}>{t}</option>)}
                                        </select>
                                        <button onClick={() => removeVar('in', idx)} className="text-[#5f6368] hover:text-[#f28b82] p-1"><Trash2 size={14}/></button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* OUTPUTS */}
                        <div className="p-4">
                            <div className="flex items-center justify-between mb-3">
                                <label className="text-xs font-bold text-[#c58af9] uppercase flex items-center gap-2">
                                    <ArrowLeft size={14} /> [ OUT ] Write Tags
                                </label>
                                <button onClick={() => addVar('out')} className="text-[#c58af9] hover:bg-[#c58af9]/20 px-2 py-1 rounded transition-colors text-[10px] font-bold">+ ADD</button>
                            </div>
                            <div className="flex flex-col gap-2">
                                {outList.map((al, idx) => (
                                    <div key={idx} className="flex gap-1.5 items-center">
                                        <span className="text-[#9aa0a6] font-mono text-[10px]">OUT.</span>
                                        <input type="text" value={al.name} onChange={(e) => updateVar('out', idx, 'name', e.target.value)} className="w-20 bg-[#171717] border border-[#3c4043] text-[#c58af9] text-xs p-1.5 rounded font-mono outline-none" placeholder="var" />
                                        <span className="text-[#5f6368] text-xs">⟶</span>
                                        <select value={al.tag} onChange={(e) => updateVar('out', idx, 'tag', e.target.value)} className="flex-1 bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-[10px] p-1.5 rounded outline-none cursor-pointer min-w-0">
                                            <option value="">Tag...</option>
                                            {globalTags.map(t => <option key={t} value={t}>{t}</option>)}
                                        </select>
                                        <button onClick={() => removeVar('out', idx)} className="text-[#5f6368] hover:text-[#f28b82] p-1"><Trash2 size={14}/></button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* CỘT PHẢI: SOẠN THẢO CODE */}
                    <div className="flex-1 bg-[#1d1f21] flex flex-col relative">
                        <div className="px-4 py-2 bg-[#171717] border-b border-[#3c4043] font-mono text-[16px] text-[#9aa0a6] flex gap-4 shrink-0 select-none">
                            <span><b className="text-[#4fd14f]">IN.var</b> : Đọc</span>
                            <span><b className="text-[#9230e7]">OUT.var = x</b> : Ghi</span>
                            <span><b className="text-[#8ab4f8]">UI.get(id)</b> / <b className="text-[#0058e6]">UI.set(id, props)</b> : Đổi giao diện</span>
                            <span><b className="text-[#fcd663]">ENGINE</b> : .addLabel(str), .queryByLabel(str), .hijack(id, nodeId), .killAllByLabel(str)</span>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar relative">
                            <Editor
                                value={code}
                                onValueChange={(newCode) => setCode(newCode)}
                                highlight={(newCode) => Prism.highlight(newCode, Prism.languages.javascript, 'javascript')}
                                padding={16}
                                tabSize={4}
                                textareaClassName="focus:outline-none min-h-full"
                                className="font-mono text-sm min-h-full leading-relaxed"
                                style={{ fontFamily: '"Fira Code", "Consolas", monospace', backgroundColor: 'transparent', color: '#e8eaed' }}
                            />
                        </div>
                    </div>
                </div>

                {/* Footer Toolbar */}
                <div className="p-3 bg-[#303134] border-t border-[#3c4043] flex justify-end gap-2 shrink-0 select-none">
                    <button onClick={onClose} className="px-4 py-1.5 rounded-lg text-xs font-bold text-[#9aa0a6] hover:bg-[#3c4043] hover:text-[#e8eaed] transition-colors">CANCEL</button>
                    <button onClick={handleSave} className="px-5 py-1.5 rounded-lg text-xs font-bold bg-[#4fd1c5]/20 text-[#4fd1c5] hover:bg-[#4fd1c5]/30 border border-[#4fd1c5]/30 transition-colors">SAVE SCRIPT</button>
                </div>

            </div>
        </div>
    );
};

export const CreateButtonModal = () => {
    const { createButtonModal, closeCreateButtonModal, addComponent } = useUIEngine();
    const globalTags = useTagDb(state => Object.keys(state.tags));
    
    const [config, setConfig] = useState({
        label: "START",
        targetTag: "",
        actionType: "toggle" as any,
        color: "#3c4043"
    });

    if (!createButtonModal.isOpen) return null;

    const handleCreate = (e: React.FormEvent) => {
        e.preventDefault();
        (addComponent as any)('soft_button', createButtonModal.parent_id, createButtonModal.x, createButtonModal.y, config);
        closeCreateButtonModal();
    };

    return (
        <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center font-sans">
            <div className="bg-[#28292c] border border-[#3c4043] rounded-xl shadow-2xl w-96 overflow-hidden">
                <div className="bg-[#303134] px-4 py-3 border-b border-[#3c4043] flex justify-between items-center">
                    <h3 className="text-[#8ab4f8] font-bold text-sm tracking-wide">Configure New Soft Button</h3>
                    <MousePointer2 size={16} className="text-[#8ab4f8]" />
                </div>
                
                <form onSubmit={handleCreate} className="p-5 flex flex-col gap-4 text-xs">
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[#9aa0a6] font-bold ml-1">BUTTON LABEL</label>
                        <input autoFocus value={config.label} onChange={e => setConfig({...config, label: e.target.value})}
                               className="w-full bg-[#171717] border border-[#3c4043] rounded-lg px-3 py-2 text-[#e8eaed] outline-none focus:border-[#8ab4f8] transition-colors"
                               placeholder="e.g. RESET, START..." />
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[#9aa0a6] font-bold ml-1">TARGET TAG (CONTROL)</label>
                        <select value={config.targetTag} onChange={e => setConfig({...config, targetTag: e.target.value})}
                                className="w-full bg-[#171717] border border-[#3c4043] rounded-lg px-3 py-2 text-[#e8eaed] outline-none cursor-pointer">
                            <option value="">-- No Tag --</option>
                            {globalTags.map(tag => <option key={tag} value={tag}>{tag}</option>)}
                        </select>
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[#9aa0a6] font-bold ml-1">ACTION TYPE</label>
                        <div className="grid grid-cols-2 gap-2">
                            {/* SỬA DÒNG DƯỚI ĐÂY: Thêm 'script' vào mảng */}
                            {['toggle', 'pulse', 'setToTrue', 'setToFalse', 'script'].map(type => (
                                <button key={type} type="button" onClick={() => setConfig({...config, actionType: type as any})}
                                        className={`py-1.5 rounded border transition-all font-bold ${config.actionType === type ? 'bg-[#8ab4f8] text-[#202124] border-[#8ab4f8]' : 'bg-[#171717] text-[#9aa0a6] border-[#3c4043] hover:border-[#5f6368]'}`}>
                                    {type}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[#9aa0a6] font-bold ml-1">BUTTON COLOR</label>
                        <div className="flex gap-2 flex-wrap">
                            {COLOR_PALETTE.slice(0, 5).map(c => (
                                <button key={c.value} type="button" onClick={() => setConfig({...config, color: c.value})}
                                        className={`w-6 h-6 rounded-full border-2 ${config.color === c.value ? 'border-white' : 'border-transparent'}`}
                                        style={{ backgroundColor: c.value }} />
                            ))}
                        </div>
                    </div>

                    <div className="flex justify-end gap-2 mt-2">
                        <button type="button" onClick={closeCreateButtonModal} className="px-4 py-1.5 rounded-lg font-bold text-[#9aa0a6] hover:bg-[#3c4043] transition-colors">CANCEL</button>
                        <button type="submit" className="px-6 py-1.5 rounded-lg font-bold bg-[#8ab4f8]/20 text-[#8ab4f8] hover:bg-[#8ab4f8]/30 border border-[#8ab4f8]/30 transition-colors">CREATE BUTTON</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export const RenameModal = () => {
    const { renameModal, closeRenameModal, renameComponent } = useUIEngine();
    const [inputValue, setInputValue] = useState("");

    React.useEffect(() => { if (renameModal.isOpen) setInputValue(renameModal.currentName); }, [renameModal]);

    if (!renameModal.isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (inputValue.trim()) renameComponent(renameModal.target_id, inputValue.trim());
        closeRenameModal();
    };

    return (
        <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center">
            <div className="bg-[#28292c] border border-[#3c4043] rounded-xl shadow-2xl w-80 overflow-hidden transform scale-100 transition-all">
                <div className="bg-[#303134] px-4 py-3 border-b border-[#3c4043]">
                    <h3 className="text-[#8ab4f8] font-bold text-sm tracking-wide">Rename Component</h3>
                </div>
                <form onSubmit={handleSubmit} className="p-4 flex flex-col gap-4">
                    <input autoFocus type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)}
                           className="w-full bg-[#171717] border border-[#3c4043] rounded-lg px-3 py-2 text-[#e8eaed] text-sm outline-none focus:border-[#8ab4f8] transition-colors"
                           placeholder="Enter new name..." />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={closeRenameModal} className="px-4 py-1.5 rounded-lg text-xs font-bold text-[#9aa0a6] hover:bg-[#3c4043] hover:text-[#e8eaed] transition-colors">CANCEL</button>
                        <button type="submit" className="px-4 py-1.5 rounded-lg text-xs font-bold bg-[#8ab4f8]/20 text-[#8ab4f8] hover:bg-[#8ab4f8]/30 border border-[#8ab4f8]/30 transition-colors">SAVE</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export const ActionMenu = () => {
    const { actionMenu, closeActionMenu, addComponent, deleteComponents, openPropertiesPanel, openRenameModal, setViewportMode, openCreateButtonModal } = useUIEngine();
    if (!actionMenu.isOpen) return null;

    return (
        <div className="absolute z-50 bg-[#28292c] border border-[#3c4043] rounded-lg shadow-2xl py-1 w-48 font-sans text-xs text-[#e8eaed]" style={{ top: actionMenu.y, left: actionMenu.x }} onMouseLeave={closeActionMenu}>
            {actionMenu.target_type === 'thumbnail' && (
                <>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { openRenameModal(actionMenu.target_id, "Screen"); }}><Edit2 size={14} /> Rename Screen</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#f28b82] hover:text-[#202124] text-[#f28b82]" onClick={() => { deleteComponents([actionMenu.target_id]); }}><Trash2 size={14} /> Delete Screen</button>
                </>
            )}
            
            {actionMenu.target_type === 'screen' && (
                <>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('frame', actionMenu.target_id, (actionMenu as any).local_x || 0, (actionMenu as any).local_y || 0); closeActionMenu(); }}><Layout size={14} /> Add Frame</button>
                    <div className="h-px bg-[#3c4043] my-1"></div>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#3c4043]" onClick={() => { setViewportMode('normal'); closeActionMenu(); }}><Monitor size={14} /> View: Normal</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#3c4043]" onClick={() => { setViewportMode('fullViewPort'); closeActionMenu(); }}><Maximize size={14} /> View: Fullport</button>
                    <div className="h-px bg-[#3c4043] my-1"></div>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => openPropertiesPanel(actionMenu.target_id)}><Settings size={14} /> Properties</button>
                </>
            )}
            
            {actionMenu.target_type === 'frame' && (
                <>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('bounding_box', actionMenu.target_id, (actionMenu as any).local_x||0, (actionMenu as any).local_y||0); closeActionMenu(); }}><Box size={14} /> Add Box</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('bounding_circle', actionMenu.target_id, (actionMenu as any).local_x||0, (actionMenu as any).local_y||0); closeActionMenu(); }}><Circle size={14} /> Add Circle</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('text', actionMenu.target_id, (actionMenu as any).local_x||0, (actionMenu as any).local_y||0); closeActionMenu(); }}><Type size={14} /> Add Text</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { openCreateButtonModal(actionMenu.target_id, (actionMenu as any).local_x || 0, (actionMenu as any).local_y || 0); closeActionMenu()}}><MousePointer2 size={14} /> Add Button</button>
                    
                    <div className="h-px bg-[#3c4043] my-1"></div>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('text_input', actionMenu.target_id, (actionMenu as any).local_x || 0, (actionMenu as any).local_y || 0); closeActionMenu(); }}><Type size={14} /> Add Input Field</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('combobox', actionMenu.target_id, (actionMenu as any).local_x || 0, (actionMenu as any).local_y || 0); closeActionMenu(); }}><List size={14} /> Add Combobox</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('slider', actionMenu.target_id, (actionMenu as any).local_x || 0, (actionMenu as any).local_y || 0); closeActionMenu(); }}><Sliders size={14} /> Add Slider</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => { addComponent('checkbox', actionMenu.target_id, (actionMenu as any).local_x || 0, (actionMenu as any).local_y || 0); closeActionMenu(); }}><CheckSquare size={14} /> Add Checkbox</button>

                    <div className="h-px bg-[#3c4043] my-1"></div>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-slate-700 text-cyan-400" onClick={() => { addComponent('dynamic_bboxes', actionMenu.target_id, (actionMenu as any).local_x || 0, (actionMenu as any).local_y || 0); closeActionMenu(); }}><Layout size={14} /> Add Dynamic BBoxes</button>
                    
                    <div className="h-px bg-[#3c4043] my-1"></div>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => openPropertiesPanel(actionMenu.target_id)}><Settings size={14} /> Properties</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#f28b82] hover:text-[#202124] text-[#f28b82]" onClick={() => deleteComponents([actionMenu.target_id])}><Trash2 size={14} /> Delete</button>
                </>
            )}
            
            {['bounding_box', 'bounding_circle', 'text', 'line', 'soft_button', 'dynamic_bboxes', 'text_input', 'combobox', 'slider', 'checkbox'].includes(actionMenu.target_type) && (
                <>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => openPropertiesPanel(actionMenu.target_id)}><Settings size={14} /> Properties</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#f28b82] hover:text-[#202124] text-[#f28b82]" onClick={() => deleteComponents([actionMenu.target_id])}><Trash2 size={14} /> Delete</button>
                </>
            )}
        </div>
    );
};

export const UIPropertiesPanel = () => {
    const { propertyPanel, components_map, closePropertiesPanel, updateComponentProps, renameComponent, bindTagToProperty, unbindTag } = useUIEngine();
    const globalTags = useTagDb(state => Object.keys(state.tags));

    const [activeScriptPath, setActiveScriptPath] = useState<string | null>(null);
    
    if (!propertyPanel.isOpen || !propertyPanel.target_id) return null;
    const node = components_map[propertyPanel.target_id];
    if (!node) return null;

    const getAvailableFields = () => {
        const fields = [];
        
        if(node.isVisible !== undefined) fields.push({ path: 'isVisible', label: 'Visible', type: 'boolean' });
        if(node.x !== undefined) fields.push({ path: 'x', label: 'X', type: 'number' });
        if(node.y !== undefined) fields.push({ path: 'y', label: 'Y', type: 'number' });
        if(node.size_x !== undefined) fields.push({ path: 'size_x', label: 'Width', type: 'number' });
        if(node.size_y !== undefined) fields.push({ path: 'size_y', label: 'Height', type: 'number' });
        if(node.radius !== undefined) fields.push({ path: 'radius', label: 'Radius', type: 'number' });
        if(node.content !== undefined) fields.push({ path: 'content', label: 'Text', type: 'string' });
        
        if(node.style) {
            if(node.style.border_thickness !== undefined) fields.push({ path: 'style.border_thickness', label: 'Stroke W', type: 'number' });
            if(node.style.strokeColor !== undefined) fields.push({ path: 'style.strokeColor', label: 'Stroke Color', type: 'color' });
            if(node.style.fillColor !== undefined) fields.push({ path: 'style.fillColor', label: 'Fill Color', type: 'color' });
            if(node.style.fontColor !== undefined) fields.push({ path: 'style.fontColor', label: 'Font Color', type: 'color' });
            if(node.style.fontSize !== undefined) fields.push({ path: 'style.fontSize', label: 'Font Size', type: 'number' });
            
            if(node.type === 'frame') {
                fields.push({ path: 'style.default_image', label: 'Default Img', type: 'image' }); 
                fields.push({ path: 'style.bgImage', label: 'Runtime Img', type: 'image' });       
            }

            if (node.type === 'soft_button') {
                fields.push({ path: 'content', label: 'Button Text', type: 'string' });
                fields.push({ path: 'targetTag', label: 'Target Tag', type: 'tag_selector' }); 
                
                // SỬA: Thêm 'script' vào options
                fields.push({ path: 'actionType', label: 'Action Type', type: 'select', options: ['toggle', 'setToTrue', 'setToFalse', 'pulse', 'script'] });
                
                // THÊM MỚI: Nếu chọn script, hiện ô nhập code
                if (node.actionType === 'script') {
                    fields.push({ path: 'script_content', label: 'JS Code', type: 'textarea' });
                }
                
                fields.push({ path: 'style.fillColor', label: 'Normal Color', type: 'color' });
                fields.push({ path: 'style.activeColor', label: 'Active Color', type: 'color' }); 
                fields.push({ path: 'style.cornerRadius', label: 'Round Corner', type: 'number' });
            }
        }

        if (node.type === 'dynamic_bboxes') {
            fields.push({ path: 'data', label: 'BBox Array Tag', type: 'tag_selector' });
        }

        if (node.type === 'text_input') {
            fields.push({ path: 'targetTag', label: 'Save To Tag', type: 'tag_selector' });
            fields.push({ path: 'style.fontSize', label: 'Font Size', type: 'number' });
            fields.push({ path: 'style.strokeColor', label: 'Border Color', type: 'color' });
        }
        if (node.type === 'combobox') {
            fields.push({ path: 'sourceTag', label: 'Options Tag (Array)', type: 'tag_selector' });
            fields.push({ path: 'targetTag', label: 'Selected Tag', type: 'tag_selector' });
        }
        if (node.type === 'slider') {
            fields.push({ path: 'targetTag', label: 'Value Tag', type: 'tag_selector' });
            fields.push({ path: 'min', label: 'Min Value', type: 'number' });
            fields.push({ path: 'max', label: 'Max Value', type: 'number' });
            fields.push({ path: 'style.activeColor', label: 'Track Color', type: 'color' });
        }
        if (node.type === 'checkbox') {
            fields.push({ path: 'content', label: 'Label', type: 'string' });
            fields.push({ path: 'targetTag', label: 'Bool Tag', type: 'tag_selector' });
            fields.push({ path: 'style.activeColor', label: 'Check Color', type: 'color' });
        }
        
        return fields;
    };

    const getNestedValue = (obj: any, path: string) => path.split('.').reduce((o, p) => o?.[p], obj);
    const setNestedValue = (path: string, value: any) => {
        if (path.startsWith('style.')) {
            const styleProp = path.split('.')[1];
            updateComponentProps(node.id, { style: { ...node.style, [styleProp]: value } });
        } else {
            updateComponentProps(node.id, { [path]: value });
        }
    };

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => { setNestedValue('style.bgImage', event.target?.result as string); };
            reader.readAsDataURL(file);
        }
    };

    return (
        <>
            <div 
                className="fixed inset-0 z-[35] bg-transparent" 
                onClick={closePropertiesPanel}
                title="Click outside to close"
            ></div>

            <div className="absolute top-20 right-4 w-[480px] bg-[#28292c] border border-[#3c4043] shadow-2xl z-40 rounded-xl font-sans flex flex-col max-h-[80vh]">
                
                <div className="flex justify-between items-center px-4 py-3 border-b border-[#3c4043] bg-[#303134] rounded-t-xl shrink-0">
                    <div className="flex flex-col flex-1 mr-4">
                        <input 
                            value={node.name}
                            onChange={(e) => renameComponent(node.id, e.target.value)}
                            className="font-bold text-[#e8eaed] text-sm bg-transparent border-b border-transparent hover:border-[#5f6368] focus:border-[#8ab4f8] outline-none w-full transition-colors"
                            title="Click to rename"
                        />
                        <span className="font-mono text-[#8ab4f8] text-[10px] uppercase tracking-wider mt-1">{node.type}</span>
                    </div>
                    <button onClick={closePropertiesPanel} className="p-1.5 hover:bg-[#3c4043] rounded-md text-[#9aa0a6] hover:text-[#f28b82] transition-colors">✕</button>
                </div>
                
                <div className="p-4 overflow-y-auto custom-scrollbar">
                    <div className="bg-[#171717] rounded-lg border border-[#3c4043] overflow-hidden">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-[#202124] border-b border-[#3c4043]">
                                <tr>
                                    <th className="p-2 text-[#9aa0a6] font-bold w-[25%] uppercase text-[10px]">Prop</th>
                                    <th className="p-2 text-[#9aa0a6] font-bold w-[12%] uppercase text-[10px] text-center">Type</th>
                                    <th className="p-2 text-[#9aa0a6] font-bold w-[33%] uppercase text-[10px]">Local Val</th>
                                    <th className="p-2 text-[#9aa0a6] font-bold w-[30%] uppercase text-[10px] text-right">Data Link</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#3c4043]">
                                {getAvailableFields().map(field => {
                                    const binding = node.bindings.find((b:any) => b.propName === field.path);
                                    const val = getNestedValue(node, field.path);
                                    
                                    return (
                                        <tr key={field.path} className="hover:bg-[#202124] transition-colors group">
                                            <td className="p-2 font-mono text-[#8ab4f8] text-[10px]">{field.label}</td>
                                            <td className="p-2 text-center"><span className="px-1 py-0.5 bg-[#3c4043] text-[#e8eaed] rounded text-[8px] uppercase">{field.type}</span></td>
                                            
                                            <td className="p-2">
                                                {binding ? (
                                                    <span className="text-[#5f6368] italic text-[10px]">Bound to Global Tag</span>
                                                ) : (
                                                    <>
                                                        {(field.type === 'string' || field.type === 'number') && (
                                                            <input 
                                                                className="w-full bg-transparent border-b border-transparent hover:border-[#5f6368] focus:border-[#8ab4f8] text-[#e8eaed] outline-none transition-colors"
                                                                value={val || ''}
                                                                onChange={(e) => setNestedValue(field.path, field.type === 'number' ? Number(e.target.value) || 0 : e.target.value)}
                                                            />
                                                        )}
                                                        
                                                        {field.type === 'boolean' && (
                                                            <select 
                                                                value={val === false ? 'false' : 'true'} 
                                                                onChange={e => setNestedValue(field.path, e.target.value === 'true')} 
                                                                className="w-full bg-[#171717] border border-[#3c4043] rounded px-1.5 py-1 text-[#e8eaed] text-[10px] outline-none cursor-pointer"
                                                            >
                                                                <option value="true">True</option>
                                                                <option value="false">False</option>
                                                            </select>
                                                        )}

                                                        {/* BỔ SUNG GIAO DIỆN SELECTOR CHO TAG */}
                                                        {field.type === 'tag_selector' && (
                                                            <select 
                                                                value={val || ''} 
                                                                onChange={e => setNestedValue(field.path, e.target.value)} 
                                                                className="w-full bg-[#171717] border border-[#8ab4f8] rounded px-1.5 py-1 text-[#8ab4f8] text-[10px] outline-none cursor-pointer font-bold"
                                                            >
                                                                <option value="">-- Select Tag --</option>
                                                                {globalTags.map(tag => <option key={tag} value={tag}>{tag}</option>)}
                                                            </select>
                                                        )}

                                                        {/* BỔ SUNG GIAO DIỆN SELECTOR CHO OPTIONS */}
                                                        {field.type === 'select' && (
                                                            <select 
                                                                value={val || ''} 
                                                                onChange={e => setNestedValue(field.path, e.target.value)} 
                                                                className="w-full bg-[#171717] border border-[#3c4043] rounded px-1.5 py-1 text-[#e8eaed] text-[10px] outline-none cursor-pointer"
                                                            >
                                                                {field.options?.map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
                                                            </select>
                                                        )}

                                                        {field.type === 'textarea' && (
                                                            <button 
                                                                type="button"
                                                                onClick={() => setActiveScriptPath(field.path)} // Đánh dấu mở modal cho field này
                                                                className="w-full py-1.5 bg-[#4fd1c5]/10 border border-[#4fd1c5]/30 hover:bg-[#4fd1c5]/20 text-[#4fd1c5] font-bold rounded flex items-center justify-center gap-1.5 transition-all text-[11px] select-none"
                                                            >
                                                                <TerminalSquare size={12} /> SCRIPT
                                                            </button>
                                                        )}

                                                        {field.type === 'color' && (
                                                            <div className="flex items-center gap-2">
                                                                <div className="relative w-5 h-5 rounded-full overflow-hidden border border-[#5f6368] cursor-pointer shrink-0">
                                                                    <input 
                                                                        type="color" 
                                                                        value={val !== 'transparent' ? val : '#000000'} 
                                                                        onChange={e => setNestedValue(field.path, e.target.value)} 
                                                                        className="absolute -top-2 -left-2 w-10 h-10 cursor-pointer" 
                                                                        title="Custom Color"
                                                                    />
                                                                </div>
                                                                <select 
                                                                    value={val || ''} 
                                                                    onChange={e => setNestedValue(field.path, e.target.value)} 
                                                                    className="w-full bg-[#171717] border border-[#3c4043] rounded px-1.5 py-1 hover:border-[#5f6368] focus:border-[#8ab4f8] text-[#e8eaed] text-[10px] outline-none cursor-pointer transition-colors"
                                                                >
                                                                    <option value={val} className="bg-[#28292c] text-[#e8eaed]">{val}</option>
                                                                    <optgroup label="Standard Palette" className="bg-[#202124] text-[#8ab4f8] font-bold">
                                                                        {COLOR_PALETTE.map(c => (
                                                                            <option key={c.value} value={c.value} className="bg-[#28292c] text-[#e8eaed] font-normal">
                                                                                {c.label}
                                                                            </option>
                                                                        ))}
                                                                    </optgroup>
                                                                </select>
                                                            </div>
                                                        )}

                                                        {field.type === 'image' && (
                                                            <div className="flex flex-col gap-1">
                                                                {val && <button onClick={() => setNestedValue(field.path, '')} className="text-[9px] text-[#f28b82] text-left hover:underline w-max">Clear Image</button>}
                                                                <input type="file" accept="image/*" onChange={handleImageUpload} className="w-full text-[9px] file:mr-2 file:py-0.5 file:px-1 file:rounded file:border-0 file:text-[9px] file:bg-[#3c4043] file:text-[#e8eaed] cursor-pointer" />
                                                            </div>
                                                        )}
                                                        
                                                    </>
                                                )}
                                            </td>

                                            <td className="p-2 text-right">
                                                {/* ẨN NÚT BINDING ĐỐI VỚI CÁC TRƯỜNG TỰ LIÊN KẾT */}
                                                {field.type !== 'tag_selector' && field.type !== 'select' && (
                                                    binding ? (
                                                        <button onClick={() => unbindTag(node.id, field.path)} className="inline-flex items-center gap-1.5 px-2 py-1 bg-[#8ab4f8]/10 text-[#8ab4f8] hover:bg-[#f28b82]/10 hover:text-[#f28b82] border border-[#8ab4f8]/30 hover:border-[#f28b82]/30 rounded transition-colors text-[9px] font-bold w-full justify-between" title="Unbind">
                                                            <span className="truncate max-w-[70px]">{binding.globalTagKey}</span>
                                                            <Unlink size={10} className="shrink-0"/>
                                                        </button>
                                                    ) : (
                                                        <select className="w-full bg-[#28292c] border border-[#3c4043] rounded px-1 py-1 text-[#9aa0a6] text-[9px] outline-none cursor-pointer focus:border-[#81c995]" value="" onChange={(e) => bindTagToProperty(node.id, field.path, e.target.value)}>
                                                            <option value="" disabled>+ Link Tag</option>
                                                            {globalTags.map(tag => <option key={tag} value={tag}>{tag}</option>)}
                                                        </select>
                                                    )
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            {/* GỌI ĐỘC LẬP COMPONENT SCRIPT MODAL */}
            <UIScriptEditorModal 
                isOpen={activeScriptPath !== null}
                title={node.name || "Soft Button"}
                initialScript={activeScriptPath ? (getNestedValue(node, activeScriptPath) || "") : ""}
                initialInAliases={(node as any).input_aliases || {}}   // Lấy config hiện tại
                initialOutAliases={(node as any).output_aliases || {}} // Lấy config hiện tại
                globalTags={globalTags}
                onClose={() => setActiveScriptPath(null)}
                onSave={(finalCode, inAliases, outAliases) => {
                    if (activeScriptPath) {
                        setNestedValue(activeScriptPath, finalCode); // Lưu code JS
                        // Lưu mảng Aliases vào thẳng object Component
                        updateComponentProps(node.id, { 
                            input_aliases: inAliases, 
                            output_aliases: outAliases 
                        });
                    }
                    setActiveScriptPath(null);
                }}
            />
        </>
    );
};