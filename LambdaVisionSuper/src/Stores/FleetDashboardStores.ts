import { create } from "zustand";
import { axiosClient } from "../api/axiosClient";
import { FleetAPI } from "../api/fleetApi";
import { persist, createJSONStorage } from "zustand/middleware";
import { NodeAPI } from "../api/nodeApi";

export interface Hardware {
    cpu_percent: number;
    ram_used_mb: number;
    ram_total_mb: number;
    ram_percent: number;
}

export interface DeviceInfo {
    host: string;
    alive: boolean;
    ping: number;
}

export interface WorkerInfoCard {
    server_id: string;
    host: string;
    alive: boolean;
    role: "master" | "worker";
    ping: number;
    hardware: Hardware;
    device_list: DeviceInfo[];
    logic_obj_count: number;
}

export interface LocalServerInfo {
    id: string;
    host: string;
    status: "online" | "offline";
    ping: number;
}


export interface FilesState { 
    filename: Record<string, { size: number; inram: boolean }>
}
export interface GraphsState { 
    name: string;
    size: number;
}

export interface PluginsState {
    name: string;
    size: number;
}

export interface ActiveLogicsState {
    name: string;
    graph_name: string;
}

export interface ResourceInfo {
    files_state: FilesState[];
    graphs_state: GraphsState[]; // Đã sửa lỗi typo "graphs_sate"
    plugins_state: PluginsState[];
    active_logics: ActiveLogicsState[];
}

export interface WorkerDetails {
    selected_worker_id : string,
    localSevsInfo: LocalServerInfo[];
    DevsInfo: DeviceInfo[];
    ResourceInfo: ResourceInfo;
}

export interface AddServerInfo {
    server_id : string,
    host: string
}

export interface AddHttpDeviceInfo {
    device_id : string,
    host: string
}

export type ResourceType = 'file' | 'graph' | 'plugin';

type FleetStore = {
    // DATA
    gateway: string | null;
    fleet_worker: WorkerInfoCard[];        // Use to display data on dashboard and somedata on pool drawers
    master_worker: WorkerInfoCard | null;  // Use to display data on dashboard
    selected_worker: WorkerDetails | null; //Use to load the data to pool drawer

    // UI
    isLoading: boolean;
    isSwitchMasterOpen: boolean;
    isPoolsDrawerOpen: boolean;
    errorMessage : string;
    isErrorModalOpen: boolean;
    isAddNewServerUIOpen: boolean;
    isAttacheNewDeviceUIOpen: boolean;
    isUploadingResource: boolean;
    isDownloadingResource: boolean;
    uploadProgress : number;
    

    // Actions:
    setGatewayandLoadFleet: (host: string) => void;
    openSwitchMaster: () => void;
    closeSwitchMaster: () => void;
    openPoolsDrawer: (worker_id: string) => void;
    closePoolsDrawer: () => void;
    addNewServer: (server_id_to_add: string, host: string) => Promise<void>;
    removeServer: (server_id_to_remove: string) => Promise<void>
    attachNewHttpDevice: (device_id_to_add: string, host: string) => Promise<void>;
    removeHttpDevice: (device_id_to_remove: string, host: string) => Promise<void>;
    uploadResource: (file: File, type: ResourceType) => Promise<void>;
    downloadResource: (filename: string, type: ResourceType) => Promise<void>;
    removeResource: (filename: string, type : ResourceType) => Promise<void>;
    deployGraph: (graph_file_name: string) => Promise<any>;
    undeployLogic: (logic_obj_id : string) => Promise<any>;
    silentRefreshFleet: () => Promise<void>;
    toggleFileRamStatus: (filename: string, isCurrentlyInRam: boolean) => Promise<void>;
};

