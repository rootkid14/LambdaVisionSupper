import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SamplingGeometryAPI } from '../../../api/samplingGeometryApi';
import { LabServiceAPI, type LabServiceDefinition } from '../../../api/labServiceApi';
import type {
  ExecutionMode,
  SamplingArtifact,
  SamplingOperatorManifest,
  SamplingPipelineDefinition,
  SamplingStackItem,
  SamplingWorkspace,
  SourceBoardConfig,
  SourceBoardManifest,
  WorkspaceState,
} from './types';

const WORKSPACES: SamplingWorkspace[] = ['geometry', 'spatial', 'spectral'];
const defaultSourceByWorkspace: Record<SamplingWorkspace, string> = {
  geometry: 'master_contours',
  spatial: 'inspected_image',
  spectral: 'inspected_image',
};

const blankPin = () => ({ service_id: '', version: null, output_name: '' });
const defaultSourceBoard = (): SourceBoardConfig => ({
  image_service: blankPin(),
  geometry_service: blankPin(),
  canny_low: 80,
  canny_high: 160,
  blur_kernel: 3,
});

const defaultWorkspaceState = (workspace: SamplingWorkspace): WorkspaceState => ({
  stack: [],
  selectedNodeId: null,
  selectedPort: null,
  sourceName: defaultSourceByWorkspace[workspace],
  timings: {},
  pending: false,
});

const firstEntry = <T,>(record: Record<string, T>): [string, T] | null => {
  const entry = Object.entries(record)[0];
  return entry ? (entry as [string, T]) : null;
};

const defaultsFor = (operator: SamplingOperatorManifest) => Object.fromEntries(
  Object.entries(operator.parameters ?? {}).map(([name, spec]) => [name, spec.default]),
);

