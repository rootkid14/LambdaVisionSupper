import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { useUIEngine } from '../../UI_Engine/UIEngineStores/InspectionStore';
import { useTagDb } from '../../UI_Engine/UIEngineStores/GlobalTagsStore';
import { useSequencerStore } from '../../UI_Engine/UIEngineStores/SequencerStores';
import { NodeAPI } from '../../api/nodeApi';
import { FleetAPI } from '../../api/fleetApi';
import { axiosClient } from '../../api/axiosClient';
import { save } from '@tauri-apps/plugin-dialog';
import { writeTextFile } from '@tauri-apps/plugin-fs';


// ==========================================
// ĐỊNH NGHĨA CẤU TRÚC FILE CHUẨN
// ==========================================
export interface Dependencies {
    files: string[];
    logic_objects: Record<string, string>;
}

export interface WorkerInformation {
    worker_id: string;
    worker_host: string;
    resource: Dependencies;
}

export interface FleetConfig {
    master_gateway_host: string;
    workers_information: WorkerInformation[];
}

export interface UIInformation {
    activeScreenId: string | null;
    nameLabelConfig: any;
    components_map: Record<string, any>;
}

export interface SequencerInformation {
    engine_tick_ms: number;
    nodes: any[];
    edges: any[];
}

export interface ProjectBundle {
    project_uuid: string;
    fleet: FleetConfig;
    UI: UIInformation;
    tags_db: Record<string, any>;
    sequencer: SequencerInformation;
}



