#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "0.2.1"

FE_FILES = {'src/components/VisionLabs/ImageProcessing/types.ts': "export type LabDataType = 'image' | 'binary_mask' | 'roi' | string;\n\nexport interface PortManifest {\n  type: LabDataType;\n  optional?: boolean;\n  label?: string | null;\n}\n\nexport interface ParameterManifest {\n  type: 'integer' | 'float' | 'boolean' | 'enum' | 'string' | string;\n  default?: any;\n  min?: number | null;\n  max?: number | null;\n  choices?: any[] | null;\n  odd?: boolean;\n  ui_hint?: string | null;\n  label?: string | null;\n  description?: string | null;\n}\n\nexport interface OperatorManifest {\n  id: string;\n  version: string;\n  label: string;\n  category: string;\n  description?: string;\n  inputs: Record<string, PortManifest>;\n  outputs: Record<string, PortManifest>;\n  parameters: Record<string, ParameterManifest>;\n}\n\nexport interface StackOperatorInstance {\n  id: string;\n  operatorId: string;\n  parameters: Record<string, any>;\n  enabled: boolean;\n  expanded: boolean;\n}\n\nexport interface PipelineEndpoint {\n  node_id: string;\n  port: string;\n}\n\nexport interface PipelineConnection {\n  source: PipelineEndpoint;\n  target: PipelineEndpoint;\n}\n\nexport interface ImagePipelineDefinition {\n  version: number;\n  nodes: Array<{\n    id: string;\n    operator_id: string;\n    operator_version?: string | null;\n    parameters: Record<string, any>;\n    enabled: boolean;\n  }>;\n  connections: PipelineConnection[];\n  inputs: Record<string, PipelineEndpoint>;\n  outputs: Record<string, PipelineEndpoint>;\n}\n\nexport interface ViewerSource {\n  key: string;\n  label: string;\n  kind: 'source' | 'node' | 'latest';\n  sourceName?: string;\n  nodeId?: string;\n  port?: string;\n  dataType?: string;\n}\n\nexport interface ViewerPane {\n  id: string;\n  sourceKey: string;\n}\n", 'src/components/VisionLabs/ImageProcessing/pipelineUtils.ts': "import type {\n  ImagePipelineDefinition,\n  OperatorManifest,\n  StackOperatorInstance,\n  ViewerSource,\n} from './types';\n\nexport const firstEntry = <T,>(record: Record<string, T>): [string, T] | null => {\n  const entry = Object.entries(record)[0];\n  return entry ? (entry as [string, T]) : null;\n};\n\nexport const operatorDefaults = (manifest: OperatorManifest): Record<string, any> => {\n  const values: Record<string, any> = {};\n  Object.entries(manifest.parameters ?? {}).forEach(([name, spec]) => {\n    values[name] = spec.default;\n  });\n  return values;\n};\n\nexport const isLinearStackOperator = (manifest: OperatorManifest): boolean => {\n  return Object.keys(manifest.inputs ?? {}).length === 1\n    && Object.keys(manifest.outputs ?? {}).length === 1;\n};\n\nexport const stackCompatibility = (\n  stack: StackOperatorInstance[],\n  candidate: OperatorManifest,\n  manifests: Map<string, OperatorManifest>,\n): { ok: boolean; reason?: string } => {\n  if (!isLinearStackOperator(candidate)) {\n    return { ok: false, reason: 'This operator needs advanced/multi-port wiring.' };\n  }\n\n  const candidateInput = firstEntry(candidate.inputs);\n  if (!candidateInput) return { ok: false, reason: 'Operator has no input port.' };\n\n  if (stack.length === 0) {\n    if (candidateInput[1].type !== 'image') {\n      return { ok: false, reason: `Stack input starts as image, not ${candidateInput[1].type}.` };\n    }\n    return { ok: true };\n  }\n\n  const previous = manifests.get(stack[stack.length - 1].operatorId);\n  if (!previous) return { ok: false, reason: 'Previous operator manifest is unavailable.' };\n  const previousOutput = firstEntry(previous.outputs);\n  if (!previousOutput) return { ok: false, reason: 'Previous operator has no output.' };\n\n  if (previousOutput[1].type !== candidateInput[1].type) {\n    return {\n      ok: false,\n      reason: `${previousOutput[1].type} cannot feed ${candidateInput[1].type}.`,\n    };\n  }\n  return { ok: true };\n};\n\nexport const validateLinearStack = (\n  stack: StackOperatorInstance[],\n  manifests: Map<string, OperatorManifest>,\n): { ok: boolean; reason?: string } => {\n  if (stack.length === 0) return { ok: true };\n\n  for (let index = 0; index < stack.length; index += 1) {\n    const manifest = manifests.get(stack[index].operatorId);\n    if (!manifest) return { ok: false, reason: `Unknown operator: ${stack[index].operatorId}` };\n    if (!isLinearStackOperator(manifest)) {\n      return { ok: false, reason: `${manifest.label} requires advanced wiring.` };\n    }\n\n    const input = firstEntry(manifest.inputs);\n    const output = firstEntry(manifest.outputs);\n    if (!input || !output) return { ok: false, reason: `${manifest.label} has invalid ports.` };\n\n    if (index === 0 && input[1].type !== 'image') {\n      return { ok: false, reason: `${manifest.label} cannot consume the source image directly.` };\n    }\n\n    if (index > 0) {\n      const previous = manifests.get(stack[index - 1].operatorId)!;\n      const previousOutput = firstEntry(previous.outputs)!;\n      if (previousOutput[1].type !== input[1].type) {\n        return {\n          ok: false,\n          reason: `${previous.label} (${previousOutput[1].type}) → ${manifest.label} (${input[1].type}) is incompatible.`,\n        };\n      }\n    }\n  }\n\n  return { ok: true };\n};\n\nexport const buildPipelineDefinition = (\n  stack: StackOperatorInstance[],\n  manifests: Map<string, OperatorManifest>,\n): ImagePipelineDefinition => {\n  if (stack.length === 0) {\n    return { version: 1, nodes: [], connections: [], inputs: {}, outputs: {} };\n  }\n\n  const nodes = stack.map((instance) => ({\n    id: instance.id,\n    operator_id: instance.operatorId,\n    operator_version: manifests.get(instance.operatorId)?.version ?? null,\n    parameters: { ...instance.parameters },\n    enabled: instance.enabled,\n  }));\n\n  const connections: ImagePipelineDefinition['connections'] = [];\n  for (let index = 1; index < stack.length; index += 1) {\n    const previousManifest = manifests.get(stack[index - 1].operatorId)!;\n    const currentManifest = manifests.get(stack[index].operatorId)!;\n    const previousOutput = firstEntry(previousManifest.outputs)!;\n    const currentInput = firstEntry(currentManifest.inputs)!;\n\n    connections.push({\n      source: { node_id: stack[index - 1].id, port: previousOutput[0] },\n      target: { node_id: stack[index].id, port: currentInput[0] },\n    });\n  }\n\n  const firstManifest = manifests.get(stack[0].operatorId)!;\n  const lastManifest = manifests.get(stack[stack.length - 1].operatorId)!;\n  const firstInput = firstEntry(firstManifest.inputs)!;\n  const lastOutput = firstEntry(lastManifest.outputs)!;\n\n  return {\n    version: 1,\n    nodes,\n    connections,\n    inputs: {\n      image: { node_id: stack[0].id, port: firstInput[0] },\n    },\n    outputs: {\n      result: { node_id: stack[stack.length - 1].id, port: lastOutput[0] },\n    },\n  };\n};\n\nexport const viewerSourcesForStack = (\n  stack: StackOperatorInstance[],\n  manifests: Map<string, OperatorManifest>,\n): ViewerSource[] => {\n  const original: ViewerSource = {\n    key: 'source:image',\n    label: 'Original',\n    kind: 'source',\n    sourceName: 'image',\n    dataType: 'image',\n  };\n\n  const nodeSources: ViewerSource[] = [];\n\n  stack.forEach((instance, index) => {\n    const manifest = manifests.get(instance.operatorId);\n    const output = manifest ? firstEntry(manifest.outputs) : null;\n    if (!manifest || !output) return;\n\n    nodeSources.push({\n      key: `node:${instance.id}:${output[0]}`,\n      label: `${index + 1}. ${manifest.label}`,\n      kind: 'node',\n      nodeId: instance.id,\n      port: output[0],\n      dataType: output[1].type,\n    });\n  });\n\n  const finalSource = nodeSources[nodeSources.length - 1];\n  const latest: ViewerSource = finalSource\n    ? {\n        ...finalSource,\n        key: 'latest',\n        label: `Latest · ${finalSource.label}`,\n        kind: 'latest',\n      }\n    : {\n        ...original,\n        key: 'latest',\n        label: 'Latest · Original',\n        kind: 'latest',\n      };\n\n  return [latest, original, ...nodeSources];\n};\n", 'src/components/VisionLabs/ImageProcessing/useImageLabController.ts': "import { useCallback, useEffect, useMemo, useRef, useState } from 'react';\nimport { ImageLabAPI } from '../../../api/imageLabApi';\nimport type {\n  OperatorManifest,\n  StackOperatorInstance,\n  ViewerPane,\n  ViewerSource,\n} from './types';\nimport {\n  buildPipelineDefinition,\n  firstEntry,\n  operatorDefaults,\n  stackCompatibility,\n  validateLinearStack,\n  viewerSourcesForStack,\n} from './pipelineUtils';\n\nconst makeId = (() => {\n  let counter = 0;\n  return () => `imgop_${Date.now().toString(36)}_${(counter += 1).toString(36)}`;\n})();\n\nconst makeViewerId = (() => {\n  let counter = 0;\n  return () => `imgview_${Date.now().toString(36)}_${(counter += 1).toString(36)}`;\n})();\n\nconst initialViewerPanes = (): ViewerPane[] => [\n  { id: makeViewerId(), sourceKey: 'source:image' },\n  { id: makeViewerId(), sourceKey: 'latest' },\n];\n\nexport const useImageLabController = () => {\n  const [operators, setOperators] = useState<OperatorManifest[]>([]);\n  const [stack, setStackState] = useState<StackOperatorInstance[]>([]);\n  const [sessionId, setSessionId] = useState<string | null>(null);\n  const [sourceLoaded, setSourceLoaded] = useState(false);\n  const [imageName, setImageName] = useState<string>('');\n  const [busy, setBusy] = useState(false);\n  const [error, setError] = useState<string>('');\n  const [status, setStatus] = useState<string>('Initializing LAB...');\n  const [timings, setTimings] = useState<Record<string, number>>({});\n  const [viewerPanes, setViewerPanesState] = useState<ViewerPane[]>(initialViewerPanes);\n  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});\n\n  const stackRef = useRef(stack);\n  const sourceLoadedRef = useRef(sourceLoaded);\n  const viewerPanesRef = useRef(viewerPanes);\n  const previewUrlsRef = useRef<Record<string, string>>({});\n  const websocketRef = useRef<WebSocket | null>(null);\n  const pendingPreviewMetaRef = useRef<any>(null);\n  const refreshVisiblePreviewsRef = useRef<(skipKeys?: Set<string>) => Promise<void>>(async () => undefined);\n  const clientRevisionRef = useRef(0);\n  const debounceRef = useRef<Record<string, number>>({});\n\n  const manifests = useMemo(\n    () => new Map(operators.map((operator) => [operator.id, operator])),\n    [operators],\n  );\n  const manifestsRef = useRef(manifests);\n\n  useEffect(() => { stackRef.current = stack; }, [stack]);\n  useEffect(() => { sourceLoadedRef.current = sourceLoaded; }, [sourceLoaded]);\n  useEffect(() => { viewerPanesRef.current = viewerPanes; }, [viewerPanes]);\n  useEffect(() => { manifestsRef.current = manifests; }, [manifests]);\n\n  const setPreviewBlob = useCallback((key: string, blob: Blob) => {\n    const nextUrl = URL.createObjectURL(blob);\n    const previous = previewUrlsRef.current[key];\n    if (previous) URL.revokeObjectURL(previous);\n\n    previewUrlsRef.current = {\n      ...previewUrlsRef.current,\n      [key]: nextUrl,\n    };\n    setPreviewUrls(previewUrlsRef.current);\n  }, []);\n\n  const availableSources: ViewerSource[] = useMemo(\n    () => viewerSourcesForStack(stack, manifests),\n    [stack, manifests],\n  );\n\n  const previewWidth = useCallback(() => {\n    const count = Math.max(1, viewerPanesRef.current.length);\n    if (count <= 1) return 1500;\n    if (count <= 2) return 1100;\n    if (count <= 4) return 850;\n    return 680;\n  }, []);\n\n  const fetchPreview = useCallback(async (source: ViewerSource) => {\n    if (!sessionId || !sourceLoadedRef.current) return;\n\n    const maxWidth = previewWidth();\n    const blob =\n      source.kind === 'source' || (source.kind === 'latest' && !source.nodeId)\n        ? await ImageLabAPI.sourcePreview(\n            sessionId,\n            source.sourceName ?? 'image',\n            maxWidth,\n          )\n        : await ImageLabAPI.nodePreview(\n            sessionId,\n            source.nodeId!,\n            source.port!,\n            maxWidth,\n          );\n\n    setPreviewBlob(source.key, blob);\n  }, [sessionId, previewWidth, setPreviewBlob]);\n\n  const refreshVisiblePreviews = useCallback(async (\n    skipKeys: Set<string> = new Set(),\n  ) => {\n    const sourcesNow = viewerSourcesForStack(\n      stackRef.current,\n      manifestsRef.current,\n    );\n    const uniqueKeys = Array.from(\n      new Set(viewerPanesRef.current.map((pane) => pane.sourceKey)),\n    );\n\n    await Promise.all(uniqueKeys.map(async (key) => {\n      if (skipKeys.has(key)) return;\n\n      const source = sourcesNow.find((item) => item.key === key)\n        ?? sourcesNow.find((item) => item.key === 'latest');\n\n      if (!source) return;\n\n      try {\n        await fetchPreview(source);\n      } catch {\n        // Intermediate preview may not exist until a pipeline run completes.\n      }\n    }));\n  }, [fetchPreview]);\n\n  useEffect(() => {\n    refreshVisiblePreviewsRef.current = refreshVisiblePreviews;\n  }, [refreshVisiblePreviews]);\n\n  const normalizeViewerPanes = useCallback((\n    nextStack: StackOperatorInstance[],\n  ) => {\n    const sources = viewerSourcesForStack(\n      nextStack,\n      manifestsRef.current,\n    );\n    const allowed = new Set(sources.map((source) => source.key));\n\n    const normalized = viewerPanesRef.current.map((pane) => (\n      allowed.has(pane.sourceKey)\n        ? pane\n        : { ...pane, sourceKey: 'latest' }\n    ));\n\n    viewerPanesRef.current = normalized;\n    setViewerPanesState(normalized);\n  }, []);\n\n  const connectWebSocket = useCallback((id: string) => {\n    websocketRef.current?.close();\n\n    const websocket = new WebSocket(ImageLabAPI.liveUrl(id));\n    websocket.binaryType = 'blob';\n    websocketRef.current = websocket;\n\n    websocket.onopen = () => setStatus('Realtime channel connected');\n    websocket.onclose = () => setStatus('Realtime channel disconnected');\n    websocket.onerror = () => setStatus('Realtime channel error');\n\n    websocket.onmessage = async (event: any) => {\n      if (typeof event.data === 'string') {\n        try {\n          const payload = JSON.parse(event.data);\n\n          if (payload.type === 'preview') {\n            pendingPreviewMetaRef.current = payload;\n            setTimings(payload.timings_ms ?? {});\n            setStatus(\n              `Preview r${payload.session_revision} · `\n              + `${payload.executed_nodes?.length ?? 0} executed / `\n              + `${payload.cached_nodes?.length ?? 0} cached`,\n            );\n          } else if (payload.type === 'error') {\n            setError(payload.message || 'Realtime Image LAB error');\n          }\n        } catch (parseError) {\n          console.error('[IMAGE LAB] Bad WebSocket JSON', parseError);\n        }\n        return;\n      }\n\n      const meta = pendingPreviewMetaRef.current;\n      if (!meta) return;\n      pendingPreviewMetaRef.current = null;\n\n      const nodeKey = `node:${meta.node_id}:${meta.port}`;\n      const blob = event.data instanceof Blob\n        ? event.data\n        : new Blob([event.data], {\n            type: meta.mime || 'image/jpeg',\n          });\n\n      setPreviewBlob(nodeKey, blob);\n\n      const latest = viewerSourcesForStack(\n        stackRef.current,\n        manifestsRef.current,\n      ).find((source) => source.key === 'latest');\n\n      const latestMatches =\n        latest?.nodeId === meta.node_id\n        && latest?.port === meta.port;\n\n      const skipKeys = new Set<string>([nodeKey]);\n\n      if (latestMatches) {\n        setPreviewBlob('latest', blob);\n        skipKeys.add('latest');\n      }\n\n      await refreshVisiblePreviewsRef.current(skipKeys);\n    };\n  }, [setPreviewBlob]);\n\n  useEffect(() => {\n    let cancelled = false;\n    let createdSession: string | null = null;\n\n    (async () => {\n      try {\n        const [catalog, session] = await Promise.all([\n          ImageLabAPI.getOperators(),\n          ImageLabAPI.createSession(),\n        ]);\n\n        if (cancelled) {\n          await ImageLabAPI.closeSession(\n            session.session_id,\n          ).catch(() => undefined);\n          return;\n        }\n\n        createdSession = session.session_id;\n        setOperators(catalog);\n        setSessionId(session.session_id);\n        setStatus(`LAB session ${session.session_id.slice(-8)} ready`);\n        connectWebSocket(session.session_id);\n      } catch (cause: any) {\n        setError(\n          cause?.response?.data?.detail\n          || cause?.message\n          || 'Failed to initialize Image LAB',\n        );\n        setStatus('LAB initialization failed');\n      }\n    })();\n\n    return () => {\n      cancelled = true;\n      websocketRef.current?.close();\n\n      Object.values(debounceRef.current).forEach((timer) => {\n        window.clearTimeout(timer);\n      });\n\n      Object.values(previewUrlsRef.current).forEach((url) => {\n        URL.revokeObjectURL(url);\n      });\n\n      if (createdSession) {\n        ImageLabAPI.closeSession(\n          createdSession,\n        ).catch(() => undefined);\n      }\n    };\n  }, [connectWebSocket]);\n\n  const applyStack = useCallback(async (\n    nextStack: StackOperatorInstance[],\n    options: { run?: boolean } = {},\n  ) => {\n    const currentManifests = manifestsRef.current;\n    const validity = validateLinearStack(\n      nextStack,\n      currentManifests,\n    );\n\n    if (!validity.ok) {\n      setError(validity.reason || 'Invalid processing stack');\n      return false;\n    }\n\n    if (!sessionId) {\n      stackRef.current = nextStack;\n      setStackState(nextStack);\n      normalizeViewerPanes(nextStack);\n      return true;\n    }\n\n    try {\n      setBusy(true);\n      setError('');\n\n      if (nextStack.length > 0) {\n        const definition = buildPipelineDefinition(\n          nextStack,\n          currentManifests,\n        );\n\n        await ImageLabAPI.setPipeline(\n          sessionId,\n          definition,\n        );\n\n        if ((options.run ?? true) && sourceLoadedRef.current) {\n          const result = await ImageLabAPI.run(sessionId);\n          setTimings(result.result?.timings_ms ?? {});\n        }\n      }\n\n      stackRef.current = nextStack;\n      setStackState(nextStack);\n      normalizeViewerPanes(nextStack);\n\n      if (sourceLoadedRef.current) {\n        await refreshVisiblePreviews();\n      }\n\n      return true;\n    } catch (cause: any) {\n      setError(\n        cause?.response?.data?.detail\n        || cause?.message\n        || 'Failed to update Image LAB pipeline',\n      );\n      return false;\n    } finally {\n      setBusy(false);\n    }\n  }, [\n    sessionId,\n    normalizeViewerPanes,\n    refreshVisiblePreviews,\n  ]);\n\n  const uploadImage = useCallback(async (file: File) => {\n    if (!sessionId) return;\n\n    try {\n      setBusy(true);\n      setError('');\n      setStatus('Uploading image...');\n\n      await ImageLabAPI.uploadInput(\n        sessionId,\n        file,\n        'image',\n      );\n\n      sourceLoadedRef.current = true;\n      setSourceLoaded(true);\n      setImageName(file.name);\n\n      const original = await ImageLabAPI.sourcePreview(\n        sessionId,\n        'image',\n        previewWidth(),\n      );\n\n      setPreviewBlob('source:image', original);\n\n      if (stackRef.current.length > 0) {\n        const definition = buildPipelineDefinition(\n          stackRef.current,\n          manifestsRef.current,\n        );\n\n        await ImageLabAPI.setPipeline(\n          sessionId,\n          definition,\n        );\n\n        const result = await ImageLabAPI.run(sessionId);\n        setTimings(result.result?.timings_ms ?? {});\n        await refreshVisiblePreviews();\n      } else {\n        setPreviewBlob('latest', original);\n      }\n\n      setStatus(`Loaded ${file.name}`);\n    } catch (cause: any) {\n      setError(\n        cause?.response?.data?.detail\n        || cause?.message\n        || 'Failed to load image',\n      );\n    } finally {\n      setBusy(false);\n    }\n  }, [\n    sessionId,\n    previewWidth,\n    setPreviewBlob,\n    refreshVisiblePreviews,\n  ]);\n\n  const addOperator = useCallback(async (\n    operator: OperatorManifest,\n  ) => {\n    const compatibility = stackCompatibility(\n      stackRef.current,\n      operator,\n      manifestsRef.current,\n    );\n\n    if (!compatibility.ok) {\n      setError(\n        compatibility.reason\n        || `${operator.label} cannot be appended here`,\n      );\n      return;\n    }\n\n    const next = [\n      ...stackRef.current,\n      {\n        id: makeId(),\n        operatorId: operator.id,\n        parameters: operatorDefaults(operator),\n        enabled: true,\n        expanded: true,\n      },\n    ];\n\n    await applyStack(next);\n  }, [applyStack]);\n\n  const deleteOperator = useCallback(async (id: string) => {\n    const next = stackRef.current.filter(\n      (instance) => instance.id !== id,\n    );\n    await applyStack(next);\n  }, [applyStack]);\n\n  const reorderOperator = useCallback(async (\n    fromIndex: number,\n    toIndex: number,\n  ) => {\n    const next = [...stackRef.current];\n    const [moved] = next.splice(fromIndex, 1);\n    next.splice(toIndex, 0, moved);\n    await applyStack(next);\n  }, [applyStack]);\n\n  const toggleExpanded = useCallback((id: string) => {\n    setStackState((current) => (\n      current.map((item) => (\n        item.id === id\n          ? { ...item, expanded: !item.expanded }\n          : item\n      ))\n    ));\n  }, []);\n\n  const toggleEnabled = useCallback(async (id: string) => {\n    const next = stackRef.current.map((item) => (\n      item.id === id\n        ? { ...item, enabled: !item.enabled }\n        : item\n    ));\n    await applyStack(next);\n  }, [applyStack]);\n\n  const resetOperator = useCallback(async (id: string) => {\n    const next = stackRef.current.map((item) => {\n      if (item.id !== id) return item;\n\n      const manifest = manifestsRef.current.get(item.operatorId);\n      return manifest\n        ? {\n            ...item,\n            parameters: operatorDefaults(manifest),\n          }\n        : item;\n    });\n\n    await applyStack(next);\n  }, [applyStack]);\n\n  const sendRealtimeUpdate = useCallback((\n    instanceId: string,\n    changes: Record<string, any>,\n    final: boolean,\n  ) => {\n    if (\n      !sourceLoadedRef.current\n      || !websocketRef.current\n      || websocketRef.current.readyState !== WebSocket.OPEN\n    ) {\n      return;\n    }\n\n    const currentStack = stackRef.current;\n    if (currentStack.length === 0) return;\n\n    const finalInstance = currentStack[currentStack.length - 1];\n    const finalManifest = manifestsRef.current.get(\n      finalInstance.operatorId,\n    );\n    const finalOutput = finalManifest\n      ? firstEntry(finalManifest.outputs)\n      : null;\n\n    if (!finalOutput) return;\n\n    clientRevisionRef.current += 1;\n\n    websocketRef.current.send(JSON.stringify({\n      type: 'parameter_update',\n      revision: clientRevisionRef.current,\n      node_id: instanceId,\n      changes,\n      mode: final ? 'final' : 'interactive',\n      preview_node: finalInstance.id,\n      preview_port: finalOutput[0],\n      max_width: previewWidth(),\n      quality: final ? 88 : 78,\n    }));\n  }, [previewWidth]);\n\n  const changeParameter = useCallback((\n    id: string,\n    key: string,\n    value: any,\n    commit = false,\n  ) => {\n    const next = stackRef.current.map((item) => (\n      item.id === id\n        ? {\n            ...item,\n            parameters: {\n              ...item.parameters,\n              [key]: value,\n            },\n          }\n        : item\n    ));\n\n    stackRef.current = next;\n    setStackState(next);\n\n    const debounceKey = `${id}:${key}`;\n\n    if (debounceRef.current[debounceKey]) {\n      window.clearTimeout(\n        debounceRef.current[debounceKey],\n      );\n    }\n\n    if (commit) {\n      sendRealtimeUpdate(\n        id,\n        { [key]: value },\n        true,\n      );\n      return;\n    }\n\n    debounceRef.current[debounceKey] = window.setTimeout(() => {\n      sendRealtimeUpdate(\n        id,\n        { [key]: value },\n        false,\n      );\n    }, 35);\n  }, [sendRealtimeUpdate]);\n\n  const setViewerSource = useCallback((\n    viewerId: string,\n    key: string,\n  ) => {\n    const next = viewerPanesRef.current.map((pane) => (\n      pane.id === viewerId\n        ? { ...pane, sourceKey: key }\n        : pane\n    ));\n\n    viewerPanesRef.current = next;\n    setViewerPanesState(next);\n\n    const source = viewerSourcesForStack(\n      stackRef.current,\n      manifestsRef.current,\n    ).find((item) => item.key === key);\n\n    if (source && sourceLoadedRef.current) {\n      fetchPreview(source).catch(() => undefined);\n    }\n  }, [fetchPreview]);\n\n  const addViewer = useCallback(() => {\n    const next = [\n      ...viewerPanesRef.current,\n      {\n        id: makeViewerId(),\n        sourceKey: 'latest',\n      },\n    ];\n\n    viewerPanesRef.current = next;\n    setViewerPanesState(next);\n\n    if (sourceLoadedRef.current) {\n      const latest = viewerSourcesForStack(\n        stackRef.current,\n        manifestsRef.current,\n      ).find((source) => source.key === 'latest');\n\n      if (latest) {\n        fetchPreview(latest).catch(() => undefined);\n      }\n    }\n  }, [fetchPreview]);\n\n  const removeViewer = useCallback((viewerId: string) => {\n    if (viewerPanesRef.current.length <= 1) return;\n\n    const next = viewerPanesRef.current.filter(\n      (pane) => pane.id !== viewerId,\n    );\n\n    viewerPanesRef.current = next;\n    setViewerPanesState(next);\n  }, []);\n\n  const setViewerPreset = useCallback((count: number) => {\n    const target = Math.max(\n      1,\n      Math.floor(count),\n    );\n\n    let next = viewerPanesRef.current.slice(\n      0,\n      target,\n    );\n\n    while (next.length < target) {\n      next = [\n        ...next,\n        {\n          id: makeViewerId(),\n          sourceKey:\n            next.length === 0\n              ? 'source:image'\n              : 'latest',\n        },\n      ];\n    }\n\n    viewerPanesRef.current = next;\n    setViewerPanesState(next);\n\n    if (sourceLoadedRef.current) {\n      window.setTimeout(() => {\n        refreshVisiblePreviews();\n      }, 0);\n    }\n  }, [refreshVisiblePreviews]);\n\n  const runNow = useCallback(async () => {\n    if (\n      !sessionId\n      || !sourceLoadedRef.current\n      || stackRef.current.length === 0\n    ) {\n      return;\n    }\n\n    try {\n      setBusy(true);\n      setError('');\n\n      const definition = buildPipelineDefinition(\n        stackRef.current,\n        manifestsRef.current,\n      );\n\n      await ImageLabAPI.setPipeline(\n        sessionId,\n        definition,\n      );\n\n      const result = await ImageLabAPI.run(sessionId);\n      setTimings(result.result?.timings_ms ?? {});\n      await refreshVisiblePreviews();\n\n      setStatus('Final pipeline run complete');\n    } catch (cause: any) {\n      setError(\n        cause?.response?.data?.detail\n        || cause?.message\n        || 'Pipeline run failed',\n      );\n    } finally {\n      setBusy(false);\n    }\n  }, [sessionId, refreshVisiblePreviews]);\n\n  const canAppend = useCallback((\n    operator: OperatorManifest,\n  ) => {\n    return stackCompatibility(\n      stackRef.current,\n      operator,\n      manifestsRef.current,\n    );\n  }, []);\n\n  return {\n    operators,\n    manifests,\n    stack,\n    sessionId,\n    sourceLoaded,\n    imageName,\n    busy,\n    error,\n    status,\n    timings,\n    viewerPanes,\n    previewUrls,\n    availableSources,\n    setError,\n    canAppend,\n    addOperator,\n    deleteOperator,\n    reorderOperator,\n    toggleExpanded,\n    toggleEnabled,\n    resetOperator,\n    changeParameter,\n    uploadImage,\n    setViewerSource,\n    addViewer,\n    removeViewer,\n    setViewerPreset,\n    runNow,\n  };\n};\n", 'src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx': 'import { useRef, useState, type CSSProperties } from \'react\';\nimport {\n  Columns2,\n  ImagePlus,\n  LayoutGrid,\n  Loader2,\n  Play,\n  Plus,\n  RotateCcw,\n  Square,\n  X,\n} from \'lucide-react\';\nimport type {\n  ViewerPane,\n  ViewerSource,\n} from \'./types\';\nimport { ZoomPanImageView } from \'./ZoomPanImageView\';\n\ninterface Props {\n  sourceLoaded: boolean;\n  imageName?: string;\n  viewerPanes: ViewerPane[];\n  sources: ViewerSource[];\n  previewUrls: Record<string, string>;\n  busy: boolean;\n  onUpload: (file: File) => void;\n  onViewerSourceChange: (\n    viewerId: string,\n    key: string,\n  ) => void;\n  onAddViewer: () => void;\n  onRemoveViewer: (viewerId: string) => void;\n  onSetViewerPreset: (count: number) => void;\n  onRun: () => void;\n}\n\nconst clamp = (\n  value: number,\n  min: number,\n  max: number,\n) => Math.min(\n  max,\n  Math.max(min, value),\n);\n\nconst defaultPaneStyle = (\n  count: number,\n): CSSProperties => {\n  if (count <= 1) {\n    return {\n      flex: \'1 1 100%\',\n      height: \'100%\',\n    };\n  }\n\n  if (count <= 2) {\n    return {\n      flex: \'1 1 calc(50% - 4px)\',\n      height: \'100%\',\n    };\n  }\n\n  if (count <= 4) {\n    return {\n      flex: \'1 1 calc(50% - 4px)\',\n      height: \'calc(50% - 4px)\',\n    };\n  }\n\n  return {\n    flex: \'1 1 360px\',\n    height: 340,\n  };\n};\n\nconst ResizableViewerPane = ({\n  pane,\n  index,\n  paneCount,\n  sources,\n  previewUrls,\n  sourceLoaded,\n  onSourceChange,\n  onRemove,\n}: {\n  pane: ViewerPane;\n  index: number;\n  paneCount: number;\n  sources: ViewerSource[];\n  previewUrls: Record<string, string>;\n  sourceLoaded: boolean;\n  onSourceChange: (key: string) => void;\n  onRemove: () => void;\n}) => {\n  const paneRef = useRef<HTMLElement | null>(null);\n  const resizeRef = useRef<{\n    pointerId: number;\n    x: number;\n    y: number;\n    width: number;\n    height: number;\n  } | null>(null);\n\n  const [size, setSize] = useState<{\n    width: number;\n    height: number;\n  } | null>(null);\n\n  const selected = sources.find(\n    (source) => source.key === pane.sourceKey,\n  )\n    ?? sources.find(\n      (source) => source.key === \'latest\',\n    )\n    ?? sources[0];\n\n  const url = selected\n    ? previewUrls[selected.key]\n    : undefined;\n\n  return (\n    <section\n      ref={paneRef}\n      className="relative min-h-[220px] min-w-[280px] bg-[#171717] flex flex-col overflow-hidden border border-[#3c4043]"\n      style={\n        size\n          ? {\n              flex: \'0 0 auto\',\n              width: size.width,\n              height: size.height,\n            }\n          : defaultPaneStyle(paneCount)\n      }\n    >\n      <div className="h-9 shrink-0 border-b border-[#3c4043] bg-[#292a2d] flex items-center px-2 gap-2">\n        <span className="text-[9px] font-black tracking-widest text-[#9aa0a6]">\n          VIEW {index + 1}\n        </span>\n\n        <select\n          value={selected?.key ?? \'latest\'}\n          onChange={(event: any) => {\n            onSourceChange(event.target.value);\n          }}\n          className="min-w-0 flex-1 rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[10px] text-[#e8eaed] outline-none focus:border-[#8ab4f8]"\n        >\n          {sources.map((source) => (\n            <option\n              key={source.key}\n              value={source.key}\n            >\n              {source.label}\n            </option>\n          ))}\n        </select>\n\n        {selected?.dataType && (\n          <span className="rounded bg-[#202124] px-1.5 py-0.5 text-[9px] text-[#9aa0a6]">\n            {selected.dataType}\n          </span>\n        )}\n\n        {size && (\n          <button\n            onClick={() => setSize(null)}\n            title="Reset pane size"\n            className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"\n          >\n            <RotateCcw size={12} />\n          </button>\n        )}\n\n        {paneCount > 1 && (\n          <button\n            onClick={onRemove}\n            title="Remove view"\n            className="rounded p-1 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-[#f28b82]"\n          >\n            <X size={13} />\n          </button>\n        )}\n      </div>\n\n      <div className="relative flex-1 min-h-0 overflow-hidden">\n        {url ? (\n          <ZoomPanImageView\n            src={url}\n            alt={\n              selected?.label\n              ?? \'Image LAB preview\'\n            }\n          />\n        ) : (\n          <div className="absolute inset-0 flex items-center justify-center text-center text-[#9aa0a6]">\n            <div>\n              <ImagePlus\n                size={34}\n                className="mx-auto mb-2 opacity-40"\n              />\n              <div className="text-xs">\n                {\n                  sourceLoaded\n                    ? \'Preview not generated yet\'\n                    : \'Load an image to start experimenting\'\n                }\n              </div>\n            </div>\n          </div>\n        )}\n      </div>\n\n      <div\n        role="separator"\n        aria-label="Resize viewer"\n        title="Drag to resize this view"\n        className="absolute bottom-0 right-0 z-30 h-5 w-5 cursor-nwse-resize"\n        onPointerDown={(event) => {\n          event.preventDefault();\n          event.stopPropagation();\n\n          const element = paneRef.current;\n          if (!element) return;\n\n          const rect = element.getBoundingClientRect();\n\n          event.currentTarget.setPointerCapture(\n            event.pointerId,\n          );\n\n          resizeRef.current = {\n            pointerId: event.pointerId,\n            x: event.clientX,\n            y: event.clientY,\n            width: rect.width,\n            height: rect.height,\n          };\n        }}\n        onPointerMove={(event) => {\n          const resize = resizeRef.current;\n\n          if (\n            !resize\n            || resize.pointerId !== event.pointerId\n          ) {\n            return;\n          }\n\n          const maxWidth = Math.max(\n            320,\n            (\n              paneRef.current\n                ?.parentElement\n                ?.clientWidth\n              ?? 1800\n            ) - 8,\n          );\n\n          const maxHeight = Math.max(\n            260,\n            (\n              paneRef.current\n                ?.parentElement\n                ?.clientHeight\n              ?? 1200\n            ) - 8,\n          );\n\n          setSize({\n            width: clamp(\n              resize.width\n                + event.clientX\n                - resize.x,\n              280,\n              maxWidth,\n            ),\n            height: clamp(\n              resize.height\n                + event.clientY\n                - resize.y,\n              220,\n              maxHeight,\n            ),\n          });\n        }}\n        onPointerUp={(event) => {\n          if (\n            resizeRef.current?.pointerId\n            === event.pointerId\n          ) {\n            resizeRef.current = null;\n          }\n        }}\n        onPointerCancel={() => {\n          resizeRef.current = null;\n        }}\n      >\n        <div className="absolute bottom-1 right-1 h-2.5 w-2.5 border-b-2 border-r-2 border-[#9aa0a6]" />\n      </div>\n    </section>\n  );\n};\n\nexport const ImageWorkbench = ({\n  sourceLoaded,\n  imageName,\n  viewerPanes,\n  sources,\n  previewUrls,\n  busy,\n  onUpload,\n  onViewerSourceChange,\n  onAddViewer,\n  onRemoveViewer,\n  onSetViewerPreset,\n  onRun,\n}: Props) => {\n  const fileRef = useRef<HTMLInputElement | null>(null);\n\n  return (\n    <main className="min-w-0 flex-1 flex flex-col bg-[#202124]">\n      <div className="h-12 shrink-0 border-b border-[#3c4043] bg-[#292a2d] flex items-center justify-between px-3 gap-3">\n        <div className="flex items-center gap-2 min-w-0">\n          <button\n            onClick={() => {\n              fileRef.current?.click();\n            }}\n            className="flex items-center gap-2 rounded-md border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-semibold text-[#e8eaed] hover:bg-[#3c4043]"\n          >\n            <ImagePlus\n              size={14}\n              className="text-[#8ab4f8]"\n            />\n            Load Image\n          </button>\n\n          <input\n            ref={fileRef}\n            type="file"\n            accept="image/*"\n            className="hidden"\n            onChange={(event: any) => {\n              const file =\n                event.target.files?.[0];\n\n              if (file) {\n                onUpload(file);\n              }\n\n              event.currentTarget.value = \'\';\n            }}\n          />\n\n          <span className="truncate text-[10px] text-[#9aa0a6]">\n            {\n              imageName\n              || \'No image loaded\'\n            }\n          </span>\n        </div>\n\n        <div className="flex items-center gap-1 rounded-md border border-[#3c4043] bg-[#202124] p-1">\n          <button\n            onClick={() => {\n              onSetViewerPreset(1);\n            }}\n            title="1 view preset"\n            className="p-1.5 rounded text-[#9aa0a6] hover:bg-[#35363a] hover:text-[#8ab4f8]"\n          >\n            <Square size={14} />\n          </button>\n\n          <button\n            onClick={() => {\n              onSetViewerPreset(2);\n            }}\n            title="2 view preset"\n            className="p-1.5 rounded text-[#9aa0a6] hover:bg-[#35363a] hover:text-[#8ab4f8]"\n          >\n            <Columns2 size={14} />\n          </button>\n\n          <button\n            onClick={() => {\n              onSetViewerPreset(4);\n            }}\n            title="4 view preset"\n            className="p-1.5 rounded text-[#9aa0a6] hover:bg-[#35363a] hover:text-[#8ab4f8]"\n          >\n            <LayoutGrid size={14} />\n          </button>\n\n          <div className="mx-0.5 h-4 w-px bg-[#5f6368]" />\n\n          <button\n            onClick={onAddViewer}\n            title="Add another independent viewer"\n            className="flex items-center gap-1 rounded px-2 py-1.5 text-[10px] font-bold text-[#bdc1c6] hover:bg-[#35363a] hover:text-[#8ab4f8]"\n          >\n            <Plus size={13} />\n            View\n          </button>\n\n          <span className="px-1 text-[9px] text-[#80868b]">\n            {viewerPanes.length} open\n          </span>\n        </div>\n\n        <button\n          onClick={onRun}\n          disabled={\n            !sourceLoaded\n            || busy\n          }\n          className="flex items-center gap-2 rounded-md border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-semibold text-[#e8eaed] hover:bg-[#3c4043] disabled:opacity-40"\n        >\n          {\n            busy\n              ? (\n                  <Loader2\n                    size={14}\n                    className="animate-spin text-[#8ab4f8]"\n                  />\n                )\n              : (\n                  <Play\n                    size={14}\n                    className="text-[#8ab4f8]"\n                  />\n                )\n          }\n          Run\n        </button>\n      </div>\n\n      <div className="flex-1 min-h-0 overflow-auto bg-[#171717] p-1">\n        <div className="min-h-full min-w-full flex flex-wrap content-start items-stretch gap-1">\n          {viewerPanes.map((pane, index) => (\n            <ResizableViewerPane\n              key={pane.id}\n              pane={pane}\n              index={index}\n              paneCount={viewerPanes.length}\n              sources={sources}\n              previewUrls={previewUrls}\n              sourceLoaded={sourceLoaded}\n              onSourceChange={(key) => {\n                onViewerSourceChange(\n                  pane.id,\n                  key,\n                );\n              }}\n              onRemove={() => {\n                onRemoveViewer(pane.id);\n              }}\n            />\n          ))}\n        </div>\n      </div>\n    </main>\n  );\n};\n', 'src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx': 'import { useState } from \'react\';\nimport {\n  ChevronDown,\n  ChevronRight,\n  Eye,\n  EyeOff,\n  GripVertical,\n  RotateCcw,\n  Trash2,\n} from \'lucide-react\';\nimport type {\n  OperatorManifest,\n  ParameterManifest,\n  StackOperatorInstance,\n} from \'./types\';\n\ninterface Props {\n  stack: StackOperatorInstance[];\n  manifests: Map<string, OperatorManifest>;\n  onToggleExpanded: (id: string) => void;\n  onDelete: (id: string) => void;\n  onToggleEnabled: (id: string) => void;\n  onReset: (id: string) => void;\n  onReorder: (\n    fromIndex: number,\n    toIndex: number,\n  ) => void;\n  onParameterChange: (\n    id: string,\n    key: string,\n    value: any,\n    commit?: boolean,\n  ) => void;\n}\n\nconst NumericEditor = ({\n  spec,\n  value,\n  onChange,\n  onCommit,\n}: {\n  spec: ParameterManifest;\n  value: number;\n  onChange: (value: number) => void;\n  onCommit: (value: number) => void;\n}) => {\n  const min = spec.min ?? 0;\n  const max =\n    spec.max\n    ?? (\n      spec.type === \'integer\'\n        ? 255\n        : 10\n    );\n\n  const step =\n    spec.odd\n      ? 2\n      : spec.type === \'integer\'\n        ? 1\n        : Math.max(\n            (max - min) / 200,\n            0.01,\n          );\n\n  const normalized =\n    Number.isFinite(Number(value))\n      ? Number(value)\n      : Number(\n          spec.default\n          ?? min,\n        );\n\n  return (\n    <div className="grid grid-cols-[1fr_76px] gap-2 items-center">\n      <input\n        type="range"\n        min={min}\n        max={max}\n        step={step}\n        value={normalized}\n        onPointerDown={(event) => {\n          event.stopPropagation();\n        }}\n        onDragStart={(event) => {\n          event.preventDefault();\n        }}\n        onChange={(event: any) => {\n          onChange(\n            Number(event.target.value),\n          );\n        }}\n        onPointerUp={(event: any) => {\n          onCommit(\n            Number(event.currentTarget.value),\n          );\n        }}\n        className="w-full accent-[#8ab4f8]"\n      />\n\n      <input\n        type="number"\n        min={min}\n        max={max}\n        step={step}\n        value={normalized}\n        onPointerDown={(event) => {\n          event.stopPropagation();\n        }}\n        onDragStart={(event) => {\n          event.preventDefault();\n        }}\n        onChange={(event: any) => {\n          onChange(\n            Number(event.target.value),\n          );\n        }}\n        onBlur={(event: any) => {\n          onCommit(\n            Number(event.currentTarget.value),\n          );\n        }}\n        className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"\n      />\n    </div>\n  );\n};\n\nconst ParameterEditor = ({\n  name,\n  spec,\n  value,\n  onChange,\n  onCommit,\n}: {\n  name: string;\n  spec: ParameterManifest;\n  value: any;\n  onChange: (value: any) => void;\n  onCommit: (value: any) => void;\n}) => {\n  const label =\n    spec.label\n    || name.replaceAll(\n      \'_\',\n      \' \',\n    );\n\n  return (\n    <div\n      className="space-y-1.5"\n      onPointerDown={(event) => {\n        event.stopPropagation();\n      }}\n      onDragStart={(event) => {\n        event.preventDefault();\n      }}\n    >\n      <div className="flex items-center justify-between gap-2">\n        <label className="text-[10px] font-bold uppercase tracking-wider text-[#bdc1c6]">\n          {label}\n        </label>\n\n        {spec.description && (\n          <span className="text-[9px] text-[#80868b] truncate">\n            {spec.description}\n          </span>\n        )}\n      </div>\n\n      {\n        (\n          spec.type === \'integer\'\n          || spec.type === \'float\'\n        )\n        && (\n          <NumericEditor\n            spec={spec}\n            value={value}\n            onChange={onChange}\n            onCommit={onCommit}\n          />\n        )\n      }\n\n      {\n        spec.type === \'boolean\'\n        && (\n          <button\n            onClick={() => {\n              const next = !Boolean(value);\n              onChange(next);\n              window.setTimeout(\n                () => onCommit(next),\n                0,\n              );\n            }}\n            className={`w-full rounded border px-2 py-1.5 text-xs font-semibold ${\n              value\n                ? \'border-[#8ab4f8] bg-[#3c4043] text-[#e8eaed]\'\n                : \'border-[#5f6368] bg-[#202124] text-[#bdc1c6]\'\n            }`}\n          >\n            {\n              value\n                ? \'Enabled\'\n                : \'Disabled\'\n            }\n          </button>\n        )\n      }\n\n      {\n        spec.type === \'enum\'\n        && (() => {\n          const choices =\n            spec.choices\n            ?? [];\n\n          let selectedIndex =\n            choices.findIndex(\n              (choice) => Object.is(\n                choice,\n                value,\n              ),\n            );\n\n          if (selectedIndex < 0) {\n            selectedIndex =\n              choices.findIndex(\n                (choice) => (\n                  String(choice)\n                  === String(value)\n                ),\n              );\n          }\n\n          return (\n            <select\n              value={\n                selectedIndex >= 0\n                  ? String(selectedIndex)\n                  : \'\'\n              }\n              onChange={(event: any) => {\n                const index =\n                  Number(\n                    event.target.value,\n                  );\n\n                const next =\n                  choices[index];\n\n                onChange(next);\n\n                window.setTimeout(\n                  () => onCommit(next),\n                  0,\n                );\n              }}\n              className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1.5 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"\n            >\n              {choices.map((choice, index) => (\n                <option\n                  key={`${index}:${String(choice)}`}\n                  value={String(index)}\n                >\n                  {String(choice)}\n                </option>\n              ))}\n            </select>\n          );\n        })()\n      }\n\n      {\n        spec.type === \'string\'\n        && (\n          <input\n            value={value ?? \'\'}\n            onChange={(event: any) => {\n              onChange(\n                event.target.value,\n              );\n            }}\n            onBlur={(event: any) => {\n              onCommit(\n                event.currentTarget.value,\n              );\n            }}\n            className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1.5 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"\n          />\n        )\n      }\n    </div>\n  );\n};\n\nexport const ProcessingStack = ({\n  stack,\n  manifests,\n  onToggleExpanded,\n  onDelete,\n  onToggleEnabled,\n  onReset,\n  onReorder,\n  onParameterChange,\n}: Props) => {\n  const [dragIndex, setDragIndex] =\n    useState<number | null>(null);\n\n  return (\n    <aside className="w-[360px] min-w-[320px] border-l border-[#3c4043] bg-[#202124] flex flex-col overflow-hidden">\n      <div className="p-3 border-b border-[#3c4043] bg-[#292a2d]">\n        <div className="flex items-center justify-between">\n          <div className="text-[11px] font-black tracking-[0.18em] text-[#e8eaed] uppercase">\n            Processing Stack\n          </div>\n\n          <span className="rounded bg-[#3c4043] px-2 py-0.5 text-[9px] font-bold text-[#bdc1c6]">\n            {stack.length}\n          </span>\n        </div>\n\n        <p className="mt-1 text-[10px] text-[#9aa0a6]">\n          Drag only the grip handle to reorder · sliders never drag the block.\n        </p>\n      </div>\n\n      <div className="flex-1 overflow-y-auto p-2 space-y-2">\n        {\n          stack.length === 0\n          && (\n            <div className="rounded-md border border-dashed border-[#5f6368] p-5 text-center text-xs text-[#9aa0a6]">\n              Select an algorithm from the Operator Library to begin.\n            </div>\n          )\n        }\n\n        {stack.map((instance, index) => {\n          const manifest =\n            manifests.get(\n              instance.operatorId,\n            );\n\n          if (!manifest) {\n            return null;\n          }\n\n          const inputTypes =\n            Object.values(\n              manifest.inputs\n              ?? {},\n            ).map(\n              (port) => port.type,\n            );\n\n          const outputTypes =\n            Object.values(\n              manifest.outputs\n              ?? {},\n            ).map(\n              (port) => port.type,\n            );\n\n          const canBypass =\n            inputTypes.length === 1\n            && outputTypes.length === 1\n            && inputTypes[0] === outputTypes[0];\n\n          return (\n            <div\n              key={instance.id}\n              onDragOver={(event: any) => {\n                event.preventDefault();\n              }}\n              onDrop={() => {\n                if (\n                  dragIndex !== null\n                  && dragIndex !== index\n                ) {\n                  onReorder(\n                    dragIndex,\n                    index,\n                  );\n                }\n\n                setDragIndex(null);\n              }}\n              className={`rounded-md border overflow-hidden transition-colors ${\n                instance.enabled\n                  ? \'border-[#5f6368] bg-[#292a2d]\'\n                  : \'border-[#3c4043] bg-[#202124] opacity-60\'\n              }`}\n            >\n              <div className="flex items-center gap-1.5 px-2 py-2">\n                <span\n                  draggable\n                  title="Drag to reorder"\n                  onDragStart={(event) => {\n                    setDragIndex(index);\n                    event.dataTransfer.effectAllowed =\n                      \'move\';\n                    event.dataTransfer.setData(\n                      \'text/plain\',\n                      instance.id,\n                    );\n                  }}\n                  onDragEnd={() => {\n                    setDragIndex(null);\n                  }}\n                  className="p-0.5 text-[#80868b] cursor-grab active:cursor-grabbing"\n                >\n                  <GripVertical size={14} />\n                </span>\n\n                <span className="w-6 h-6 rounded bg-[#3c4043] flex items-center justify-center text-[10px] font-black text-[#bdc1c6]">\n                  {index + 1}\n                </span>\n\n                <button\n                  onClick={() => {\n                    onToggleExpanded(\n                      instance.id,\n                    );\n                  }}\n                  className="min-w-0 flex-1 flex items-center gap-1.5 text-left text-[#e8eaed]"\n                >\n                  {\n                    instance.expanded\n                      ? <ChevronDown size={14} />\n                      : <ChevronRight size={14} />\n                  }\n\n                  <span className="truncate text-xs font-semibold">\n                    {manifest.label}\n                  </span>\n                </button>\n\n                <button\n                  onClick={() => {\n                    onReset(instance.id);\n                  }}\n                  title="Reset parameters"\n                  className="p-1 text-[#9aa0a6] hover:text-[#8ab4f8]"\n                >\n                  <RotateCcw size={13} />\n                </button>\n\n                <button\n                  disabled={!canBypass}\n                  onClick={() => {\n                    if (canBypass) {\n                      onToggleEnabled(\n                        instance.id,\n                      );\n                    }\n                  }}\n                  title={\n                    canBypass\n                      ? \'Enable / bypass\'\n                      : \'Bypass unavailable when input/output types differ\'\n                  }\n                  className="p-1 text-[#9aa0a6] hover:text-white disabled:opacity-25 disabled:cursor-not-allowed"\n                >\n                  {\n                    instance.enabled\n                      ? <Eye size={13} />\n                      : <EyeOff size={13} />\n                  }\n                </button>\n\n                <button\n                  onClick={() => {\n                    onDelete(instance.id);\n                  }}\n                  title="Delete"\n                  className="p-1 text-[#9aa0a6] hover:text-[#f28b82]"\n                >\n                  <Trash2 size={13} />\n                </button>\n              </div>\n\n              {\n                instance.expanded\n                && (\n                  <div className="border-t border-[#3c4043] px-3 py-3 space-y-3 bg-[#202124]">\n                    <div className="flex flex-wrap gap-1.5 text-[9px] text-[#80868b]">\n                      {\n                        Object.entries(\n                          manifest.inputs\n                          ?? {},\n                        ).map(\n                          ([portName, port]) => (\n                            <span\n                              key={`i-${portName}`}\n                              className="rounded bg-[#292a2d] px-1.5 py-0.5"\n                            >\n                              IN {portName}:{port.type}\n                            </span>\n                          ),\n                        )\n                      }\n\n                      {\n                        Object.entries(\n                          manifest.outputs\n                          ?? {},\n                        ).map(\n                          ([portName, port]) => (\n                            <span\n                              key={`o-${portName}`}\n                              className="rounded bg-[#292a2d] px-1.5 py-0.5"\n                            >\n                              OUT {portName}:{port.type}\n                            </span>\n                          ),\n                        )\n                      }\n                    </div>\n\n                    {\n                      Object.keys(\n                        manifest.parameters\n                        ?? {},\n                      ).length === 0\n                        ? (\n                            <div className="text-[10px] text-[#80868b]">\n                              No adjustable parameters.\n                            </div>\n                          )\n                        : (\n                            Object.entries(\n                              manifest.parameters,\n                            ).map(\n                              ([name, spec]) => (\n                                <ParameterEditor\n                                  key={name}\n                                  name={name}\n                                  spec={spec}\n                                  value={\n                                    instance.parameters[name]\n                                  }\n                                  onChange={(value) => {\n                                    onParameterChange(\n                                      instance.id,\n                                      name,\n                                      value,\n                                      false,\n                                    );\n                                  }}\n                                  onCommit={(value) => {\n                                    onParameterChange(\n                                      instance.id,\n                                      name,\n                                      value,\n                                      true,\n                                    );\n                                  }}\n                                />\n                              ),\n                            )\n                          )\n                    }\n                  </div>\n                )\n              }\n            </div>\n          );\n        })}\n      </div>\n    </aside>\n  );\n};\n', 'src/Pages/ImageProcessingLabPage.tsx': 'import { useNavigate } from \'react-router-dom\';\nimport {\n  AlertTriangle,\n  ArrowLeft,\n  FlaskConical,\n  Gauge,\n  Wifi,\n} from \'lucide-react\';\nimport { OperatorLibrary } from \'../components/VisionLabs/ImageProcessing/OperatorLibrary\';\nimport { ProcessingStack } from \'../components/VisionLabs/ImageProcessing/ProcessingStack\';\nimport { ImageWorkbench } from \'../components/VisionLabs/ImageProcessing/ImageWorkbench\';\nimport { useImageLabController } from \'../components/VisionLabs/ImageProcessing/useImageLabController\';\n\nexport const ImageProcessingLabPage = () => {\n  const navigate = useNavigate();\n  const lab = useImageLabController();\n\n  const totalTiming =\n    Object.values(\n      lab.timings,\n    ).reduce(\n      (sum, value) => (\n        sum\n        + Number(value || 0)\n      ),\n      0,\n    );\n\n  return (\n    <div className="h-screen w-screen overflow-hidden bg-[#202124] text-[#e8eaed] flex flex-col">\n      <header className="h-14 shrink-0 border-b border-[#3c4043] bg-[#292a2d] flex items-center px-3 gap-3 shadow-sm">\n        <button\n          onClick={() => navigate(\'/labs\')}\n          className="w-8 h-8 rounded-md border border-[#5f6368] bg-[#35363a] flex items-center justify-center text-[#bdc1c6] hover:bg-[#3c4043] hover:text-white"\n        >\n          <ArrowLeft size={16} />\n        </button>\n\n        <div className="w-px h-7 bg-[#5f6368]" />\n\n        <FlaskConical\n          size={18}\n          className="text-[#8ab4f8]"\n        />\n\n        <div className="min-w-0">\n          <div className="text-xs font-black tracking-[0.14em] text-[#e8eaed]">\n            IMAGE PROCESSING LAB\n          </div>\n\n          <div className="text-[9px] text-[#9aa0a6]">\n            Interactive raster processing workbench\n          </div>\n        </div>\n\n        <div className="ml-auto flex items-center gap-2 text-[10px] text-[#9aa0a6]">\n          <span className="flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124] px-2 py-1">\n            <Wifi\n              size={11}\n              className={\n                lab.sessionId\n                  ? \'text-[#81c995]\'\n                  : \'text-[#fdd663]\'\n              }\n            />\n            {lab.status}\n          </span>\n\n          <span className="flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124] px-2 py-1">\n            <Gauge\n              size={11}\n              className="text-[#8ab4f8]"\n            />\n            {totalTiming.toFixed(2)} ms\n          </span>\n        </div>\n      </header>\n\n      {\n        lab.error\n        && (\n          <div className="shrink-0 border-b border-[#f28b82]/40 bg-[#5f2120] px-4 py-2 flex items-center gap-2 text-xs text-[#f28b82]">\n            <AlertTriangle size={14} />\n\n            <span className="flex-1">\n              {lab.error}\n            </span>\n\n            <button\n              onClick={() => {\n                lab.setError(\'\');\n              }}\n              className="text-[10px] font-bold hover:text-white"\n            >\n              DISMISS\n            </button>\n          </div>\n        )\n      }\n\n      <div className="flex-1 min-h-0 flex overflow-hidden">\n        <OperatorLibrary\n          operators={lab.operators}\n          onAdd={lab.addOperator}\n          canAppend={lab.canAppend}\n        />\n\n        <ImageWorkbench\n          sourceLoaded={lab.sourceLoaded}\n          imageName={lab.imageName}\n          viewerPanes={lab.viewerPanes}\n          sources={lab.availableSources}\n          previewUrls={lab.previewUrls}\n          busy={lab.busy}\n          onUpload={lab.uploadImage}\n          onViewerSourceChange={lab.setViewerSource}\n          onAddViewer={lab.addViewer}\n          onRemoveViewer={lab.removeViewer}\n          onSetViewerPreset={lab.setViewerPreset}\n          onRun={lab.runNow}\n        />\n\n        <ProcessingStack\n          stack={lab.stack}\n          manifests={lab.manifests}\n          onToggleExpanded={lab.toggleExpanded}\n          onDelete={lab.deleteOperator}\n          onToggleEnabled={lab.toggleEnabled}\n          onReset={lab.resetOperator}\n          onReorder={lab.reorderOperator}\n          onParameterChange={lab.changeParameter}\n        />\n      </div>\n    </div>\n  );\n};\n'}

