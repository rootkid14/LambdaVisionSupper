import { axiosClient, api_version } from './axiosClient';
import type {
  SamplingArtifact,
  SamplingOperatorManifest,
  SamplingPipelineDefinition,
  SamplingRunResponse,
  SamplingWorkspace,
} from '../components/VisionLabs/SamplingGeometry/types';

export const SamplingGeometryAPI = {
  operators: async (
    workspace?: SamplingWorkspace,
  ): Promise<SamplingOperatorManifest[]> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/operators`,
      { params: workspace ? { workspace } : undefined },
    );
    return response.data?.operators ?? [];
  },

  createSession: async (): Promise<{ session_id: string; revision: number }> => {
    const response = await axiosClient.post(`${api_version}/sampling-geometry/sessions`);
    return response.data;
  },

  closeSession: async (sessionId: string): Promise<void> => {
    await axiosClient.delete(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}`,
    );
  },

  uploadInput: async (
    sessionId: string,
    file: File,
    inputType: 'image' | 'binary_mask',
    sourceName = 'input',
  ): Promise<any> => {
    const response = await axiosClient.post(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/input/${encodeURIComponent(sourceName)}`,
      file,
      {
        params: { input_type: inputType },
        headers: { 'Content-Type': 'application/octet-stream' },
        timeout: 60_000,
        transformRequest: [(data) => data],
      },
    );
    return response.data;
  },

  bindFromLabService: async (
    sessionId: string,
    file: File,
    serviceId: string,
    outputName: string,
    version?: number,
    sourceName = 'input',
  ): Promise<any> => {
    const response = await axiosClient.post(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/input/${encodeURIComponent(sourceName)}/from-lab-service`,
      file,
      {
        params: {
          service_id: serviceId,
          output_name: outputName,
          ...(version ? { version } : {}),
        },
        headers: { 'Content-Type': 'application/octet-stream' },
        timeout: 60_000,
        transformRequest: [(data) => data],
      },
    );
    return response.data;
  },

  setPipeline: async (
    sessionId: string,
    pipeline: SamplingPipelineDefinition,
  ): Promise<any> => {
    const response = await axiosClient.put(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/pipeline`,
      pipeline,
    );
    return response.data;
  },

  run: async (sessionId: string): Promise<SamplingRunResponse> => {
    const response = await axiosClient.post(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/run`,
    );
    return response.data;
  },

  sourcePreview: async (
    sessionId: string,
    sourceName = 'input',
  ): Promise<Blob> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/preview/source/${encodeURIComponent(sourceName)}`,
      { params: { max_width: 1800, quality: 92 }, responseType: 'blob' },
    );
    return response.data;
  },

  artifact: async (
    sessionId: string,
    nodeId: string,
    port: string,
  ): Promise<SamplingArtifact> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/artifact/${encodeURIComponent(nodeId)}/${encodeURIComponent(port)}`,
    );
    return response.data.artifact;
  },

  artifactPreview: async (
    sessionId: string,
    nodeId: string,
    port: string,
  ): Promise<Blob> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/preview/node/${encodeURIComponent(nodeId)}/${encodeURIComponent(port)}`,
      { params: { max_width: 1800, quality: 92 }, responseType: 'blob' },
    );
    return response.data;
  },
};
