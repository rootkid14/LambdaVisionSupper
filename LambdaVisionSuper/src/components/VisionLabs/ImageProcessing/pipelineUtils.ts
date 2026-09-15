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
  const original: ViewerSource = {
    key: 'source:image',
    label: 'Original',
    kind: 'source',
    sourceName: 'image',
    dataType: 'image',
  };

  const nodeSources: ViewerSource[] = [];

  stack.forEach((instance, index) => {
    const manifest = manifests.get(instance.operatorId);
    const output = manifest ? firstEntry(manifest.outputs) : null;
    if (!manifest || !output) return;

    nodeSources.push({
      key: `node:${instance.id}:${output[0]}`,
      label: `${index + 1}. ${manifest.label}`,
      kind: 'node',
      nodeId: instance.id,
      port: output[0],
      dataType: output[1].type,
    });
  });

  const finalSource = nodeSources[nodeSources.length - 1];
  const latest: ViewerSource = finalSource
    ? {
        ...finalSource,
        key: 'latest',
        label: `Latest · ${finalSource.label}`,
        kind: 'latest',
      }
    : {
        ...original,
        key: 'latest',
        label: 'Latest · Original',
        kind: 'latest',
      };

  return [latest, original, ...nodeSources];
};