TEST_FILE = 'from app.services.vision_labs.core import EnumParam\nfrom app.services.vision_labs.image.operators import load_builtin_operators\nfrom app.services.vision_labs.image.registry import IMAGE_OPERATOR_REGISTRY\n\n\ndef test_numeric_enum_coerces_string_to_declared_choice_type():\n    spec = EnumParam((1, 3, 5, 7), default=3)\n    value = spec.validate("5")\n    assert value == 5\n    assert isinstance(value, int)\n\n\ndef test_edge_operator_accepts_numeric_enum_from_html_select():\n    load_builtin_operators()\n    definition = IMAGE_OPERATOR_REGISTRY.get("image.edge.sobel_x")\n    resolved = definition.operator_class.resolve_parameters({"kernel_size": "5"})\n    assert resolved["kernel_size"] == 5\n    assert isinstance(resolved["kernel_size"], int)\n\n\ndef test_canny_aperture_accepts_numeric_enum_from_html_select():\n    load_builtin_operators()\n    definition = IMAGE_OPERATOR_REGISTRY.get("image.edge.canny")\n    resolved = definition.operator_class.resolve_parameters({"aperture": "7"})\n    assert resolved["aperture"] == 7\n'

ENUM_OLD = """        elif self.kind == "enum":
            if self.choices is None:
                raise ValueError("enum parameter has no choices")
"""

