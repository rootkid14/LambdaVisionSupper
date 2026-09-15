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
