#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap

VERSION = "0.1.0"
BACKUP_DIRNAME = ".lambda_updater_backups"


def dedent(s: str) -> str:
    return textwrap.dedent(s).lstrip("\n").rstrip() + "\n"


GENERATED = {
    "api/imageLabApi.ts": dedent(r'''
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
            const formData = new FormData();
            formData.append('file', file);
            const response = await axiosClient.post(
              `${api_version}/image-lab/sessions/${sessionId}/input/${encodeURIComponent(sourceName)}`,
              formData,
              { headers: { 'Content-Type': 'multipart/form-data' } },
            );
            return response.data;
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
    '''),

    "components/VisionLabs/ImageProcessing/types.ts": dedent(r'''
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
          kind: 'source' | 'node';
          sourceName?: string;
          nodeId?: string;
          port?: string;
          dataType?: string;
        }

        export type ViewerCount = 1 | 2 | 4;
    '''),

    "components/VisionLabs/ImageProcessing/pipelineUtils.ts": dedent(r'''
        import type {
          ImagePipelineDefinition,
          OperatorManifest,
          StackOperatorInstance,
          ViewerSource,
        } from './types';

        export const firstEntry = <T,>(record: Record<string, T>): [string, T] | null => {
          const entry = Object.entries(record)[0];
          return entry ? (entry as [string, T]) : null;
        };

        export const operatorDefaults = (manifest: OperatorManifest): Record<string, any> => {
          const values: Record<string, any> = {};
          Object.entries(manifest.parameters ?? {}).forEach(([name, spec]) => {
            values[name] = spec.default;
          });
          return values;
        };

        export const isLinearStackOperator = (manifest: OperatorManifest): boolean => {
          return Object.keys(manifest.inputs ?? {}).length === 1
            && Object.keys(manifest.outputs ?? {}).length === 1;
        };

        export const stackCompatibility = (
          stack: StackOperatorInstance[],
          candidate: OperatorManifest,
          manifests: Map<string, OperatorManifest>,
        ): { ok: boolean; reason?: string } => {
          if (!isLinearStackOperator(candidate)) {
            return { ok: false, reason: 'This operator needs advanced/multi-port wiring.' };
          }

          const candidateInput = firstEntry(candidate.inputs);
          if (!candidateInput) return { ok: false, reason: 'Operator has no input port.' };

          if (stack.length === 0) {
            if (candidateInput[1].type !== 'image') {
              return { ok: false, reason: `Stack input starts as image, not ${candidateInput[1].type}.` };
            }
            return { ok: true };
          }

          const previous = manifests.get(stack[stack.length - 1].operatorId);
          if (!previous) return { ok: false, reason: 'Previous operator manifest is unavailable.' };
          const previousOutput = firstEntry(previous.outputs);
          if (!previousOutput) return { ok: false, reason: 'Previous operator has no output.' };

          if (previousOutput[1].type !== candidateInput[1].type) {
            return {
              ok: false,
              reason: `${previousOutput[1].type} cannot feed ${candidateInput[1].type}.`,
            };
          }
          return { ok: true };
        };

        export const validateLinearStack = (
          stack: StackOperatorInstance[],
          manifests: Map<string, OperatorManifest>,
        ): { ok: boolean; reason?: string } => {
          if (stack.length === 0) return { ok: true };

          for (let index = 0; index < stack.length; index += 1) {
            const manifest = manifests.get(stack[index].operatorId);
            if (!manifest) return { ok: false, reason: `Unknown operator: ${stack[index].operatorId}` };
            if (!isLinearStackOperator(manifest)) {
              return { ok: false, reason: `${manifest.label} requires advanced wiring.` };
            }
            const input = firstEntry(manifest.inputs);
            const output = firstEntry(manifest.outputs);
            if (!input || !output) return { ok: false, reason: `${manifest.label} has invalid ports.` };
            if (index === 0 && input[1].type !== 'image') {
              return { ok: false, reason: `${manifest.label} cannot consume the source image directly.` };
            }
            if (index > 0) {
              const previous = manifests.get(stack[index - 1].operatorId)!;
              const previousOutput = firstEntry(previous.outputs)!;
              if (previousOutput[1].type !== input[1].type) {
                return {
                  ok: false,
                  reason: `${previous.label} (${previousOutput[1].type}) → ${manifest.label} (${input[1].type}) is incompatible.`,
                };
              }
            }
          }
          return { ok: true };
        };

        export const buildPipelineDefinition = (
          stack: StackOperatorInstance[],
          manifests: Map<string, OperatorManifest>,
        ): ImagePipelineDefinition => {
          if (stack.length === 0) {
            return { version: 1, nodes: [], connections: [], inputs: {}, outputs: {} };
          }

          const nodes = stack.map((instance) => ({
            id: instance.id,
            operator_id: instance.operatorId,
            operator_version: manifests.get(instance.operatorId)?.version ?? null,
            parameters: { ...instance.parameters },
            enabled: instance.enabled,
          }));

          const connections: ImagePipelineDefinition['connections'] = [];
          for (let index = 1; index < stack.length; index += 1) {
            const previousManifest = manifests.get(stack[index - 1].operatorId)!;
            const currentManifest = manifests.get(stack[index].operatorId)!;
            const previousOutput = firstEntry(previousManifest.outputs)!;
            const currentInput = firstEntry(currentManifest.inputs)!;
            connections.push({
              source: { node_id: stack[index - 1].id, port: previousOutput[0] },
              target: { node_id: stack[index].id, port: currentInput[0] },
            });
          }

          const firstManifest = manifests.get(stack[0].operatorId)!;
          const lastManifest = manifests.get(stack[stack.length - 1].operatorId)!;
          const firstInput = firstEntry(firstManifest.inputs)!;
          const lastOutput = firstEntry(lastManifest.outputs)!;

          return {
            version: 1,
            nodes,
            connections,
            inputs: {
              image: { node_id: stack[0].id, port: firstInput[0] },
            },
            outputs: {
              result: { node_id: stack[stack.length - 1].id, port: lastOutput[0] },
            },
          };
        };

        export const viewerSourcesForStack = (
          stack: StackOperatorInstance[],
          manifests: Map<string, OperatorManifest>,
        ): ViewerSource[] => {
          const sources: ViewerSource[] = [
            { key: 'source:image', label: 'Original', kind: 'source', sourceName: 'image', dataType: 'image' },
          ];

          stack.forEach((instance, index) => {
            const manifest = manifests.get(instance.operatorId);
            const output = manifest ? firstEntry(manifest.outputs) : null;
            if (!manifest || !output) return;
            sources.push({
              key: `node:${instance.id}:${output[0]}`,
              label: `${index + 1}. ${manifest.label}`,
              kind: 'node',
              nodeId: instance.id,
              port: output[0],
              dataType: output[1].type,
            });
          });
          return sources;
        };
    '''),

    "components/VisionLabs/ImageProcessing/OperatorLibrary.tsx": dedent(r'''
        import { useMemo, useState } from 'react';
        import { ChevronDown, ChevronRight, Search, Plus, LockKeyhole } from 'lucide-react';
        import type { OperatorManifest } from './types';

        interface Props {
          operators: OperatorManifest[];
          onAdd: (operator: OperatorManifest) => void;
          canAppend: (operator: OperatorManifest) => { ok: boolean; reason?: string };
        }

        export const OperatorLibrary = ({ operators, onAdd, canAppend }: Props) => {
          const [query, setQuery] = useState('');
          const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({});

          const grouped = useMemo(() => {
            const result = new Map<string, OperatorManifest[]>();
            operators
              .filter((operator) => {
                const haystack = `${operator.label} ${operator.category} ${operator.description ?? ''}`.toLowerCase();
                return haystack.includes(query.trim().toLowerCase());
              })
              .forEach((operator) => {
                const category = operator.category || 'Other';
                const items = result.get(category) ?? [];
                items.push(operator);
                result.set(category, items);
              });
            return Array.from(result.entries()).sort(([a], [b]) => a.localeCompare(b));
          }, [operators, query]);

          return (
            <aside className="w-[270px] min-w-[240px] border-r border-slate-800 bg-slate-950/80 flex flex-col overflow-hidden">
              <div className="p-3 border-b border-slate-800">
                <div className="text-[11px] font-black tracking-[0.22em] text-cyan-400 uppercase mb-2">Operator Library</div>
                <div className="relative">
                  <Search size={14} className="absolute left-2.5 top-2.5 text-slate-500" />
                  <input
                    value={query}
                    onChange={(event: any) => setQuery(event.target.value)}
                    placeholder="Search algorithms..."
                    className="w-full rounded-lg border border-slate-700 bg-slate-900/80 pl-8 pr-2 py-2 text-xs text-slate-100 outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {grouped.map(([category, items]) => {
                  const isOpen = openCategories[category] ?? true;
                  return (
                    <div key={category} className="rounded-lg border border-slate-800/80 overflow-hidden bg-slate-900/30">
                      <button
                        onClick={() => setOpenCategories((current) => ({ ...current, [category]: !isOpen }))}
                        className="w-full flex items-center justify-between px-3 py-2 text-left text-xs font-bold text-slate-200 hover:bg-slate-800/70"
                      >
                        <span className="flex items-center gap-2">
                          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                          {category}
                        </span>
                        <span className="text-[10px] text-slate-500">{items.length}</span>
                      </button>

                      {isOpen && (
                        <div className="border-t border-slate-800">
                          {items.map((operator) => {
                            const compatibility = canAppend(operator);
                            return (
                              <button
                                key={operator.id}
                                onClick={() => compatibility.ok && onAdd(operator)}
                                title={compatibility.ok ? operator.description : compatibility.reason}
                                className={`w-full px-3 py-2.5 flex items-start gap-2 text-left border-b last:border-b-0 border-slate-800/60 transition-colors ${
                                  compatibility.ok
                                    ? 'hover:bg-cyan-500/10 text-slate-200'
                                    : 'opacity-45 cursor-not-allowed text-slate-500'
                                }`}
                              >
                                <span className={`mt-0.5 flex items-center justify-center w-6 h-6 rounded-md ${compatibility.ok ? 'bg-cyan-500/10 text-cyan-400' : 'bg-slate-800 text-slate-600'}`}>
                                  {compatibility.ok ? <Plus size={13} /> : <LockKeyhole size={12} />}
                                </span>
                                <span className="min-w-0 flex-1">
                                  <span className="block text-xs font-semibold truncate">{operator.label}</span>
                                  <span className="block text-[10px] text-slate-500 mt-0.5 line-clamp-2">
                                    {compatibility.ok ? operator.description : compatibility.reason}
                                  </span>
                                </span>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </aside>
          );
        };
    '''),

    "components/VisionLabs/ImageProcessing/ProcessingStack.tsx": dedent(r'''
        import { useState } from 'react';
        import {
          ChevronDown,
          ChevronRight,
          GripVertical,
          Trash2,
          RotateCcw,
          Eye,
          EyeOff,
        } from 'lucide-react';
        import type { OperatorManifest, ParameterManifest, StackOperatorInstance } from './types';

        interface Props {
          stack: StackOperatorInstance[];
          manifests: Map<string, OperatorManifest>;
          onToggleExpanded: (id: string) => void;
          onDelete: (id: string) => void;
          onToggleEnabled: (id: string) => void;
          onReset: (id: string) => void;
          onReorder: (fromIndex: number, toIndex: number) => void;
          onParameterChange: (id: string, key: string, value: any, commit?: boolean) => void;
        }

        const NumericEditor = ({
          spec,
          value,
          onChange,
          onCommit,
        }: {
          spec: ParameterManifest;
          value: number;
          onChange: (value: number) => void;
          onCommit: (value: number) => void;
        }) => {
          const min = spec.min ?? (spec.type === 'integer' ? 0 : 0);
          const max = spec.max ?? (spec.type === 'integer' ? 255 : 10);
          const step = spec.odd ? 2 : spec.type === 'integer' ? 1 : Math.max((max - min) / 200, 0.01);
          const normalized = Number.isFinite(Number(value)) ? Number(value) : Number(spec.default ?? min);
          return (
            <div className="grid grid-cols-[1fr_72px] gap-2 items-center">
              <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={normalized}
                onChange={(event: any) => onChange(Number(event.target.value))}
                onPointerUp={() => onCommit(normalized)}
                className="w-full accent-cyan-500"
              />
              <input
                type="number"
                min={min}
                max={max}
                step={step}
                value={normalized}
                onChange={(event: any) => onChange(Number(event.target.value))}
                onBlur={(event: any) => onCommit(Number(event.currentTarget.value))}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100 outline-none focus:border-cyan-500"
              />
            </div>
          );
        };

        const ParameterEditor = ({
          name,
          spec,
          value,
          onChange,
          onCommit,
        }: {
          name: string;
          spec: ParameterManifest;
          value: any;
          onChange: (value: any) => void;
          onCommit: (value: any) => void;
        }) => {
          const label = spec.label || name.replaceAll('_', ' ');
          return (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</label>
                {spec.description && <span className="text-[9px] text-slate-600 truncate">{spec.description}</span>}
              </div>

              {(spec.type === 'integer' || spec.type === 'float') && (
                <NumericEditor spec={spec} value={value} onChange={onChange} onCommit={onCommit} />
              )}

              {spec.type === 'boolean' && (
                <button
                  onClick={() => { const next = !Boolean(value); onChange(next); window.setTimeout(() => onCommit(next), 0); }}
                  className={`w-full rounded-md border px-2 py-1.5 text-xs font-bold ${
                    value
                      ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-300'
                      : 'border-slate-700 bg-slate-950 text-slate-400'
                  }`}
                >
                  {value ? 'Enabled' : 'Disabled'}
                </button>
              )}

              {spec.type === 'enum' && (
                <select
                  value={value ?? spec.default ?? ''}
                  onChange={(event: any) => { const next = event.target.value; onChange(next); window.setTimeout(() => onCommit(next), 0); }}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-100 outline-none focus:border-cyan-500"
                >
                  {(spec.choices ?? []).map((choice) => (
                    <option key={String(choice)} value={choice}>{String(choice)}</option>
                  ))}
                </select>
              )}

              {spec.type === 'string' && (
                <input
                  value={value ?? ''}
                  onChange={(event: any) => onChange(event.target.value)}
                  onBlur={(event: any) => onCommit(event.currentTarget.value)}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-100 outline-none focus:border-cyan-500"
                />
              )}
            </div>
          );
        };

        export const ProcessingStack = ({
          stack,
          manifests,
          onToggleExpanded,
          onDelete,
          onToggleEnabled,
          onReset,
          onReorder,
          onParameterChange,
        }: Props) => {
          const [dragIndex, setDragIndex] = useState<number | null>(null);

          return (
            <aside className="w-[350px] min-w-[310px] border-l border-slate-800 bg-slate-950/80 flex flex-col overflow-hidden">
              <div className="p-3 border-b border-slate-800">
                <div className="text-[11px] font-black tracking-[0.22em] text-fuchsia-400 uppercase">Processing Stack</div>
                <p className="mt-1 text-[10px] text-slate-500">Drag rows to reorder. Expand a row to tune its parameters.</p>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {stack.length === 0 && (
                  <div className="rounded-xl border border-dashed border-slate-700 p-5 text-center text-xs text-slate-500">
                    Select an algorithm from the Operator Library to begin.
                  </div>
                )}

                {stack.map((instance, index) => {
                  const manifest = manifests.get(instance.operatorId);
                  if (!manifest) return null;
                  const inputTypes = Object.values(manifest.inputs ?? {}).map((port) => port.type);
                  const outputTypes = Object.values(manifest.outputs ?? {}).map((port) => port.type);
                  const canBypass = inputTypes.length === 1 && outputTypes.length === 1 && inputTypes[0] === outputTypes[0];
                  return (
                    <div
                      key={instance.id}
                      draggable
                      onDragStart={() => setDragIndex(index)}
                      onDragOver={(event: any) => event.preventDefault()}
                      onDrop={() => {
                        if (dragIndex !== null && dragIndex !== index) onReorder(dragIndex, index);
                        setDragIndex(null);
                      }}
                      className={`rounded-xl border overflow-hidden transition-colors ${
                        instance.enabled
                          ? 'border-slate-700 bg-slate-900/70'
                          : 'border-slate-800 bg-slate-950/70 opacity-60'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 px-2 py-2">
                        <GripVertical size={14} className="text-slate-600 cursor-grab" />
                        <span className="w-6 h-6 rounded-md bg-slate-800 flex items-center justify-center text-[10px] font-black text-slate-400">{index + 1}</span>
                        <button
                          onClick={() => onToggleExpanded(instance.id)}
                          className="min-w-0 flex-1 flex items-center gap-1.5 text-left"
                        >
                          {instance.expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                          <span className="truncate text-xs font-bold text-slate-100">{manifest.label}</span>
                        </button>
                        <button onClick={() => onReset(instance.id)} title="Reset parameters" className="p-1 text-slate-500 hover:text-cyan-300"><RotateCcw size={13} /></button>
                        <button
                          disabled={!canBypass}
                          onClick={() => canBypass && onToggleEnabled(instance.id)}
                          title={canBypass ? 'Enable / bypass' : 'Bypass unavailable when input/output types differ'}
                          className="p-1 text-slate-500 hover:text-amber-300 disabled:opacity-25 disabled:cursor-not-allowed"
                        >
                          {instance.enabled ? <Eye size={13} /> : <EyeOff size={13} />}
                        </button>
                        <button onClick={() => onDelete(instance.id)} title="Delete" className="p-1 text-slate-500 hover:text-rose-400"><Trash2 size={13} /></button>
                      </div>

                      {instance.expanded && (
                        <div className="border-t border-slate-800 px-3 py-3 space-y-3 bg-slate-950/60">
                          {Object.keys(manifest.parameters ?? {}).length === 0 ? (
                            <div className="text-[10px] text-slate-600">No adjustable parameters.</div>
                          ) : (
                            Object.entries(manifest.parameters).map(([name, spec]) => (
                              <ParameterEditor
                                key={name}
                                name={name}
                                spec={spec}
                                value={instance.parameters[name]}
                                onChange={(value) => onParameterChange(instance.id, name, value, false)}
                                onCommit={(value) => onParameterChange(instance.id, name, value, true)}
                              />
                            ))
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </aside>
          );
        };
    '''),

    "components/VisionLabs/ImageProcessing/ImageWorkbench.tsx": dedent(r'''
        import { useRef } from 'react';
        import { ImagePlus, LayoutGrid, Columns2, Square, Play, Loader2 } from 'lucide-react';
        import type { ViewerCount, ViewerSource } from './types';

        interface Props {
          sourceLoaded: boolean;
          imageName?: string;
          viewerCount: ViewerCount;
          viewerKeys: string[];
          sources: ViewerSource[];
          previewUrls: Record<string, string>;
          busy: boolean;
          onUpload: (file: File) => void;
          onViewerCountChange: (count: ViewerCount) => void;
          onViewerSourceChange: (index: number, key: string) => void;
          onRun: () => void;
        }

        const viewGridClass = (count: ViewerCount) => {
          if (count === 1) return 'grid-cols-1 grid-rows-1';
          if (count === 2) return 'grid-cols-2 grid-rows-1';
          return 'grid-cols-2 grid-rows-2';
        };

        export const ImageWorkbench = ({
          sourceLoaded,
          imageName,
          viewerCount,
          viewerKeys,
          sources,
          previewUrls,
          busy,
          onUpload,
          onViewerCountChange,
          onViewerSourceChange,
          onRun,
        }: Props) => {
          const fileRef = useRef<HTMLInputElement | null>(null);

          return (
            <main className="min-w-0 flex-1 flex flex-col bg-slate-950">
              <div className="h-12 border-b border-slate-800 bg-slate-900/70 flex items-center justify-between px-3 gap-3">
                <div className="flex items-center gap-2 min-w-0">
                  <button
                    onClick={() => fileRef.current?.click()}
                    className="flex items-center gap-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-bold text-cyan-300 hover:bg-cyan-500/20"
                  >
                    <ImagePlus size={14} /> Load Image
                  </button>
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(event: any) => {
                      const file = event.target.files?.[0];
                      if (file) onUpload(file);
                      event.currentTarget.value = '';
                    }}
                  />
                  <span className="truncate text-[10px] text-slate-500">{imageName || 'No image loaded'}</span>
                </div>

                <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950 p-1">
                  <button onClick={() => onViewerCountChange(1)} title="1 viewer" className={`p-1.5 rounded ${viewerCount === 1 ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-200'}`}><Square size={14} /></button>
                  <button onClick={() => onViewerCountChange(2)} title="2 viewers" className={`p-1.5 rounded ${viewerCount === 2 ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-200'}`}><Columns2 size={14} /></button>
                  <button onClick={() => onViewerCountChange(4)} title="4 viewers" className={`p-1.5 rounded ${viewerCount === 4 ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-200'}`}><LayoutGrid size={14} /></button>
                </div>

                <button
                  onClick={onRun}
                  disabled={!sourceLoaded || busy}
                  className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-40"
                >
                  {busy ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                  Run
                </button>
              </div>

              <div className={`flex-1 min-h-0 grid ${viewGridClass(viewerCount)} gap-px bg-slate-800 p-px`}>
                {Array.from({ length: viewerCount }).map((_, index) => {
                  const selectedKey = viewerKeys[index] ?? sources[0]?.key ?? 'source:image';
                  const selected = sources.find((source) => source.key === selectedKey) ?? sources[0];
                  const url = selected ? previewUrls[selected.key] : undefined;
                  return (
                    <section key={index} className="relative min-h-0 min-w-0 bg-[#060a12] flex flex-col overflow-hidden">
                      <div className="h-9 border-b border-slate-800 bg-slate-950/90 flex items-center px-2 gap-2">
                        <span className="text-[9px] font-black tracking-widest text-slate-600">VIEW {index + 1}</span>
                        <select
                          value={selectedKey}
                          onChange={(event: any) => onViewerSourceChange(index, event.target.value)}
                          className="min-w-0 flex-1 rounded-md border border-slate-800 bg-slate-900 px-2 py-1 text-[10px] text-slate-300 outline-none focus:border-cyan-500"
                        >
                          {sources.map((source) => (
                            <option key={source.key} value={source.key}>{source.label}</option>
                          ))}
                        </select>
                        {selected?.dataType && <span className="rounded bg-slate-900 px-1.5 py-0.5 text-[9px] text-slate-600">{selected.dataType}</span>}
                      </div>

                      <div className="relative flex-1 min-h-0 flex items-center justify-center overflow-hidden p-2">
                        {url ? (
                          <img
                            src={url}
                            alt={selected?.label ?? 'Image LAB preview'}
                            draggable={false}
                            className="max-w-full max-h-full object-contain select-none shadow-[0_0_30px_rgba(0,0,0,0.35)]"
                          />
                        ) : (
                          <div className="text-center text-slate-600">
                            <ImagePlus size={34} className="mx-auto mb-2 opacity-40" />
                            <div className="text-xs">{sourceLoaded ? 'Preview not generated yet' : 'Load an image to start experimenting'}</div>
                          </div>
                        )}
                      </div>
                    </section>
                  );
                })}
              </div>
            </main>
          );
        };
    '''),

    "components/VisionLabs/ImageProcessing/useImageLabController.ts": dedent(r'''
        import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
        import { ImageLabAPI } from '../../../api/imageLabApi';
        import type {
          OperatorManifest,
          StackOperatorInstance,
          ViewerCount,
          ViewerSource,
        } from './types';
        import {
          buildPipelineDefinition,
          firstEntry,
          operatorDefaults,
          stackCompatibility,
          validateLinearStack,
          viewerSourcesForStack,
        } from './pipelineUtils';

        const makeId = (() => {
          let counter = 0;
          return () => `imgop_${Date.now().toString(36)}_${(counter += 1).toString(36)}`;
        })();

        export const useImageLabController = () => {
          const [operators, setOperators] = useState<OperatorManifest[]>([]);
          const [stack, setStackState] = useState<StackOperatorInstance[]>([]);
          const [sessionId, setSessionId] = useState<string | null>(null);
          const [sourceLoaded, setSourceLoaded] = useState(false);
          const [imageName, setImageName] = useState<string>('');
          const [busy, setBusy] = useState(false);
          const [error, setError] = useState<string>('');
          const [status, setStatus] = useState<string>('Initializing LAB...');
          const [timings, setTimings] = useState<Record<string, number>>({});
          const [viewerCount, setViewerCountState] = useState<ViewerCount>(2);
          const [viewerKeys, setViewerKeys] = useState<string[]>(['source:image', 'source:image', 'source:image', 'source:image']);
          const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});

          const stackRef = useRef(stack);
          const sourceLoadedRef = useRef(sourceLoaded);
          const viewerKeysRef = useRef(viewerKeys);
          const previewUrlsRef = useRef<Record<string, string>>({});
          const websocketRef = useRef<WebSocket | null>(null);
          const pendingPreviewMetaRef = useRef<any>(null);
          const refreshVisiblePreviewsRef = useRef<(skipKey?: string) => Promise<void>>(async () => undefined);
          const clientRevisionRef = useRef(0);
          const debounceRef = useRef<Record<string, number>>({});

          const manifests = useMemo(
            () => new Map(operators.map((operator) => [operator.id, operator])),
            [operators],
          );
          const manifestsRef = useRef(manifests);

          useEffect(() => { stackRef.current = stack; }, [stack]);
          useEffect(() => { sourceLoadedRef.current = sourceLoaded; }, [sourceLoaded]);
          useEffect(() => { viewerKeysRef.current = viewerKeys; }, [viewerKeys]);
          useEffect(() => { manifestsRef.current = manifests; }, [manifests]);

          const setPreviewBlob = useCallback((key: string, blob: Blob) => {
            const nextUrl = URL.createObjectURL(blob);
            const previous = previewUrlsRef.current[key];
            if (previous) URL.revokeObjectURL(previous);
            previewUrlsRef.current = { ...previewUrlsRef.current, [key]: nextUrl };
            setPreviewUrls(previewUrlsRef.current);
          }, []);

          const availableSources: ViewerSource[] = useMemo(
            () => viewerSourcesForStack(stack, manifests),
            [stack, manifests],
          );

          const fetchPreview = useCallback(async (source: ViewerSource) => {
            if (!sessionId || !sourceLoadedRef.current) return;
            const maxWidth = viewerCount === 4 ? 760 : viewerCount === 2 ? 1000 : 1400;
            const blob = source.kind === 'source'
              ? await ImageLabAPI.sourcePreview(sessionId, source.sourceName ?? 'image', maxWidth)
              : await ImageLabAPI.nodePreview(sessionId, source.nodeId!, source.port!, maxWidth);
            setPreviewBlob(source.key, blob);
          }, [sessionId, viewerCount, setPreviewBlob]);

          const refreshVisiblePreviews = useCallback(async (skipKey?: string) => {
            const sourcesNow = viewerSourcesForStack(stackRef.current, manifestsRef.current);
            const uniqueKeys = Array.from(new Set(viewerKeysRef.current.slice(0, viewerCount)));
            await Promise.all(uniqueKeys.map(async (key) => {
              if (key === skipKey) return;
              const source = sourcesNow.find((item) => item.key === key);
              if (!source) return;
              try { await fetchPreview(source); } catch { /* preview may not exist until pipeline ran */ }
            }));
          }, [fetchPreview, viewerCount]);

          useEffect(() => {
            refreshVisiblePreviewsRef.current = refreshVisiblePreviews;
          }, [refreshVisiblePreviews]);

          const connectWebSocket = useCallback((id: string) => {
            websocketRef.current?.close();
            const websocket = new WebSocket(ImageLabAPI.liveUrl(id));
            websocket.binaryType = 'blob';
            websocketRef.current = websocket;

            websocket.onopen = () => setStatus('Realtime channel connected');
            websocket.onclose = () => setStatus('Realtime channel disconnected');
            websocket.onerror = () => setStatus('Realtime channel error');
            websocket.onmessage = async (event: any) => {
              if (typeof event.data === 'string') {
                try {
                  const payload = JSON.parse(event.data);
                  if (payload.type === 'preview') {
                    pendingPreviewMetaRef.current = payload;
                    setTimings(payload.timings_ms ?? {});
                    setStatus(`Preview r${payload.session_revision} · ${payload.executed_nodes?.length ?? 0} executed / ${payload.cached_nodes?.length ?? 0} cached`);
                  } else if (payload.type === 'error') {
                    setError(payload.message || 'Realtime Image LAB error');
                  }
                } catch (parseError) {
                  console.error('[IMAGE LAB] Bad WebSocket JSON', parseError);
                }
                return;
              }

              const meta = pendingPreviewMetaRef.current;
              if (!meta) return;
              pendingPreviewMetaRef.current = null;
              const key = `node:${meta.node_id}:${meta.port}`;
              const blob = event.data instanceof Blob ? event.data : new Blob([event.data], { type: meta.mime || 'image/jpeg' });
              setPreviewBlob(key, blob);
              await refreshVisiblePreviewsRef.current(key);
            };
          }, [setPreviewBlob]);

          useEffect(() => {
            let cancelled = false;
            let createdSession: string | null = null;
            (async () => {
              try {
                const [catalog, session] = await Promise.all([
                  ImageLabAPI.getOperators(),
                  ImageLabAPI.createSession(),
                ]);
                if (cancelled) {
                  await ImageLabAPI.closeSession(session.session_id).catch(() => undefined);
                  return;
                }
                createdSession = session.session_id;
                setOperators(catalog);
                setSessionId(session.session_id);
                setStatus(`LAB session ${session.session_id.slice(-8)} ready`);
                connectWebSocket(session.session_id);
              } catch (cause: any) {
                setError(cause?.response?.data?.detail || cause?.message || 'Failed to initialize Image LAB');
                setStatus('LAB initialization failed');
              }
            })();

            return () => {
              cancelled = true;
              websocketRef.current?.close();
              Object.values(debounceRef.current).forEach((timer) => window.clearTimeout(timer));
              Object.values(previewUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
              if (createdSession) ImageLabAPI.closeSession(createdSession).catch(() => undefined);
            };
          }, [connectWebSocket]);

          const applyStack = useCallback(async (
            nextStack: StackOperatorInstance[],
            options: { run?: boolean; preserveViewerSelection?: boolean } = {},
          ) => {
            const currentManifests = manifestsRef.current;
            const validity = validateLinearStack(nextStack, currentManifests);
            if (!validity.ok) {
              setError(validity.reason || 'Invalid processing stack');
              return false;
            }

            if (!sessionId) {
              setStackState(nextStack);
              return true;
            }

            try {
              setBusy(true);
              setError('');
              if (nextStack.length > 0) {
                const definition = buildPipelineDefinition(nextStack, currentManifests);
                await ImageLabAPI.setPipeline(sessionId, definition);
                if ((options.run ?? true) && sourceLoadedRef.current) {
                  const result = await ImageLabAPI.run(sessionId);
                  setTimings(result.result?.timings_ms ?? {});
                }
              }
              setStackState(nextStack);
              stackRef.current = nextStack;

              const sources = viewerSourcesForStack(nextStack, currentManifests);
              const finalKey = sources[sources.length - 1]?.key ?? 'source:image';
              if (!options.preserveViewerSelection) {
                setViewerKeys((current) => {
                  const next = [...current];
                  next[0] = 'source:image';
                  next[1] = finalKey;
                  viewerKeysRef.current = next;
                  return next;
                });
              }

              if (sourceLoadedRef.current) {
                window.setTimeout(() => refreshVisiblePreviews(), 0);
              }
              return true;
            } catch (cause: any) {
              setError(cause?.response?.data?.detail || cause?.message || 'Failed to update Image LAB pipeline');
              return false;
            } finally {
              setBusy(false);
            }
          }, [sessionId, refreshVisiblePreviews]);

          const uploadImage = useCallback(async (file: File) => {
            if (!sessionId) return;
            try {
              setBusy(true);
              setError('');
              setStatus('Uploading image...');
              await ImageLabAPI.uploadInput(sessionId, file, 'image');
              sourceLoadedRef.current = true;
              setSourceLoaded(true);
              setImageName(file.name);
              const original = await ImageLabAPI.sourcePreview(sessionId, 'image', viewerCount === 4 ? 760 : 1200);
              setPreviewBlob('source:image', original);

              if (stackRef.current.length > 0) {
                const definition = buildPipelineDefinition(stackRef.current, manifestsRef.current);
                await ImageLabAPI.setPipeline(sessionId, definition);
                const result = await ImageLabAPI.run(sessionId);
                setTimings(result.result?.timings_ms ?? {});
                await refreshVisiblePreviews();
              }
              setStatus(`Loaded ${file.name}`);
            } catch (cause: any) {
              setError(cause?.response?.data?.detail || cause?.message || 'Failed to load image');
            } finally {
              setBusy(false);
            }
          }, [sessionId, viewerCount, setPreviewBlob, refreshVisiblePreviews]);

          const addOperator = useCallback(async (operator: OperatorManifest) => {
            const compatibility = stackCompatibility(stackRef.current, operator, manifestsRef.current);
            if (!compatibility.ok) {
              setError(compatibility.reason || `${operator.label} cannot be appended here`);
              return;
            }
            const next = [
              ...stackRef.current,
              {
                id: makeId(),
                operatorId: operator.id,
                parameters: operatorDefaults(operator),
                enabled: true,
                expanded: true,
              },
            ];
            await applyStack(next);
          }, [applyStack]);

          const deleteOperator = useCallback(async (id: string) => {
            const next = stackRef.current.filter((instance) => instance.id !== id);
            await applyStack(next);
          }, [applyStack]);

          const reorderOperator = useCallback(async (fromIndex: number, toIndex: number) => {
            const next = [...stackRef.current];
            const [moved] = next.splice(fromIndex, 1);
            next.splice(toIndex, 0, moved);
            await applyStack(next);
          }, [applyStack]);

          const toggleExpanded = useCallback((id: string) => {
            setStackState((current) => current.map((item) => item.id === id ? { ...item, expanded: !item.expanded } : item));
          }, []);

          const toggleEnabled = useCallback(async (id: string) => {
            const next = stackRef.current.map((item) => item.id === id ? { ...item, enabled: !item.enabled } : item);
            await applyStack(next);
          }, [applyStack]);

          const resetOperator = useCallback(async (id: string) => {
            const next = stackRef.current.map((item) => {
              if (item.id !== id) return item;
              const manifest = manifestsRef.current.get(item.operatorId);
              return manifest ? { ...item, parameters: operatorDefaults(manifest) } : item;
            });
            await applyStack(next);
          }, [applyStack]);

          const sendRealtimeUpdate = useCallback((
            instanceId: string,
            changes: Record<string, any>,
            final: boolean,
          ) => {
            if (!sourceLoadedRef.current || !websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) return;
            const currentStack = stackRef.current;
            if (currentStack.length === 0) return;
            const finalInstance = currentStack[currentStack.length - 1];
            const finalManifest = manifestsRef.current.get(finalInstance.operatorId);
            const finalOutput = finalManifest ? firstEntry(finalManifest.outputs) : null;
            if (!finalOutput) return;

            clientRevisionRef.current += 1;
            websocketRef.current.send(JSON.stringify({
              type: 'parameter_update',
              revision: clientRevisionRef.current,
              node_id: instanceId,
              changes,
              mode: final ? 'final' : 'interactive',
              preview_node: finalInstance.id,
              preview_port: finalOutput[0],
              max_width: viewerCount === 4 ? 760 : viewerCount === 2 ? 1000 : 1400,
              quality: final ? 88 : 78,
            }));
          }, [viewerCount]);

          const changeParameter = useCallback((
            id: string,
            key: string,
            value: any,
            commit = false,
          ) => {
            const next = stackRef.current.map((item) => item.id === id
              ? { ...item, parameters: { ...item.parameters, [key]: value } }
              : item);
            stackRef.current = next;
            setStackState(next);

            const debounceKey = `${id}:${key}`;
            if (debounceRef.current[debounceKey]) window.clearTimeout(debounceRef.current[debounceKey]);
            if (commit) {
              sendRealtimeUpdate(id, { [key]: value }, true);
              return;
            }
            debounceRef.current[debounceKey] = window.setTimeout(() => {
              sendRealtimeUpdate(id, { [key]: value }, false);
            }, 35);
          }, [sendRealtimeUpdate]);

          const setViewerCount = useCallback((count: ViewerCount) => {
            setViewerCountState(count);
            window.setTimeout(() => refreshVisiblePreviews(), 0);
          }, [refreshVisiblePreviews]);

          const setViewerSource = useCallback((index: number, key: string) => {
            setViewerKeys((current) => {
              const next = [...current];
              next[index] = key;
              viewerKeysRef.current = next;
              return next;
            });
            const source = viewerSourcesForStack(stackRef.current, manifestsRef.current).find((item) => item.key === key);
            if (source && sourceLoadedRef.current) fetchPreview(source).catch(() => undefined);
          }, [fetchPreview]);

          const runNow = useCallback(async () => {
            if (!sessionId || !sourceLoadedRef.current || stackRef.current.length === 0) return;
            try {
              setBusy(true);
              setError('');
              const definition = buildPipelineDefinition(stackRef.current, manifestsRef.current);
              await ImageLabAPI.setPipeline(sessionId, definition);
              const result = await ImageLabAPI.run(sessionId);
              setTimings(result.result?.timings_ms ?? {});
              await refreshVisiblePreviews();
              setStatus('Final pipeline run complete');
            } catch (cause: any) {
              setError(cause?.response?.data?.detail || cause?.message || 'Pipeline run failed');
            } finally {
              setBusy(false);
            }
          }, [sessionId, refreshVisiblePreviews]);

          const canAppend = useCallback((operator: OperatorManifest) => {
            return stackCompatibility(stackRef.current, operator, manifestsRef.current);
          }, []);

          return {
            operators,
            manifests,
            stack,
            sessionId,
            sourceLoaded,
            imageName,
            busy,
            error,
            status,
            timings,
            viewerCount,
            viewerKeys,
            previewUrls,
            availableSources,
            setError,
            canAppend,
            addOperator,
            deleteOperator,
            reorderOperator,
            toggleExpanded,
            toggleEnabled,
            resetOperator,
            changeParameter,
            uploadImage,
            setViewerCount,
            setViewerSource,
            runNow,
          };
        };
    '''),

    "Pages/LabView.tsx": dedent(r'''
        import { useNavigate } from 'react-router-dom';
        import {
          ArrowLeft,
          Image as ImageIcon,
          ScanLine,
          Boxes,
          BrainCircuit,
          Scale,
          FlaskConical,
        } from 'lucide-react';

        const labs = [
          {
            id: 'image-processing',
            title: 'Image Processing LAB',
            subtitle: 'Raster transforms, filtering, thresholding and morphology.',
            icon: ImageIcon,
            enabled: true,
            route: '/labs/image-processing',
          },
          { id: 'sampling', title: 'Sampling / Geometry LAB', subtitle: 'Contours, curves, profiles and spatial sampling.', icon: ScanLine, enabled: false },
          { id: 'representation', title: 'Representation LAB', subtitle: 'Vectors, matrices, tensors and feature representations.', icon: Boxes, enabled: false },
          { id: 'ai', title: 'AI LAB', subtitle: 'Model architecture, inference and training experiments.', icon: BrainCircuit, enabled: false },
          { id: 'rule', title: 'Comparison / Rule LAB', subtitle: 'Measurements, comparison, specs and decision primitives.', icon: Scale, enabled: false },
        ];

        export const LabView = () => {
          const navigate = useNavigate();
          return (
            <div className="h-screen w-screen overflow-hidden bg-[#050812] text-slate-100 flex flex-col">
              <header className="h-16 shrink-0 border-b border-slate-800 bg-slate-950/90 flex items-center px-4 gap-3">
                <button onClick={() => navigate('/')} className="w-9 h-9 rounded-lg border border-slate-700 bg-slate-900 flex items-center justify-center text-slate-400 hover:text-white hover:border-cyan-500/50">
                  <ArrowLeft size={17} />
                </button>
                <div className="w-px h-8 bg-slate-800" />
                <FlaskConical size={20} className="text-fuchsia-400" />
                <div>
                  <div className="text-sm font-black tracking-[0.18em]">VISION LABS</div>
                  <div className="text-[10px] text-slate-500">Experimental workhorses for Lambda Vision</div>
                </div>
              </header>

              <main className="flex-1 overflow-y-auto px-8 py-10">
                <div className="max-w-6xl mx-auto">
                  <div className="mb-8">
                    <div className="text-xs font-black tracking-[0.28em] text-fuchsia-400 uppercase">LAB Launcher</div>
                    <h1 className="mt-2 text-3xl font-black text-white">Choose an experimental environment</h1>
                    <p className="mt-2 max-w-2xl text-sm text-slate-500">Each LAB is optimized around its native data and workflow. Pipelines can later be reused inside Vision Stations.</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {labs.map((lab) => {
                      const Icon = lab.icon;
                      return (
                        <button
                          key={lab.id}
                          disabled={!lab.enabled}
                          onClick={() => lab.enabled && lab.route && navigate(lab.route)}
                          className={`group min-h-[190px] rounded-2xl border p-5 text-left transition-all ${
                            lab.enabled
                              ? 'border-fuchsia-500/30 bg-fuchsia-500/[0.06] hover:-translate-y-1 hover:border-fuchsia-400/60 hover:bg-fuchsia-500/[0.10] hover:shadow-[0_0_40px_rgba(217,70,239,0.12)]'
                              : 'border-slate-800 bg-slate-900/30 opacity-55 cursor-not-allowed'
                          }`}
                        >
                          <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${lab.enabled ? 'bg-fuchsia-500/15 text-fuchsia-300' : 'bg-slate-800 text-slate-600'}`}>
                            <Icon size={22} />
                          </div>
                          <div className="mt-5 flex items-center gap-2">
                            <h2 className="font-black text-base text-slate-100">{lab.title}</h2>
                            {!lab.enabled && <span className="rounded bg-slate-800 px-2 py-0.5 text-[9px] font-bold text-slate-500">COMING SOON</span>}
                          </div>
                          <p className="mt-2 text-xs leading-5 text-slate-500">{lab.subtitle}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </main>
            </div>
          );
        };
    '''),

    "Pages/ImageProcessingLabPage.tsx": dedent(r'''
        import { useNavigate } from 'react-router-dom';
        import { ArrowLeft, FlaskConical, Wifi, AlertTriangle, Gauge } from 'lucide-react';
        import { OperatorLibrary } from '../components/VisionLabs/ImageProcessing/OperatorLibrary';
        import { ProcessingStack } from '../components/VisionLabs/ImageProcessing/ProcessingStack';
        import { ImageWorkbench } from '../components/VisionLabs/ImageProcessing/ImageWorkbench';
        import { useImageLabController } from '../components/VisionLabs/ImageProcessing/useImageLabController';

        export const ImageProcessingLabPage = () => {
          const navigate = useNavigate();
          const lab = useImageLabController();

          const totalTiming = Object.values(lab.timings).reduce((sum, value) => sum + Number(value || 0), 0);

          return (
            <div className="h-screen w-screen overflow-hidden bg-[#050812] text-slate-100 flex flex-col">
              <header className="h-14 shrink-0 border-b border-slate-800 bg-slate-950/95 flex items-center px-3 gap-3">
                <button onClick={() => navigate('/labs')} className="w-8 h-8 rounded-lg border border-slate-700 bg-slate-900 flex items-center justify-center text-slate-400 hover:text-white hover:border-cyan-500/50">
                  <ArrowLeft size={16} />
                </button>
                <div className="w-px h-7 bg-slate-800" />
                <FlaskConical size={18} className="text-cyan-400" />
                <div className="min-w-0">
                  <div className="text-xs font-black tracking-[0.16em]">IMAGE PROCESSING LAB</div>
                  <div className="text-[9px] text-slate-500">Interactive raster processing workbench</div>
                </div>

                <div className="ml-auto flex items-center gap-2 text-[10px] text-slate-500">
                  <span className="flex items-center gap-1 rounded-md border border-slate-800 bg-slate-900 px-2 py-1">
                    <Wifi size={11} className={lab.sessionId ? 'text-emerald-400' : 'text-amber-400'} />
                    {lab.status}
                  </span>
                  <span className="flex items-center gap-1 rounded-md border border-slate-800 bg-slate-900 px-2 py-1">
                    <Gauge size={11} className="text-cyan-400" />
                    {totalTiming.toFixed(2)} ms
                  </span>
                </div>
              </header>

              {lab.error && (
                <div className="shrink-0 border-b border-rose-500/30 bg-rose-500/10 px-4 py-2 flex items-center gap-2 text-xs text-rose-300">
                  <AlertTriangle size={14} />
                  <span className="flex-1">{lab.error}</span>
                  <button onClick={() => lab.setError('')} className="text-[10px] font-bold hover:text-white">DISMISS</button>
                </div>
              )}

              <div className="flex-1 min-h-0 flex overflow-hidden">
                <OperatorLibrary operators={lab.operators} onAdd={lab.addOperator} canAppend={lab.canAppend} />
                <ImageWorkbench
                  sourceLoaded={lab.sourceLoaded}
                  imageName={lab.imageName}
                  viewerCount={lab.viewerCount}
                  viewerKeys={lab.viewerKeys}
                  sources={lab.availableSources}
                  previewUrls={lab.previewUrls}
                  busy={lab.busy}
                  onUpload={lab.uploadImage}
                  onViewerCountChange={lab.setViewerCount}
                  onViewerSourceChange={lab.setViewerSource}
                  onRun={lab.runNow}
                />
                <ProcessingStack
                  stack={lab.stack}
                  manifests={lab.manifests}
                  onToggleExpanded={lab.toggleExpanded}
                  onDelete={lab.deleteOperator}
                  onToggleEnabled={lab.toggleEnabled}
                  onReset={lab.resetOperator}
                  onReorder={lab.reorderOperator}
                  onParameterChange={lab.changeParameter}
                />
              </div>
            </div>
          );
        };
    '''),
}


