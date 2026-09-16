export type LabDataType = 'image' | 'binary_mask' | 'roi' | string;

export interface PortManifest {
  type: LabDataType;
  optional?: boolean;
  label?: string | null;
}

export interface ParameterManifest {
  type: 'integer' | 'float' | 'boolean' | 'enum' | 'string' | string;
  default?: any;
  min?: number | null;
  max?: number | null;
  choices?: any[] | null;
  odd?: boolean;
  ui_hint?: string | null;
  label?: string | null;
  description?: string | null;
}

export interface OperatorManifest {
  id: string;
  version: string;
  label: string;
  category: string;
  description?: string;
  inputs: Record<string, PortManifest>;
  outputs: Record<string, PortManifest>;
  parameters: Record<string, ParameterManifest>;
}

export interface StackOperatorInstance {
  id: string;
  operatorId: string;
  parameters: Record<string, any>;
  enabled: boolean;
  expanded: boolean;
}

export interface PipelineEndpoint {
  node_id: string;
  port: string;
}

export interface PipelineConnection {
  source: PipelineEndpoint;
  target: PipelineEndpoint;
}

export interface ImagePipelineDefinition {
  version: number;
  nodes: Array<{
    id: string;
    operator_id: string;
    operator_version?: string | null;
    parameters: Record<string, any>;
    enabled: boolean;
  }>;
  connections: PipelineConnection[];
  inputs: Record<string, PipelineEndpoint>;
  outputs: Record<string, PipelineEndpoint>;
}

export interface ViewerSource {
  key: string;
  label: string;
  kind: 'source' | 'node' | 'latest';
  sourceName?: string;
  nodeId?: string;
  port?: string;
  dataType?: string;
}

export interface ViewerPane {
  id: string;
  sourceKey: string;
}

export type ImageLabExecutionMode = 'live' | 'manual';

export interface LabServiceOutputSelection {
  nodeId: string;
  port: string;
  name: string;
  dataType: string;
}
