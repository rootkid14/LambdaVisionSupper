import { axiosClient, api_version } from './axiosClient';
import { WorkerInfoCard, LocalServerInfo, ResourceInfo, DeviceInfo, AddServerInfo, AddHttpDeviceInfo, ResourceType } from "../Stores/FleetDashboardStores";;
import { AxiosProgressEvent } from 'axios';

export const FleetAPI = {
    // Help master worker aggregate a big picture
    getFleetStatus: async (): Promise<WorkerInfoCard[]> => {
        const resp = await axiosClient.get(`/fleetstatus`);
        return resp.data;
    },

    getMasterLocalServers: async (): Promise<LocalServerInfo[]> => {
        const resp = await axiosClient.get(`${api_version}/infra/servers`);
        return resp.data;
    },

    getMasterLocalDevices: async (): Promise<DeviceInfo[]> => {
        const resp = await axiosClient.get(`${api_version}/infra/devices`)
        return resp.data;
    },

    getMasterLocalResource: async (): Promise<ResourceInfo> => {
        const resp = await axiosClient.get(`${api_version}/infra/resources/status`);
        return resp.data;
    },

    master_addLocalWorker: async (info: AddServerInfo): Promise<any> => {
        const resp = await axiosClient.post(`${api_version}/infra/servers/add`, info)
        return resp.data;
    },

    master_removeLocalServer: async(server_id_to_remove: string) : Promise<any> => {
        const resp = await axiosClient.delete(`${api_version}/infra/servers/delete/${server_id_to_remove}`)
        return resp.data;
    },

    master_addLocalDevice: async (info: AddHttpDeviceInfo): Promise<any> => {
        const resp = await axiosClient.post(`${api_version}/infra/devices/add`, info)
        return resp.data;
    },

    master_removeLocalDevice: async(device_id_to_remove: string) : Promise<any> => {
        const resp = await axiosClient.delete(`${api_version}/infra/devices/delete/${device_id_to_remove}`)
        return resp.data;
    },

    master_downloadFile: async (filename: string, filetype: string): Promise<Blob> => {
        const resp = await axiosClient.get(`${api_version}/infra/resources/files/${filetype}/${filename}/download`, {
            responseType: 'blob' // QUAN TRỌNG: Nói cho Axios biết đây là file nhị phân
        });
        return resp.data;
    },

    master_uploadFile: async (file: File, filetype: string, onUploadProgress?: (progressEvent: AxiosProgressEvent) => void): Promise<any> => {
        const formData = new FormData();
        formData.append('file', file);
        const resp = await axiosClient.post(`${api_version}/infra/resources/files/${filetype}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress
        });
        return resp.data;
    },


    master_removeResource: async (filename_to_remove: string, filetype: ResourceType) => {
        const resp = await axiosClient.delete(`${api_version}/infra/resources/delete/${filetype}/${filename_to_remove}`)
        return resp.data
    },

    proxy_getWorkerLocalServers: async (server_id: string): Promise<LocalServerInfo[]> => {
        // Returning a list of local workers relative to this server_id List[{"id", "host", "status", "ping"}]
        const resp = await axiosClient.get(`/proxy/${server_id}${api_version}/infra/servers`);
        return resp.data; // Đã thêm ;
    },

    proxy_getWorkerLocalResource: async (server_id: string): Promise<ResourceInfo> => {
        // Returning an overview of the files and graphs resources being deployed onto this worker
        const resp = await axiosClient.get(`/proxy/${server_id}${api_version}/infra/resources/status`);
        return resp.data; // Đã thêm ;
    },
    proxy_getWorkerLocalDevices: async (server_id: string): Promise<DeviceInfo[]> => {
        //Returning list of local devices relative to this server_id
        const resp = await axiosClient.get(`/proxy/${server_id}${api_version}/infra/devices`);
        return resp.data;
    },
    proxy_addLocalWorker: async (server_id: string , info: AddServerInfo): Promise<any> => {
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/infra/servers/add`, info)
        return resp.data
    },

    proxy_removeLocalServer: async(server_id :string, server_id_to_remove: string) : Promise<any> => {
        const resp = await axiosClient.delete(`/proxy/${server_id}${api_version}/infra/servers/delete/${server_id_to_remove}`)
        return resp.data;
    },

    proxy_addLocalDevice: async (server_id: string , info: AddHttpDeviceInfo): Promise<any> => {
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/infra/devices/add`, info)
        return resp.data
    },

    proxy_removeLocalDevice: async(server_id :string, device_id_to_remove: string) : Promise<any> => {
        const resp = await axiosClient.delete(`/proxy/${server_id}${api_version}/infra/devices/delete/${device_id_to_remove}`)
        return resp.data;
    },

    proxy_uploadFile: async (server_id: string, file: File, filetype: string, onUploadProgress?: (progressEvent: AxiosProgressEvent) => void): Promise<any> => {
        const formData = new FormData();
        formData.append('file', file);
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/infra/resources/files/${filetype}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress
        });
        return resp.data;
    },

    proxy_downloadFile: async (server_id: string, filename: string, filetype: string): Promise<Blob> => {
        const resp = await axiosClient.get(`/proxy/${server_id}${api_version}/infra/resources/files/${filetype}/${filename}/download`, {
            responseType: 'blob' // QUAN TRỌNG: Nói cho Axios biết đây là file nhị phân
        });
        return resp.data;
    },

    proxy_removeResource: async (server_id: string, filename_to_remove: string, filetype: ResourceType) => {
        const resp = await axiosClient.delete(`/proxy/${server_id}${api_version}/infra/resources/delete/${filetype}/${filename_to_remove}`)
        return resp.data
    },

    master_loadFileToRam: async (filename: string): Promise<any> => {
        const resp = await axiosClient.post(`${api_version}/infra/resources/files/load-to-ram/${filename}`);
        return resp.data;
    },
    proxy_loadFileToRam: async (server_id: string, filename: string): Promise<any> => {
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/infra/resources/files/load-to-ram/${filename}`);
        return resp.data;
    },

    master_unloadFileFromRam: async (filename: string): Promise<any> => {
        const resp = await axiosClient.post(`${api_version}/infra/resources/files/unload-from-ram/${filename}`);
        return resp.data;
    },
    proxy_unloadFileFromRam: async (server_id: string, filename: string): Promise<any> => {
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/infra/resources/files/unload-from-ram/${filename}`);
        return resp.data;
    },
    master_getFileContent: async (filename: string, filetype: string): Promise<any> => {
        const resp = await axiosClient.get(`${api_version}/infra/resources/files/${filetype}/${filename}/content`);
        return resp.data;
    },
}; 