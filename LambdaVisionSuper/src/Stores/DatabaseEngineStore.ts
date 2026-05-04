import { create } from "zustand";
import { DBEngineAPI } from "../api/dbEngineApi";

export interface DBFilter {
    id: string;
    column: string;
    // Thêm toán tử BETWEEN
    operator: '==' | '!=' | '>' | '<' | 'CONTAINS' | 'BETWEEN';
    value: any; // Chuyển thành any vì giá trị có thể là mảng ['start', 'end']
}

export interface ColumnConfig {
    originalName: string;
    displayName: string;     
    isVisible: boolean;      
    isImage: boolean;
    // Thêm boolean
    dataType: 'text' | 'number' | 'datetime' | 'boolean';
}

export interface DBEngineErrorModal {
    ErrorMessage: string;
    isOpen: boolean;
}

export interface DBImageModal {
    isOpen: boolean;
    imageFileName: string | null;
}

export interface DatabaseEngineStore {
    selectedServerId: string | null;
    selectedTable: string | null;
    setSelectedServer: (serverId: string) => void;
    setSelectedTable: (table: string) => void;
    
    tables: string[];
    schemaConfig: Record<string, ColumnConfig>; 
    filters: DBFilter[];
    
    queryResults: any[];
    isLoading: boolean;
    errorModal: DBEngineErrorModal;
    imageModal: DBImageModal;

    fetchTables: (serverId: string) => Promise<void>;
    fetchSchema: (serverId: string, tableName: string) => Promise<void>;
    updateColumnConfig: (columnName: string, updates: Partial<ColumnConfig>) => void;
    addFilter: () => void;
    updateFilter: (id: string, updates: Partial<DBFilter>) => void;
    removeFilter: (id: string) => void;
    executeQuery: () => Promise<void>; 
    
    openImageViewModal: (filename: string) => void; 
    closeImageViewModal: () => void;
    showErrorMessage: (msg: string) => void;
    closeErrorModal: () => void;
    downloadImage: (filename: string) => Promise<void>;

    isCreateTableModalOpen: boolean;
    openCreateTableModal: () => void;
    closeCreateTableModal: () => void;
    createTable: (payload: any) => Promise<void>;
}

