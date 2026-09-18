import { axiosClient, api_version } from './axiosClient';
import type {
  SamplingArtifact,
  SamplingOperatorManifest,
  SamplingPipelineDefinition,
  SamplingRunResponse,
  SamplingWorkspace,
  SourceBoardConfig,
  SourceBoardManifest,
} from '../components/VisionLabs/SamplingGeometry/types';

export const SamplingGeometryAPI = {
  operators: async (workspace?: SamplingWorkspace): Promise<SamplingOperatorManifest[]> => {
    const response = await axiosClient.get(`${api_version}/sampling-geometry/operators`, {
      params: workspace ? { workspace } : undefined,
    });
    return response.data?.operators ?? [];
  },

  createSession: async (): Promise<{ session_id: string; revision: number }> => {
    const response = await axiosClient.post(`${api_version}/sampling-geometry/sessions`);
    return response.data;
  },

  closeSession: async (sessionId: string): Promise<void> => {
    await axiosClient.delete(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}`);
  },

  buildSourceBoard: async (
    sessionId: string,
    file: File,
    config: SourceBoardConfig,
  ): Promise<SourceBoardManifest> => {
    const response = await axiosClient.post(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/source-board`,
      file,
      {
        params: {
          image_service_id: config.image_service.service_id || undefined,
          image_output_name: config.image_service.output_name || undefined,
          image_version: config.image_service.version || undefined,
          geometry_service_id: config.geometry_service.service_id || undefined,
          geometry_output_name: config.geometry_service.output_name || undefined,
          geometry_version: config.geometry_service.version || undefined,
          canny_low: config.canny_low,
          canny_high: config.canny_high,
          blur_kernel: config.blur_kernel,
        },
        headers: { 'Content-Type': 'application/octet-stream' },
        timeout: 90_000,
        transformRequest: [(data) => data],
      },
    );
    return response.data.source_board;
  },

  sourceBoard: async (sessionId: string): Promise<SourceBoardManifest> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/source-board`,
    );
    return response.data.source_board;
  },

  sourceArtifact: async (sessionId: string, sourceName: string): Promise<SamplingArtifact> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/source-board/${encodeURIComponent(sourceName)}/artifact`,
    );
    return response.data.artifact;
  },

  setPipeline: async (sessionId: string, pipeline: SamplingPipelineDefinition): Promise<any> => {
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

  sourcePreview: async (sessionId: string, sourceName: string): Promise<Blob> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/preview/source/${encodeURIComponent(sourceName)}`,
      { params: { max_width: 2200, quality: 94 }, responseType: 'blob' },
    );
    return response.data;
  },

  artifact: async (sessionId: string, nodeId: string, port: string): Promise<SamplingArtifact> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/artifact/${encodeURIComponent(nodeId)}/${encodeURIComponent(port)}`,
    );
    return response.data.artifact;
  },

  artifactPreview: async (sessionId: string, nodeId: string, port: string): Promise<Blob> => {
    const response = await axiosClient.get(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/preview/node/${encodeURIComponent(nodeId)}/${encodeURIComponent(port)}`,
      { params: { max_width: 2200, quality: 94 }, responseType: 'blob' },
    );
    return response.data;
  },
};