ENUM_NEW = """        elif self.kind == "enum":
            if self.choices is None:
                raise ValueError("enum parameter has no choices")

            # HTML <select> values arrive as strings. Preserve the declared
            # enum choice type by mapping an equivalent string representation
            # back to the original choice object.
            if value not in self.choices:
                sentinel = object()
                matched = next(
                    (
                        choice
                        for choice in self.choices
                        if str(choice) == str(value)
                    ),
                    sentinel,
                )
                if matched is not sentinel:
                    value = matched
"""


def resolve_roots(frontend_arg, backend_arg):
    cwd = Path.cwd().resolve()

    fe_candidates = []
    be_candidates = []

    if frontend_arg:
        fe_candidates.append(
            Path(frontend_arg).expanduser().resolve()
        )
    if backend_arg:
        be_candidates.append(
            Path(backend_arg).expanduser().resolve()
        )

    fe_candidates += [
        cwd,
        cwd / "LambdaVisionSuper",
        cwd.parent / "LambdaVisionSuper",
    ]

    be_candidates += [
        cwd,
        cwd / "LambdaVisionSuperBackEnd",
        cwd.parent / "LambdaVisionSuperBackEnd",
    ]

    frontend = next(
        (
            path
            for path in fe_candidates
            if (
                path
                / "src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx"
            ).exists()
        ),
        None,
    )

    backend = next(
        (
            path
            for path in be_candidates
            if (
                path
                / "app/services/vision_labs/core/specs.py"
            ).exists()
        ),
        None,
    )

    if frontend is None:
        raise RuntimeError(
            "Cannot locate Lambda Vision frontend. "
            "Use --frontend /path/to/LambdaVisionSuper"
        )

    if backend is None:
        raise RuntimeError(
            "Cannot locate Lambda Vision backend. "
            "Use --backend /path/to/LambdaVisionSuperBackEnd"
        )

    return frontend, backend