export const useDBEngineStore = create<DatabaseEngineStore>((set, get) => ({
    selectedServerId: null,
    selectedTable: null,
    tables: [],
    schemaConfig: {},
    filters: [],
    queryResults: [],
    isLoading: false,
    
    errorModal: { ErrorMessage: "", isOpen: false },
    imageModal: { isOpen: false, imageFileName: null },

    isCreateTableModalOpen: false,
    openCreateTableModal: () => set({ isCreateTableModalOpen: true }),
    closeCreateTableModal: () => set({ isCreateTableModalOpen: false }),

    setSelectedServer: async (serverId) => {
        set({ selectedServerId: serverId, selectedTable: null, schemaConfig: {}, queryResults: [] });
        if (serverId) await get().fetchTables(serverId);
    },

    setSelectedTable: async (table) => {
        set({ selectedTable: table, queryResults: [] });
        const serverId = get().selectedServerId;
        if (serverId && table) await get().fetchSchema(serverId, table);
    },

    fetchTables: async (serverId) => {
        set({ isLoading: true });
        const isMaster = serverId === "master_gateway";
        try {
            const resp = await (
                isMaster 
                ? DBEngineAPI.master_getTables() 
                : DBEngineAPI.proxy_getTables(serverId)
            );
            // FIX LỖI: resp đã là mảng dữ liệu thật, không cần chấm data nữa
            set({ tables: Array.isArray(resp) ? resp : [], isLoading: false });
        } catch (error: any) {
            get().showErrorMessage(error?.response?.data?.detail || "Lỗi khi tải danh sách bảng từ Server.");
            set({ tables: [], isLoading: false });
        }
    },

    fetchSchema: async (serverId, tableName) => {
        set({ isLoading: true });
        const isMaster = serverId === "master_gateway";
        try {
            const resp = await (
                isMaster 
                ? DBEngineAPI.master_getSchema(tableName) 
                : DBEngineAPI.proxy_getSchema(serverId, tableName)
            );
            // FIX LỖI: resp chính là Object Schema config
            set({ schemaConfig: resp || {}, isLoading: false });
        } catch (error: any) {
            get().showErrorMessage(error?.response?.data?.detail || "Lỗi khi tải Schema của bảng.");
            set({ schemaConfig: {}, isLoading: false });
        }
    },

    updateColumnConfig: (columnName, updates) => set((state) => ({
        schemaConfig: {
            ...state.schemaConfig,
            [columnName]: { ...state.schemaConfig[columnName], ...updates }
        }
    })),

    addFilter: () => set((state) => ({
        filters: [...state.filters, { id: `flt_${Date.now()}`, column: '', operator: '==', value: '' }]
    })),

    updateFilter: (id, updates) => set((state) => ({
        filters: state.filters.map(f => f.id === id ? { ...f, ...updates } : f)
    })),

    removeFilter: (id) => set((state) => ({
        filters: state.filters.filter(f => f.id !== id)
    })),

    executeQuery: async () => {
        const { selectedServerId, selectedTable, schemaConfig, filters } = get();
        if (!selectedServerId || !selectedTable) return;

        set({ isLoading: true });
        
        const payload = {
            table: selectedTable,
            select_columns: Object.keys(schemaConfig).filter(k => schemaConfig[k].isVisible),
            conditions: filters.filter(f => f.column && f.value !== '')
        };

        const isMaster = selectedServerId === "master_gateway";
        try {
            const resp = await (
                isMaster 
                ? DBEngineAPI.master_executeQuery(payload) 
                : DBEngineAPI.proxy_executeQuery(selectedServerId, payload)
            );
            // FIX LỖI: resp chính là mảng chứa các object row kết quả
            set({ queryResults: Array.isArray(resp) ? resp : [], isLoading: false });
        } catch (error: any) {
            get().showErrorMessage(error?.response?.data?.detail || "Lỗi khi truy vấn Database.");
            set({ isLoading: false });
        }
    },

    openImageViewModal: (filename) => set({ imageModal: { isOpen: true, imageFileName: filename } }),
    closeImageViewModal: () => set({ imageModal: { isOpen: false, imageFileName: null } }),
    showErrorMessage: (msg) => set({ errorModal: { isOpen: true, ErrorMessage: msg } }),
    closeErrorModal: () => set({ errorModal: { isOpen: false, ErrorMessage: "" } }),
    
    downloadImage: async (filename) => {
        const { selectedServerId } = get();
        if (!selectedServerId) return;

        const isMaster = selectedServerId === "master_gateway";
        try {
            // 1. Gọi API lấy file thô (Blob)
            const blob = await (
                isMaster 
                ? DBEngineAPI.master_downloadImageBlob(filename) 
                : DBEngineAPI.proxy_downloadImageBlob(selectedServerId, filename)
            );
            
            // 2. Ép trình duyệt mở hộp thoại tải file (Save As...)
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename; // Tên file khi lưu về máy
            document.body.appendChild(a);
            a.click();
            
            // 3. Dọn dẹp bộ nhớ
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            get().showErrorMessage("Lỗi mạng: Không thể tải ảnh về máy.");
        }
    },
    createTable: async (payload) => {
        const { selectedServerId } = get();
        if (!selectedServerId) return;
        set({ isLoading: true });
        const isMaster = selectedServerId === "master_gateway";
        try {
            await (isMaster 
                ? DBEngineAPI.master_createTable(payload) 
                : DBEngineAPI.proxy_createTable(selectedServerId, payload));
            
            get().closeCreateTableModal();
            await get().fetchTables(selectedServerId); // Refresh danh sách bảng ngay lập tức
        } catch (error: any) {
            get().showErrorMessage(error?.response?.data?.detail || "Lỗi khi tạo bảng mới.");
            set({ isLoading: false });
        }
    },
}));