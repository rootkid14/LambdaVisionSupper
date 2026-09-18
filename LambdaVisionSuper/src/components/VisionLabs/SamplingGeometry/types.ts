export type SamplingWorkspace = 'geometry' | 'spatial' | 'spectral';
export type ActiveSamplingWorkspace = 'spatial' | 'spectral';
export type ExecutionMode = 'live' | 'manual';

export interface SamplingPortManifest { type: string; optional: boolean; label?: string | null; }
export interface SamplingParameterManifest {
  type: 'integer' | 'float' | 'boolean' | 'enum' | 'string';
  default: any; min?: number | null; max?: number | null; choices?: any[] | null;
  odd?: boolean; ui_hint?: string | null; label?: string | null; description?: string | null;
}
export interface SamplingGuideManifest { overview?: string; how_it_works?: string; tips?: string[]; notes?: string[]; visualization?: string; }
export interface SamplingOperatorManifest {
  id: string; version: string; label: string; category: string; workspace: SamplingWorkspace;
  description?: string; catalog_visible?: boolean;
  inputs: Record<string, SamplingPortManifest>; outputs: Record<string, SamplingPortManifest>;
  parameters: Record<string, SamplingParameterManifest>; guide?: SamplingGuideManifest;
}
export interface SamplingEndpoint { node_id: string; port: string; }
export interface SourceBoardServicePin { service_id: string; version?: number | null; output_name: string; }
export interface SourceBoardConfig {
  image_service: SourceBoardServicePin;
  geometry_service?: SourceBoardServicePin;
  enable_geometry: boolean;
  canny_low?: number; canny_high?: number; blur_kernel?: number;
}
export interface SourceBoardEntry { name: string; label: string; type: string; shape?: number[] | null; origin: string; }
export interface SourceBoardManifest { config: SourceBoardConfig; upstream?: Record<string, any>; entries: SourceBoardEntry[]; geometry_contour_count?: number; }
export interface SamplingPipelineDefinition {
  version: number; workspace: SamplingWorkspace;
  nodes: Array<{ id: string; operator_id: string; operator_version?: string | null; parameters: Record<string, any>; enabled: boolean; }>;
  connections: Array<{ source: SamplingEndpoint; target: SamplingEndpoint; }>;
  inputs: Record<string, SamplingEndpoint>; outputs: Record<string, SamplingEndpoint>;
  input_sources?: Record<string, string>; source_board?: SourceBoardConfig | Record<string, any>;
}
export interface SamplingStackItem {
  id: string; operator: SamplingOperatorManifest; parameters: Record<string, any>; enabled: boolean;
  referenceBindings: Record<string, string>; exposedOutputs: Record<string, string>;
}
export interface DataBlockArtifact {
  block_id: string; label: string; shape: number[]; source_element: string; channel: string; kind: string;
  description?: string; values: number[]; metadata?: Record<string, any>;
}
export type SamplingArtifact =
  | { type: 'image'; shape: number[]; color_space?: string }
  | { type: 'binary_mask'; shape: number[] }
  | { type: 'sampling_housing'; kind: string; source_shape: number[]; elements: any[]; element_count: number; geometry?: any; metadata?: any }
  | { type: 'data_block_set'; count: number; blocks: DataBlockArtifact[]; metadata?: any }
  | { type: 'composed_data'; shape: number[]; layout: string; block_order: string[]; block_shapes: Record<string, number[]>; values: number[] | number[][]; metadata?: any }
  | { type: 'profile_set'; x: number[]; series: number[][]; labels: string[]; geometry?: any; units?: string; metadata?: any }
  | { type: 'histogram_1d'; bins: number[]; values: number[]; channel: string; normalized: boolean }
  | { type: 'feature_vector'; values: number[]; names: string[]; groups?: string[] | null; metadata?: any; dimension?: number }
  | { type: 'feature_matrix'; values: number[][]; feature_names: string[]; row_labels: string[]; geometry?: any; metadata?: any; shape?: number[] }
  | { type: 'spectrum_2d'; shape: number[]; source_shape: number[]; window: string; channel: string; metadata?: any }
  | Record<string, any>;
export interface SamplingRunResponse { success: boolean; revision: number; result: { timings_ms: Record<string, number>; outputs: Record<string, {type:string;shape?:number[]|null}>; }; }
export interface WorkspaceState { stack: SamplingStackItem[]; selectedNodeId: string | null; selectedPort: string | null; sourceName: string; timings: Record<string, number>; pending: boolean; }

export interface SpatialSamplingUnit {
  id: string;
  name: string;
  housing: SamplingOperatorManifest;
  housingParameters: Record<string, any>;
  extractor: SamplingOperatorManifest;
  extractorParameters: Record<string, any>;
  visible: boolean;
  exposedAlias: string;
  housingArtifact?: SamplingArtifact | null;
  blocksArtifact?: SamplingArtifact | null;
  dataArtifact?: SamplingArtifact | null;
}
