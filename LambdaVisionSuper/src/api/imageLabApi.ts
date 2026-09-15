import { axiosClient, api_version } from './axiosClient';
import type { ImagePipelineDefinition, OperatorManifest } from '../components/VisionLabs/ImageProcessing/types';

export interface ImageLabSessionInfo {
  success: boolean;
  session_id: string;
  revision: number;
}

export interface ImageLabRunResponse {
  success: boolean;
  revision: number;
  result: {
    outputs: Record<string, any>;
    timings_ms: Record<string, number>;
    executed_nodes: string[];
    cached_nodes: string[];
  };
  artifacts: any[];
}

const readGateway = (): string => {
  const configured = axiosClient.defaults.baseURL;
  if (configured) return String(configured).replace(/\/$/, '');

  try {
    const raw = localStorage.getItem('fleet-storage');
    if (raw) {
      const parsed = JSON.parse(raw);
      const gateway = parsed?.state?.gateway;
      if (gateway) return String(gateway).replace(/\/$/, '');
    }
  } catch (error) {
    console.warn('[IMAGE LAB] Could not read gateway from localStorage', error);
  }

  return window.location.origin.replace(/\/$/, '');
};

export const ImageLabAPI = {
  getOperators: async (): Promise<OperatorManifest[]> => {
    const response = await axiosClient.get(`${api_version}/image-lab/operators`);
    return response.data?.operators ?? [];
  },

  createSession: async (): Promise<ImageLabSessionInfo> => {
    const response = await axiosClient.post(`${api_version}/image-lab/sessions`);
    return response.data;
  },

  closeSession: async (sessionId: string): Promise<void> => {
    await axiosClient.delete(`${api_version}/image-lab/sessions/${sessionId}`);
  },

  uploadInput: async (
    sessionId: string,
    file: File,
    sourceName = 'image',
  ): Promise<any> => {
    try {
      console.info(
        '[IMAGE LAB] Upload start',
        { sessionId, sourceName, name: file.name, size: file.size, type: file.type },
      );

      const response = await axiosClient.post(
        `${api_version}/image-lab/sessions/${sessionId}/input/${encodeURIComponent(sourceName)}`,
        file,
        {
          headers: {
            'Content-Type': 'application/octet-stream',
            'X-Image-Filename': encodeURIComponent(file.name),
          },
          timeout: 30_000,
          transformRequest: [(data) => data],
        },
      );

      console.info(
        '[IMAGE LAB] Upload complete',
        { status: response.status, bytesReceived: response.data?.bytes_received },
      );
      return response.data;
    } catch (error: any) {
      const detail =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        'Unknown upload error';

      if (error?.code === 'ECONNABORTED') {
        throw new Error('Image upload timed out after 30 seconds');
      }
      throw new Error(`Image upload failed: ${detail}`);
    }
  },

  setPipeline: async (
    sessionId: string,
    pipeline: ImagePipelineDefinition,
  ): Promise<any> => {
    const response = await axiosClient.put(
      `${api_version}/image-lab/sessions/${sessionId}/pipeline`,
      pipeline,
    );
    return response.data;
  },

  validatePipeline: async (pipeline: ImagePipelineDefinition): Promise<any> => {
    const response = await axiosClient.post(
      `${api_version}/image-lab/pipelines/validate`,
      pipeline,
    );
    return response.data;
  },

  run: async (sessionId: string): Promise<ImageLabRunResponse> => {
    const response = await axiosClient.post(
      `${api_version}/image-lab/sessions/${sessionId}/run`,
    );
    return response.data;
  },

  sourcePreview: async (
    sessionId: string,
    sourceName = 'image',
    maxWidth = 1200,
    quality = 82,
  ): Promise<Blob> => {
    const response = await axiosClient.get(
      `${api_version}/image-lab/sessions/${sessionId}/preview/source/${encodeURIComponent(sourceName)}`,
      { params: { max_width: maxWidth, quality }, responseType: 'blob' },
    );
    return response.data;
  },

  nodePreview: async (
    sessionId: string,
    nodeId: string,
    port: string,
    maxWidth = 1200,
    quality = 82,
  ): Promise<Blob> => {
    const response = await axiosClient.get(
      `${api_version}/image-lab/sessions/${sessionId}/preview/node/${encodeURIComponent(nodeId)}/${encodeURIComponent(port)}`,
      { params: { max_width: maxWidth, quality }, responseType: 'blob' },
    );
    return response.data;
  },

  liveUrl: (sessionId: string): string => {
    const gateway = readGateway();
    const url = new URL(
      `${api_version}/image-lab/sessions/${encodeURIComponent(sessionId)}/live`,
      `${gateway}/`,
    );
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return url.toString();
  },
};