MAIN_MARKER = "navigate('/labs')"
APP_MARKER = 'path="/labs/image-processing"'


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def discover_project(explicit: str | None) -> tuple[Path, Path]:
    if explicit:
        project = Path(explicit).expanduser().resolve()
        candidates = [project / "src", project]
    else:
        cwd = Path.cwd().resolve()
        projects = [cwd, *cwd.parents]
        candidates = []
        for project in projects:
            candidates.extend([project / "src", project])

    for source in candidates:
        if (source / "App.tsx").exists() and (source / "Pages" / "MainScreen.tsx").exists():
            project = source.parent if source.name == "src" else source
            return project, source

    raise SystemExit(
        "[ERROR] Cannot find Lambda Vision frontend root.\n"
        "        Expected src/App.tsx + src/Pages/MainScreen.tsx (or App.tsx + Pages/MainScreen.tsx).\n"
        "        Use --project /path/to/frontend if needed."
    )


def patch_main_screen(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []

    if "FlaskConical" not in text:
        pattern = re.compile(r"import\s*\{([^}]*)\}\s*from\s*['\"]lucide-react['\"];")
        match = pattern.search(text)
        if not match:
            raise RuntimeError("Could not find lucide-react import in Pages/MainScreen.tsx")
        names = [item.strip() for item in match.group(1).split(',') if item.strip()]
        if "FlaskConical" not in names:
            names.append("FlaskConical")
        replacement = "import { " + ", ".join(names) + " } from 'lucide-react';"
        text = text[:match.start()] + replacement + text[match.end():]
        changes.append("add FlaskConical icon import")

    if MAIN_MARKER not in text:
        lines = text.splitlines()
        anchor_index = None
        for i, line in enumerate(lines):
            if "label: 'App Builder'" in line and "navigate('/inspection')" in line:
                anchor_index = i
                break
        if anchor_index is None:
            raise RuntimeError("Could not find App Builder action in Pages/MainScreen.tsx")
        indent = re.match(r"\s*", lines[anchor_index]).group(0)
        lines.insert(
            anchor_index + 1,
            indent + "{ id: 'labs', label: 'LAB', icon: FlaskConical, activeColor: 'purple', onClick: () => navigate('/labs') },",
        )
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        changes.append("add LAB action next to App Builder")

    return text, changes


def patch_app(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []

    if "./Pages/LabView" not in text:
        anchor = "import { DatabasePage } from './Pages/DatabasePage';"
        if anchor not in text:
            raise RuntimeError("Could not find DatabasePage import in App.tsx")
        text = text.replace(
            anchor,
            anchor + "\nimport { LabView } from './Pages/LabView';\nimport { ImageProcessingLabPage } from './Pages/ImageProcessingLabPage';",
            1,
        )
        changes.append("import LAB pages")

    if APP_MARKER not in text:
        anchor = '<Route path="/inspection" element={<InspectionPage />} />'
        if anchor not in text:
            raise RuntimeError("Could not find /inspection route in App.tsx")
        replacement = (
            anchor
            + '\n        <Route path="/labs" element={<LabView />} />'
            + '\n        <Route path="/labs/image-processing" element={<ImageProcessingLabPage />} />'
        )
        text = text.replace(anchor, replacement, 1)
        changes.append("mount /labs and /labs/image-processing")

    return text, changes


def generated_status(path: Path, expected: str) -> str:
    if not path.exists():
        return "CREATE"
    current = path.read_text(encoding="utf-8")
    return "SAME" if sha256_text(current) == sha256_text(expected) else "CONFLICT"


def backup_files(project: Path, files: list[Path]) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project / BACKUP_DIRNAME / f"image_lab_frontend_v001_{stamp}"
    for path in files:
        if not path.exists():
            continue
        try:
            rel = path.relative_to(project)
        except ValueError:
            rel = Path(path.name)
        target = backup_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return backup_root


def scan(project: Path, source: Path) -> int:
    print("=" * 78)
    print("IMAGE PROCESSING LAB FRONTEND V0.1")
    print("=" * 78)
    print(f"Project : {project}")
    print(f"Source  : {source}")
    print("\nGenerated modules:")
    conflicts = 0
    for rel, content in GENERATED.items():
        path = source / rel
        status = generated_status(path, content)
        if status == "CONFLICT":
            conflicts += 1
        print(f"  [{status:<8}] {path.relative_to(project)}")

    main = source / "Pages/MainScreen.tsx"
    app = source / "App.tsx"
    main_text = main.read_text(encoding="utf-8")
    app_text = app.read_text(encoding="utf-8")
    main_patched, main_changes = patch_main_screen(main_text)
    app_patched, app_changes = patch_app(app_text)

    print("\nPatch targets:")
    print(f"  MainScreen.tsx : {'PATCH NEEDED' if main_patched != main_text else 'READY'}")
    for change in main_changes:
        print(f"    - {change}")
    print(f"  App.tsx        : {'PATCH NEEDED' if app_patched != app_text else 'READY'}")
    for change in app_changes:
        print(f"    - {change}")

    print("\nExisting modules intentionally untouched:")
    print("  ProgrammingPage / FlowStore / UI Engine / Sequencer : untouched")
    print("  Fleet / Database / Inspection                        : untouched")

    if conflicts:
        print(f"\n[WARN] {conflicts} generated file(s) already exist with different content.")
        print("       apply will refuse unless --force is used.")
    else:
        print("\nNext:")
        print("  python update_image_processing_lab_frontend_v001.py apply")
    return 1 if conflicts else 0


def apply(project: Path, source: Path, force: bool) -> int:
    conflicts = [source / rel for rel, content in GENERATED.items() if generated_status(source / rel, content) == "CONFLICT"]
    if conflicts and not force:
        print("[ERROR] Refusing to overwrite existing generated LAB files:")
        for path in conflicts:
            print(f"  - {path.relative_to(project)}")
        print("Use --force only after reviewing those files.")
        return 2

    main = source / "Pages/MainScreen.tsx"
    app = source / "App.tsx"
    touched = [main, app, *[source / rel for rel in GENERATED]]
    backup_root = backup_files(project, touched)

    for rel, content in GENERATED.items():
        path = source / rel
        status = generated_status(path, content)
        if status == "SAME":
            print(f"[SAME ] {path.relative_to(project)}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"[WRITE] {path.relative_to(project)}")

    main_text = main.read_text(encoding="utf-8")
    main_patched, main_changes = patch_main_screen(main_text)
    if main_patched != main_text:
        main.write_text(main_patched, encoding="utf-8")
        for change in main_changes:
            print(f"[PATCH] {main.relative_to(project)}: {change}")
    else:
        print(f"[SAME ] {main.relative_to(project)}")

    app_text = app.read_text(encoding="utf-8")
    app_patched, app_changes = patch_app(app_text)
    if app_patched != app_text:
        app.write_text(app_patched, encoding="utf-8")
        for change in app_changes:
            print(f"[PATCH] {app.relative_to(project)}: {change}")
    else:
        print(f"[SAME ] {app.relative_to(project)}")

    print(f"\n[OK] Update applied. Backup: {backup_root}")
    print("\nRun verification:")
    print("  python update_image_processing_lab_frontend_v001.py verify")
    return 0


def verify(project: Path, source: Path, skip_build: bool) -> int:
    print("=" * 78)
    print("VERIFY IMAGE PROCESSING LAB FRONTEND V0.1")
    print("=" * 78)
    errors: list[str] = []

    for rel, expected in GENERATED.items():
        path = source / rel
        if not path.exists():
            errors.append(f"Missing generated file: {path.relative_to(project)}")
        elif sha256_text(path.read_text(encoding="utf-8")) != sha256_text(expected):
            errors.append(f"Generated file differs from updater v0.1: {path.relative_to(project)}")

    main_text = (source / "Pages/MainScreen.tsx").read_text(encoding="utf-8")
    app_text = (source / "App.tsx").read_text(encoding="utf-8")
    if MAIN_MARKER not in main_text or "label: 'LAB'" not in main_text:
        errors.append("MainScreen LAB launcher patch is missing")
    if APP_MARKER not in app_text or 'path="/labs"' not in app_text:
        errors.append("App.tsx LAB routes are missing")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 2

    print("[OK] Generated modules and route patches are present")
    print("[OK] MainScreen LAB launcher is present")
    print("[OK] /labs and /labs/image-processing routes are present")

    if not skip_build:
        package_json = project / "package.json"
        node_modules = project / "node_modules"
        if package_json.exists() and node_modules.exists():
            try:
                package = json.loads(package_json.read_text(encoding="utf-8"))
                scripts = package.get("scripts", {})
                if "build" in scripts:
                    print("\n[BUILD] npm run build")
                    proc = subprocess.run(["npm", "run", "build"], cwd=project, text=True)
                    if proc.returncode != 0:
                        print("[FAIL] Frontend build failed")
                        return proc.returncode
                    print("[OK] Frontend build")
                else:
                    print("[WARN] package.json has no build script; skipped compile check")
            except Exception as exc:
                print(f"[WARN] Could not run frontend build: {exc}")
        else:
            print("[WARN] node_modules/package.json not found; skipped npm build")
    else:
        print("[SKIP] npm build (--skip-build)")

    print("\n[OK] Image Processing LAB Frontend v0.1 verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lambda Vision Image Processing LAB Frontend v0.1 updater")
    parser.add_argument("--project", help="Frontend project root (directory containing src/App.tsx or App.tsx)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan")
    ap = sub.add_parser("apply")
    ap.add_argument("--force", action="store_true", help="Overwrite conflicting generated LAB files")
    vp = sub.add_parser("verify")
    vp.add_argument("--skip-build", action="store_true", help="Do not run npm run build")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project, source = discover_project(args.project)
    if args.command == "scan":
        return scan(project, source)
    if args.command == "apply":
        return apply(project, source, bool(args.force))
    if args.command == "verify":
        return verify(project, source, bool(args.skip_build))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
