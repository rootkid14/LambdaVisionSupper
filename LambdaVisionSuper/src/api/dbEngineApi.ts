import { axiosClient, api_version } from "./axiosClient";

export const DBEngineAPI = {
    // 1. Lấy danh sách bảng trong DB
    master_getTables: async () => {
        const response = await axiosClient.get(`${api_version}/db/tables`);
        return response.data;
    },
    proxy_getTables: async (server_id: string) => {
        const response = await axiosClient.get(`/proxy/${server_id}${api_version}/db/tables`);
        return response.data;
    },

    // 2. Lấy cấu hình các cột (Schema) của một bảng
    master_getSchema: async (table_name: string) => {
        const response = await axiosClient.get(`${api_version}/db/schema/${table_name}`);
        return response.data;
    },
    proxy_getSchema: async (server_id: string, table_name: string) => {
        const response = await axiosClient.get(`/proxy/${server_id}${api_version}/db/schema/${table_name}`);
        return response.data;
    },

    // 3. Gửi kịch bản truy vấn (AST JSON) và nhận kết quả
    master_executeQuery: async (payload: any) => {
        const response = await axiosClient.post(`${api_version}/db/query`, payload);
        return response.data;
    },
    proxy_executeQuery: async (server_id: string, payload: any) => {
        const response = await axiosClient.post(`/proxy/${server_id}${api_version}/db/query`, payload);
        return response.data;
    },

    master_uploadImage: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axiosClient.post(`${api_version}/db/images/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data' 
            }
        });
        return response.data;
    },
    
    proxy_uploadImage: async (server_id: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axiosClient.post(`/proxy/${api_version}${server_id}/db/images/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    },

    // 2. GET IMAGE URL (Tạo chuỗi URL sạch để nhét vào thẻ <img src="...">)
    master_getImageUrl: (filename: string) => {
        // CLEAN CODE: Dùng getUri() để tự động sinh URL đầy đủ dựa trên baseURL hiện tại
        return axiosClient.getUri({ 
            url: `${api_version}/db/images/${filename}/download` 
        });
    },
    
    proxy_getImageUrl: (server_id: string, filename: string) => {
        // CLEAN CODE: Dùng getUri()
        return axiosClient.getUri({ 
            url: `/proxy/${server_id}${api_version}/db/images/${filename}/download` 
        });
    },

    // 3. DOWNLOAD IMAGE BLOB (Lấy file thô về để làm tính năng "Tải Ảnh Về Máy")
    master_downloadImageBlob: async (filename: string) => {
        const response = await axiosClient.get(`${api_version}/db/images/${filename}/download`, {
            responseType: 'blob'
        });
        return response.data;
    },
    
    proxy_downloadImageBlob: async (server_id: string, filename: string) => {
        const response = await axiosClient.get(`/proxy/${server_id}${api_version}/db/images/${filename}/download`, {
            responseType: 'blob'
        });
        return response.data; 
    },

    master_createTable: async (payload: { table_name: string, columns: any[] }) => {
        // Giả định prefix API của bạn là '/db', điều chỉnh lại cho khớp với route thực tế của bạn
        const response = await axiosClient.post(`${api_version}/db/tables/create`, payload);
        return response.data;
    },
    proxy_createTable: async (server_id: string, payload: { table_name: string, columns: any[] }) => {
        const response = await axiosClient.post(`/proxy/${server_id}${api_version}/db/tables/create`, payload);
        return response.data;
    },

    // ==========================================
    // 2. API CHÈN DỮ LIỆU ĐỘNG (INSERT DATA)
    // ==========================================
    master_insertData: async (payload: { table: string, data: Record<string, any> }) => {
        const response = await axiosClient.post(`${api_version}/db/insert`, payload);
        return response.data;
    },
    proxy_insertData: async (server_id: string, payload: { table: string, data: Record<string, any> }) => {
        const response = await axiosClient.post(`/proxy/${server_id}${api_version}/db/insert`, payload);
        return response.data;
    },
};