def backup(frontend, backend, paths):
    stamp = _dt.datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    root = (
        frontend
        / ".lambda_updater_backups"
        / f"image_lab_viewer_ux_v0021_{stamp}"
    )

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for path in paths:
        if not path.exists():
            continue

        try:
            rel = path.relative_to(frontend)
            prefix = Path("frontend")
        except ValueError:
            rel = path.relative_to(backend)
            prefix = Path("backend")

        dest = root / prefix / rel
        dest.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        shutil.copy2(
            path,
            dest,
        )

    return root


def patch_enum_spec(text):
    if ENUM_NEW in text:
        return text, False

    if ENUM_OLD not in text:
        raise RuntimeError(
            "Could not locate enum validation block in "
            "app/services/vision_labs/core/specs.py"
        )

    return (
        text.replace(
            ENUM_OLD,
            ENUM_NEW,
            1,
        ),
        True,
    )


def scan(frontend, backend):
    print("=" * 80)
    print(
        "IMAGE PROCESSING LAB VIEWER / UX FIX V0.2.1"
    )
    print("=" * 80)
    print(f"Frontend : {frontend}")
    print(f"Backend  : {backend}")
    print()

    for rel, desired in FE_FILES.items():
        path = frontend / rel

        if not path.exists():
            status = "CREATE"
        elif (
            path.read_text(encoding="utf-8")
            == desired
        ):
            status = "OK"
        else:
            status = "UPDATE"

        print(
            f"  [{status:6}] FE {rel}"
        )

    specs = (
        backend
        / "app/services/vision_labs/core/specs.py"
    )

    specs_text = specs.read_text(
        encoding="utf-8"
    )

    enum_status = (
        "OK"
        if ENUM_NEW in specs_text
        else "PATCH"
    )

    print(
        f"  [{enum_status:6}] BE "
        "app/services/vision_labs/core/specs.py"
    )

    test_path = (
        backend
        / "tests/vision_labs/image/"
        "test_image_lab_enum_coercion.py"
    )

    print(
        f"  [{'OK' if test_path.exists() else 'CREATE':6}] "
        "BE tests/vision_labs/image/"
        "test_image_lab_enum_coercion.py"
    )

    print()
    print("Fixes / features:")
    print(
        "  - numeric enum select values preserve number type"
    )
    print(
        "  - only the grip handle can drag a processing block"
    )
    print(
        "  - stable Latest viewer source follows final pipeline output"
    )
    print(
        "  - fixed effect viewers keep their selected effect"
    )
    print(
        "  - dynamic ViewerPane[] instead of hard 1/2/4 count"
    )
    print(
        "  - + View allows more than four viewers"
    )
    print(
        "  - each viewer pane has an independent resize handle"
    )

    return 0


