import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SamplingGeometryAPI } from '../../../api/samplingGeometryApi';
import { LabServiceAPI, type LabServiceDefinition } from '../../../api/labServiceApi';
import type {
  ExecutionMode,
  InputBindingState,
  SamplingArtifact,
  SamplingOperatorManifest,
  SamplingPipelineDefinition,
  SamplingStackItem,
  SamplingWorkspace,
} from './types';

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

export const buildSamplingPipeline = (
  workspace: SamplingWorkspace,
  stack: SamplingStackItem[],
): SamplingPipelineDefinition => {
  if (!stack.length) {
    return { version: 1, workspace, nodes: [], connections: [], inputs: {}, outputs: {} };
  }

  const nodes = stack.map((item) => ({
    id: item.id,
    operator_id: item.operator.id,
    operator_version: item.operator.version,
    parameters: { ...item.parameters },
    enabled: item.enabled,
  }));

  const connections: SamplingPipelineDefinition['connections'] = [];
  for (let i = 1; i < stack.length; i += 1) {
    const previous = firstEntry(stack[i - 1].operator.outputs);
    const current = firstEntry(stack[i].operator.inputs);
    if (!previous || !current) continue;
    connections.push({
      source: { node_id: stack[i - 1].id, port: previous[0] },
      target: { node_id: stack[i].id, port: current[0] },
    });
  }

  const firstInput = firstEntry(stack[0].operator.inputs);
  const lastOutput = firstEntry(stack[stack.length - 1].operator.outputs);

  return {
    version: 1,
    workspace,
    nodes,
    connections,
    inputs: firstInput ? { input: { node_id: stack[0].id, port: firstInput[0] } } : {},
    outputs: lastOutput ? { result: { node_id: stack[stack.length - 1].id, port: lastOutput[0] } } : {},
  };
};

