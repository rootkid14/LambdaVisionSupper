import { axiosClient, api_version } from './axiosClient';

export interface LabServicePort {
  type: string;
  required: boolean;
  label?: string | null;
}

export interface LabServiceOutputBinding {
  type: string;
  node_id: string;
  port: string;
  label?: string | null;
}

export interface LabServiceDefinition {
  service_id: string;
  name: string;
  lab_type: string;
  workspace_type?: string | null;
  version: number;
  status: string;
  inputs: Record<string, LabServicePort>;
  outputs: Record<string, LabServiceOutputBinding>;
  pipeline_snapshot: Record<string, any>;
  description?: string | null;
  created_at: string;
  deployed_at: string;
}

export interface LabServiceRunManifest {
  run_id: string;
  service_id: string;
  service_version: number;
  lab_type: string;
  workspace_type?: string | null;
  outputs: Record<string, {
    type: string;
    node_id: string;
    port: string;
    shape?: number[] | null;
    artifact_id?: string;
  }>;
  timings_ms: Record<string, number>;
  total_ms: number;
  started_at: string;
}

export interface DeployLabServiceRequest {
  service_id?: string | null;
  name: string;
  lab_type: string;
  workspace_type?: string | null;
  pipeline_snapshot: Record<string, any>;
  outputs: Record<string, {
    node_id: string;
    port: string;
    label?: string | null;
  }>;
  description?: string | null;
}

export const LabServiceAPI = {
  list: async (): Promise<LabServiceDefinition[]> => {
    const response = await axiosClient.get(`${api_version}/lab-services`);
    return response.data?.services ?? [];
  },

  deploy: async (
    request: DeployLabServiceRequest,
  ): Promise<LabServiceDefinition> => {
    const response = await axiosClient.post(
      `${api_version}/lab-services/deploy`,
      request,
    );
    return response.data.service;
  },

  get: async (
    serviceId: string,
    version?: number,
  ): Promise<LabServiceDefinition> => {
    const response = await axiosClient.get(
      `${api_version}/lab-services/${encodeURIComponent(serviceId)}`,
      { params: version ? { version } : undefined },
    );
    return response.data.service;
  },

  runImage: async (
    serviceId: string,
    file: File,
    version?: number,
  ): Promise<LabServiceRunManifest> => {
    const response = await axiosClient.post(
      `${api_version}/lab-services/${encodeURIComponent(serviceId)}/run`,
      file,
      {
        params: version ? { version } : undefined,
        headers: {
          'Content-Type': 'application/octet-stream',
          'X-Image-Filename': encodeURIComponent(file.name),
        },
        timeout: 60_000,
        transformRequest: [(data) => data],
      },
    );
    return response.data.run;
  },


  remove: async (serviceId: string): Promise<void> => {
    await axiosClient.delete(`${api_version}/lab-services/${encodeURIComponent(serviceId)}`);
  },

  outputPreview: async (
    runId: string,
    outputName: string,
    maxWidth = 1200,
    quality = 88,
  ): Promise<Blob> => {
    const response = await axiosClient.get(
      `${api_version}/lab-services/runs/${encodeURIComponent(runId)}/outputs/${encodeURIComponent(outputName)}`,
      {
        params: { max_width: maxWidth, quality },
        responseType: 'blob',
      },
    );
    return response.data;
  },
};