def apply(frontend, backend):
    specs = (
        backend
        / "app/services/vision_labs/core/specs.py"
    )

    test_path = (
        backend
        / "tests/vision_labs/image/"
        "test_image_lab_enum_coercion.py"
    )

    touched = [
        frontend / rel
        for rel in FE_FILES
    ] + [
        specs,
        test_path,
    ]

    backup_root = backup(
        frontend,
        backend,
        touched,
    )

    for rel, desired in FE_FILES.items():
        path = frontend / rel
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            not path.exists()
            or path.read_text(encoding="utf-8")
            != desired
        ):
            path.write_text(
                desired,
                encoding="utf-8",
            )
            print(
                f"[WRITE] FE {rel}"
            )

    specs_old = specs.read_text(
        encoding="utf-8"
    )

    specs_new, changed = patch_enum_spec(
        specs_old
    )

    if changed:
        specs.write_text(
            specs_new,
            encoding="utf-8",
        )
        print(
            "[PATCH] BE core/specs.py "
            "numeric enum coercion"
        )

    test_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if (
        not test_path.exists()
        or test_path.read_text(
            encoding="utf-8"
        )
        != TEST_FILE
    ):
        test_path.write_text(
            TEST_FILE,
            encoding="utf-8",
        )
        print(
            "[WRITE] BE "
            "tests/vision_labs/image/"
            "test_image_lab_enum_coercion.py"
        )

    print(
        f"[OK] Backup: {backup_root}"
    )
    print(
        "Run verify next."
    )

    return 0