export const useSamplingGeometryController = () => {
  const [searchParams] = useSearchParams();
  const editServiceId = searchParams.get('editService');

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [allOperators, setAllOperators] = useState<SamplingOperatorManifest[]>([]);
  const [services, setServices] = useState<LabServiceDefinition[]>([]);
  const [workspace, setWorkspace] = useState<SamplingWorkspace>('geometry');
  const [stack, setStack] = useState<SamplingStackItem[]>([]);
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('manual');
  const [inputBinding, setInputBinding] = useState<InputBindingState>({ mode: 'upload', inputType: 'binary_mask', file: null, serviceId: '', serviceOutput: '' });
  const [sourceLoaded, setSourceLoaded] = useState(false);
  const [sourceUrl, setSourceUrl] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<SamplingArtifact | null>(null);
  const [artifactPreviewUrl, setArtifactPreviewUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [timings, setTimings] = useState<Record<string, number>>({});
  const [serviceName, setServiceName] = useState('Sampling Geometry Service');
  const [editingService, setEditingService] = useState<LabServiceDefinition | null>(null);
  const liveTimer = useRef<number | null>(null);

  const revoke = (url: string | null) => { if (url) URL.revokeObjectURL(url); };

  const refreshServices = useCallback(async () => {
    try { setServices(await LabServiceAPI.list()); } catch { /* keep LAB usable */ }
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
        if (!active) { await SamplingGeometryAPI.closeSession(session.session_id).catch(() => undefined); return; }
        created = session.session_id;
        setSessionId(session.session_id);
        setAllOperators(operators);
        await refreshServices();
      } catch (cause: any) {
        setError(cause?.message || 'Failed to initialize Sampling / Geometry LAB');
      }
    })();
    return () => {
      active = false;
      if (liveTimer.current) window.clearTimeout(liveTimer.current);
      if (created) SamplingGeometryAPI.closeSession(created).catch(() => undefined);
      revoke(sourceUrl);
      revoke(artifactPreviewUrl);
    };
  }, []);

  useEffect(() => {
    if (!editServiceId || !allOperators.length) return;
    (async () => {
      try {
        const service = await LabServiceAPI.get(editServiceId);
        if (service.lab_type !== 'sampling_geometry') return;
        const pipeline = service.pipeline_snapshot as SamplingPipelineDefinition;
        const opMap = new Map(allOperators.map((op) => [op.id, op]));
        const rebuilt: SamplingStackItem[] = (pipeline.nodes ?? []).map((node: any) => {
          const operator = opMap.get(node.operator_id);
          if (!operator) throw new Error(`Missing operator manifest: ${node.operator_id}`);
          const exposed = Object.entries(service.outputs).find(([, binding]) => binding.node_id === node.id);
          return { id: node.id, operator, parameters: { ...node.parameters }, enabled: node.enabled !== false, exposedName: exposed?.[0] ?? null };
        });
        setEditingService(service);
        setServiceName(service.name);
        setWorkspace((service.workspace_type as SamplingWorkspace) || pipeline.workspace || 'geometry');
        setStack(rebuilt);
        setSelectedNodeId(rebuilt.at(-1)?.id ?? null);
        setExecutionMode('manual');
        setPending(true);
        setSourceLoaded(false);
        setArtifact(null);
      } catch (cause: any) {
        setError(cause?.message || 'Failed to load deployed Sampling / Geometry service');
      }
    })();
  }, [editServiceId, allOperators.length]);

  const operators = useMemo(() => allOperators.filter((op) => op.workspace === workspace), [allOperators, workspace]);

  const currentInputType = useMemo(() => {
    if (inputBinding.mode === 'lab_service') {
      const service = services.find((item) => item.service_id === inputBinding.serviceId);
      const output = service?.outputs?.[inputBinding.serviceOutput];
      if (output?.type === 'image' || output?.type === 'binary_mask') return output.type;
    }
    return inputBinding.inputType;
  }, [inputBinding, services]);

  const canAppend = useCallback((operator: SamplingOperatorManifest) => {
    const input = firstEntry(operator.inputs);
    if (!input) return { ok: false, reason: 'Operator has no primary input' };
    const requiredType = input[1].type;
    if (!stack.length) return requiredType === currentInputType ? { ok: true } : { ok: false, reason: `Needs ${requiredType}; current source is ${currentInputType}` };
    const previous = firstEntry(stack[stack.length - 1].operator.outputs);
    const available = previous?.[1].type;
    return available === requiredType ? { ok: true } : { ok: false, reason: `Needs ${requiredType}; stack currently outputs ${available}` };
  }, [stack, currentInputType]);

  const fetchArtifactFor = useCallback(async (nodeId: string) => {
    if (!sessionId) return;
    const item = stack.find((entry) => entry.id === nodeId);
    const output = item ? firstEntry(item.operator.outputs) : null;
    if (!output) return;
    const nextArtifact = await SamplingGeometryAPI.artifact(sessionId, nodeId, output[0]);
    setArtifact(nextArtifact);
    setSelectedNodeId(nodeId);
    revoke(artifactPreviewUrl);
    if (['spectrum_2d', 'image', 'binary_mask'].includes((nextArtifact as any).type)) {
      const blob = await SamplingGeometryAPI.artifactPreview(sessionId, nodeId, output[0]);
      setArtifactPreviewUrl(URL.createObjectURL(blob));
    } else {
      setArtifactPreviewUrl(null);
    }
  }, [sessionId, stack, artifactPreviewUrl]);

  const runNow = useCallback(async () => {
    if (!sessionId || !sourceLoaded || !stack.length) return;
    try {
      setBusy(true); setError('');
      const pipeline = buildSamplingPipeline(workspace, stack);
      await SamplingGeometryAPI.setPipeline(sessionId, pipeline);
      const result = await SamplingGeometryAPI.run(sessionId);
      setTimings(result.result?.timings_ms ?? {});
      setPending(false);
      const target = selectedNodeId && stack.some((item) => item.id === selectedNodeId) ? selectedNodeId : stack[stack.length - 1].id;
      await fetchArtifactFor(target);
    } catch (cause: any) {
      setError(cause?.response?.data?.detail || cause?.message || 'Sampling / Geometry run failed');
    } finally { setBusy(false); }
  }, [sessionId, sourceLoaded, stack, workspace, selectedNodeId, fetchArtifactFor]);

  const markChanged = useCallback(() => {
    setPending(true);
  }, []);

  useEffect(() => {
    if (executionMode !== 'live' || !sourceLoaded || !pending || !stack.length) return;
    if (liveTimer.current) window.clearTimeout(liveTimer.current);
    liveTimer.current = window.setTimeout(() => { void runNow(); }, 160);
    return () => {
      if (liveTimer.current) window.clearTimeout(liveTimer.current);
    };
  }, [executionMode, sourceLoaded, pending, stack, runNow]);

  const addOperator = (operator: SamplingOperatorManifest) => {
    if (!canAppend(operator).ok) return;
    const item: SamplingStackItem = { id: makeNodeId(), operator, parameters: defaultsFor(operator), enabled: true, exposedName: null };
    setStack((current) => [...current, item]);
    setSelectedNodeId(item.id);
    setPending(true);
  };

  const updateParameter = (nodeId: string, name: string, value: any) => {
    setStack((current) => current.map((item) => item.id === nodeId ? { ...item, parameters: { ...item.parameters, [name]: value } } : item));
    markChanged();
  };

  const removeOperator = (nodeId: string) => {
    setStack((current) => current.filter((item) => item.id !== nodeId));
    if (selectedNodeId === nodeId) setSelectedNodeId(null);
    setArtifact(null); setPending(true);
  };

  const moveOperator = (nodeId: string, delta: number) => {
    setStack((current) => {
      const index = current.findIndex((item) => item.id === nodeId);
      const target = index + delta;
      if (index < 0 || target < 0 || target >= current.length) return current;
      const next = [...current]; [next[index], next[target]] = [next[target], next[index]]; return next;
    });
    setArtifact(null); setPending(true);
  };

  const toggleExpose = (nodeId: string) => {
    setStack((current) => current.map((item) => item.id === nodeId ? { ...item, exposedName: item.exposedName ? null : safeOutputAlias(item.operator.label, `output_${current.indexOf(item) + 1}`) } : item));
  };

  const setExposeName = (nodeId: string, name: string) => {
    setStack((current) => current.map((item) => item.id === nodeId ? { ...item, exposedName: name.replace(/[^A-Za-z0-9_]/g, '_') } : item));
  };

  const switchWorkspace = (next: SamplingWorkspace) => {
    if (next === workspace) return;
    setWorkspace(next); setStack([]); setArtifact(null); setSelectedNodeId(null); setSourceLoaded(false); revoke(sourceUrl); setSourceUrl(null); setInputBinding({ mode: 'upload', inputType: next === 'geometry' ? 'binary_mask' : 'image', file: null, serviceId: '', serviceOutput: '' }); setEditingService(null); setPending(false);
  };

  const loadSource = async () => {
    if (!sessionId || !inputBinding.file) return;
    try {
      setBusy(true); setError('');
      if (inputBinding.mode === 'upload') {
        await SamplingGeometryAPI.uploadInput(sessionId, inputBinding.file, inputBinding.inputType);
      } else {
        if (!inputBinding.serviceId || !inputBinding.serviceOutput) throw new Error('Select an upstream Lab Service and output');
        await SamplingGeometryAPI.bindFromLabService(sessionId, inputBinding.file, inputBinding.serviceId, inputBinding.serviceOutput, inputBinding.serviceVersion);
      }
      const blob = await SamplingGeometryAPI.sourcePreview(sessionId);
      revoke(sourceUrl); setSourceUrl(URL.createObjectURL(blob)); setSourceLoaded(true); setArtifact(null); setPending(true);
    } catch (cause: any) { setError(cause?.response?.data?.detail || cause?.message || 'Failed to load source'); }
    finally { setBusy(false); }
  };

  const deploy = async (asNew = false) => {
    if (!stack.length) return;
    const outputs: Record<string, { node_id: string; port: string }> = {};
    stack.forEach((item) => {
      if (!item.exposedName) return;
      const output = firstEntry(item.operator.outputs);
      if (output) outputs[item.exposedName] = { node_id: item.id, port: output[0] };
    });
    if (!Object.keys(outputs).length) { setError('Expose at least one stack output before deploying.'); return; }
    try {
      setBusy(true); setError('');
      const service = await LabServiceAPI.deploy({
        service_id: !asNew ? editingService?.service_id : undefined,
        name: serviceName,
        lab_type: 'sampling_geometry',
        workspace_type: workspace,
        pipeline_snapshot: buildSamplingPipeline(workspace, stack),
        outputs,
        description: `Sampling / Geometry · ${workspace}`,
      } as any);
      setEditingService(service);
      await refreshServices();
    } catch (cause: any) { setError(cause?.response?.data?.detail || cause?.message || 'Failed to deploy Sampling / Geometry service'); }
    finally { setBusy(false); }
  };

  const upstreamServices = useMemo(() => services.filter((service) => service.lab_type === 'image_processing' && Object.values(service.outputs).some((output) => ['image', 'binary_mask'].includes(output.type))), [services]);

  return {
    sessionId, workspace, switchWorkspace, operators, stack, executionMode, setExecutionMode,
    inputBinding, setInputBinding, currentInputType, upstreamServices, sourceLoaded, sourceUrl,
    artifact, artifactPreviewUrl, selectedNodeId, fetchArtifactFor, busy, error, setError, pending, timings,
    canAppend, addOperator, updateParameter, removeOperator, moveOperator, toggleExpose, setExposeName,
    loadSource, runNow, serviceName, setServiceName, editingService, deploy,
  };
};
