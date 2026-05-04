import React, { useState, useEffect } from 'react';
import { useKeyboardTriggerStore, TriggerActionType } from '../UIEngineStores/KeyboardTriggerStore';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { Settings, Plus, Trash2, Keyboard, X } from 'lucide-react';

export const SettingsModal = () => {
    const { isSettingsModalOpen, shortcuts, toggleSettingsModal, addShortcut, updateShortcut, removeShortcut } = useKeyboardTriggerStore();
    
    // --- CẢI TIẾN: CHỈ LỌC RA CÁC TAGS CÓ KIỂU BOOLEAN ---
    const booleanTags = useTagDb(state => 
        Object.entries(state.tags)
            .filter(([_, value]) => typeof value === 'boolean')
            .map(([key]) => key)
    );

    const [recordingId, setRecordingId] = useState<string | null>(null);

    // Lắng nghe phím khi đang ở chế độ Record
    useEffect(() => {
        if (!recordingId) return;

        const handleRecordKey = (e: KeyboardEvent) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Bỏ qua các phím Modifier đứng một mình
            if (['Shift', 'Control', 'Alt', 'Meta'].includes(e.key)) return;

            // Format tên phím cho đẹp (Vd: Space, Enter, Numpad1...)
            let label = e.code.replace('Key', '').replace('Digit', '');
            if (e.code === 'Space') label = 'SPACE';
            
            updateShortcut(recordingId, { 
                keyCode: e.code, 
                keyLabel: label.toUpperCase() 
            });
            
            setRecordingId(null); // Tắt chế độ record
        };

        window.addEventListener('keydown', handleRecordKey);
        return () => window.removeEventListener('keydown', handleRecordKey);
    }, [recordingId, updateShortcut]);

    if (!isSettingsModalOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-black/20 flex items-center justify-center font-sans">
            <div className="bg-[#202124] border border-[#3c4043] rounded-xl shadow-2xl w-[700px] overflow-hidden flex flex-col max-h-[85vh]">
                
                {/* HEADER */}
                <div className="flex items-center justify-between px-5 py-4 bg-[#303134] border-b border-[#3c4043]">
                    <div className="flex items-center gap-3 text-[#e8eaed]">
                        <Settings className="text-[#8ab4f8]" size={20} />
                        <h2 className="font-bold text-sm tracking-wide uppercase">System Settings</h2>
                    </div>
                    <button onClick={toggleSettingsModal} className="p-1 hover:bg-[#3c4043] rounded-md transition-colors text-[#9aa0a6] hover:text-[#f28b82]">
                        <X size={20} />
                    </button>
                </div>

                {/* CONTENT */}
                <div className="p-5 flex-1 overflow-y-auto custom-scrollbar">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h3 className="text-[#8ab4f8] font-bold text-xs uppercase tracking-wider mb-1 flex items-center gap-2">
                                <Keyboard size={14}/> Keyboard Triggers
                            </h3>
                            <p className="text-[#9aa0a6] text-[10px]">Map physical keys to Boolean Global Tags for manual triggers.</p>
                        </div>
                        <button onClick={addShortcut} className="flex items-center gap-2 px-3 py-1.5 bg-[#8ab4f8]/10 text-[#8ab4f8] hover:bg-[#8ab4f8]/20 border border-[#8ab4f8]/30 rounded text-xs font-bold transition-colors">
                            <Plus size={14} /> ADD TRIGGER
                        </button>
                    </div>

                    <div className="bg-[#171717] rounded-lg border border-[#3c4043] overflow-hidden">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-[#28292c] border-b border-[#3c4043]">
                                <tr>
                                    <th className="p-3 text-[#9aa0a6] font-bold uppercase text-[10px] w-1/4">Key Bind</th>
                                    <th className="p-3 text-[#9aa0a6] font-bold uppercase text-[10px] w-1/4">Action</th>
                                    <th className="p-3 text-[#9aa0a6] font-bold uppercase text-[10px] w-2/4">Target Tag (Boolean Only)</th>
                                    <th className="p-3 w-10"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#3c4043]">
                                {shortcuts.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="p-8 text-center text-[#5f6368] italic">No keyboard triggers assigned.</td>
                                    </tr>
                                ) : (
                                    shortcuts.map(shortcut => (
                                        <tr key={shortcut.id} className="hover:bg-[#202124] transition-colors">
                                            {/* CỘT 1: CHỌN PHÍM */}
                                            <td className="p-2">
                                                <button 
                                                    onClick={() => setRecordingId(shortcut.id)}
                                                    className={`w-full py-1.5 px-2 rounded border font-mono text-[11px] font-bold transition-all ${
                                                        recordingId === shortcut.id 
                                                        ? 'bg-[#fcd663]/20 text-[#fcd663] border-[#fcd663] animate-pulse' 
                                                        : shortcut.keyCode ? 'bg-[#3c4043] text-[#e8eaed] border-[#5f6368] hover:border-[#8ab4f8]' : 'bg-[#f28b82]/10 text-[#f28b82] border-[#f28b82]/50 border-dashed'
                                                    }`}
                                                >
                                                    {recordingId === shortcut.id ? 'PRESS ANY KEY...' : shortcut.keyLabel}
                                                </button>
                                            </td>

                                            {/* CỘT 2: CHỌN LOẠI ACTION */}
                                            <td className="p-2">
                                                <select 
                                                    value={shortcut.actionType}
                                                    onChange={(e) => updateShortcut(shortcut.id, { actionType: e.target.value as TriggerActionType })}
                                                    className="w-full bg-[#28292c] border border-[#3c4043] rounded px-2 py-1.5 text-[#e8eaed] outline-none focus:border-[#8ab4f8] cursor-pointer"
                                                >
                                                    <option value="toggle">Toggle (T/F)</option>
                                                    <option value="setToTrue">Set to TRUE</option>
                                                    <option value="setToFalse">Set to FALSE</option>
                                                    <option value="pulse">Pulse (Hold)</option>
                                                </select>
                                            </td>

                                            {/* CỘT 3: CHỌN TAG - GIỜ ĐÂY CHỈ HIỂN THỊ BOOLEAN TAGS */}
                                            <td className="p-2">
                                                <select 
                                                    value={shortcut.targetTag}
                                                    onChange={(e) => updateShortcut(shortcut.id, { targetTag: e.target.value })}
                                                    className={`w-full bg-[#28292c] border rounded px-2 py-1.5 outline-none cursor-pointer ${shortcut.targetTag ? 'border-[#3c4043] text-[#8ab4f8] focus:border-[#8ab4f8]' : 'border-[#f28b82]/50 text-[#f28b82] border-dashed'}`}
                                                >
                                                    <option value="" disabled>Select a Boolean Tag...</option>
                                                    {booleanTags.length > 0 ? (
                                                        booleanTags.map(tag => <option key={tag} value={tag} className="text-[#e8eaed]">{tag}</option>)
                                                    ) : (
                                                        <option value="" disabled className="italic text-[#f28b82]">No boolean tags found in DB</option>
                                                    )}
                                                </select>
                                            </td>

                                            {/* CỘT 4: NÚT XÓA */}
                                            <td className="p-2 text-right">
                                                <button onClick={() => removeShortcut(shortcut.id)} className="p-1.5 text-[#5f6368] hover:text-[#f28b82] hover:bg-[#f28b82]/10 rounded transition-colors">
                                                    <Trash2 size={14}/>
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};