const makeNodeId = () => `sgop_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

const safeOutputAlias = (label: string, fallback: string) => {
  const value = label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  return value || fallback;
};

const defaultReferenceSource = (type: string): string => {
  if (type === 'image') return 'inspected_image';
  if (type === 'binary_mask') return 'edge_map';
  if (type === 'contour_set') return 'master_contours';
  return '';
};

export const buildSamplingPipeline = (
  workspace: SamplingWorkspace,
  state: WorkspaceState,
  sourceBoard: SourceBoardConfig,
): SamplingPipelineDefinition => {
  const stack = state.stack;
  if (!stack.length) {
    return {
      version: 2,
      workspace,
      nodes: [],
      connections: [],
      inputs: {},
      outputs: {},
      input_sources: {},
      source_board: sourceBoard,
    };
  }

  const nodes = stack.map((item) => ({
    id: item.id,
    operator_id: item.operator.id,
    operator_version: item.operator.version,
    parameters: { ...item.parameters },
    enabled: item.enabled,
  }));

  const connections: SamplingPipelineDefinition['connections'] = [];
  const inputs: Record<string, any> = {};
  const input_sources: Record<string, string> = {};

  for (let index = 0; index < stack.length; index += 1) {
    const item = stack[index];
    const inputEntries = Object.entries(item.operator.inputs ?? {});
    const primary = inputEntries[0];

    if (primary) {
      const [portName] = primary;
      if (index === 0) {
        const alias = `primary__${item.id}__${portName}`;
        inputs[alias] = { node_id: item.id, port: portName };
        input_sources[alias] = state.sourceName;
      } else {
        const previous = firstEntry(stack[index - 1].operator.outputs);
        if (previous) {
          connections.push({
            source: { node_id: stack[index - 1].id, port: previous[0] },
            target: { node_id: item.id, port: portName },
          });
        }
      }
    }

    for (const [portName, portSpec] of inputEntries.slice(1)) {
      const sourceName = item.referenceBindings[portName] || defaultReferenceSource(portSpec.type);
      if (!sourceName) continue;
      const alias = `ref__${item.id}__${portName}`;
      inputs[alias] = { node_id: item.id, port: portName };
      input_sources[alias] = sourceName;
    }
  }

  const outputs: Record<string, any> = {};
  for (const item of stack) {
    for (const [port, alias] of Object.entries(item.exposedOutputs ?? {})) {
      if (!alias) continue;
      outputs[alias] = { node_id: item.id, port };
    }
  }

  if (!Object.keys(outputs).length) {
    const last = stack[stack.length - 1];
    const primary = firstEntry(last.operator.outputs);
    if (primary) outputs.result = { node_id: last.id, port: primary[0] };
  }

  return {
    version: 2,
    workspace,
    nodes,
    connections,
    inputs,
    outputs,
    input_sources,
    source_board: sourceBoard,
  };
};

export const useSamplingGeometryController = () => {
  const [searchParams] = useSearchParams();
  const editServiceId = searchParams.get('editService');

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [allOperators, setAllOperators] = useState<SamplingOperatorManifest[]>([]);
  const [services, setServices] = useState<LabServiceDefinition[]>([]);
  const [workspace, setWorkspace] = useState<SamplingWorkspace>('geometry');
  const [workspaceStates, setWorkspaceStates] = useState<Record<SamplingWorkspace, WorkspaceState>>({
    geometry: defaultWorkspaceState('geometry'),
    spatial: defaultWorkspaceState('spatial'),
    spectral: defaultWorkspaceState('spectral'),
  });
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('manual');
  const [inputFile, setInputFile] = useState<File | null>(null);
  const [sourceBoardConfig, setSourceBoardConfig] = useState<SourceBoardConfig>(defaultSourceBoard());
  const [sourceBoard, setSourceBoard] = useState<SourceBoardManifest | null>(null);
  const [sourceUrls, setSourceUrls] = useState<Record<string, string>>({});
  const [masterContours, setMasterContours] = useState<SamplingArtifact | null>(null);
  const [artifact, setArtifact] = useState<SamplingArtifact | null>(null);
  const [artifactPreviewUrl, setArtifactPreviewUrl] = useState<string | null>(null);
  const [inspector, setInspector] = useState<{ nodeId: string; port: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [serviceName, setServiceName] = useState('Sampling Geometry Service');
  const [editingService, setEditingService] = useState<LabServiceDefinition | null>(null);
  const liveTimer = useRef<number | null>(null);

  const current = workspaceStates[workspace];
  const stack = current.stack;

  const revokeUrl = (url?: string | null) => { if (url) URL.revokeObjectURL(url); };
  const replaceSourceUrls = (next: Record<string, string>) => {
    setSourceUrls((currentUrls) => {
      Object.values(currentUrls).forEach(revokeUrl);
      return next;
    });
  };

  const refreshServices = useCallback(async () => {
    try { setServices(await LabServiceAPI.list()); } catch { /* editor stays usable */ }
  }, []);

  useEffect(() => {
    let active = true;
    let created: string | null = null;
    (async () => {
      try {
        const [session, operators] = await Promise.all([
          SamplingGeometryAPI.createSession(),
          SamplingGeometryAPI.operators(),
        ]);
        if (!active) {
          await SamplingGeometryAPI.closeSession(session.session_id).catch(() => undefined);
          return;
        }
        created = session.session_id;
        setSessionId(session.session_id);
        setAllOperators(operators.filter((operator) => operator.catalog_visible !== false));
        await refreshServices();
      } catch (cause: any) {
        setError(cause?.message || 'Failed to initialize Sampling / Geometry LAB');
      }
    })();
    return () => {
      active = false;
      if (liveTimer.current) window.clearTimeout(liveTimer.current);
      if (created) SamplingGeometryAPI.closeSession(created).catch(() => undefined);
      Object.values(sourceUrls).forEach(revokeUrl);
      revokeUrl(artifactPreviewUrl);
    };
  }, []);

  useEffect(() => {
    if (!editServiceId || !allOperators.length) return;
    (async () => {
      try {
        const service = await LabServiceAPI.get(editServiceId);
        if (service.lab_type !== 'sampling_geometry') return;
        const pipeline = service.pipeline_snapshot as SamplingPipelineDefinition;
        const targetWorkspace = (service.workspace_type as SamplingWorkspace) || pipeline.workspace || 'geometry';
        const opMap = new Map(allOperators.map((op) => [op.id, op]));
        const rebuilt: SamplingStackItem[] = (pipeline.nodes ?? []).map((node: any) => {
          const operator = opMap.get(node.operator_id);
          if (!operator) throw new Error(`Missing operator manifest: ${node.operator_id}`);
          const exposedOutputs: Record<string, string> = {};
          for (const [alias, binding] of Object.entries(service.outputs ?? {}) as any) {
            if (binding.node_id === node.id) exposedOutputs[binding.port] = alias;
          }
          const referenceBindings: Record<string, string> = {};
          for (const [externalName, endpoint] of Object.entries(pipeline.inputs ?? {}) as any) {
            if (endpoint.node_id !== node.id) continue;
            if (externalName.startsWith('ref__')) {
              referenceBindings[endpoint.port] = pipeline.input_sources?.[externalName] ?? '';
            }
          }
          return {
            id: node.id,
            operator,
            parameters: { ...node.parameters },
            enabled: node.enabled !== false,
            referenceBindings,
            exposedOutputs,
          };
        });
        const firstExternal = Object.entries(pipeline.inputs ?? {}).find(([, endpoint]: any) => endpoint.node_id === rebuilt[0]?.id);
        const restoredSource = firstExternal
          ? pipeline.input_sources?.[firstExternal[0]] ?? defaultSourceByWorkspace[targetWorkspace]
          : defaultSourceByWorkspace[targetWorkspace];
        setEditingService(service);
        setServiceName(service.name);
        setSourceBoardConfig({ ...defaultSourceBoard(), ...(pipeline.source_board as any ?? {}) });
        setWorkspaceStates((states) => ({
          ...states,
          [targetWorkspace]: {
            ...defaultWorkspaceState(targetWorkspace),
            stack: rebuilt,
            sourceName: restoredSource,
            selectedNodeId: rebuilt.at(-1)?.id ?? null,
            selectedPort: rebuilt.length ? firstEntry(rebuilt.at(-1)!.operator.outputs)?.[0] ?? null : null,
            pending: true,
          },
        }));
        setWorkspace(targetWorkspace);
        setExecutionMode('manual');
      } catch (cause: any) {
        setError(cause?.message || 'Failed to load deployed Sampling / Geometry service');
      }
    })();
  }, [editServiceId, allOperators.length]);

  const operators = useMemo(
    () => allOperators.filter((operator) => operator.workspace === workspace),
    [allOperators, workspace],
  );

  const imageServices = useMemo(
    () => services.filter((service) => service.lab_type === 'image_processing' && Object.values(service.inputs).filter((port) => port.type === 'image').length === 1),
    [services],
  );

  const sourceType = useCallback((name: string) => {
    const entry = sourceBoard?.entries?.find((item) => item.name === name);
    if (entry) return entry.type;
    if (name === 'master_contours') return 'contour_set';
    if (name === 'edge_map') return 'binary_mask';
    return 'image';
  }, [sourceBoard]);

  const canAppend = useCallback((operator: SamplingOperatorManifest) => {
    const input = firstEntry(operator.inputs);
    if (!input) return { ok: false, reason: 'Operator has no primary input' };
    const requiredType = input[1].type;
    if (!stack.length) {
      const available = sourceType(current.sourceName);
      return requiredType === available
        ? { ok: true }
        : { ok: false, reason: `Needs ${requiredType}; workspace source is ${available}` };
    }
    const previous = firstEntry(stack[stack.length - 1].operator.outputs);
    const available = previous?.[1].type;
    return available === requiredType
      ? { ok: true }
      : { ok: false, reason: `Needs ${requiredType}; stack currently outputs ${available}` };
  }, [stack, current.sourceName, sourceType]);

  const setWorkspaceState = (target: SamplingWorkspace, updater: (state: WorkspaceState) => WorkspaceState) => {
    setWorkspaceStates((states) => ({ ...states, [target]: updater(states[target]) }));
  };

  const markChanged = () => setWorkspaceState(workspace, (state) => ({ ...state, pending: true }));

  const buildBoard = useCallback(async () => {
    if (!sessionId || !inputFile) return;
    try {
      setBusy(true); setError('');
      const manifest = await SamplingGeometryAPI.buildSourceBoard(sessionId, inputFile, sourceBoardConfig);
      setSourceBoard(manifest);
      const previewNames = ['raw_image', 'inspected_image', 'geometry_raster', 'edge_map', 'contour_image'];
      const nextUrls: Record<string, string> = {};
      for (const name of previewNames) {
        try {
          const blob = await SamplingGeometryAPI.sourcePreview(sessionId, name);
          nextUrls[name] = URL.createObjectURL(blob);
        } catch { /* source may be non-previewable in future */ }
      }
      replaceSourceUrls(nextUrls);
      setMasterContours(await SamplingGeometryAPI.sourceArtifact(sessionId, 'master_contours'));
      setWorkspaceStates((states) => Object.fromEntries(
        WORKSPACES.map((name) => [name, { ...states[name], pending: states[name].stack.length > 0 }]),
      ) as Record<SamplingWorkspace, WorkspaceState>);
      setArtifact(null);
      revokeUrl(artifactPreviewUrl);
      setArtifactPreviewUrl(null);
    } catch (cause: any) {
      setError(cause?.response?.data?.detail || cause?.message || 'Failed to build Source Board');
    } finally { setBusy(false); }
  }, [sessionId, inputFile, sourceBoardConfig, artifactPreviewUrl]);

  const fetchArtifactFor = useCallback(async (nodeId: string, port?: string) => {
    if (!sessionId) return;
    const item = workspaceStates[workspace].stack.find((entry) => entry.id === nodeId);
    const outputPort = port || (item ? firstEntry(item.operator.outputs)?.[0] : null);
    if (!outputPort) return;
    const nextArtifact = await SamplingGeometryAPI.artifact(sessionId, nodeId, outputPort);
    setArtifact(nextArtifact);
    setWorkspaceState(workspace, (state) => ({ ...state, selectedNodeId: nodeId, selectedPort: outputPort }));
    revokeUrl(artifactPreviewUrl);
    if (['spectrum_2d', 'image', 'binary_mask'].includes((nextArtifact as any).type)) {
      const blob = await SamplingGeometryAPI.artifactPreview(sessionId, nodeId, outputPort);
      setArtifactPreviewUrl(URL.createObjectURL(blob));
    } else {
      setArtifactPreviewUrl(null);
    }
  }, [sessionId, workspaceStates, workspace, artifactPreviewUrl]);

  const runNow = useCallback(async () => {
    if (!sessionId || !sourceBoard || !stack.length) return;
    try {
      setBusy(true); setError('');
      const state = workspaceStates[workspace];
      const pipeline = buildSamplingPipeline(workspace, state, sourceBoardConfig);
      await SamplingGeometryAPI.setPipeline(sessionId, pipeline);
      const result = await SamplingGeometryAPI.run(sessionId);
      setWorkspaceState(workspace, (old) => ({ ...old, timings: result.result?.timings_ms ?? {}, pending: false }));
      const targetNode = state.selectedNodeId && stack.some((item) => item.id === state.selectedNodeId)
        ? state.selectedNodeId
        : stack[stack.length - 1].id;
      const targetItem = stack.find((item) => item.id === targetNode)!;
      const targetPort = state.selectedPort && targetItem.operator.outputs[state.selectedPort]
        ? state.selectedPort
        : firstEntry(targetItem.operator.outputs)?.[0];
      if (targetPort) await fetchArtifactFor(targetNode, targetPort);
    } catch (cause: any) {
      setError(cause?.response?.data?.detail || cause?.message || 'Sampling / Geometry run failed');
    } finally { setBusy(false); }
  }, [sessionId, sourceBoard, stack, workspaceStates, workspace, sourceBoardConfig, fetchArtifactFor]);

  useEffect(() => {
    if (executionMode !== 'live' || !sourceBoard || !current.pending || !stack.length) return;
    if (liveTimer.current) window.clearTimeout(liveTimer.current);
    liveTimer.current = window.setTimeout(() => { void runNow(); }, 180);
    return () => { if (liveTimer.current) window.clearTimeout(liveTimer.current); };
  }, [executionMode, sourceBoard, current.pending, stack, runNow]);

  const addOperator = (operator: SamplingOperatorManifest) => {
    if (!canAppend(operator).ok) return;
    const referenceBindings = Object.fromEntries(
      Object.entries(operator.inputs).slice(1).map(([port, spec]) => [port, defaultReferenceSource(spec.type)]),
    );
    const item: SamplingStackItem = {
      id: makeNodeId(), operator, parameters: defaultsFor(operator), enabled: true,
      referenceBindings, exposedOutputs: {},
    };
    setWorkspaceState(workspace, (state) => ({
      ...state,
      stack: [...state.stack, item],
      selectedNodeId: item.id,
      selectedPort: firstEntry(operator.outputs)?.[0] ?? null,
      pending: true,
    }));
  };

  const updateParameter = (id: string, name: string, value: any) => setWorkspaceState(workspace, (state) => ({
    ...state,
    stack: state.stack.map((item) => item.id === id ? { ...item, parameters: { ...item.parameters, [name]: value } } : item),
    pending: true,
  }));

  const updateReferenceBinding = (id: string, port: string, sourceName: string) => setWorkspaceState(workspace, (state) => ({
    ...state,
    stack: state.stack.map((item) => item.id === id ? { ...item, referenceBindings: { ...item.referenceBindings, [port]: sourceName } } : item),
    pending: true,
  }));

  const moveOperator = (id: string, delta: number) => setWorkspaceState(workspace, (state) => {
    const index = state.stack.findIndex((item) => item.id === id);
    const target = index + delta;
    if (index < 0 || target < 0 || target >= state.stack.length) return state;
    const next = [...state.stack];
    [next[index], next[target]] = [next[target], next[index]];
    return { ...state, stack: next, pending: true };
  });

  const removeOperator = (id: string) => setWorkspaceState(workspace, (state) => {
    const next = state.stack.filter((item) => item.id !== id);
    return {
      ...state,
      stack: next,
      selectedNodeId: state.selectedNodeId === id ? next.at(-1)?.id ?? null : state.selectedNodeId,
      selectedPort: state.selectedNodeId === id ? (next.length ? firstEntry(next.at(-1)!.operator.outputs)?.[0] ?? null : null) : state.selectedPort,
      pending: true,
    };
  });

  const toggleExpose = (id: string, port: string) => setWorkspaceState(workspace, (state) => ({
    ...state,
    stack: state.stack.map((item) => {
      if (item.id !== id) return item;
      const next = { ...item.exposedOutputs };
      if (next[port]) delete next[port];
      else next[port] = safeOutputAlias(`${item.operator.label}_${port}`, `${port}_${id.slice(-4)}`);
      return { ...item, exposedOutputs: next };
    }),
  }));

  const setExposeName = (id: string, port: string, name: string) => setWorkspaceState(workspace, (state) => ({
    ...state,
    stack: state.stack.map((item) => item.id === id ? { ...item, exposedOutputs: { ...item.exposedOutputs, [port]: name.replace(/[^A-Za-z0-9_]/g, '_') } } : item),
  }));

  const setWorkspaceSource = (sourceName: string) => setWorkspaceState(workspace, (state) => ({ ...state, sourceName, pending: true }));

  const deploy = async (saveAsNew = false) => {
    const state = workspaceStates[workspace];
    const exposed: Record<string, any> = {};
    const aliases = new Set<string>();
    for (const item of state.stack) {
      for (const [port, alias] of Object.entries(item.exposedOutputs)) {
        if (!alias) continue;
        if (aliases.has(alias)) { setError(`Duplicate service output alias: ${alias}`); return; }
        aliases.add(alias);
        exposed[alias] = { node_id: item.id, port, label: `${item.operator.label} · ${port}` };
      }
    }
    if (!Object.keys(exposed).length) { setError('Expose at least one operator output before deploy.'); return; }
    try {
      setBusy(true); setError('');
      const service = await LabServiceAPI.deploy({
        service_id: saveAsNew ? null : editingService?.service_id ?? null,
        name: serviceName,
        lab_type: 'sampling_geometry',
        workspace_type: workspace,
        pipeline_snapshot: buildSamplingPipeline(workspace, state, sourceBoardConfig),
        outputs: exposed,
        description: `Sampling / Geometry · ${workspace} · Source Board v2`,
      });
      setEditingService(service);
      setServiceName(service.name);
      await refreshServices();
    } catch (cause: any) {
      setError(cause?.response?.data?.detail || cause?.message || 'Deploy failed');
    } finally { setBusy(false); }
  };

  const inspectOutput = async (nodeId: string, port: string) => {
    await fetchArtifactFor(nodeId, port);
    setInspector({ nodeId, port });
  };

  const inspectSource = async (sourceName: string) => {
    if (!sessionId || !sourceBoard) return;
    try {
      const next = await SamplingGeometryAPI.sourceArtifact(sessionId, sourceName);
      setArtifact(next);
      setInspector({ nodeId: `source:${sourceName}`, port: sourceName });
      revokeUrl(artifactPreviewUrl);
      if (['image', 'binary_mask'].includes((next as any).type)) {
        const blob = await SamplingGeometryAPI.sourcePreview(sessionId, sourceName);
        setArtifactPreviewUrl(URL.createObjectURL(blob));
      } else setArtifactPreviewUrl(null);
    } catch (cause: any) {
      setError(cause?.message || 'Failed to inspect source');
    }
  };

  return {
    sessionId, workspace, switchWorkspace: setWorkspace,
    allOperators, operators,
    workspaceStates, current, stack,
    executionMode, setExecutionMode,
    inputFile, setInputFile,
    sourceBoardConfig, setSourceBoardConfig,
    sourceBoard, sourceUrls, masterContours,
    imageServices, services,
    artifact, artifactPreviewUrl,
    inspector, setInspector,
    busy, error, setError,
    serviceName, setServiceName,
    editingService,
    canAppend, buildBoard, runNow, fetchArtifactFor,
    addOperator, updateParameter, updateReferenceBinding,
    moveOperator, removeOperator,
    toggleExpose, setExposeName, setWorkspaceSource,
    deploy, inspectOutput, inspectSource,
    sourceType,
  };
};
