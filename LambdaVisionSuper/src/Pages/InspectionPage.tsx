import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, TerminalSquare, Image as ImageIcon, Plus, ArrowLeft, GitMerge, Settings, Type, Eye, EyeOff, Play, Square, AlertTriangle, FolderOpen, CheckCircle2, Loader2, XCircle, Terminal, ChevronDown, ChevronUp, FileJson } from 'lucide-react';
import { useUIEngine } from '../UI_Engine/UIEngineStores/InspectionStore';
import { useTagDb } from '../UI_Engine/UIEngineStores/GlobalTagsStore';
import { InspectionCanvas } from '../UI_Engine/UIEngineComponents/InspectionCanvas';
import { ActionMenu, UIPropertiesPanel, RenameModal, CreateButtonModal } from '../UI_Engine/UIEngineComponents/FloatingPanels';
import { TagManagerTable } from '../UI_Engine/UIEngineComponents/GlobalTagsTable';
import { TerminalLog } from '../UI_Engine/SequencerComponents/TerminalLog';
import { useKeyboardTriggerStore } from '../UI_Engine/UIEngineStores/KeyboardTriggerStore';
import { useKeyboardTrigger } from '../UI_Engine/hooks/useKeyboardTrigger';
import { SettingsModal } from '../UI_Engine/UIEngineComponents/SettingModal';
import { useSequencerStore } from '../UI_Engine/UIEngineStores/SequencerStores';
import { ProjectCompiler } from '../ProjectCompiler/ProjectCompilerCore/ProjectCompilerCore';
import { FileManagerModal } from '../UI_Engine/UIEngineComponents/FileManagerModal';
import { FleetAPI } from '../api/fleetApi';
import { InspectionTopbar } from '../UI_Engine/UIEngineComponents/InspectionTopbar';