export const useFleetStore = create<FleetStore>()(persist(
    (set,get) => ({
    gateway: null,
    fleet_worker: [],
    master_worker: null,
    selected_worker: null,
    errorMessage: '',

    isLoading: false,
    isSwitchMasterOpen: true,
    isPoolsDrawerOpen: false,
    isErrorModalOpen: false,
    isAddNewServerUIOpen: false,
    isAttacheNewDeviceUIOpen: false,
    isUploadingResource: false,
    isDownloadingResource: false,
    uploadProgress : 0,

    setGatewayandLoadFleet: async (host: string) => {
        if (!host.trim()) return;

        // 1. Lưu lại gateway đang hoạt động hiện tại để dự phòng (Rollback)
        const previousGateway = get().gateway;

        // 2. Chuẩn hóa địa chỉ nhập vào (Auto-fix lỗi thiếu http://)
        let formattedHost = host.trim();
        if (!/^https?:\/\//i.test(formattedHost)) {
            formattedHost = `http://${formattedHost}`;
        }

        try {
            // Thử thiết lập kết nối tới địa chỉ mới
            axiosClient.defaults.baseURL = formattedHost;
            set({ isLoading: true });

            const data: any = await FleetAPI.getFleetStatus();
            
            // Kiểm tra tính hợp lệ của dữ liệu trả về
            if (!Array.isArray(data)) {
                throw new Error(data.error || "Dữ liệu trả về từ Gateway không hợp lệ (Không phải mảng)");
            }

            const master = data.find((node: any) => node.role === "master") ?? null;
            const workers = data.filter((node: any) => node.role !== "master");

            // KẾT NỐI THÀNH CÔNG: Cập nhật state mới và đóng modal nhập gateway
            set({
                gateway: formattedHost,
                master_worker: master,
                fleet_worker: workers,
                isSwitchMasterOpen: false, // Thành công thì đóng modal
                errorMessage: ""
            });
            
        } catch (error: any) {
            console.error("Load fleet failed", error);

            // Xử lý thông báo lỗi chi tiết
            let errorMsg = "Lỗi kết nối không xác định.";
            if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
                errorMsg = `Không thể kết nối đến Gateway [${formattedHost}]. Vui lòng kiểm tra Server hoặc Port.`;
            } else if (error instanceof TypeError && error.message.includes("URL")) {
                errorMsg = `Địa chỉ IP/URL bạn nhập không đúng định dạng.`;
            } else {
                errorMsg = error.message || "Lỗi giao tiếp với hệ thống.";
            }

            // 3. LOGIC ROLLBACK (QUAY LẠI CÁI CŨ) THEO YÊU CẦU CỦA BẠN
            if (previousGateway) {
                // Nếu đã có gateway cũ đang chạy tốt -> Quay lại an toàn
                axiosClient.defaults.baseURL = previousGateway;
                set({ 
                    gateway: previousGateway, // Giữ nguyên gateway cũ trong store
                    errorMessage: errorMsg,
                    isErrorModalOpen: true,
                    // Lúc này Dashboard vẫn hiển thị dữ liệu của gateway cũ, không bị trắng trang
                });
            } else {
                // Nếu trước đó chưa có gateway nào (null) -> Bắt buộc ở lại màn hình nhập
                set({ 
                    gateway: null,
                    errorMessage: errorMsg,
                    isErrorModalOpen: true,
                    isSwitchMasterOpen: true // Giữ nguyên modal SwitchMaster trên màn hình
                });
            }
            
        } finally {
            set({ isLoading: false }); 
        }
    },

    openSwitchMaster: () => set({ isSwitchMasterOpen: true }),
    closeSwitchMaster: () => set({ isSwitchMasterOpen: false }),

    openPoolsDrawer: async (worker_id: string) => {
        if (!worker_id.trim()) return;

        try {
            const isMaster = worker_id === "master_gateway";

            const [local_resource, local_servers, local_devices] = await Promise.all([
                isMaster ? FleetAPI.getMasterLocalResource() : FleetAPI.proxy_getWorkerLocalResource(worker_id),
                isMaster ? FleetAPI.getMasterLocalServers() : FleetAPI.proxy_getWorkerLocalServers(worker_id),
                isMaster ? FleetAPI.getMasterLocalDevices() : FleetAPI.proxy_getWorkerLocalDevices(worker_id)
            ]);
            
            const WorkerDetailsData: WorkerDetails = {
                selected_worker_id : worker_id,
                localSevsInfo: local_servers,
                // Thêm ?? [] để đảm bảo luôn trả về Array như type yêu cầu, tránh lỗi khi local_devices là undefined
                DevsInfo: local_devices ?? [], 
                ResourceInfo: local_resource

            };

            set({ selected_worker: WorkerDetailsData });
            set({ isPoolsDrawerOpen: true });
            
        } catch (error) {
            console.error("Load worker details failed", error);
        }
    },

    closePoolsDrawer: () => {
        set({ selected_worker: null });
        set({ isPoolsDrawerOpen: false });
    },
    
    
    addNewServer: async (server_id_to_add : string, host: string) => {
        const new_server_info : AddServerInfo = {
            server_id: server_id_to_add,
            host: host
        }
        const selected_worker_id = get().selected_worker?.selected_worker_id
        const isMaster = selected_worker_id === "master_gateway"
        if(!selected_worker_id) {
            set({
                errorMessage: "selected worker is is null, cancelling",
                isErrorModalOpen: true
            })
            return;
        }
        try {
            const resp = await (
            isMaster
                ? FleetAPI.master_addLocalWorker(new_server_info)
                : FleetAPI.proxy_addLocalWorker(selected_worker_id, new_server_info)
            )

            if (resp.success) {
                await get().openPoolsDrawer(selected_worker_id)

                if (isMaster) {
                    await get().setGatewayandLoadFleet(get().gateway!)
                }
                set({ isAddNewServerUIOpen: false})
                return
            }

            set({
                errorMessage:
                resp.message || "Add server failed",
                isErrorModalOpen: true
            })

        } catch (error: any) {
            set({
                errorMessage:
                error?.response?.data?.detail ||
                error.message ||
                "Network error",
                isErrorModalOpen: true
            })
        }
    },

    removeServer: async (server_id_to_remove : string) => {
        const selected_worker_id = get().selected_worker?.selected_worker_id
        const isMaster = selected_worker_id === "master_gateway"
        if(!selected_worker_id) {
            set({
                errorMessage: "selected worker is is null, cancelling",
                isErrorModalOpen: true
            })
            return;
        }
        try{
            const resp = await (
                isMaster
                    ?FleetAPI.master_removeLocalServer(server_id_to_remove)
                    :FleetAPI.proxy_removeLocalServer(selected_worker_id, server_id_to_remove)
            )

            if(resp.success) {
                await get().openPoolsDrawer(selected_worker_id)
                if(isMaster){
                    await get().setGatewayandLoadFleet(get().gateway!)
                }
                return;
            }

        } catch (error : any){
            set({
                errorMessage: error?.response?.data?.detail || error.message || "Network Error",
                isErrorModalOpen: true
            })
        }
    },

    attachNewHttpDevice : async (device_id_to_add : string, host: string) => {
        const new_device_info : AddHttpDeviceInfo = {
            device_id: device_id_to_add,
            host: host
        }
        const selected_worker_id = get().selected_worker?.selected_worker_id
        const isMaster = selected_worker_id === "master_gateway"
        if(!selected_worker_id) {
            set({
                errorMessage: "selected worker is is null, cancelling",
                isErrorModalOpen: true
            })
            return;
        }
        try {
            const resp = await (
            isMaster
                ? FleetAPI.master_addLocalDevice(new_device_info)
                : FleetAPI.proxy_addLocalDevice(selected_worker_id, new_device_info)
            )

            if (resp.success) {
                await get().openPoolsDrawer(selected_worker_id)

                if (isMaster) {
                    await get().setGatewayandLoadFleet(get().gateway!)
                }
                set({ isAttacheNewDeviceUIOpen: false})
                return
            }

            set({
                errorMessage:
                resp.message || "Add device failed",
                isErrorModalOpen: true
            })

        } catch (error: any) {
            set({
                errorMessage:
                error?.response?.data?.detail ||
                error.message ||
                "Network error",
                isErrorModalOpen: true
            })
        }
    },

    removeHttpDevice: async (device_id_to_remove: string) => {
        const selected_worker_id = get().selected_worker?.selected_worker_id
        const isMaster = selected_worker_id === "master_gateway"
        if(!selected_worker_id) {
            set({
                errorMessage: "selected worker is is null, cancelling",
                isErrorModalOpen: true
            })
            return;
        }
        try{
            const resp = await (
                isMaster
                    ?FleetAPI.master_removeLocalDevice(device_id_to_remove)
                    :FleetAPI.proxy_removeLocalDevice(selected_worker_id, device_id_to_remove)
            )

            if(resp.success) {
                await get().openPoolsDrawer(selected_worker_id)
                if(isMaster){
                    await get().setGatewayandLoadFleet(get().gateway!)
                }
                return;
            }

        } catch (error : any){
            set({
                errorMessage: error?.response?.data?.detail || error.message || "Network Error",
                isErrorModalOpen: true
            })
        }
    },

    uploadResource: async (file: File, type: ResourceType) => {
        const selected_worker_id = get().selected_worker?.selected_worker_id;
        if (!selected_worker_id) {
            set({ errorMessage: "Không xác định được Worker đang thao tác", isErrorModalOpen: true });
            return;
        }

        const isMaster = selected_worker_id === "master_gateway"; // Kiểm tra Master

        set({ isUploadingResource: true, uploadProgress: 0 });
        try {
            const handleProgress = (progressEvent: any) => {
                if (progressEvent.total) {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    set({ uploadProgress: percentCompleted });
                }
            };

            let resp;
            if (isMaster) {
                // Nếu là Master, gọi API thẳng
                resp = await FleetAPI.master_uploadFile(file, type, handleProgress);
                
            } else {
                // Nếu là Worker, gọi qua Proxy
                resp = await FleetAPI.proxy_uploadFile(selected_worker_id, file, type, handleProgress);
            }

            if (resp.success) {
                set({ uploadProgress: 100 });
                await get().openPoolsDrawer(selected_worker_id);
            } else {
                set({ errorMessage: resp.message || "Upload thất bại", isErrorModalOpen: true });
            }
        } catch (error: any) {
            set({
                errorMessage: error?.response?.data?.detail || error.message || "Lỗi mạng khi upload",
                isErrorModalOpen: true
            });
        } finally {
            setTimeout(() => {
                set({ isUploadingResource: false, uploadProgress: 0 });
            }, 500);
        }
    },

    downloadResource: async (filename: string, type: ResourceType) => {
        const selected_worker_id = get().selected_worker?.selected_worker_id;
        if (!selected_worker_id) {
            set({ errorMessage: "Không xác định được Worker đang thao tác", isErrorModalOpen: true });
            return;
        }

        const isMaster = selected_worker_id === "master_gateway"; // Kiểm tra Master

        set({ isDownloadingResource: true });
        try {
            let blob: Blob;
            
            if (isMaster) {
                // Master download trực tiếp
                blob = await FleetAPI.master_downloadFile(filename, type);
            } else {
                // Worker download qua proxy
                blob = await FleetAPI.proxy_downloadFile(selected_worker_id, filename, type);
            }

            // Xử lý tạo link ảo để ép trình duyệt tải file về máy
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename; 
            document.body.appendChild(a);
            a.click();
            
            // Dọn dẹp bộ nhớ
            a.remove();
            window.URL.revokeObjectURL(url);

        } catch (error: any) {
            if (error.response?.data instanceof Blob) {
                const textError = await error.response.data.text();
                try {
                    const jsonError = JSON.parse(textError);
                    set({ errorMessage: jsonError.detail || "Lỗi tải file", isErrorModalOpen: true });
                } catch {
                    set({ errorMessage: textError, isErrorModalOpen: true });
                }
            } else {
                set({
                    errorMessage: error?.message || "Lỗi mạng khi download",
                    isErrorModalOpen: true
                });
            }
        } finally {
            set({ isDownloadingResource: false });
        }
    },

    removeResource: async (filename: string, type : ResourceType) => {
        const selected_worker_id = get().selected_worker?.selected_worker_id;
        if (!selected_worker_id) {
            set({ errorMessage: "Không xác định được Worker đang thao tác", isErrorModalOpen: true });
            return;
        }

        const isMaster = selected_worker_id === "master_gateway"; // Kiểm tra Master

        try{
            const resp = await (
                isMaster
                ?FleetAPI.master_removeResource(filename, type)
                :FleetAPI.proxy_removeResource(selected_worker_id, filename, type)
            )
            if (resp?.success){
                await get().openPoolsDrawer(selected_worker_id)
                return resp;
            } else {
                set({ errorMessage: "Something failed trying to delete the file, did not receive success message", isErrorModalOpen: true });    
            }

        } catch (error: any) {
            set({ errorMessage: error?.response?.data?.detail ||error.message ||"Network error", isErrorModalOpen: true });
        }
    },
    deployGraph: async (graph_file_name : string) => {
        const selected_worker_id = get().selected_worker?.selected_worker_id;
        if (!selected_worker_id) {
            set({ errorMessage: "Không xác định được Worker đang thao tác", isErrorModalOpen: true });
            return;
        }

        const isMaster = selected_worker_id === "master_gateway"; // Kiểm tra Master

        try{
            const resp = await (
                isMaster
                ?NodeAPI.master_deploy_graph_to_ram(graph_file_name)
                :NodeAPI.proxy_deploy_graph_to_ram(selected_worker_id ,graph_file_name)
            )
            if (resp?.success) {
                await get().openPoolsDrawer(selected_worker_id)
                return;
            } else {
                set({errorMessage: resp?.error_message || "Failed to deploy the graph to Ram", isErrorModalOpen: true})
            }
        } catch (error: any){
            set({ errorMessage: error?.response?.data?.detail ||error.message ||"Network error", isErrorModalOpen: true });
        }
    },
    undeployLogic: async (logic_obj_id: string) => {
        const selected_worker_id = get().selected_worker?.selected_worker_id;
        if (!selected_worker_id) {
            set({ errorMessage: "Không xác định được Worker đang thao tác", isErrorModalOpen: true });
            return;
        }

        const isMaster = selected_worker_id === "master_gateway"; // Kiểm tra Master

        try {
            const resp = await (
                isMaster
                ?NodeAPI.master_undeploy_graph_from_ram(logic_obj_id)
                :NodeAPI.proxy_undeploy_graph_from_ram(selected_worker_id, logic_obj_id)
            )
            if(resp.success){
                await get().openPoolsDrawer(selected_worker_id)
                return;
            } else {
                set({errorMessage: resp?.error_message || "Failed to Undeploy the graph to Ram", isErrorModalOpen: true})
            }
        } catch (error : any){
            set({ errorMessage: error?.response?.data?.detail ||error.message ||"Network error", isErrorModalOpen: true });
        }
    },

    
    silentRefreshFleet: async () => {
        const host = get().gateway;
        if (!host) return;

        try {
            // FIX BUG MẤT KẾT NỐI API SAU KHI F5: 
            // Phải nạp lại địa chỉ host vào axiosClient vì RAM đã bị xóa
            axiosClient.defaults.baseURL = host; 
            
            // Chỉ gọi API ngầm, KHÔNG set isLoading = true để tránh giật UI
            const data: any = await FleetAPI.getFleetStatus();
            
            if (Array.isArray(data)) {
                const master = data.find((node: any) => node.role === "master") ?? null;
                const workers = data.filter((node: any) => node.role !== "master");

                set({
                    master_worker: master,
                    fleet_worker: workers,
                });
            }
        } catch (error) {
            console.error("Silent refresh failed", error);
        }
    },

    toggleFileRamStatus: async (filename: string, isCurrentlyInRam: boolean) => {
            const selected_worker_id = get().selected_worker?.selected_worker_id;
            if (!selected_worker_id) {
                set({ errorMessage: "Không xác định được Worker đang thao tác", isErrorModalOpen: true });
                return;
            }
            const isMaster = selected_worker_id === "master_gateway";

            try {
                let resp;
                if (isCurrentlyInRam) {
                    // Đang ở trong RAM -> Gọi API Unload
                    resp = await (isMaster 
                        ? FleetAPI.master_unloadFileFromRam(filename) 
                        : FleetAPI.proxy_unloadFileFromRam(selected_worker_id, filename));
                } else {
                    // Chưa ở trong RAM -> Gọi API Load
                    resp = await (isMaster 
                        ? FleetAPI.master_loadFileToRam(filename) 
                        : FleetAPI.proxy_loadFileToRam(selected_worker_id, filename));
                }

                if (resp?.success) {
                    // Load/Unload thành công thì refresh lại UI của Drawer ngay lập tức
                    await get().openPoolsDrawer(selected_worker_id);
                } else {
                    set({ errorMessage: resp?.message || "Thao tác RAM thất bại", isErrorModalOpen: true });
                }
            } catch (error: any) {
                set({ errorMessage: error?.response?.data?.detail || error.message || "Lỗi mạng", isErrorModalOpen: true });
            }
        },
}),
{
    name: "fleet-storage", // Tên bộ nhớ lưu IP Server
    storage: createJSONStorage(() => localStorage),
    // CHỈ LƯU DUY NHẤT ĐỊA CHỈ IP (GATEWAY) ĐỂ BẢO VỆ MẠNG
    partialize: (state) => ({ gateway: state.gateway }),
}
));