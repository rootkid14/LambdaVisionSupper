import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ImageLabAPI } from '../../../api/imageLabApi';
import { LabServiceAPI } from '../../../api/labServiceApi';
import type {
  OperatorManifest,
  StackOperatorInstance,
  ViewerPane,
  ViewerSource,
  ImageLabExecutionMode,
  LabServiceOutputSelection,
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

const makeViewerId = (() => {
  let counter = 0;
  return () => `imgview_${Date.now().toString(36)}_${(counter += 1).toString(36)}`;
})();

const initialViewerPanes = (): ViewerPane[] => [
  { id: makeViewerId(), sourceKey: 'source:image' },
  { id: makeViewerId(), sourceKey: 'latest' },
];

const sanitizeServiceOutputName = (value: string): string => {
  let normalized = value
    .trim()
    .replace(/[^A-Za-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '');

  if (!normalized) normalized = 'output';
  if (!/^[A-Za-z]/.test(normalized)) normalized = `output_${normalized}`;
  return normalized;
};

const defaultServiceOutputName = (label: string): string => {
  return sanitizeServiceOutputName(label.toLowerCase().replace(/\s+/g, '_'));
};

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
  const [viewerPanes, setViewerPanesState] = useState<ViewerPane[]>(initialViewerPanes);
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});

  const [executionMode, setExecutionModeState] = useState<ImageLabExecutionMode>('live');
  const [dirty, setDirty] = useState(false);
  const [serviceMode, setServiceMode] = useState(false);
  const [serviceName, setServiceNameState] = useState('Image Processing Service');
  const [serviceId, setServiceId] = useState<string | null>(null);
  const [serviceVersion, setServiceVersion] = useState<number | null>(null);
  const [serviceOutputs, setServiceOutputs] = useState<LabServiceOutputSelection[]>([]);

  const stackRef = useRef(stack);
  const sourceLoadedRef = useRef(sourceLoaded);
  const viewerPanesRef = useRef(viewerPanes);
  const previewUrlsRef = useRef<Record<string, string>>({});
  const websocketRef = useRef<WebSocket | null>(null);
  const pendingPreviewMetaRef = useRef<any>(null);
  const refreshVisiblePreviewsRef = useRef<(skipKeys?: Set<string>) => Promise<void>>(async () => undefined);
  const clientRevisionRef = useRef(0);
  const debounceRef = useRef<Record<string, number>>({});
  const executionModeRef = useRef<ImageLabExecutionMode>('live');
  const dirtyRef = useRef(false);

  const manifests = useMemo(
    () => new Map(operators.map((operator) => [operator.id, operator])),
    [operators],
  );
  const manifestsRef = useRef(manifests);

  useEffect(() => { stackRef.current = stack; }, [stack]);
  useEffect(() => { sourceLoadedRef.current = sourceLoaded; }, [sourceLoaded]);
  useEffect(() => { viewerPanesRef.current = viewerPanes; }, [viewerPanes]);
  useEffect(() => { manifestsRef.current = manifests; }, [manifests]);
  useEffect(() => { executionModeRef.current = executionMode; }, [executionMode]);
  useEffect(() => { dirtyRef.current = dirty; }, [dirty]);

  const setPreviewBlob = useCallback((key: string, blob: Blob) => {
    const nextUrl = URL.createObjectURL(blob);
    const previous = previewUrlsRef.current[key];
    if (previous) URL.revokeObjectURL(previous);

    previewUrlsRef.current = {
      ...previewUrlsRef.current,
      [key]: nextUrl,
    };
    setPreviewUrls(previewUrlsRef.current);
  }, []);

  const availableSources: ViewerSource[] = useMemo(
    () => viewerSourcesForStack(stack, manifests),
    [stack, manifests],
  );

  const previewWidth = useCallback(() => {
    const count = Math.max(1, viewerPanesRef.current.length);
    if (count <= 1) return 1500;
    if (count <= 2) return 1100;
    if (count <= 4) return 850;
    return 680;
  }, []);

  const fetchPreview = useCallback(async (source: ViewerSource) => {
    if (!sessionId || !sourceLoadedRef.current) return;

    const maxWidth = previewWidth();
    const blob =
      source.kind === 'source' || (source.kind === 'latest' && !source.nodeId)
        ? await ImageLabAPI.sourcePreview(
            sessionId,
            source.sourceName ?? 'image',
            maxWidth,
          )
        : await ImageLabAPI.nodePreview(
            sessionId,
            source.nodeId!,
            source.port!,
            maxWidth,
          );

    setPreviewBlob(source.key, blob);
  }, [sessionId, previewWidth, setPreviewBlob]);

  const refreshVisiblePreviews = useCallback(async (
    skipKeys: Set<string> = new Set(),
  ) => {
    const sourcesNow = viewerSourcesForStack(
      stackRef.current,
      manifestsRef.current,
    );
    const uniqueKeys = Array.from(
      new Set(viewerPanesRef.current.map((pane) => pane.sourceKey)),
    );

    await Promise.all(uniqueKeys.map(async (key) => {
      if (skipKeys.has(key)) return;

      const source = sourcesNow.find((item) => item.key === key)
        ?? sourcesNow.find((item) => item.key === 'latest');

      if (!source) return;

      try {
        await fetchPreview(source);
      } catch {
        // Intermediate preview may not exist until a pipeline run completes.
      }
    }));
  }, [fetchPreview]);

  useEffect(() => {
    refreshVisiblePreviewsRef.current = refreshVisiblePreviews;
  }, [refreshVisiblePreviews]);

  const normalizeViewerPanes = useCallback((
    nextStack: StackOperatorInstance[],
  ) => {
    const sources = viewerSourcesForStack(
      nextStack,
      manifestsRef.current,
    );
    const allowed = new Set(sources.map((source) => source.key));

    const normalized = viewerPanesRef.current.map((pane) => (
      allowed.has(pane.sourceKey)
        ? pane
        : { ...pane, sourceKey: 'latest' }
    ));

    viewerPanesRef.current = normalized;
    setViewerPanesState(normalized);
  }, []);

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
            setStatus(
              `Preview r${payload.session_revision} · `
              + `${payload.executed_nodes?.length ?? 0} executed / `
              + `${payload.cached_nodes?.length ?? 0} cached`,
            );
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

      const nodeKey = `node:${meta.node_id}:${meta.port}`;
      const blob = event.data instanceof Blob
        ? event.data
        : new Blob([event.data], {
            type: meta.mime || 'image/jpeg',
          });

      setPreviewBlob(nodeKey, blob);

      const latest = viewerSourcesForStack(
        stackRef.current,
        manifestsRef.current,
      ).find((source) => source.key === 'latest');

      const latestMatches =
        latest?.nodeId === meta.node_id
        && latest?.port === meta.port;

      const skipKeys = new Set<string>([nodeKey]);

      if (latestMatches) {
        setPreviewBlob('latest', blob);
        skipKeys.add('latest');
      }

      await refreshVisiblePreviewsRef.current(skipKeys);
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
          await ImageLabAPI.closeSession(
            session.session_id,
          ).catch(() => undefined);
          return;
        }

        createdSession = session.session_id;
        setOperators(catalog);
        setSessionId(session.session_id);
        setStatus(`LAB session ${session.session_id.slice(-8)} ready`);
        connectWebSocket(session.session_id);
      } catch (cause: any) {
        setError(
          cause?.response?.data?.detail
          || cause?.message
          || 'Failed to initialize Image LAB',
        );
        setStatus('LAB initialization failed');
      }
    })();

    return () => {
      cancelled = true;
      websocketRef.current?.close();

      Object.values(debounceRef.current).forEach((timer) => {
        window.clearTimeout(timer);
      });

      Object.values(previewUrlsRef.current).forEach((url) => {
        URL.revokeObjectURL(url);
      });

      if (createdSession) {
        ImageLabAPI.closeSession(
          createdSession,
        ).catch(() => undefined);
      }
    };
  }, [connectWebSocket]);

  const applyStack = useCallback(async (
    nextStack: StackOperatorInstance[],
    options: { run?: boolean } = {},
  ) => {
    const currentManifests = manifestsRef.current;
    const validity = validateLinearStack(
      nextStack,
      currentManifests,
    );

    if (!validity.ok) {
      setError(validity.reason || 'Invalid processing stack');
      return false;
    }

    const nodeIds = new Set(nextStack.map((item) => item.id));
    setServiceOutputs((current) => (
      current.filter((output) => nodeIds.has(output.nodeId))
    ));

    if (executionModeRef.current === 'manual') {
      stackRef.current = nextStack;
      setStackState(nextStack);
      normalizeViewerPanes(nextStack);
      dirtyRef.current = true;
      setDirty(true);
      setStatus('Manual mode · changes pending Run');
      return true;
    }

    if (!sessionId) {
      stackRef.current = nextStack;
      setStackState(nextStack);
      normalizeViewerPanes(nextStack);
      return true;
    }

    try {
      setBusy(true);
      setError('');

      if (nextStack.length > 0) {
        const definition = buildPipelineDefinition(
          nextStack,
          currentManifests,
        );

        await ImageLabAPI.setPipeline(
          sessionId,
          definition,
        );

        if ((options.run ?? true) && sourceLoadedRef.current) {
          const result = await ImageLabAPI.run(sessionId);
          setTimings(result.result?.timings_ms ?? {});
        }
      }

      stackRef.current = nextStack;
      setStackState(nextStack);
      normalizeViewerPanes(nextStack);
      dirtyRef.current = false;
      setDirty(false);

      if (sourceLoadedRef.current) {
        await refreshVisiblePreviews();
      }

      return true;
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Failed to update Image LAB pipeline',
      );
      return false;
    } finally {
      setBusy(false);
    }
  }, [
    sessionId,
    normalizeViewerPanes,
    refreshVisiblePreviews,
  ]);

  const uploadImage = useCallback(async (file: File) => {
    if (!sessionId) return;

    try {
      setBusy(true);
      setError('');
      setStatus('Uploading image...');

      await ImageLabAPI.uploadInput(
        sessionId,
        file,
        'image',
      );

      sourceLoadedRef.current = true;
      setSourceLoaded(true);
      setImageName(file.name);

      const original = await ImageLabAPI.sourcePreview(
        sessionId,
        'image',
        previewWidth(),
      );

      setPreviewBlob('source:image', original);

      if (stackRef.current.length > 0) {
        if (executionModeRef.current === 'manual') {
          dirtyRef.current = true;
          setDirty(true);
          setStatus(`Loaded ${file.name} · Manual mode pending Run`);
        } else {
          const definition = buildPipelineDefinition(
            stackRef.current,
            manifestsRef.current,
          );

          await ImageLabAPI.setPipeline(
            sessionId,
            definition,
          );

          const result = await ImageLabAPI.run(sessionId);
          setTimings(result.result?.timings_ms ?? {});
          await refreshVisiblePreviews();
          dirtyRef.current = false;
          setDirty(false);
          setStatus(`Loaded ${file.name}`);
        }
      } else {
        setPreviewBlob('latest', original);
        dirtyRef.current = false;
        setDirty(false);
        setStatus(`Loaded ${file.name}`);
      }
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Failed to load image',
      );
    } finally {
      setBusy(false);
    }
  }, [
    sessionId,
    previewWidth,
    setPreviewBlob,
    refreshVisiblePreviews,
  ]);

  const addOperator = useCallback(async (
    operator: OperatorManifest,
  ) => {
    const compatibility = stackCompatibility(
      stackRef.current,
      operator,
      manifestsRef.current,
    );

    if (!compatibility.ok) {
      setError(
        compatibility.reason
        || `${operator.label} cannot be appended here`,
      );
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
    const next = stackRef.current.filter(
      (instance) => instance.id !== id,
    );
    await applyStack(next);
  }, [applyStack]);

  const reorderOperator = useCallback(async (
    fromIndex: number,
    toIndex: number,
  ) => {
    const next = [...stackRef.current];
    const [moved] = next.splice(fromIndex, 1);
    next.splice(toIndex, 0, moved);
    await applyStack(next);
  }, [applyStack]);

  const toggleExpanded = useCallback((id: string) => {
    setStackState((current) => (
      current.map((item) => (
        item.id === id
          ? { ...item, expanded: !item.expanded }
          : item
      ))
    ));
  }, []);

  const toggleEnabled = useCallback(async (id: string) => {
    const next = stackRef.current.map((item) => (
      item.id === id
        ? { ...item, enabled: !item.enabled }
        : item
    ));
    await applyStack(next);
  }, [applyStack]);

  const resetOperator = useCallback(async (id: string) => {
    const next = stackRef.current.map((item) => {
      if (item.id !== id) return item;

      const manifest = manifestsRef.current.get(item.operatorId);
      return manifest
        ? {
            ...item,
            parameters: operatorDefaults(manifest),
          }
        : item;
    });

    await applyStack(next);
  }, [applyStack]);

  const sendRealtimeUpdate = useCallback((
    instanceId: string,
    changes: Record<string, any>,
    final: boolean,
  ) => {
    if (
      !sourceLoadedRef.current
      || !websocketRef.current
      || websocketRef.current.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    const currentStack = stackRef.current;
    if (currentStack.length === 0) return;

    const finalInstance = currentStack[currentStack.length - 1];
    const finalManifest = manifestsRef.current.get(
      finalInstance.operatorId,
    );
    const finalOutput = finalManifest
      ? firstEntry(finalManifest.outputs)
      : null;

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
      max_width: previewWidth(),
      quality: final ? 88 : 78,
    }));
  }, [previewWidth]);

  const changeParameter = useCallback((
    id: string,
    key: string,
    value: any,
    commit = false,
  ) => {
    const next = stackRef.current.map((item) => (
      item.id === id
        ? {
            ...item,
            parameters: {
              ...item.parameters,
              [key]: value,
            },
          }
        : item
    ));

    stackRef.current = next;
    setStackState(next);

    if (executionModeRef.current === 'manual') {
      dirtyRef.current = true;
      setDirty(true);
      setStatus('Manual mode · parameter changes pending Run');
      return;
    }

    const debounceKey = `${id}:${key}`;

    if (debounceRef.current[debounceKey]) {
      window.clearTimeout(
        debounceRef.current[debounceKey],
      );
    }

    if (commit) {
      sendRealtimeUpdate(
        id,
        { [key]: value },
        true,
      );
      return;
    }

    debounceRef.current[debounceKey] = window.setTimeout(() => {
      sendRealtimeUpdate(
        id,
        { [key]: value },
        false,
      );
    }, 35);
  }, [sendRealtimeUpdate]);

  const setViewerSource = useCallback((
    viewerId: string,
    key: string,
  ) => {
    const next = viewerPanesRef.current.map((pane) => (
      pane.id === viewerId
        ? { ...pane, sourceKey: key }
        : pane
    ));

    viewerPanesRef.current = next;
    setViewerPanesState(next);

    const source = viewerSourcesForStack(
      stackRef.current,
      manifestsRef.current,
    ).find((item) => item.key === key);

    if (source && sourceLoadedRef.current) {
      fetchPreview(source).catch(() => undefined);
    }
  }, [fetchPreview]);

  const addViewer = useCallback(() => {
    const next = [
      ...viewerPanesRef.current,
      {
        id: makeViewerId(),
        sourceKey: 'latest',
      },
    ];

    viewerPanesRef.current = next;
    setViewerPanesState(next);

    if (sourceLoadedRef.current) {
      const latest = viewerSourcesForStack(
        stackRef.current,
        manifestsRef.current,
      ).find((source) => source.key === 'latest');

      if (latest) {
        fetchPreview(latest).catch(() => undefined);
      }
    }
  }, [fetchPreview]);

  const removeViewer = useCallback((viewerId: string) => {
    if (viewerPanesRef.current.length <= 1) return;

    const next = viewerPanesRef.current.filter(
      (pane) => pane.id !== viewerId,
    );

    viewerPanesRef.current = next;
    setViewerPanesState(next);
  }, []);

  const setViewerPreset = useCallback((count: number) => {
    const target = Math.max(
      1,
      Math.floor(count),
    );

    let next = viewerPanesRef.current.slice(
      0,
      target,
    );

    while (next.length < target) {
      next = [
        ...next,
        {
          id: makeViewerId(),
          sourceKey:
            next.length === 0
              ? 'source:image'
              : 'latest',
        },
      ];
    }

    viewerPanesRef.current = next;
    setViewerPanesState(next);

    if (sourceLoadedRef.current) {
      window.setTimeout(() => {
        refreshVisiblePreviews();
      }, 0);
    }
  }, [refreshVisiblePreviews]);

  const runNow = useCallback(async () => {
    if (
      !sessionId
      || !sourceLoadedRef.current
      || stackRef.current.length === 0
    ) {
      return;
    }

    try {
      setBusy(true);
      setError('');

      const definition = buildPipelineDefinition(
        stackRef.current,
        manifestsRef.current,
      );

      await ImageLabAPI.setPipeline(
        sessionId,
        definition,
      );

      const result = await ImageLabAPI.run(sessionId);
      setTimings(result.result?.timings_ms ?? {});
      await refreshVisiblePreviews();
      dirtyRef.current = false;
      setDirty(false);

      setStatus('Final pipeline run complete');
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Pipeline run failed',
      );
    } finally {
      setBusy(false);
    }
  }, [sessionId, refreshVisiblePreviews]);

  const setExecutionMode = useCallback(async (mode: ImageLabExecutionMode) => {
    executionModeRef.current = mode;
    setExecutionModeState(mode);

    if (mode === 'manual') {
      setStatus('Manual execution · pipeline runs only when Run is pressed');
      return;
    }

    if (
      dirtyRef.current
      && sourceLoadedRef.current
      && stackRef.current.length > 0
    ) {
      await runNow();
    } else {
      setStatus('Live execution enabled');
    }
  }, [runNow]);

  const toggleServiceOutput = useCallback((nodeId: string) => {
    const existing = serviceOutputs.find((item) => item.nodeId === nodeId);
    if (existing) {
      setServiceOutputs((current) => current.filter((item) => item.nodeId !== nodeId));
      return;
    }

    const instance = stackRef.current.find((item) => item.id === nodeId);
    if (!instance) return;
    const manifest = manifestsRef.current.get(instance.operatorId);
    const output = manifest ? firstEntry(manifest.outputs) : null;
    if (!manifest || !output) return;

    const usedNames = new Set(serviceOutputs.map((item) => item.name));
    const base = defaultServiceOutputName(manifest.label);
    let candidate = base;
    let suffix = 2;
    while (usedNames.has(candidate)) {
      candidate = `${base}_${suffix}`;
      suffix += 1;
    }

    setServiceOutputs((current) => [
      ...current,
      {
        nodeId,
        port: output[0],
        name: candidate,
        dataType: output[1].type,
      },
    ]);
  }, [serviceOutputs]);

  const renameServiceOutput = useCallback((nodeId: string, value: string) => {
    const normalized = sanitizeServiceOutputName(value);
    setServiceOutputs((current) => (
      current.map((item) => (
        item.nodeId === nodeId
          ? { ...item, name: normalized }
          : item
      ))
    ));
  }, []);

  const setServiceName = useCallback((value: string) => {
    setServiceNameState(value);
    if (serviceVersion !== null) {
      setServiceId(null);
      setServiceVersion(null);
    }
  }, [serviceVersion]);

  const deployService = useCallback(async () => {
    const name = serviceName.trim();
    if (!name) {
      setError('Lab Service name is required');
      return;
    }
    if (stackRef.current.length === 0) {
      setError('Cannot deploy an empty processing stack');
      return;
    }
    if (serviceOutputs.length === 0) {
      setError('Expose at least one stack checkpoint as a Lab Service output');
      return;
    }

    const names = serviceOutputs.map((item) => item.name);
    if (new Set(names).size !== names.length) {
      setError('Lab Service output names must be unique');
      return;
    }

    try {
      setBusy(true);
      setError('');
      const definition = buildPipelineDefinition(
        stackRef.current,
        manifestsRef.current,
      );

      const outputs = Object.fromEntries(
        serviceOutputs.map((item) => [
          item.name,
          {
            node_id: item.nodeId,
            port: item.port,
            label: item.name,
          },
        ]),
      );

      const deployed = await LabServiceAPI.deploy({
        service_id: serviceId,
        name,
        lab_type: 'image_processing',
        pipeline_snapshot: definition,
        outputs,
      });

      setServiceId(deployed.service_id);
      setServiceVersion(deployed.version);
      setServiceNameState(deployed.name);
      setStatus(`Lab Service ${deployed.name} v${deployed.version} deployed`);
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Failed to deploy Lab Service',
      );
    } finally {
      setBusy(false);
    }
  }, [serviceId, serviceName, serviceOutputs]);

  const canAppend = useCallback((
    operator: OperatorManifest,
  ) => {
    return stackCompatibility(
      stackRef.current,
      operator,
      manifestsRef.current,
    );
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
    viewerPanes,
    previewUrls,
    availableSources,
    executionMode,
    dirty,
    serviceMode,
    serviceName,
    serviceId,
    serviceVersion,
    serviceOutputs,
    setError,
    setExecutionMode,
    setServiceMode,
    setServiceName,
    toggleServiceOutput,
    renameServiceOutput,
    deployService,
    canAppend,
    addOperator,
    deleteOperator,
    reorderOperator,
    toggleExpanded,
    toggleEnabled,
    resetOperator,
    changeParameter,
    uploadImage,
    setViewerSource,
    addViewer,
    removeViewer,
    setViewerPreset,
    runNow,
  };
};
