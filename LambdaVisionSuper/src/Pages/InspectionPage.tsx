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
        <div className="w-56 bg-[#28292c] border-r border-[#3c4043] flex flex-col z-10 shadow-xl">
            <div className="p-3 border-b border-[#3c4043] flex justify-between items-center bg-[#202124]">
                <span className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest">Screens</span>
                <button onClick={addScreen} className="p-1.5 rounded-md bg-[#8ab4f8]/10 text-[#8ab4f8] hover:bg-[#8ab4f8]/30 transition-colors">
                    <Plus size={14} />
                </button>
            </div>
            <div className="flex-1 p-3 flex flex-col gap-3 overflow-y-auto custom-scrollbar">
                {screens.map((s:any) => (
                    <div key={s.id} onClick={() => changeScreen(s.id)} onContextMenu={(e) => { e.preventDefault(); openActionMenu(s.id, 'thumbnail', e.clientX, e.clientY, 0, 0); }} className={`cursor-pointer rounded-xl border-2 p-3 flex flex-col items-center gap-2 transition-all shadow-sm ${activeScreenId === s.id ? 'border-[#8ab4f8] bg-[#8ab4f8]/10' : 'border-[#3c4043] bg-[#171717] hover:border-[#5f6368]'}`}>
                        <div className="w-full aspect-video bg-[#202124] rounded border border-[#3c4043] flex items-center justify-center pointer-events-none">
                             <ImageIcon size={28} className={activeScreenId === s.id ? 'text-[#8ab4f8]' : 'text-[#5f6368]'} />
                        </div>
                        <span className={`text-[10px] font-bold uppercase truncate w-full text-center tracking-wider ${activeScreenId === s.id ? 'text-[#8ab4f8]' : 'text-[#9aa0a6]'}`}>{s.name}</span>
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
    const navigate = useNavigate();
    const isTagsOpen = useTagDb(state => state.isGlobalTagsTableOpen);
    const { showTerminalLog, toggleTerminalLog, importFileContext, setImportFile, changeScreen, components_map, fileManagerContext, openFileManager, closeFileManager } = useUIEngine();
    const sequencerStore = useSequencerStore();
    useKeyboardTrigger();
    const toggleSettings = useKeyboardTriggerStore(state => state.toggleSettingsModal);

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

    // Luồng xử lý khi chọn một Project File trên Server để nạp vào RAM ảo của hệ thống
    const handleServerFileLoad = (filename: string, fileContent: any) => {
        const blob = new Blob([JSON.stringify(fileContent, null, 2)], { type: 'application/json' });
        const virtualFile = new File([blob], filename, { type: 'application/json' });
        
        setImportFile(virtualFile); 
        closeFileManager();
    };

    // Luồng đóng gói Bundle của Project và đẩy lên Server lưu trữ thông qua FleetAPI công nghiệp
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
        <div className="h-screen w-screen bg-[#202124] text-[#e8eaed] flex flex-col overflow-hidden font-sans relative select-none">
            
            {/* RENDER IMPORT MODAL KHI CÓ CONTEXT FILE NẠP VÀO */}
            {importFileContext && (
                <ModernImportModal file={importFileContext} onClose={() => setImportFile(null)} />
            )}

            {/* HEADER TOOLBAR TẬP TRUNG */}
            <header className="h-16 bg-[#303134] border-b border-[#3c4043] flex items-center justify-between px-4 z-30 shrink-0 shadow-lg relative">
                
                <div className="flex items-center gap-4 z-10 w-auto min-w-[250px]">
                    <button onClick={() => navigate('/')} className="group flex items-center justify-center w-8 h-8 bg-[#202124] border border-[#5f6368] hover:border-[#8ab4f8] hover:bg-[#8ab4f8]/10 text-[#e8eaed] hover:text-[#8ab4f8] rounded-md transition-all shadow-sm" title="Back to Dashboard">
                        <ArrowLeft size={18} className="group-hover:-translate-x-0.5 transition-transform duration-200" />
                    </button>
                    <div className="w-px h-8 bg-[#3c4043]"></div>
                    <div className="flex flex-col justify-center">
                        <h1 className="font-extrabold text-[#e8eaed] text-[13px] tracking-wide leading-tight flex items-baseline gap-1">
                            LAMBDA VISION SUPER
                        </h1>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <span className={`w-2.5 h-2.5 rounded-full ${sequencerStore.isEngineRunning ? 'bg-[#81c995] animate-pulse shadow-[0_0_4px_#81c995]' : 'bg-[#f28b82]'}`}></span>
                            <span className="text-[#9aa0a6] text-[14px] font-bold tracking-[0.2em] uppercase font-mono">UI Editor</span>
                        </div>
                    </div>
                </div>
                
                {/* THANH ĐIỀU HƯỚNG TRUNG TÂM SẠCH SẼ */}
                <div className="absolute left-1/2 -translate-x-1/2 flex items-center bg-[#171717] border border-[#3c4043] p-1 rounded-lg shadow-inner transition-all">
                    <button 
                        onClick={() => openFileManager('manage')} 
                        className="flex items-center gap-2 px-4 py-1.5 rounded-md hover:bg-[#3c4043] text-[11px] font-bold text-[#8ab4f8] bg-[#8ab4f8]/10 transition-colors"
                    >
                        <FolderOpen size={14} /> ASSET MANAGER
                    </button>

                    <div className="w-px h-5 bg-[#3c4043] mx-1"></div>
                    <button onClick={() => useTagDb.setState({ isGlobalTagsTableOpen: true })} className="flex items-center gap-2 px-4 py-1.5 rounded-md hover:bg-[#3c4043] text-[11px] font-bold text-[#9aa0a6] hover:text-[#fcd663] transition-colors"><Database size={14} /> DATA TAGS</button>
                    <div className="w-px h-5 bg-[#3c4043] mx-1"></div>
                    <button onClick={toggleTerminalLog} className={`flex items-center gap-2 px-4 py-1.5 rounded-md transition-colors text-[11px] font-bold ${showTerminalLog ? 'text-[#8ab4f8] bg-[#8ab4f8]/10' : 'text-[#9aa0a6] hover:bg-[#3c4043] hover:text-[#8ab4f8]'}`}><TerminalSquare size={14} /> TERMINAL</button>
                    <div className="w-px h-5 bg-[#3c4043] mx-1"></div>
                    <NameConfigDropdown />
                    <div className="w-px h-5 bg-[#3c4043] mx-1"></div>
                    <button onClick={() => navigate('/sequencer')} className="flex items-center gap-2 px-4 py-1.5 rounded-md hover:bg-[#3c4043] text-[11px] font-bold text-[#9aa0a6] hover:text-[#c58af9] transition-colors"><GitMerge size={14} /> SEQUENCER</button>
                    <div className="w-px h-5 bg-[#3c4043] mx-1"></div>
                    <button onClick={toggleSettings} className="flex items-center gap-2 px-4 py-1.5 rounded-md hover:bg-[#3c4043] text-[11px] font-bold text-[#9aa0a6] hover:text-[#e8eaed] transition-colors"><Settings size={14} /> KEY MAPPING</button>
                </div>

                <div className="flex items-center gap-3">
                     {sequencerStore.isGraphDirty && (
                        <div className="text-[#fcd663] text-[14px] font-bold flex items-center gap-1.5 px-3 py-1 bg-[#fcd663]/10 rounded border border-[#fcd663]/20">
                            <AlertTriangle size={14}/> Graph Dirty, Need recompiling
                        </div>
                     )}

                     {!sequencerStore.isEngineRunning ? (
                        <button 
                            onClick={() => sequencerStore.runEngine()} 
                            disabled={sequencerStore.isGraphDirty || sequencerStore.isCompiling}
                            className="flex items-center gap-2 px-5 py-2 bg-[#81c995] text-[#202124] rounded-lg text-xs font-bold hover:bg-[#a8dab5] disabled:opacity-50 transition-colors shadow-md"
                        >
                            <Play size={14} fill="currentColor" /> RUN ENGINE
                        </button>
                     ) : (
                        <button 
                            onClick={() => sequencerStore.stopEngine()} 
                            className="flex items-center gap-2 px-5 py-2 bg-[#f28b82] text-[#202124] rounded-lg text-xs font-bold hover:bg-[#f6aea9] transition-colors shadow-[0_0_15px_rgba(242,139,130,0.5)]"
                        >
                            <Square size={14} fill="currentColor" /> STOP ENGINE
                        </button>
                     )}
                </div>
            </header>

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
            
            <div className={`absolute top-0 right-0 h-full w-[450px] z-40 transition-transform duration-300 ease-out shadow-[-10px_0_30px_rgba(0,0,0,0.5)] ${isTagsOpen ? 'translate-x-0' : 'translate-x-full'}`}>
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