def verify(frontend, backend, skip_build):
    print("=" * 80)
    print(
        "VERIFY IMAGE PROCESSING LAB "
        "VIEWER / UX FIX V0.2.1"
    )
    print("=" * 80)

    failures = 0

    files_text = {
        rel: (
            frontend
            / rel
        ).read_text(
            encoding="utf-8"
        )
        for rel in FE_FILES
    }

    checks = [
        (
            "FE enum select uses choice index, not raw string value",
            "const next =\n                  choices[index];"
            in files_text[
                "src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx"
            ],
        ),
        (
            "Processing block itself is not draggable",
            "<div\n              key={instance.id}\n              draggable"
            not in files_text[
                "src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx"
            ],
        ),
        (
            "Grip handle is draggable",
            "<span\n                  draggable"
            in files_text[
                "src/components/VisionLabs/ImageProcessing/ProcessingStack.tsx"
            ],
        ),
        (
            "Latest source exists",
            "key: 'latest'"
            in files_text[
                "src/components/VisionLabs/ImageProcessing/pipelineUtils.ts"
            ],
        ),
        (
            "Dynamic ViewerPane model exists",
            "export interface ViewerPane"
            in files_text[
                "src/components/VisionLabs/ImageProcessing/types.ts"
            ],
        ),
        (
            "+ View action exists",
            "onAddViewer"
            in files_text[
                "src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx"
            ],
        ),
        (
            "Viewer resize handle exists",
            'aria-label="Resize viewer"'
            in files_text[
                "src/components/VisionLabs/ImageProcessing/ImageWorkbench.tsx"
            ],
        ),
        (
            "Controller no longer uses hard ViewerCount",
            "ViewerCount"
            not in files_text[
                "src/components/VisionLabs/ImageProcessing/useImageLabController.ts"
            ],
        ),
        (
            "Controller preserves stable Latest selection",
            "sourceKey: 'latest'"
            in files_text[
                "src/components/VisionLabs/ImageProcessing/useImageLabController.ts"
            ],
        ),
    ]

    for label, ok in checks:
        print(
            f"[{'OK' if ok else 'FAIL'}] {label}"
        )

        if not ok:
            failures += 1

    specs = (
        backend
        / "app/services/vision_labs/core/specs.py"
    )

    specs_text = specs.read_text(
        encoding="utf-8"
    )

    enum_ok = (
        "if str(choice) == str(value)"
        in specs_text
    )

    print(
        f"[{'OK' if enum_ok else 'FAIL'}] "
        "BE numeric enum coercion"
    )

    if not enum_ok:
        failures += 1

    try:
        py_compile.compile(
            str(specs),
            doraise=True,
        )
        print(
            "[OK] Backend specs.py syntax"
        )
    except Exception as exc:
        print(
            f"[FAIL] Backend specs.py syntax: {exc}"
        )
        failures += 1

    test_path = (
        backend
        / "tests/vision_labs/image/"
        "test_image_lab_enum_coercion.py"
    )

    try:
        py_compile.compile(
            str(test_path),
            doraise=True,
        )
        print(
            "[OK] Enum regression test syntax"
        )
    except Exception as exc:
        print(
            f"[FAIL] Enum regression test syntax: {exc}"
        )
        failures += 1

    pytest_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(
                test_path.relative_to(
                    backend
                )
            ),
        ],
        cwd=str(backend),
        text=True,
        capture_output=True,
    )

    if pytest_proc.returncode == 0:
        print(
            "[OK] Numeric enum regression tests"
        )
        output = pytest_proc.stdout.strip()
        if output:
            print(output)
    else:
        print(
            "[FAIL] Numeric enum regression tests"
        )
        print(
            (
                pytest_proc.stdout
                + "\n"
                + pytest_proc.stderr
            ).strip()
        )
        failures += 1

    if (
        not skip_build
        and (
            frontend
            / "package.json"
        ).exists()
        and (
            frontend
            / "node_modules"
        ).exists()
    ):
        proc = subprocess.run(
            [
                "npm",
                "run",
                "build",
            ],
            cwd=str(frontend),
        )

        if proc.returncode == 0:
            print(
                "[OK] Frontend npm build"
            )
        else:
            print(
                "[FAIL] Frontend npm build"
            )
            failures += 1
    else:
        print(
            "[SKIP] Frontend npm build"
        )

    if failures:
        print(
            f"[FAIL] Verification completed "
            f"with {failures} issue(s)."
        )
        return 1

    print(
        "[OK] Image Processing LAB "
        "v0.2.1 verified."
    )
    return 0


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command",
        choices=[
            "scan",
            "apply",
            "verify",
        ],
    )

    parser.add_argument(
        "--frontend",
    )

    parser.add_argument(
        "--backend",
    )

    parser.add_argument(
        "--skip-build",
        action="store_true",
    )

    args = parser.parse_args()

    try:
        frontend, backend = resolve_roots(
            args.frontend,
            args.backend,
        )

        if args.command == "scan":
            return scan(
                frontend,
                backend,
            )

        if args.command == "apply":
            return apply(
                frontend,
                backend,
            )

        return verify(
            frontend,
            backend,
            args.skip_build,
        )

    except Exception as exc:
        print(
            f"[ERROR] {exc}"
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