// ==========================================
// MODULE COMPILER (CORE LOGIC)
// ==========================================
export const ProjectCompiler = {
    // ----------------------------------------------------
    // 1. EXPORT PROJECT
    // ----------------------------------------------------
    exportProject: async (projectName: string = "Lambda_Project") => {
        // ... (GIỮ NGUYÊN CODE EXPORT CỦA BẠN - Không thay đổi gì)
        const fleetState = useFleetStore.getState();
        const uiState = useUIEngine.getState();
        const tagState = useTagDb.getState();
        const seqState = useSequencerStore.getState();

        const cleanTags: Record<string, any> = tagState.tags;

        const requiredLogicsByWorker: Record<string, Set<string>> = {};
        
        seqState.nodes.forEach((node: any) => {
            if (node.type === 'proc') {
                const config = node.data?.sequencer_data?.config;
                const workerId = config?.logic_object_info?.worker_id;
                const logicId = config?.logic_object_info?.logic_object_id;

                if (workerId && logicId) {
                    if (!requiredLogicsByWorker[workerId]) {
                        requiredLogicsByWorker[workerId] = new Set();
                    }
                    requiredLogicsByWorker[workerId].add(logicId);
                }
            }
        });

        const workerResourceMap: Record<string, Dependencies> = {};

        for (const workerId of Object.keys(requiredLogicsByWorker)) {
            workerResourceMap[workerId] = { files: [], logic_objects: {} };
            const isMaster = workerId === "master_gateway";
            
            try {
                const be_dependencies = await (isMaster 
                    ? NodeAPI.master_get_logic_dependencies() 
                    : NodeAPI.proxy_get_logic_dependencies(workerId));

                requiredLogicsByWorker[workerId].forEach(logicId => {
                    const graphFileName = be_dependencies[logicId] || logicId;
                    workerResourceMap[workerId].logic_objects[logicId] = graphFileName;
                });
            } catch (error) {
                console.error(`Không thể lấy dependencies từ Worker [${workerId}]:`, error);
                requiredLogicsByWorker[workerId].forEach(logicId => {
                    workerResourceMap[workerId].logic_objects[logicId] = logicId;
                });
            }
        }

        const workersInfo: WorkerInformation[] = [];
        
        if (fleetState.master_worker) {
            workersInfo.push({
                worker_id: fleetState.master_worker.server_id,
                worker_host: fleetState.master_worker.host,
                resource: workerResourceMap['master_gateway'] || { files: [], logic_objects: {} }
            });
        }

        fleetState.fleet_worker.forEach((w) => {
            workersInfo.push({
                worker_id: w.server_id,
                worker_host: w.host,
                resource: workerResourceMap[w.server_id] || { files: [], logic_objects: {} }
            });
        });

        Object.keys(workerResourceMap).forEach(wId => {
            if (wId !== 'master_gateway' && !workersInfo.find(w => w.worker_id === wId)) {
                workersInfo.push({
                    worker_id: wId,
                    worker_host: "unknown_host",
                    resource: workerResourceMap[wId]
                });
            }
        });

        const bundle: ProjectBundle = {
            project_uuid: crypto.randomUUID(),
            fleet: {
                master_gateway_host: fleetState.gateway || "",
                workers_information: workersInfo // Giả sử workersInfo đã được tính toán ở trên
            },
            UI: {
                activeScreenId: uiState.activeScreenId,
                nameLabelConfig: uiState.nameLabelConfig,
                components_map: uiState.components_map
            },
            tags_db: cleanTags,
            sequencer: {
                engine_tick_ms: seqState.engine_tick_ms,
                nodes: seqState.nodes,
                edges: seqState.edges
            }
        };

        const jsonString = JSON.stringify(bundle, null, 2);
        const defaultFilename = `${projectName.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.json`;

        try {
            // KIỂM TRA MÔI TRƯỜNG: NẾU LÀ TAURI (DESKTOP APP)
            if ((window as any).__TAURI__) {
                // Mở hộp thoại "Save As" chuẩn của hệ điều hành
                const filePath = await save({
                    defaultPath: defaultFilename,
                    filters: [{ name: 'Lambda Project', extensions: ['json', 'lambda_proj'] }]
                });

                // Nếu người dùng không ấn Cancel
                if (filePath) {
                    await writeTextFile(filePath, jsonString);
                    // Hiển thị thông báo (Bạn có thể thay bằng Custom Toast Modal của bạn cho đẹp)
                    alert(`✅ Export Project thành công!\nĐã lưu tại: ${filePath}`);
                }
            } 
            // NẾU LÀ TRÌNH DUYỆT WEB BÌNH THƯỜNG
            else {
                const blob = new Blob([jsonString], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = defaultFilename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                alert(`✅ Export Project thành công!\nFile đã được tải xuống thư mục Downloads của trình duyệt.`);
            }
        } catch (error: any) {
            console.error("Export Error:", error);
            alert(`❌ Lỗi khi Export Project:\n${error.message}`);
        }
    },

    // ----------------------------------------------------
    // 2. TRIGGER MỞ GIAO DIỆN (UI)
    // ----------------------------------------------------
    triggerImport: (file: File) => {
        if (!file.name.endsWith('.json') && !file.name.endsWith('.lambda_proj')) {
            alert("File không hợp lệ. Vui lòng chọn file .lambda_proj hoặc .json");
            return;
        }
        useUIEngine.getState().setImportFile(file);
    },

    // ----------------------------------------------------
    // 3. IMPORT PROJECT (CORE LOGIC)
    // ----------------------------------------------------
    importProject: async (
        file: File,
        onLog: (type: 'info' | 'success' | 'warning' | 'error', message: string) => void,
        onStatus: (status: 'reading' | 'restoring' | 'fleet' | 'logic' | 'compiling' | 'done' | 'failed') => void
    ) => {
        try {
            // STEP 1: ĐỌC VÀ PHÂN TÍCH FILE
            onStatus('reading');
            onLog('info', `Đang đọc file: ${file.name}...`);
            const fileText = await file.text();
            const bundle: ProjectBundle = JSON.parse(fileText);
            
            if (!bundle.project_uuid || !bundle.UI || !bundle.sequencer) {
                throw new Error("ERROR : File Must BE JSON");
            }
            onLog('success', `=========  ANALYZED JSON FILED. Project ID: ${bundle.project_uuid} =========`);

            // STEP 2: NẠP DỮ LIỆU FRONTEND
            onStatus('restoring');
            onLog('info', 'Load UI, Data Tags, Sequencer Map into RAM...');
            
            useUIEngine.setState({
                components_map: bundle.UI.components_map,
                activeScreenId: bundle.UI.activeScreenId,
                nameLabelConfig: bundle.UI.nameLabelConfig
            });
            useTagDb.setState({ tags: bundle.tags_db });
            useSequencerStore.setState({
                nodes: bundle.sequencer.nodes,
                edges: bundle.sequencer.edges,
                engine_tick_ms: bundle.sequencer.engine_tick_ms || 25,
                isGraphDirty: true 
            });
            onLog('success', '============ REBUILT UI SUCCESSFULLY ==========');

            // STEP 3: ĐÁNH THỨC FLEET BUS
            onStatus('fleet');
            onLog('info', 'Restoring Fleet Connections (Fleet Topology)...');
            
            const gateway = bundle.fleet.master_gateway_host;
            if (gateway) {
                axiosClient.defaults.baseURL = gateway;
                useFleetStore.setState({ gateway });
                onLog('info', `Established Gateway Router: ${gateway}`);
            }

            for (const worker of bundle.fleet.workers_information) {
                if (worker.worker_id !== "master_gateway" && worker.worker_host !== "unknown_host") {
                    onLog('info', `Requesting Worker: [${worker.worker_id}], message sent to Master...`);
                    try {
                        await FleetAPI.master_addLocalWorker({ server_id: worker.worker_id, host: worker.worker_host });
                        onLog('success', `Worker [${worker.worker_id}] has been established.`);
                    } catch (e: any) {
                        onLog('warning', `Worker [${worker.worker_id}] did not response. Error DETAIL: ${e.message}`);
                    }
                }
            }
            await useFleetStore.getState().silentRefreshFleet();

            // STEP 4: ĐỒNG BỘ LOGIC (ĐÁNH THỨC BE RAM)
            onStatus('logic');
            onLog('info', 'Requesting BE to load Dependencies...');

            let hasLogicError = false;
            for (const worker of bundle.fleet.workers_information) {
                const logicObjectsMap = worker.resource?.logic_objects || {};
                
                if (Object.keys(logicObjectsMap).length > 0) {
                    onLog('info', `Requesting Sync RAM to [${worker.worker_id}]...`);
                    try {
                        const isMaster = worker.worker_id === "master_gateway";
                        const payload = { logic_objects: logicObjectsMap };
                        const syncRes = await (isMaster 
                            ? NodeAPI.master_sync_dependencies(payload) 
                            : NodeAPI.proxy_sync_dependencies(worker.worker_id, payload));
                        
                        for (const [logicId, report] of Object.entries(syncRes.details as Record<string, any>)) {
                            if (report.success) {
                                const msg = report.status === "exist" ? "Existed in ram" : "Constructing new instance from disk";
                                onLog('success', `[${worker.worker_id}] Object '${logicId}': ${msg}.`);
                            } else {
                                hasLogicError = true;
                                onLog('error', `[${worker.worker_id}] Lỗi nạp '${logicId}': ${report.error_message}`);
                            }
                        }
                    } catch (e: any) {
                        hasLogicError = true;
                        onLog('error', `Communication Error with [${worker.worker_id}] when trying to Sync: ${e.message}`);
                    }
                }
            }

            if (hasLogicError) {
                throw new Error(`Severe Issue happen trying to load / create the Logic Object Instance to RAM`);
            }

            // STEP 5: BIÊN DỊCH SEQUENCER GRAPH
            onStatus('compiling');
            onLog('info', '============== Compiling Sequencer Graph... =============');
            
            await useSequencerStore.getState().compileGraph();
            
            // CHỐNG LỖI BẤT ĐỒNG BỘ STATE: Chờ 100ms để Zustand kịp ghi nhận kết quả Compile
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const isDirty = useSequencerStore.getState().isGraphDirty;
            
            if (isDirty) {
                 onLog('error', 'Sequencer Graph Validation Failed!');
                 throw new Error("There is something wrong during compilation of the Sequencer Graph");
            }

            onLog('success', '======================= LOAD SUCCESSFULLY. SYSTEM READY ===================');
            onStatus('done');

        } catch (err: any) {
            onLog('error', err.message || "Unknown Error");
            onStatus('failed');
            throw err; // Ném lỗi ra để Component bên ngoài biết
        }
    },
};