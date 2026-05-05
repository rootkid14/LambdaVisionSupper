import React, { useState } from 'react';
import { useUIEngine } from '../UIEngineStores/InspectionStore';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { Settings, Trash2, Box, Type, Circle, Edit2, Maximize, Layout, Monitor, Unlink, KeyIcon, MousePointer2 } from 'lucide-react';
import { COLOR_PALETTE } from "../../utils/ColorConst";


export const CreateButtonModal = () => {
    const { createButtonModal, closeCreateButtonModal, addComponent } = useUIEngine();
    const globalTags = useTagDb(state => Object.keys(state.tags));
    
    // State tạm thời để lưu thông tin trước khi nhấn Create
    const [config, setConfig] = useState({
        label: "START",
        targetTag: "",
        actionType: "toggle" as any,
        color: "#3c4043"
    });

    if (!createButtonModal.isOpen) return null;

    const handleCreate = (e: React.FormEvent) => {
        e.preventDefault();
        // Gọi addComponent với đầy đủ tham số cấu hình
        // Lưu ý: Bạn cần cập nhật hàm addComponent trong Store để nhận thêm config object này
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
                    {/* Nhập nhãn nút */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[#9aa0a6] font-bold ml-1">BUTTON LABEL</label>
                        <input autoFocus value={config.label} onChange={e => setConfig({...config, label: e.target.value})}
                               className="w-full bg-[#171717] border border-[#3c4043] rounded-lg px-3 py-2 text-[#e8eaed] outline-none focus:border-[#8ab4f8] transition-colors"
                               placeholder="e.g. RESET, START..." />
                    </div>

                    {/* Chọn Tag mục tiêu */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[#9aa0a6] font-bold ml-1">TARGET TAG (CONTROL)</label>
                        <select value={config.targetTag} onChange={e => setConfig({...config, targetTag: e.target.value})}
                                className="w-full bg-[#171717] border border-[#3c4043] rounded-lg px-3 py-2 text-[#e8eaed] outline-none cursor-pointer">
                            <option value="">-- No Tag --</option>
                            {globalTags.map(tag => <option key={tag} value={tag}>{tag}</option>)}
                        </select>
                    </div>

                    {/* Chọn kiểu tác động */}
                    <div className="flex flex-col gap-1.5">
                        <label className="text-[#9aa0a6] font-bold ml-1">ACTION TYPE</label>
                        <div className="grid grid-cols-2 gap-2">
                            {['toggle', 'pulse', 'setToTrue', 'setToFalse'].map(type => (
                                <button key={type} type="button" onClick={() => setConfig({...config, actionType: type as any})}
                                        className={`py-1.5 rounded border transition-all font-bold ${config.actionType === type ? 'bg-[#8ab4f8] text-[#202124] border-[#8ab4f8]' : 'bg-[#171717] text-[#9aa0a6] border-[#3c4043] hover:border-[#5f6368]'}`}>
                                    {type}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Chọn màu sắc */}
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

    // Khởi tạo value khi modal mở
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
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#8ab4f8] hover:text-[#202124]" onClick={() => openPropertiesPanel(actionMenu.target_id)}><Settings size={14} /> Properties</button>
                    <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-[#f28b82] hover:text-[#202124] text-[#f28b82]" onClick={() => deleteComponents([actionMenu.target_id])}><Trash2 size={14} /> Delete</button>
                </>
            )}
            {['bounding_box', 'bounding_circle', 'text', 'line', 'soft_button'].includes(actionMenu.target_type) && (
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
    
    if (!propertyPanel.isOpen || !propertyPanel.target_id) return null;
    const node = components_map[propertyPanel.target_id];
    if (!node) return null;

    // FIX LỖI CRASH: Đảm bảo hàm luôn return mảng `fields` hợp lệ
    const getAvailableFields = () => {
        const fields = [];
        // Layout & Data
        if(node.isVisible !== undefined) fields.push({ path: 'isVisible', label: 'Visible', type: 'boolean' });
        if(node.x !== undefined) fields.push({ path: 'x', label: 'X', type: 'number' });
        if(node.y !== undefined) fields.push({ path: 'y', label: 'Y', type: 'number' });
        if(node.size_x !== undefined) fields.push({ path: 'size_x', label: 'Width', type: 'number' });
        if(node.size_y !== undefined) fields.push({ path: 'size_y', label: 'Height', type: 'number' });
        if(node.radius !== undefined) fields.push({ path: 'radius', label: 'Radius', type: 'number' });
        if(node.content !== undefined) fields.push({ path: 'content', label: 'Text', type: 'string' });
        
        // Styles
        if(node.style) {
            if(node.style.border_thickness !== undefined) fields.push({ path: 'style.border_thickness', label: 'Stroke W', type: 'number' });
            if(node.style.strokeColor !== undefined) fields.push({ path: 'style.strokeColor', label: 'Stroke Color', type: 'color' });
            if(node.style.fillColor !== undefined) fields.push({ path: 'style.fillColor', label: 'Fill Color', type: 'color' });
            if(node.style.fontColor !== undefined) fields.push({ path: 'style.fontColor', label: 'Font Color', type: 'color' });
            if(node.style.fontSize !== undefined) fields.push({ path: 'style.fontSize', label: 'Font Size', type: 'number' });
            
            // CẢI TIẾN: Hỗ trợ 2 trường ảnh cho Frame
            if(node.type === 'frame') {
                fields.push({ path: 'style.default_image', label: 'Default Img', type: 'image' }); 
                fields.push({ path: 'style.bgImage', label: 'Runtime Img', type: 'image' });       
            }

            if (node.type === 'soft_button') {
                fields.push({ path: 'content', label: 'Button Text', type: 'string' });
                fields.push({ path: 'targetTag', label: 'Target Tag', type: 'tag_selector' }); 
                fields.push({ path: 'actionType', label: 'Action Type', type: 'select', options: ['toggle', 'setToTrue', 'setToFalse', 'pulse'] });
                fields.push({ path: 'style.fillColor', label: 'Normal Color', type: 'color' });
                fields.push({ path: 'style.activeColor', label: 'Active Color', type: 'color' }); // <--- BỔ SUNG DÒNG NÀY
                fields.push({ path: 'style.cornerRadius', label: 'Round Corner', type: 'number' });
            }
        }
        
        return fields; // <--- CỰC KỲ QUAN TRỌNG: Không có dòng này là sập màn hình!
    };

    // Helper functions để đọc ghi object lồng nhau (Nested object: style.strokeColor)
    const getNestedValue = (obj: any, path: string) => path.split('.').reduce((o, p) => o?.[p], obj);
    const setNestedValue = (path: string, value: any) => {
        if (path.startsWith('style.')) {
            const styleProp = path.split('.')[1];
            updateComponentProps(node.id, { style: { ...node.style, [styleProp]: value } });
        } else {
            updateComponentProps(node.id, { [path]: value });
        }
    };

    // Upload Ảnh Base64
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
            {/* BACKDROP TÀNG HÌNH CHẶN CLICK & ĐÓNG PANEL */}
            <div 
                className="fixed inset-0 z-[35] bg-transparent" 
                onClick={closePropertiesPanel}
                title="Click outside to close"
            ></div>

            {/* BẢNG PROPERTIES PANEL CHÍNH */}
            <div className="absolute top-20 right-4 w-[480px] bg-[#28292c] border border-[#3c4043] shadow-2xl z-40 rounded-xl font-sans flex flex-col max-h-[80vh]">
                
                {/* HEADER - INLINE RENAME */}
                <div className="flex justify-between items-center px-4 py-3 border-b border-[#3c4043] bg-[#303134] rounded-t-xl shrink-0">
                    <div className="flex flex-col flex-1 mr-4">
                        {/* SỬA TÊN TRỰC TIẾP Ở ĐÂY */}
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
                                            
                                            {/* CỘT INPUT LOCAL VALUE TÙY THEO TYPE */}
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

                                            {/* CỘT BINDING */}
                                            <td className="p-2 text-right">
                                                {/* CẢI TIẾN 3: Bỏ chặn điều kiện field.type, cho phép Bind Tag ở mọi trường[cite: 17] */}
                                                {binding ? (
                                                    <button onClick={() => unbindTag(node.id, field.path)} className="inline-flex items-center gap-1.5 px-2 py-1 bg-[#8ab4f8]/10 text-[#8ab4f8] hover:bg-[#f28b82]/10 hover:text-[#f28b82] border border-[#8ab4f8]/30 hover:border-[#f28b82]/30 rounded transition-colors text-[9px] font-bold w-full justify-between" title="Unbind">
                                                        <span className="truncate max-w-[70px]">{binding.globalTagKey}</span>
                                                        <Unlink size={10} className="shrink-0"/>
                                                    </button>
                                                ) : (
                                                    <select className="w-full bg-[#28292c] border border-[#3c4043] rounded px-1 py-1 text-[#9aa0a6] text-[9px] outline-none cursor-pointer focus:border-[#81c995]" value="" onChange={(e) => bindTagToProperty(node.id, field.path, e.target.value)}>
                                                        <option value="" disabled>+ Link Tag</option>
                                                        {globalTags.map(tag => <option key={tag} value={tag}>{tag}</option>)}
                                                    </select>
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
        </>
    );
};

