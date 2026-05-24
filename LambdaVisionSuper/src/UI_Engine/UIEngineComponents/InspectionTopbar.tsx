import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    ArrowLeft, FolderOpen, Database, TerminalSquare, 
    Type, GitMerge, Settings, Play, Square, AlertTriangle, Eye, EyeOff,
    ChevronDown
} from 'lucide-react';

import { useUIEngine } from '../UIEngineStores/InspectionStore';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';
import { useKeyboardTriggerStore } from '../UIEngineStores/KeyboardTriggerStore';

// ==========================================================
// DROP DOWN QUẢN LÝ LABEL CONFIG 
// ==========================================================
const NameConfigDropdown = () => {
    const { nameLabelConfig, updateNameLabelConfig } = useUIEngine();
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const LABEL_COLORS = ['#8ab4f8', '#f28b82', '#81c995', '#fcd663', '#e8eaed', '#5f6368'];

    return (
        <div className="relative flex items-center" ref={menuRef}>
            {/* NÚT LABEL DẠNG RỘNG */}
            <button 
                onClick={() => setIsOpen(!isOpen)} 
                className={`flex items-center gap-2 px-3 h-9 rounded-md transition-colors ${nameLabelConfig.isVisible ? 'text-[#81c995] bg-[#81c995]/10 hover:bg-[#81c995]/20' : 'text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#e4e4e7]'}`}
            >
                <Type size={16} strokeWidth={2} />
                <span className="text-[11px] font-bold uppercase tracking-wider">Labels</span>
                <ChevronDown size={14} className={`transition-transform opacity-50 ${isOpen ? 'rotate-180' : ''}`}/>
            </button>

            {isOpen && (
                <div className="absolute top-full mt-2 right-0 w-64 bg-[#18181b] border border-[#27272a] rounded-lg shadow-xl p-3 z-50 flex flex-col gap-3 font-sans text-xs">
                    <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
                        <span className="text-[#e8eaed] font-bold">Viewport Labels</span>
                        <button 
                            onClick={() => updateNameLabelConfig({ isVisible: !nameLabelConfig.isVisible })}
                            className={`p-1.5 rounded-md transition-colors ${nameLabelConfig.isVisible ? 'text-[#81c995] bg-[#81c995]/10 hover:bg-[#81c995]/20' : 'text-[#f43f5e] bg-[#f43f5e]/10 hover:bg-[#f43f5e]/20'}`}
                        >
                            {nameLabelConfig.isVisible ? <Eye size={14} /> : <EyeOff size={14} />}
                        </button>
                    </div>
                    
                    <div className="flex gap-2">
                        <div className="flex flex-col gap-1 w-1/3">
                            <label className="text-[#71717a] text-[10px] uppercase font-bold">Size</label>
                            <input type="number" value={nameLabelConfig.fontSize} onChange={(e) => updateNameLabelConfig({ fontSize: Number(e.target.value) || 10 })} className="w-full bg-[#09090b] border border-[#27272a] text-[#e8eaed] rounded px-2 py-1.5 outline-none focus:border-[#8ab4f8] transition-colors font-mono" />
                        </div>
                        <div className="flex flex-col gap-1 w-2/3">
                            <label className="text-[#71717a] text-[10px] uppercase font-bold">Font</label>
                            <select value={nameLabelConfig.fontFamily} onChange={(e) => updateNameLabelConfig({ fontFamily: e.target.value })} className="w-full bg-[#09090b] border border-[#27272a] text-[#e8eaed] rounded px-2 py-1.5 outline-none focus:border-[#8ab4f8] transition-colors">
                                <option value="Arial">Arial</option>
                                <option value="Verdana">Verdana</option>
                                <option value="monospace">Monospace</option>
                            </select>
                        </div>
                    </div>
                    
                    <div className="flex flex-col gap-1">
                        <label className="text-[#71717a] text-[10px] uppercase font-bold">Color</label>
                        <div className="flex items-center justify-between bg-[#09090b] border border-[#27272a] p-1.5 rounded-md">
                            {LABEL_COLORS.map(color => (
                                <div key={color} onClick={() => updateNameLabelConfig({ fontColor: color })} className={`w-5 h-5 rounded-full cursor-pointer transition-transform ${nameLabelConfig.fontColor === color ? 'ring-2 ring-white scale-110' : 'hover:scale-110'}`} style={{ backgroundColor: color }} />
                            ))}
                            <div className="w-px h-5 bg-[#27272a] mx-1"></div>
                            <div className="relative w-5 h-5 rounded-full overflow-hidden border border-[#5f6368] cursor-pointer hover:scale-110 transition-transform">
                                <input type="color" value={nameLabelConfig.fontColor} onChange={(e) => updateNameLabelConfig({ fontColor: e.target.value })} className="absolute -top-2 -left-2 w-10 h-10 cursor-pointer" />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// ==========================================================
// TOPBAR CHÍNH
// ==========================================================
export const InspectionTopbar = () => {
    const navigate = useNavigate();
    const { showTerminalLog, toggleTerminalLog, openFileManager } = useUIEngine();
    const sequencerStore = useSequencerStore();
    const toggleSettings = useKeyboardTriggerStore(state => state.toggleSettingsModal);

    return (
        // Sử dụng Flex chia 3 phần đều nhau, tăng height lên h-14 để nút nhìn bề thế hơn
        <header className="flex items-center justify-between h-14 bg-[#111113] border-b border-[#27272a] px-4 z-30 shrink-0 select-none">
            
            {/* CỘT TRÁI: Nhóm Navigation */}
            <div className="flex-1 flex items-center gap-3 justify-start min-w-[300px]">
                <button 
                    onClick={() => navigate('/')} 
                    className="flex items-center gap-2 px-3 h-9 rounded-md text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#e4e4e7] transition-colors" 
                >
                    <ArrowLeft size={16} strokeWidth={2}/>
                    <span className="text-[11px] font-bold uppercase tracking-wider hidden sm:block">Dashboard</span>
                </button>
                
                <div className="w-px h-5 bg-[#27272a] mx-1"></div>

                <div className="flex flex-col justify-center">
                    <h1 className="font-extrabold text-[#e4e4e7] text-[13px] tracking-wide">Lambda UI</h1>
                    <span className="text-[#a1a1aa] text-[10px] font-mono tracking-widest uppercase">Editor</span>
                </div>
            </div>
            
            {/* CỘT GIỮA: Nút Engine (To & Rộng) */}
            <div className="flex-1 flex items-center justify-center gap-3">
                {sequencerStore.isGraphDirty && (
                    <span className="text-amber-400 text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 px-3 h-9 bg-amber-400/10 rounded-md border border-amber-400/20">
                        <AlertTriangle size={14} /> Dirty
                    </span>
                )}

                {!sequencerStore.isEngineRunning ? (
                    <button 
                        onClick={() => sequencerStore.runEngine()} 
                        disabled={sequencerStore.isGraphDirty || sequencerStore.isCompiling}
                        className="flex items-center gap-2 px-6 h-9 bg-[#10b981]/10 text-[#10b981] hover:bg-[#10b981]/20 border border-[#10b981]/30 rounded-md text-[12px] font-bold uppercase tracking-widest transition-colors disabled:opacity-50"
                    >
                        <Play size={16} fill="currentColor" /> Start Engine
                    </button>
                ) : (
                    <button 
                        onClick={() => sequencerStore.stopEngine()} 
                        className="flex items-center gap-2 px-6 h-9 bg-[#f43f5e]/10 text-[#f43f5e] hover:bg-[#f43f5e]/20 border border-[#f43f5e]/30 rounded-md text-[12px] font-bold uppercase tracking-widest transition-colors shadow-[0_0_15px_rgba(244,63,94,0.1)]"
                    >
                        <Square size={14} fill="currentColor" /> Stop Engine
                    </button>
                )}
            </div>

            {/* CỘT PHẢI: Khay công cụ Nút Rộng (Wide Buttons) */}
            <div className="flex-1 flex items-center justify-end gap-1.5 min-w-[300px]">
                
                <button 
                    onClick={() => openFileManager('manage')} 
                    className="flex items-center gap-2 px-3 h-9 rounded-md text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#8ab4f8] transition-colors"
                >
                    <FolderOpen size={16} strokeWidth={2}/>
                    <span className="text-[11px] font-bold uppercase tracking-wider hidden xl:block">Assets</span>
                </button>
                
                <button 
                    onClick={() => useTagDb.setState({ isGlobalTagsTableOpen: true })} 
                    className="flex items-center gap-2 px-3 h-9 rounded-md text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#fcd663] transition-colors"
                >
                    <Database size={16} strokeWidth={2}/>
                    <span className="text-[11px] font-bold uppercase tracking-wider hidden xl:block">Tags</span>
                </button>

                <button 
                    onClick={toggleTerminalLog} 
                    className={`flex items-center gap-2 px-3 h-9 rounded-md transition-colors ${showTerminalLog ? 'text-[#8ab4f8] bg-[#8ab4f8]/10' : 'text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#e4e4e7]'}`}
                >
                    <TerminalSquare size={16} strokeWidth={2}/>
                    <span className="text-[11px] font-bold uppercase tracking-wider hidden xl:block">Logs</span>
                </button>

                <div className="w-px h-5 bg-[#27272a] mx-0.5"></div>
                
                <NameConfigDropdown />

                <div className="w-px h-5 bg-[#27272a] mx-0.5"></div>

                <button 
                    onClick={() => navigate('/sequencer')} 
                    className="flex items-center gap-2 px-3 h-9 rounded-md text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#c58af9] transition-colors"
                >
                    <GitMerge size={16} strokeWidth={2}/>
                    <span className="text-[11px] font-bold uppercase tracking-wider hidden xl:block">SEQUENCERS</span>
                </button>

                {/* Nút Settings không cần text, để góc phải làm điểm nhấn */}
                <button 
                    onClick={toggleSettings} 
                    className="flex items-center justify-center w-9 h-9 ml-1 rounded-md text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#e4e4e7] transition-colors"
                >
                    <Settings size={18} strokeWidth={2}/>
                </button>

            </div>
        </header>
    );
};