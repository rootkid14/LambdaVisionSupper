import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, AlertTriangle, XCircle, Terminal } from 'lucide-react';
import { ProjectBundle } from '../../ProjectCompiler/ProjectCompilerCore/ProjectCompilerCore';
import { useUIEngine } from '../UIEngineStores/InspectionStore';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';
import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { FleetAPI } from '../../api/fleetApi';
import { NodeAPI } from '../../api/nodeApi';
import { axiosClient } from '../../api/axiosClient';

interface ImportModalProps {
    file: File;
    onClose: () => void;
}

interface LogEntry {
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
}

export const ImportProjectModal = ({ file, onClose }: ImportModalProps) => {
    const [status, setStatus] = useState<'reading' | 'restoring' | 'fleet' | 'logic' | 'compiling' | 'done' | 'failed'>('reading');
    const [logs, setLogs] = useState<LogEntry[]>([]);

    const addLog = (type: LogEntry['type'], message: string) => {
        setLogs(prev => [...prev, { type, message }]);
    };

    useEffect(() => {
        const executeImport = async () => {
            try {
                // ==========================================
                // STEP 1: ĐỌC VÀ PHÂN TÍCH FILE JSON
                // ==========================================
                addLog('info', `Đang đọc file: ${file.name}...`);
                const fileText = await file.text();
                const bundle: ProjectBundle = JSON.parse(fileText);
                
                if (!bundle.project_uuid || !bundle.UI || !bundle.sequencer) {
                    throw new Error("File cấu trúc không hợp lệ (Không phải chuẩn Lambda Project).");
                }
                addLog('success', `Đã phân tích JSON. Project ID: ${bundle.project_uuid}`);

                // ==========================================
                // STEP 2: NẠP DỮ LIỆU FRONTEND (STATE RESTORATION)
                // ==========================================
                setStatus('restoring');
                addLog('info', 'Đang ghi đè UI, Data Tags và Sequencer Map vào RAM cục bộ...');
                
                // Nạp UI
                useUIEngine.setState({
                    components_map: bundle.UI.components_map,
                    activeScreenId: bundle.UI.activeScreenId,
                    nameLabelConfig: bundle.UI.nameLabelConfig
                });

                // Nạp Global Tags
                useTagDb.setState({ tags: bundle.tags_db });

                // Nạp Sequencer Graph và ép hệ thống báo "Bẩn" (Dirty) để lát nữa Compile lại
                useSequencerStore.setState({
                    nodes: bundle.sequencer.nodes,
                    edges: bundle.sequencer.edges,
                    engine_tick_ms: bundle.sequencer.engine_tick_ms || 25,
                    isGraphDirty: true 
                });

                addLog('success', 'Nạp dữ liệu Frontend thành công.');

                // ==========================================
                // STEP 3: ĐÁNH THỨC FLEET BUS (MẠNG LƯỚI THIẾT BỊ)
                // ==========================================
                setStatus('fleet');
                addLog('info', 'Đang khôi phục kết nối Mạng Lưới (Fleet Topology)...');
                
                const gateway = bundle.fleet.master_gateway_host;
                if (gateway) {
                    // Cài đặt địa chỉ trung tâm cho Axios và Store
                    axiosClient.defaults.baseURL = gateway;
                    useFleetStore.setState({ gateway });
                    addLog('info', `Đã thiết lập Gateway Router: ${gateway}`);
                }

                // Khai báo danh sách các Worker Nodes cho Master Gateway
                for (const worker of bundle.fleet.workers_information) {
                    if (worker.worker_id !== "master_gateway" && worker.worker_host !== "unknown_host") {
                        addLog('info', `Bắn tín hiệu khai báo Worker: [${worker.worker_id}] tới Master...`);
                        try {
                            // Gọi API để BE lưu Worker này vào Cache
                            await FleetAPI.master_addLocalWorker({ server_id: worker.worker_id, host: worker.worker_host });
                            addLog('success', `Worker [${worker.worker_id}] đã được Master tiếp nhận.`);
                        } catch (e: any) {
                            addLog('warning', `Worker [${worker.worker_id}] không phản hồi hoặc đã tồn tại. Chi tiết: ${e.message}`);
                        }
                    }
                }

                // Cập nhật lại UI Fleet Dashboard
                await useFleetStore.getState().silentRefreshFleet();

                // ==========================================
                // STEP 4: ĐỒNG BỘ LOGIC (ĐÁNH THỨC BE RAM)
                // ==========================================
                setStatus('logic');
                addLog('info', 'Đang yêu cầu Backend kiểm tra và nạp Logic Objects (Dependencies)...');

                let hasLogicError = false;
                for (const worker of bundle.fleet.workers_information) {
                    const logicObjectsMap = worker.resource?.logic_objects || {};
                    
                    // Nếu máy Worker này có chứa Logic Objects cần nạp
                    if (Object.keys(logicObjectsMap).length > 0) {
                        addLog('info', `Gửi lệnh Sync RAM tới máy [${worker.worker_id}]...`);
                        
                        try {
                            const isMaster = worker.worker_id === "master_gateway";
                            const payload = { logic_objects: logicObjectsMap };
                            
                            // Gọi API Sync Dependencies
                            const syncRes = await (isMaster 
                                ? NodeAPI.master_sync_dependencies(payload) 
                                : NodeAPI.proxy_sync_dependencies(worker.worker_id, payload));
                            
                            // Phân tích báo cáo trả về từ Backend cho từng Logic Object
                            for (const [logicId, report] of Object.entries(syncRes.details as Record<string, any>)) {
                                if (report.success) {
                                    // Object đã tồn tại (Status: "exist") hoặc Mới được nạp thành công (Status: "loaded")
                                    const msg = report.status === "exist" ? "Đã có sẵn trên RAM" : "Đã nạp mới từ Ổ cứng";
                                    addLog('success', `[${worker.worker_id}] Object '${logicId}': ${msg}.`);
                                } else {
                                    hasLogicError = true;
                                    addLog('error', `[${worker.worker_id}] Lỗi nạp '${logicId}': ${report.error_message}`);
                                }
                            }
                        } catch (e: any) {
                            hasLogicError = true;
                            addLog('error', `Lỗi giao tiếp với [${worker.worker_id}] khi Sync: ${e.message}`);
                        }
                    }
                }

                if (hasLogicError) {
                    throw new Error("Có lỗi nghiêm trọng xảy ra trong quá trình nạp Logic Objects ở phía Backend. Vui lòng kiểm tra Log.");
                }

                // ==========================================
                // STEP 5: BIÊN DỊCH SEQUENCER GRAPH
                // ==========================================
                setStatus('compiling');
                addLog('info', 'Tiến hành biên dịch (Compile) Sequencer Graph...');
                
                // Kích hoạt hàm Compile của Sequencer
                await useSequencerStore.getState().compileGraph();
                
                // Nếu biên dịch xong mà hệ thống vẫn báo lỗi (isGraphDirty)
                const isDirty = useSequencerStore.getState().isGraphDirty;
                if (isDirty) {
                     addLog('error', 'Trình biên dịch báo lỗi (Graph Validation Failed). Xem Terminal trong màn hình Sequencer để biết chi tiết.');
                     setStatus('failed');
                     return;
                }

                addLog('success', 'Hệ thống đã biên dịch thành công và SẴN SÀNG CHẠY!');
                setStatus('done');

            } catch (err: any) {
                addLog('error', err.message || "Lỗi không xác định");
                setStatus('failed');
            }
        };

        // Bắt đầu quá trình Import ngay khi Component được Mount
        executeImport();
    }, [file]);

    return (
        // Vùng nền mờ (Backdrop)
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center font-mono">
            
            {/* Modal Container */}
            <div className="bg-[#1e1e1e] border border-[#3c4043] rounded-xl shadow-2xl w-[650px] flex flex-col overflow-hidden">
                
                {/* Header */}
                <div className="px-5 py-4 border-b border-[#3c4043] bg-[#252526] flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        {status === 'done' ? <CheckCircle2 className="text-[#81c995]" /> : 
                         status === 'failed' ? <XCircle className="text-[#f28b82]" /> : 
                         <Loader2 className="animate-spin text-[#8ab4f8]" />}
                        <h2 className="text-[#e8eaed] font-bold tracking-wider">SYSTEM BOOT SEQUENCE</h2>
                    </div>
                    {/* Nút ĐÓNG chỉ hiện khi quá trình đã kết thúc (thành công hoặc thất bại) */}
                    {(status === 'done' || status === 'failed') && (
                        <button 
                            onClick={onClose} 
                            className="px-4 py-1.5 bg-[#3c4043] hover:bg-[#5f6368] text-[#e8eaed] rounded font-bold text-xs transition-colors"
                        >
                            ĐÓNG
                        </button>
                    )}
                </div>

                {/* Khu vực Terminal Logs */}
                <div className="h-[420px] bg-black p-5 overflow-y-auto flex flex-col gap-2 custom-scrollbar text-[11px] leading-relaxed">
                    {logs.map((log, i) => (
                        <div key={i} className={`flex items-start gap-2 ${
                            log.type === 'error' ? 'text-[#f28b82]' :
                            log.type === 'warning' ? 'text-[#fcd663]' :
                            log.type === 'success' ? 'text-[#81c995]' : 'text-[#9aa0a6]'
                        }`}>
                            <span className="shrink-0 mt-1 opacity-70"><Terminal size={12}/></span>
                            <span>{log.message}</span>
                        </div>
                    ))}
                    
                    {/* Hiệu ứng nhấp nháy "Đang xử lý..." */}
                    {status !== 'done' && status !== 'failed' && (
                        <div className="flex items-center gap-2 text-[#8ab4f8] mt-2 animate-pulse">
                            <span className="shrink-0"><Terminal size={12}/></span>
                            <span>[ Processing ... ]</span>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};