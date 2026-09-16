export type SamplingWorkspace = 'geometry' | 'spatial' | 'spectral';
export type ExecutionMode = 'live' | 'manual';

export interface SamplingPortManifest {
  type: string;
  optional: boolean;
  label?: string | null;
}

export interface SamplingParameterManifest {
  type: 'integer' | 'float' | 'boolean' | 'enum' | 'string';
  default: any;
  min?: number | null;
  max?: number | null;
  choices?: any[] | null;
  odd?: boolean;
  ui_hint?: string | null;
  label?: string | null;
  description?: string | null;
}

export interface SamplingGuideManifest {
  overview?: string;
  how_it_works?: string;
  tips?: string[];
  notes?: string[];
  visualization?: string;
}

export interface SamplingOperatorManifest {
  id: string;
  version: string;
  label: string;
  category: string;
  workspace: SamplingWorkspace;
  description?: string;
  inputs: Record<string, SamplingPortManifest>;
  outputs: Record<string, SamplingPortManifest>;
  parameters: Record<string, SamplingParameterManifest>;
  guide?: SamplingGuideManifest;
}

export interface SamplingEndpoint {
  node_id: string;
  port: string;
}

export interface SamplingPipelineDefinition {
  version: number;
  workspace: SamplingWorkspace;
  nodes: Array<{
    id: string;
    operator_id: string;
    operator_version?: string | null;
    parameters: Record<string, any>;
    enabled: boolean;
  }>;
  connections: Array<{
    source: SamplingEndpoint;
    target: SamplingEndpoint;
  }>;
  inputs: Record<string, SamplingEndpoint>;
  outputs: Record<string, SamplingEndpoint>;
}

export interface SamplingStackItem {
  id: string;
  operator: SamplingOperatorManifest;
  parameters: Record<string, any>;
  enabled: boolean;
  exposedName?: string | null;
}

export type SamplingArtifact =
  | { type: 'image'; shape: number[]; color_space?: string }
  | { type: 'binary_mask'; shape: number[] }
  | { type: 'contour_set'; source_shape: number[]; contours: number[][][] }
  | { type: 'polyline'; points: number[][]; closed: boolean; source_shape?: number[] | null }
  | { type: 'profile_set'; x: number[]; series: number[][]; labels: string[]; geometry?: any; units?: string; metadata?: any }
  | { type: 'histogram_1d'; bins: number[]; values: number[]; channel: string; normalized: boolean }
  | { type: 'feature_vector'; values: number[]; names: string[]; groups?: string[] | null; metadata?: any }
  | { type: 'feature_matrix'; values: number[][]; feature_names: string[]; row_labels: string[]; geometry?: any; metadata?: any }
  | { type: 'spectrum_2d'; shape: number[]; source_shape: number[]; window: string; channel: string; metadata?: any }
  | { type: 'measurement_table'; columns: string[]; rows: Record<string, any>[]; metadata?: any }
  | Record<string, any>;

export interface SamplingRunResponse {
  success: boolean;
  revision: number;
  result: {
    timings_ms: Record<string, number>;
    outputs: Record<string, { type: string; shape?: number[] | null }>;
  };
}

export interface InputBindingState {
  mode: 'upload' | 'lab_service';
  inputType: 'image' | 'binary_mask';
  file: File | null;
  serviceId: string;
  serviceVersion?: number;
  serviceOutput: string;
}
