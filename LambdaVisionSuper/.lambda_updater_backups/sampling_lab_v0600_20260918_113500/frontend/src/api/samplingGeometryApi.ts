import { axiosClient, api_version } from './axiosClient';
import type { SamplingArtifact, SamplingOperatorManifest, SamplingPipelineDefinition, SamplingRunResponse, SamplingWorkspace, SourceBoardConfig, SourceBoardManifest } from '../components/VisionLabs/SamplingGeometry/types';
import type { SamplingMethodCatalogItem, SamplingProgramDefinition, SamplingProgramRun } from '../components/VisionLabs/SamplingProgram/types';

export const SamplingGeometryAPI = {
  operators: async (workspace?: SamplingWorkspace): Promise<SamplingOperatorManifest[]> => {
    const response = await axiosClient.get(`${api_version}/sampling-geometry/operators`, { params: workspace ? { workspace } : undefined });
    return response.data?.operators ?? [];
  },
  createSession: async () => (await axiosClient.post(`${api_version}/sampling-geometry/sessions`)).data,
  closeSession: async (sessionId: string) => { await axiosClient.delete(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}`); },
  buildSourceBoard: async (sessionId: string, file: File, config: SourceBoardConfig): Promise<SourceBoardManifest> => {
    const response = await axiosClient.post(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/source-board`, file, {
      params: {
        image_service_id: config.image_service.service_id || undefined,
        image_output_name: config.image_service.output_name || undefined,
        image_version: config.image_service.version || undefined,
        enable_geometry: false,
      },
      headers: { 'Content-Type': 'application/octet-stream' }, timeout: 90_000,
      transformRequest: [(data) => data],
    });
    return response.data.source_board;
  },
  setPipeline: async (sessionId: string, pipeline: SamplingPipelineDefinition) => (await axiosClient.put(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/pipeline`, pipeline)).data,
  run: async (sessionId: string): Promise<SamplingRunResponse> => (await axiosClient.post(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/run`)).data,
  sourceArtifact: async (sessionId: string, sourceName: string): Promise<SamplingArtifact> => (await axiosClient.get(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/source-board/${encodeURIComponent(sourceName)}/artifact`)).data.artifact,
  channelPreview: async (sessionId: string, sourceName: string, channel: string): Promise<Blob> => (await axiosClient.get(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/source-board/${encodeURIComponent(sourceName)}/channel-preview`, { params:{channel,max_width:1400}, responseType:'blob' })).data,
  sourcePreview: async (sessionId: string, sourceName: string): Promise<Blob> => (await axiosClient.get(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/preview/source/${encodeURIComponent(sourceName)}`, { params: {max_width:2200,quality:94}, responseType:'blob' })).data,
  artifact: async (sessionId: string, nodeId: string, port: string): Promise<SamplingArtifact> => (await axiosClient.get(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/artifact/${encodeURIComponent(nodeId)}/${encodeURIComponent(port)}`)).data.artifact,
  artifactPreview: async (sessionId: string, nodeId: string, port: string): Promise<Blob> => (await axiosClient.get(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/preview/node/${encodeURIComponent(nodeId)}/${encodeURIComponent(port)}`, { params:{max_width:2200,quality:94}, responseType:'blob' })).data,
  fftReconstruction: async (sessionId: string, nodeId: string, params: Record<string, any>): Promise<Blob> => (await axiosClient.get(`${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/fft-reconstruction/${encodeURIComponent(nodeId)}`, { params, responseType:'blob' })).data,

  programMethods: async (): Promise<SamplingMethodCatalogItem[]> => {
    const response = await axiosClient.get(`${api_version}/sampling-geometry/program/methods`);
    return response.data?.methods ?? [];
  },

  runProgram: async (sessionId: string, program: SamplingProgramDefinition): Promise<SamplingProgramRun> => {
    const response = await axiosClient.post(
      `${api_version}/sampling-geometry/sessions/${encodeURIComponent(sessionId)}/program/run`,
      program,
      { timeout: 120_000 },
    );
    return response.data;
  },
};
