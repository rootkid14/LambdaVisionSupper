import axios from "axios";

export const api_version = "/api/v1";

export const axiosClient = axios.create({
    headers: {
        'Content-Type': 'application/json',
    },
});

// Thêm Interceptor để tự động gắn baseURL từ LocalStorage trước mọi request
axiosClient.interceptors.request.use((config) => {
    try {
        // Tên "fleet-storage" là tên bạn đặt trong persist của Zustand (ở FleetDashboardStores)
        const storageStr = localStorage.getItem("fleet-storage");
        if (storageStr) {
            const parsed = JSON.parse(storageStr);
            const gateway = parsed?.state?.gateway;
            
            // Nếu tìm thấy gateway trong ổ cứng và request chưa có baseURL, tự động gắn vào
            if (gateway && !config.baseURL) {
                config.baseURL = gateway;
            }
        }
    } catch (e) {
        console.error("Lỗi khi đọc gateway từ LocalStorage", e);
    }
    
    return config;
}, (error) => {
    return Promise.reject(error);
});