// ==========================================================
// COMPONENT IMPORT MODAL (GIỮ NGUYÊN HOẠT ĐỘNG THEO CORE)
// ==========================================================
const ModernImportModal = ({ file, onClose }: { file: File, onClose: () => void }) => {
    type BootStatus = 'reading' | 'restoring' | 'fleet' | 'logic' | 'compiling' | 'done' | 'failed';
    const [status, setStatus] = useState<BootStatus>('reading');
    const [logs, setLogs] = useState<{type: string, msg: string}[]>([]);
    const [showLogs, setShowLogs] = useState(true);
    
    const hasStarted = useRef(false);

    const STEPS = [
        { id: 'reading', label: 'Phân tích cấu trúc Project' },
        { id: 'restoring', label: 'Khôi phục Giao diện & Biến (UI/Tags)' },
        { id: 'fleet', label: 'Khởi động Bus Mạng (Fleet Network)' },
        { id: 'logic', label: 'Đồng bộ AI & Logic Objects (RAM)' },
        { id: 'compiling', label: 'Biên dịch Hệ thống (Compile)' },
    ];

    useEffect(() => {
        if (hasStarted.current) return;
        hasStarted.current = true;

        const runImport = async () => {
            try {
                await ProjectCompiler.importProject(
                    file,
                    (type, msg) => setLogs(prev => [...prev, { type, msg }]),
                    (newStatus) => setStatus(newStatus)
                );
            } catch (error) {
                // Core logic tự động throw trạng thái failed thông qua callback
            }
        };

        runImport();
    }, [file]);

    const getCurrentStepIndex = () => {
        if (status === 'done') return 5;
        if (status === 'failed') {
          return STEPS.findIndex(s => 
            s.id === (logs[logs.length - 1]?.msg.includes('Biên dịch') ? 'compiling' : status)
          );
        }
        return STEPS.findIndex(s => s.id === status);
    };

    const stepIndex = getCurrentStepIndex();

    return (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center font-sans select-none">
            <div className="bg-[#202124] border border-[#3c4043] rounded-2xl shadow-2xl w-[800px] flex flex-col overflow-hidden">
                
                {/* Header */}
                <div className="px-6 py-5 border-b border-[#3c4043] bg-[#28292c] flex items-center gap-4">
                    <div className="p-3 bg-[#8ab4f8]/10 rounded-xl">
                        <FileJson size={24} className="text-[#8ab4f8]" />
                    </div>
                    <div>
                        <h2 className="text-[#e8eaed] font-extrabold text-lg">LOADING A PROGRAM FILE</h2>
                        <p className="text-[#9aa0a6] text-s font-mono truncate max-w-[300px]">{file.name}</p>
                    </div>
                </div>

                {/* Stepper */}
                <div className="p-6 flex flex-col gap-4">
                    {STEPS.map((step, idx) => {
                        const isDone = idx < stepIndex || status === 'done';
                        const isActive = idx === stepIndex && status !== 'done' && status !== 'failed';
                        const isFailed = status === 'failed' && idx === stepIndex;
                        const isWaiting = idx > stepIndex;

                        return (
                            <div key={step.id} className={`flex items-center gap-4 transition-opacity duration-300 ${isWaiting ? 'opacity-40' : 'opacity-100'}`}>
                                <div className="relative shrink-0">
                                    {isDone && <CheckCircle2 size={20} className="text-[#81c995]" />}
                                    {isActive && <Loader2 size={20} className="text-[#8ab4f8] animate-spin" />}
                                    {isFailed && <XCircle size={20} className="text-[#f28b82]" />}
                                    {isWaiting && <div className="w-5 h-5 rounded-full border-2 border-[#5f6368]"></div>}
                                    
                                    {idx !== STEPS.length - 1 && (
                                        <div className={`absolute top-6 left-1/2 -translate-x-1/2 w-0.5 h-4 ${isDone ? 'bg-[#81c995]' : 'bg-[#3c4043]'}`}></div>
                                    )}
                                </div>
                                <span className={`text-sm font-bold ${isActive ? 'text-[#e8eaed]' : isFailed ? 'text-[#f28b82]' : 'text-[#9aa0a6]'}`}>
                                    {step.label}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Kết quả & Log Terminal */}
                <div className="px-6 py-4 bg-[#28292c] border-t border-[#3c4043] flex flex-col gap-3">
                    <button 
                        onClick={() => setShowLogs(!showLogs)}
                        className="flex items-center gap-2 text-xs font-bold text-[#9aa0a6] hover:text-[#e8eaed] transition-colors self-start"
                    >
                        {showLogs ? <ChevronUp size={18}/> : <ChevronDown size={18}/>} 
                        {showLogs ? 'HIDE DETAILS' : 'SHOW DETAILS'}
                    </button>

                    {showLogs && (
                        <div className="h-40 bg-[#171717] rounded-lg border border-[#3c4043] p-3 overflow-y-auto flex flex-col gap-1.5 custom-scrollbar font-mono text-[14px]">
                            {logs.map((log, i) => (
                                <div key={i} className={`flex items-start gap-2 ${
                                    log.type === 'error' ? 'text-[#f28b82]' :
                                    log.type === 'warning' ? 'text-[#fcd663]' :
                                    log.type === 'success' ? 'text-[#81c995]' : 'text-[#9aa0a6]'
                                }`}>
                                    <span className="shrink-0 mt-0.5 opacity-50"><Terminal size={15}/></span>
                                    <span>{log.msg}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {(status === 'done' || status === 'failed') && (
                        <button 
                            onClick={onClose} 
                            className={`w-full py-2.5 rounded-lg text-sm font-bold transition-all mt-2 ${
                                status === 'done' 
                                ? 'bg-[#81c995] hover:bg-[#a8dab5] text-[#202124] shadow-[0_0_15px_rgba(129,201,149,0.3)]' 
                                : 'bg-[#f28b82] hover:bg-[#f6aea9] text-[#202124]'
                            }`}
                        >
                            {status === 'done' ? 'COMPLETE LOAD' : 'CLOSE (ERROR)'}
                        </button>
                    )}
                </div>

            </div>
        </div>
    );
};


// ==========================================================
// DROP DOWN QUẢN LÝ LABEL CONFIG
// ==========================================================
export const NameConfigDropdown = () => {
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
        <div className="relative" ref={menuRef}>
            <button 
                onClick={() => setIsOpen(!isOpen)} 
                className={`flex items-center gap-2 px-4 py-1.5 rounded-md transition-colors text-[11px] font-bold ${nameLabelConfig.isVisible ? 'text-[#81c995] bg-[#81c995]/10 hover:bg-[#81c995]/20' : 'text-[#9aa0a6] hover:bg-[#3c4043] hover:text-[#81c995]'}`}
            >
                <Type size={14} /> LABELS
            </button>

            {isOpen && (
                <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 w-56 bg-[#28292c] border border-[#3c4043] rounded-lg shadow-2xl p-3 z-50 flex flex-col gap-3 font-sans text-xs">
                    <div className="flex items-center justify-between border-b border-[#3c4043] pb-2">
                        <span className="text-[#9aa0a6] font-bold">Show Labels</span>
                        <button 
                            onClick={() => updateNameLabelConfig({ isVisible: !nameLabelConfig.isVisible })}
                            className={`p-1 rounded transition-colors ${nameLabelConfig.isVisible ? 'text-[#81c995] bg-[#81c995]/20' : 'text-[#f28b82] bg-[#f28b82]/20'}`}
                        >
                            {nameLabelConfig.isVisible ? <Eye size={16} /> : <EyeOff size={16} />}
                        </button>
                    </div>
                    <div className="flex gap-2">
                        <div className="flex flex-col gap-1 w-1/3">
                            <label className="text-[#5f6368] text-[10px] uppercase font-bold">Size</label>
                            <input type="number" value={nameLabelConfig.fontSize} onChange={(e) => updateNameLabelConfig({ fontSize: Number(e.target.value) || 10 })} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] rounded px-2 py-1 outline-none focus:border-[#8ab4f8]" />
                        </div>
                        <div className="flex flex-col gap-1 w-2/3">
                            <label className="text-[#5f6368] text-[10px] uppercase font-bold">Font</label>
                            <select value={nameLabelConfig.fontFamily} onChange={(e) => updateNameLabelConfig({ fontFamily: e.target.value })} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] rounded px-2 py-1 outline-none focus:border-[#8ab4f8] cursor-pointer">
                                <option value="Arial">Arial</option>
                                <option value="Verdana">Verdana</option>
                                <option value="monospace">Monospace</option>
                            </select>
                        </div>
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="text-[#5f6368] text-[10px] uppercase font-bold">Color</label>
                        <div className="flex items-center justify-between bg-[#171717] border border-[#3c4043] p-1.5 rounded">
                            {LABEL_COLORS.map(color => (
                                <div key={color} onClick={() => updateNameLabelConfig({ fontColor: color })} className={`w-5 h-5 rounded-full cursor-pointer border-2 transition-all ${nameLabelConfig.fontColor === color ? 'border-white scale-110' : 'border-transparent hover:scale-110'}`} style={{ backgroundColor: color }} />
                            ))}
                            <div className="relative w-5 h-5 rounded-full overflow-hidden border border-[#5f6368] cursor-pointer">
                                <input type="color" value={nameLabelConfig.fontColor} onChange={(e) => updateNameLabelConfig({ fontColor: e.target.value })} className="absolute -top-2 -left-2 w-10 h-10 cursor-pointer" />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};




// ==========================================
// THUMBNAIL SIDEBAR QUẢN LÝ MÀN HÌNH CON
// ==========================================
const ThumbnailSidebar = () => {
    const { components_map, activeScreenId, changeScreen, addScreen, openActionMenu } = useUIEngine();
    const screens = Object.values(components_map).filter((n:any) => n.type === 'screen');

    return (
        <div className="w-56 bg-[#18181b] border-r border-white/5 flex flex-col z-10 shadow-xl shrink-0">
            <div className="p-3 border-b border-white/5 flex justify-between items-center bg-[#111113]">
                <span className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-widest">Screens</span>
                <button onClick={addScreen} className="p-1.5 rounded-md hover:bg-white/10 text-[#a1a1aa] hover:text-white transition-colors">
                    <Plus size={14} />
                </button>
            </div>
            <div className="flex-1 p-3 flex flex-col gap-3 overflow-y-auto custom-scrollbar">
                {screens.map((s:any) => (
                    <div 
                        key={s.id} 
                        onClick={() => changeScreen(s.id)} 
                        onContextMenu={(e) => { e.preventDefault(); openActionMenu(s.id, 'thumbnail', e.clientX, e.clientY, 0, 0); }} 
                        className={`cursor-pointer rounded-lg border p-3 flex flex-col items-center gap-2 transition-all shadow-sm ${activeScreenId === s.id ? 'border-[#8ab4f8] bg-[#8ab4f8]/10' : 'border-white/5 bg-[#09090b] hover:border-white/20'}`}
                    >
                        <div className="w-full aspect-video bg-[#111113] rounded border border-white/5 flex items-center justify-center pointer-events-none">
                             <ImageIcon size={24} className={activeScreenId === s.id ? 'text-[#8ab4f8]' : 'text-[#52525b]'} />
                        </div>
                        <span className={`text-[10px] font-bold uppercase truncate w-full text-center tracking-wider ${activeScreenId === s.id ? 'text-[#8ab4f8]' : 'text-[#a1a1aa]'}`}>{s.name}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};


// ==========================================
// MÀN HÌNH CHÍNH INSPECTION PAGE
// ==========================================
export const InspectionPage = () => {
    const isTagsOpen = useTagDb(state => state.isGlobalTagsTableOpen);
    const { showTerminalLog, importFileContext, setImportFile, changeScreen, components_map, fileManagerContext, closeFileManager } = useUIEngine();
    const sequencerStore = useSequencerStore();
    useKeyboardTrigger();

    const activeScreenTagValue = useTagDb(state => state.tags['SYS_ACTIVE_SCREEN']);

    useEffect(() => {
        if (sequencerStore.isEngineRunning && activeScreenTagValue && typeof activeScreenTagValue === 'string') {
            const targetScreen = Object.values(components_map).find(
                (c: any) => c.type === 'screen' && c.name === activeScreenTagValue
            );
            if (targetScreen) {
                changeScreen(targetScreen.id); 
            }
        }
    }, [activeScreenTagValue, sequencerStore.isEngineRunning, changeScreen, components_map]);

    const handleServerFileLoad = (filename: string, fileContent: any) => {
        const blob = new Blob([JSON.stringify(fileContent, null, 2)], { type: 'application/json' });
        const virtualFile = new File([blob], filename, { type: 'application/json' });
        setImportFile(virtualFile); 
        closeFileManager();
    };

    const handleServerFileSave = async (filename: string) => {
        try {
            const bundle = await ProjectCompiler.generateProjectBundle(); 
            const finalName = filename.endsWith('.json') ? filename : `${filename}.json`;
            const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
            const fileToUpload = new File([blob], finalName, { type: 'application/json' });
            await FleetAPI.master_uploadFile(fileToUpload, 'projects');
            closeFileManager();
        } catch (error) {
            console.error("Lỗi khi lưu lên Server: ", error);
            alert("Lưu thất bại, vui lòng kiểm tra kết nối với Master Node!");
        }
    };

    return (
        // Đổi màu nền bao quát thành nền đen cực sâu của App chuyên nghiệp
        <div className="h-screen w-screen bg-[#09090b] text-[#e8eaed] flex flex-col overflow-hidden font-sans relative select-none">
            
            {importFileContext && (
                <ModernImportModal file={importFileContext} onClose={() => setImportFile(null)} />
            )}

            {/* CHÈN COMPONENT TOPBAR MỚI VÀO ĐÂY */}
            <InspectionTopbar />

            {/* BỐ CỤC KHU VỰC THIẾT KẾ CANVAS */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="flex-1 flex overflow-hidden">
                    <ThumbnailSidebar />
                    <InspectionCanvas />
                </div>
                {showTerminalLog && <TerminalLog />}
            </div>

            {/* FLOATING PANELS HỆ THỐNG */}
            <ActionMenu />
            <UIPropertiesPanel />
            <RenameModal />
            <SettingsModal />
            <CreateButtonModal/>
            
            {/* Panel Global Tags trượt từ phải sang */}
            <div className={`absolute top-0 right-0 h-full w-[450px] z-40 transition-transform duration-300 ease-out shadow-[-20px_0_40px_rgba(0,0,0,0.6)] border-l border-white/5 ${isTagsOpen ? 'translate-x-0' : 'translate-x-full'}`}>
                <TagManagerTable onClose={() => useTagDb.setState({ isGlobalTagsTableOpen: false })} />
            </div>

            {/* CENTRAL ASSET MANAGER TABLE MODAL */}
            <FileManagerModal 
                isOpen={fileManagerContext?.isOpen || false}
                onClose={closeFileManager}
                defaultTab="projects"
                mode={fileManagerContext?.mode || 'manage'}
                onFileSelect={handleServerFileLoad}
                onSaveAs={handleServerFileSave}
            />
        </div>
    );
};