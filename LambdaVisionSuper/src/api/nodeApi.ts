import { axiosClient, api_version } from './axiosClient';
import { PreflightData } from '../Stores/FlowStore';

export const NodeAPI = {
    // Gọi BE để lấy mảng manifest các nodes
    master_getCatalog: async (): Promise<any> => {
        const response = await axiosClient.get(`${api_version}/nodes/catalog`);
        return response; 
    },

    master_preflight_run: async (preflightData: PreflightData) : Promise<any> =>{
        const resp = await axiosClient.post(`${api_version}/nodes/preflight`, preflightData);
        return resp;
    },
    master_deploy_graph_to_ram: async(graph_file_name: string) : Promise<any> => {
        const resp = await axiosClient.post(`${api_version}/nodes/deploygraph/${graph_file_name}`)
        return resp.data
    },

    master_undeploy_graph_from_ram: async(logic_object_id: string) : Promise<any> => {
        const resp = await axiosClient.delete(`${api_version}/nodes/undeploygraph/${logic_object_id}`)
        return resp.data
    },

    master_execute_logic: async(logic_object_id: string, payload: any) : Promise<any> => {
        const resp = await axiosClient.post(`${api_version}/nodes/executelogic/${logic_object_id}`, payload)
        return resp.data
    },

    master_get_logic_id_list: async() : Promise<any> => {
        const resp = await axiosClient.get(`${api_version}/nodes/getLogicIDs`)
        return resp.data
    },

    master_get_inout_schemas: async(logic_object_id: string) : Promise<any> => {
        const resp = await axiosClient.get(`${api_version}/nodes/getinoutschema/${logic_object_id}`)
        return resp.data
    },

    proxy_getCatalog: async (server_id: string): Promise<any> => {
        const response = await axiosClient.get(`/proxy/${server_id}${api_version}/nodes/catalog`);
        return response; 
    },

    proxy_preflight_run: async (server_id: string, preflightData: PreflightData) : Promise<any> =>{
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/nodes/preflight`, preflightData);
        return resp;
    },
    proxy_deploy_graph_to_ram: async(server_id : string, graph_file_name: string) : Promise<any> => {
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/nodes/deploygraph/${graph_file_name}`)
        return resp.data
    },
    proxy_undeploy_graph_from_ram: async(server_id: string, logic_object_id: string) : Promise<any> => {
        const resp = await axiosClient.delete(`/proxy/${server_id}${api_version}/nodes/undeploygraph/${logic_object_id}`)
        return resp.data
    },
    proxy_execute_logic: async(server_id: string, logic_object_id: string, payload: any) : Promise<any> => {
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/nodes/executelogic/${logic_object_id}`, payload)
        return resp.data
    },
    proxy_get_logic_id_list: async(server_id: string) : Promise<any> => {
        const resp = await axiosClient.get(`/proxy/${server_id}${api_version}/nodes/getLogicIDs`)
        return resp.data
    },
    proxy_get_inout_schemas: async(server_id: string, logic_object_id: string) : Promise<any> => {
        const resp = await axiosClient.get(`/proxy/${server_id}${api_version}/nodes/getinoutschema/${logic_object_id}`)
        return resp.data
    },

    master_get_logic_dependencies: async (): Promise<Record<string, string>> => {
        const resp = await axiosClient.get(`${api_version}/nodes/dependencies`);
        return resp.data;
    },
    
    proxy_get_logic_dependencies: async (server_id: string): Promise<Record<string, string>> => {
        const resp = await axiosClient.get(`/proxy/${server_id}${api_version}/nodes/dependencies`);
        return resp.data;
    },

    master_sync_dependencies: async (payload: { logic_objects: Record<string, string> }): Promise<any> => {
        const resp = await axiosClient.post(`${api_version}/nodes/sync-dependencies`, payload);
        return resp.data;
    },
    proxy_sync_dependencies: async (server_id: string, payload: { logic_objects: Record<string, string> }): Promise<any> => {
        const resp = await axiosClient.post(`/proxy/${server_id}${api_version}/nodes/sync-dependencies`, payload);
        return resp.data;
    },
};

