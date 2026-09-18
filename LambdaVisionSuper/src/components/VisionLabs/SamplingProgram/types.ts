import type { SourceBoardConfig, SourceBoardManifest } from '../SamplingGeometry/types';

export type SamplingDomain = 'global' | 'local';
export type SamplingMethodKind = 'histogram' | 'statistics' | 'rays' | 'cross' | 'rings';
export type SamplingPlacementMode = 'domain' | 'center' | 'auto_grid';
export type SamplingMode = 'count' | 'step' | 'full';
export type LocalLayout = 'vector' | 'matrix';
export type LocalVectorOrder = 'patch_major' | 'feature_major';
export type LocalMatrixAxis = 'patch_rows' | 'patch_columns';

export interface SamplingMethodCatalogItem {
  kind: SamplingMethodKind;
  label: string;
  family: string;
  description: string;
  supports_placement: boolean;
  default_measures: string[];
  guide?: { concept?: string; formula?: string; visual?: string };
}

export interface SamplingPlacement {
  mode: SamplingPlacementMode;
  center_x: number;
  center_y: number;
  rows: number;
  cols: number;
}

export interface SamplingMethodDefinition {
  id: string;
  kind: SamplingMethodKind;
  label?: string | null;
  enabled: boolean;
  channels: string[];
  measures: string[];
  placement: SamplingPlacement;
  sampling_mode: SamplingMode;
  sample_count: number;
  sample_step: number;
  histogram_bins: number;
  parameters: Record<string, any>;
}

export interface SamplingProgramDefinition {
  version: 6;
  program_kind: 'sampling_program_v2';
  source_board: SourceBoardConfig | Record<string, any>;
  input_source: string;
  global_domain: { methods: SamplingMethodDefinition[] };
  local_domain: {
    grid: { rows: number; cols: number; gap_px: number };
    methods: SamplingMethodDefinition[];
  };
  output_shape: {
    global_layout: 'vector';
    local_layout: LocalLayout;
    local_vector_order: LocalVectorOrder;
    local_matrix_axis: LocalMatrixAxis;
    include_global: boolean;
    include_local: boolean;
    include_combined: boolean;
  };
}

export interface ProgramDataBlock {
  block_id: string;
  label: string;
  shape: number[];
  source_element: string;
  channel: string;
  kind: string;
  description?: string;
  values: number[];
  metadata?: Record<string, any>;
}

export interface ProgramDataBlockSet {
  type: 'data_block_set';
  count: number;
  blocks: ProgramDataBlock[];
  metadata?: Record<string, any>;
}

export interface ProgramComposedData {
  type: 'composed_data';
  shape: number[];
  layout: 'vector' | 'matrix' | string;
  block_order: string[];
  block_shapes: Record<string, number[]>;
  values: any;
  metadata?: Record<string, any>;
}

export interface SamplingProgramRun {
  success: boolean;
  program_kind: 'sampling_program_v2';
  formulation_only?: boolean;
  manifest: {
    global_feature_count: number;
    local_shape: number[];
    combined_feature_count: number;
    patch_count: number;
    features_per_patch: number;
    local_representation: string;
    method_summaries: Record<string, any>;
    timings_ms: Record<string, number>;
  };
  global_blocks: ProgramDataBlockSet;
  global_data: ProgramComposedData;
  local: {
    grid: { rows: number; cols: number };
    patch_bounds: number[][];
    patches: ProgramDataBlockSet[];
  };
  local_data: ProgramComposedData;
  combined_data: ProgramComposedData;
}

export interface SamplingProgramState {
  activeDomain: SamplingDomain;
  selectedMethodId: string | null;
  program: SamplingProgramDefinition;
  run: SamplingProgramRun | null;
  sourceBoard: SourceBoardManifest | null;
}
