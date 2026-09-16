import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  AlertTriangle,
  ImagePlus,
  Loader2,
  Play,
  RotateCcw,
  X,
} from 'lucide-react';
import { ImageLabAPI } from '../../../api/imageLabApi';
import type {
  ImagePipelineDefinition,
  OperatorManifest,
  ParameterManifest,
} from './types';
import { ZoomPanImageView } from './ZoomPanImageView';
import { buildOperatorGuide } from './operatorGuide';

interface Props {
  operator: OperatorManifest;
  onClose: () => void;
}

const NODE_ID = '__guide_target__';
const GRAY_ID = '__guide_gray_adapter__';
const MASK_ID = '__guide_mask_adapter__';

const defaultsFor = (
  operator: OperatorManifest,
): Record<string, any> => Object.fromEntries(
  Object.entries(operator.parameters ?? {}).map(
    ([name, spec]) => [name, spec.default],
  ),
);

const firstEntry = <T,>(
  record: Record<string, T>,
): [string, T] | null => {
  const entry = Object.entries(record)[0];
  return entry ? (entry as [string, T]) : null;
};

const ParameterEditor = ({
  name,
  spec,
  value,
  tip,
  onChange,
}: {
  name: string;
  spec: ParameterManifest;
  value: any;
  tip?: string;
  onChange: (value: any) => void;
}) => {
  const label = spec.label || name.replaceAll('_', ' ');
  const min = spec.min ?? 0;
  const max = spec.max ?? (
    spec.type === 'integer'
      ? 255
      : 10
  );
  const step = spec.odd
    ? 2
    : spec.type === 'integer'
      ? 1
      : Math.max((max - min) / 200, 0.01);

  return (
    <div className="space-y-1.5 rounded-md border border-[#3c4043] bg-[#292a2d] p-2.5">
      <div className="flex items-start justify-between gap-2">
        <label className="text-[10px] font-black uppercase tracking-wider text-[#e8eaed]">
          {label}
        </label>

        <span className="font-mono text-[9px] text-[#8ab4f8]">
          {String(value ?? '')}
        </span>
      </div>

      {spec.type === 'integer' || spec.type === 'float' ? (
        <div className="grid grid-cols-[1fr_78px] gap-2">
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={Number(value ?? spec.default ?? min)}
            onChange={(event: any) => {
              onChange(Number(event.target.value));
            }}
            className="w-full accent-[#8ab4f8]"
          />

          <input
            type="number"
            min={min}
            max={max}
            step={step}
            value={Number(value ?? spec.default ?? min)}
            onChange={(event: any) => {
              onChange(Number(event.target.value));
            }}
            className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
          />
        </div>
      ) : null}

      {spec.type === 'boolean' ? (
        <button
          onClick={() => onChange(!Boolean(value))}
          className={`w-full rounded border px-2 py-1.5 text-xs font-semibold ${
            value
              ? 'border-[#8ab4f8] bg-[#3c4043] text-[#e8eaed]'
              : 'border-[#5f6368] bg-[#202124] text-[#bdc1c6]'
          }`}
        >
          {value ? 'Enabled' : 'Disabled'}
        </button>
      ) : null}

      {spec.type === 'enum' ? (() => {
        const choices = spec.choices ?? [];
        let selectedIndex = choices.findIndex(
          (choice) => Object.is(choice, value),
        );

        if (selectedIndex < 0) {
          selectedIndex = choices.findIndex(
            (choice) => String(choice) === String(value),
          );
        }

        return (
          <select
            value={selectedIndex >= 0 ? String(selectedIndex) : ''}
            onChange={(event: any) => {
              onChange(choices[Number(event.target.value)]);
            }}
            className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1.5 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
          >
            {choices.map((choice, index) => (
              <option
                key={`${index}:${String(choice)}`}
                value={String(index)}
              >
                {String(choice)}
              </option>
            ))}
          </select>
        );
      })() : null}

      {spec.type === 'string' ? (
        <input
          value={value ?? ''}
          onChange={(event: any) => onChange(event.target.value)}
          className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1.5 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
        />
      ) : null}

      {tip && (
        <p className="text-[9px] leading-4 text-[#9aa0a6]">
          {tip}
        </p>
      )}
    </div>
  );
};

const buildStandalonePipeline = (
  operator: OperatorManifest,
  parameters: Record<string, any>,
  maskThreshold: number,
): {
  pipeline: ImagePipelineDefinition;
  outputPort: string;
  outputType: string;
  adapterDescription?: string;
} => {
  const inputs = Object.entries(operator.inputs ?? {});
  const output = firstEntry(operator.outputs ?? {});

  if (inputs.length !== 1 || !output) {
    throw new Error(
      'Standalone playground currently supports operators with exactly one input and at least one output.',
    );
  }

  const [inputPortName, inputPort] = inputs[0];
  const [outputPort, outputSpec] = output;

  const nodes: ImagePipelineDefinition['nodes'] = [];
  const connections: ImagePipelineDefinition['connections'] = [];

  const targetNode = {
    id: NODE_ID,
    operator_id: operator.id,
    operator_version: operator.version ?? null,
    parameters: { ...parameters },
    enabled: true,
  };

  let externalTarget = {
    node_id: NODE_ID,
    port: inputPortName,
  };

  let adapterDescription: string | undefined;

  if (inputPort.type === 'binary_mask') {
    nodes.push(
      {
        id: GRAY_ID,
        operator_id: 'image.color.grayscale',
        parameters: {},
        enabled: true,
      },
      {
        id: MASK_ID,
        operator_id: 'image.threshold.binary',
        parameters: {
          threshold: maskThreshold,
          invert: false,
        },
        enabled: true,
      },
    );

    connections.push(
      {
        source: {
          node_id: GRAY_ID,
          port: 'image',
        },
        target: {
          node_id: MASK_ID,
          port: 'image',
        },
      },
      {
        source: {
          node_id: MASK_ID,
          port: 'mask',
        },
        target: {
          node_id: NODE_ID,
          port: inputPortName,
        },
      },
    );

    externalTarget = {
      node_id: GRAY_ID,
      port: 'image',
    };

    adapterDescription = `Uploaded image is converted to grayscale, then thresholded at ${maskThreshold} to create the BinaryMask input.`;
  } else if (inputPort.type !== 'image') {
    throw new Error(
      `Standalone playground does not yet have an input adapter for type "${inputPort.type}".`,
    );
  } else if (operator.id === 'image.threshold.binary') {
    nodes.push({
      id: GRAY_ID,
      operator_id: 'image.color.grayscale',
      parameters: {},
      enabled: true,
    });

    connections.push({
      source: {
        node_id: GRAY_ID,
        port: 'image',
      },
      target: {
        node_id: NODE_ID,
        port: inputPortName,
      },
    });

    externalTarget = {
      node_id: GRAY_ID,
      port: 'image',
    };

    adapterDescription = 'A grayscale adapter is inserted because Binary Threshold expects a single-channel image.';
  }

  nodes.push(targetNode);

  return {
    pipeline: {
      version: 1,
      nodes,
      connections,
      inputs: {
        image: externalTarget,
      },
      outputs: {
        result: {
          node_id: NODE_ID,
          port: outputPort,
        },
      },
    },
    outputPort,
    outputType: outputSpec.type,
    adapterDescription,
  };
};

export const FilterGuideModal = ({
  operator,
  onClose,
}: Props) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [parameters, setParameters] = useState<Record<string, any>>(
    defaultsFor(operator),
  );
  const [maskThreshold, setMaskThreshold] = useState(127);
  const [fileName, setFileName] = useState('');
  const [inputUrl, setInputUrl] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [activePreview, setActivePreview] = useState<'input' | 'result'>('input');
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  const [timing, setTiming] = useState<number | null>(null);
  const [adapterDescription, setAdapterDescription] = useState<string>('');
  const fileRef = useRef<HTMLInputElement | null>(null);

  const guide = useMemo(
    () => buildOperatorGuide(operator),
    [operator],
  );

  const standaloneSupported = useMemo(() => {
    const inputs = Object.values(operator.inputs ?? {});
    return (
      inputs.length === 1
      && ['image', 'binary_mask'].includes(inputs[0].type)
      && Object.keys(operator.outputs ?? {}).length >= 1
    );
  }, [operator]);

  useEffect(() => {
    let cancelled = false;
    let createdSession: string | null = null;

    setParameters(defaultsFor(operator));
    setMaskThreshold(127);
    setFileName('');
    setInputUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
    setResultUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
    setActivePreview('input');
    setError('');
    setTiming(null);
    setDirty(false);
    setAdapterDescription('');

    if (!standaloneSupported) {
      return () => undefined;
    }

    (async () => {
      try {
        const session = await ImageLabAPI.createSession();

        if (cancelled) {
          await ImageLabAPI.closeSession(
            session.session_id,
          ).catch(() => undefined);
          return;
        }

        createdSession = session.session_id;
        setSessionId(session.session_id);
      } catch (cause: any) {
        setError(
          cause?.response?.data?.detail
          || cause?.message
          || 'Failed to create standalone filter test session',
        );
      }
    })();

    return () => {
      cancelled = true;

      if (createdSession) {
        ImageLabAPI.closeSession(createdSession).catch(() => undefined);
      }
    };
  }, [operator.id, standaloneSupported]);

  useEffect(() => {
    return () => {
      if (inputUrl) URL.revokeObjectURL(inputUrl);
    };
  }, [inputUrl]);

  useEffect(() => {
    return () => {
      if (resultUrl) URL.revokeObjectURL(resultUrl);
    };
  }, [resultUrl]);

  const loadImage = async (file: File) => {
    if (!sessionId) return;

    try {
      setBusy(true);
      setError('');

      await ImageLabAPI.uploadInput(
        sessionId,
        file,
        'image',
      );

      const preview = await ImageLabAPI.sourcePreview(
        sessionId,
        'image',
        1200,
        88,
      );

      const url = URL.createObjectURL(preview);

      setInputUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return url;
      });

      setResultUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });

      setFileName(file.name);
      setActivePreview('input');
      setTiming(null);
      setDirty(true);
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Failed to load playground image',
      );
    } finally {
      setBusy(false);
    }
  };

  const runTest = async () => {
    if (!sessionId || !inputUrl) return;

    try {
      setBusy(true);
      setError('');

      const built = buildStandalonePipeline(
        operator,
        parameters,
        maskThreshold,
      );

      setAdapterDescription(
        built.adapterDescription ?? '',
      );

      await ImageLabAPI.setPipeline(
        sessionId,
        built.pipeline,
      );

      const result = await ImageLabAPI.run(sessionId);

      const blob = await ImageLabAPI.nodePreview(
        sessionId,
        NODE_ID,
        built.outputPort,
        1400,
        90,
      );

      const url = URL.createObjectURL(blob);

      setResultUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return url;
      });

      const timings = result.result?.timings_ms ?? {};
      setTiming(
        timings[NODE_ID] !== undefined
          ? Number(timings[NODE_ID])
          : Object.values(timings).reduce(
              (sum: number, value: any) => sum + Number(value || 0),
              0,
            ),
      );

      setDirty(false);
      setActivePreview('result');
    } catch (cause: any) {
      setError(
        cause?.response?.data?.detail
        || cause?.message
        || 'Standalone filter test failed',
      );
    } finally {
      setBusy(false);
    }
  };

  const resetParameters = () => {
    setParameters(defaultsFor(operator));
    setMaskThreshold(127);
    setDirty(true);
  };

  const input = firstEntry(operator.inputs ?? {});
  const output = firstEntry(operator.outputs ?? {});

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/75 p-4">
      <div className="flex h-[90vh] w-[96vw] max-w-[1800px] flex-col overflow-hidden rounded-xl border border-[#5f6368] bg-[#202124] shadow-2xl">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-[#3c4043] bg-[#292a2d] px-4">
          <div className="min-w-0 flex-1">
            <div className="text-xs font-black tracking-[0.15em] text-[#8ab4f8]">
              FILTER GUIDE / STANDALONE PLAYGROUND
            </div>

            <div className="truncate text-sm font-bold text-[#e8eaed]">
              {operator.label}
              <span className="ml-2 font-normal text-[#9aa0a6]">
                {operator.category}
              </span>
            </div>
          </div>

          {timing !== null && (
            <span className="rounded border border-[#3c4043] bg-[#202124] px-2 py-1 font-mono text-[10px] text-[#bdc1c6]">
              {timing.toFixed(2)} ms
            </span>
          )}

          <button
            onClick={onClose}
            className="rounded p-2 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"
            title="Close guide"
          >
            <X size={17} />
          </button>
        </header>

        {error && (
          <div className="flex shrink-0 items-center gap-2 border-b border-[#f28b82]/40 bg-[#5f2120] px-4 py-2 text-xs text-[#f28b82]">
            <AlertTriangle size={14} />
            <span className="flex-1">{error}</span>
            <button
              onClick={() => setError('')}
              className="font-bold hover:text-white"
            >
              DISMISS
            </button>
          </div>
        )}

        <div className="grid min-h-0 flex-1 grid-cols-[340px_minmax(0,1fr)_360px]">
          <section className="overflow-y-auto border-r border-[#3c4043] bg-[#292a2d] p-4">
            <div className="mb-4">
              <div className="text-[10px] font-black uppercase tracking-[0.18em] text-[#8ab4f8]">
                What it does
              </div>
              <p className="mt-2 text-xs leading-5 text-[#e8eaed]">
                {guide.overview}
              </p>
            </div>

            <div className="mb-4">
              <div className="text-[10px] font-black uppercase tracking-[0.18em] text-[#bdc1c6]">
                How it works
              </div>
              <p className="mt-2 text-xs leading-5 text-[#bdc1c6]">
                {guide.howItWorks}
              </p>
            </div>

            <div className="mb-4 rounded-md border border-[#3c4043] bg-[#202124] p-3">
              <div className="text-[10px] font-black uppercase tracking-wider text-[#9aa0a6]">
                Contract
              </div>
              <div className="mt-2 space-y-1 font-mono text-[10px] text-[#bdc1c6]">
                <div>
                  IN&nbsp;&nbsp;
                  {input
                    ? `${input[0]} : ${input[1].type}`
                    : 'none'}
                </div>
                <div>
                  OUT&nbsp;
                  {output
                    ? `${output[0]} : ${output[1].type}`
                    : 'none'}
                </div>
              </div>
            </div>

            <div className="mb-4">
              <div className="text-[10px] font-black uppercase tracking-[0.18em] text-[#bdc1c6]">
                Tuning tips
              </div>

              <ul className="mt-2 space-y-2 text-[11px] leading-4 text-[#bdc1c6]">
                {guide.tuningTips.map((tip) => (
                  <li
                    key={tip}
                    className="flex gap-2"
                  >
                    <span className="text-[#8ab4f8]">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <div className="text-[10px] font-black uppercase tracking-[0.18em] text-[#bdc1c6]">
                Notes
              </div>

              <ul className="mt-2 space-y-2 text-[11px] leading-4 text-[#9aa0a6]">
                {guide.notes.map((note) => (
                  <li
                    key={note}
                    className="flex gap-2"
                  >
                    <span>•</span>
                    <span>{note}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="flex min-w-0 flex-col bg-[#171717]">
            <div className="flex h-12 shrink-0 items-center gap-2 border-b border-[#3c4043] bg-[#292a2d] px-3">
              <button
                onClick={() => fileRef.current?.click()}
                disabled={!standaloneSupported || !sessionId || busy}
                className="flex items-center gap-2 rounded border border-[#5f6368] bg-[#35363a] px-3 py-1.5 text-xs font-semibold text-[#e8eaed] hover:bg-[#3c4043] disabled:opacity-40"
              >
                <ImagePlus size={14} className="text-[#8ab4f8]" />
                Load Test Image
              </button>

              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(event: any) => {
                  const file = event.target.files?.[0];

                  if (file) {
                    loadImage(file);
                  }

                  event.currentTarget.value = '';
                }}
              />

              <span className="min-w-0 flex-1 truncate text-[10px] text-[#9aa0a6]">
                {fileName || 'No standalone test image loaded'}
              </span>

              {inputUrl && (
                <div className="flex rounded border border-[#3c4043] bg-[#202124] p-0.5">
                  <button
                    onClick={() => setActivePreview('input')}
                    className={`rounded px-2 py-1 text-[10px] font-bold ${
                      activePreview === 'input'
                        ? 'bg-[#3c4043] text-[#8ab4f8]'
                        : 'text-[#9aa0a6]'
                    }`}
                  >
                    Input
                  </button>

                  <button
                    disabled={!resultUrl}
                    onClick={() => setActivePreview('result')}
                    className={`rounded px-2 py-1 text-[10px] font-bold ${
                      activePreview === 'result'
                        ? 'bg-[#3c4043] text-[#8ab4f8]'
                        : 'text-[#9aa0a6]'
                    } disabled:opacity-30`}
                  >
                    Result
                  </button>
                </div>
              )}

              <button
                onClick={runTest}
                disabled={
                  !standaloneSupported
                  || !sessionId
                  || !inputUrl
                  || busy
                }
                className="flex items-center gap-2 rounded border border-[#8ab4f8]/60 bg-[#35363a] px-3 py-1.5 text-xs font-bold text-[#e8eaed] hover:bg-[#3c4043] disabled:opacity-40"
              >
                {busy ? (
                  <Loader2
                    size={14}
                    className="animate-spin text-[#8ab4f8]"
                  />
                ) : (
                  <Play
                    size={14}
                    className="text-[#8ab4f8]"
                  />
                )}
                Run Test
                {dirty && (
                  <span className="rounded bg-[#8ab4f8] px-1.5 py-0.5 text-[8px] text-[#202124]">
                    DIRTY
                  </span>
                )}
              </button>
            </div>

            {adapterDescription && (
              <div className="shrink-0 border-b border-[#3c4043] bg-[#202124] px-3 py-1.5 text-[9px] text-[#fdd663]">
                Input adapter: {adapterDescription}
              </div>
            )}

            <div className="relative min-h-0 flex-1">
              {!standaloneSupported ? (
                <div className="absolute inset-0 flex items-center justify-center p-8 text-center">
                  <div className="max-w-lg">
                    <AlertTriangle
                      size={36}
                      className="mx-auto mb-3 text-[#fdd663]"
                    />
                    <div className="text-sm font-bold text-[#e8eaed]">
                      Guide available, standalone execution unavailable
                    </div>
                    <p className="mt-2 text-xs leading-5 text-[#9aa0a6]">
                      This operator needs a multi-input or unsupported input contract.
                      The current playground intentionally does not invent extra semantic inputs.
                    </p>
                  </div>
                </div>
              ) : activePreview === 'result' && resultUrl ? (
                <ZoomPanImageView
                  src={resultUrl}
                  alt={`${operator.label} standalone result`}
                  resetKey={`${operator.id}:result`}
                />
              ) : inputUrl ? (
                <ZoomPanImageView
                  src={inputUrl}
                  alt={`${operator.label} standalone input`}
                  resetKey={`${operator.id}:input`}
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center p-8 text-center">
                  <div>
                    <ImagePlus
                      size={40}
                      className="mx-auto mb-3 text-[#5f6368]"
                    />
                    <div className="text-sm font-bold text-[#bdc1c6]">
                      Load one image to test {operator.label} by itself
                    </div>
                    <p className="mt-2 text-xs text-[#80868b]">
                      The playground uses its own temporary Image LAB session and does not modify your current processing stack.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>

          <section className="overflow-y-auto border-l border-[#3c4043] bg-[#202124] p-3">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-black uppercase tracking-[0.18em] text-[#e8eaed]">
                  Parameters
                </div>
                <div className="mt-0.5 text-[9px] text-[#80868b]">
                  Changes are local until Run Test.
                </div>
              </div>

              <button
                onClick={resetParameters}
                title="Reset playground parameters"
                className="rounded border border-[#5f6368] bg-[#292a2d] p-1.5 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"
              >
                <RotateCcw size={13} />
              </button>
            </div>

            {input?.[1].type === 'binary_mask' && (
              <div className="mb-3 rounded-md border border-[#fdd663]/40 bg-[#4a3d16] p-2.5">
                <div className="text-[9px] font-black uppercase tracking-wider text-[#fdd663]">
                  Playground mask adapter
                </div>

                <p className="mt-1 text-[9px] leading-4 text-[#e8d58a]">
                  This filter consumes BinaryMask. The uploaded image is converted to grayscale and thresholded before the selected operator runs.
                </p>

                <div className="mt-2 grid grid-cols-[1fr_70px] gap-2">
                  <input
                    type="range"
                    min={0}
                    max={255}
                    step={1}
                    value={maskThreshold}
                    onChange={(event: any) => {
                      setMaskThreshold(Number(event.target.value));
                      setDirty(true);
                    }}
                    className="accent-[#fdd663]"
                  />

                  <input
                    type="number"
                    min={0}
                    max={255}
                    value={maskThreshold}
                    onChange={(event: any) => {
                      setMaskThreshold(Number(event.target.value));
                      setDirty(true);
                    }}
                    className="rounded border border-[#8a7130] bg-[#202124] px-2 py-1 text-xs text-[#e8eaed]"
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              {Object.entries(operator.parameters ?? {}).length === 0 ? (
                <div className="rounded-md border border-dashed border-[#5f6368] p-4 text-center text-xs text-[#9aa0a6]">
                  This operator has no adjustable parameters.
                </div>
              ) : (
                Object.entries(operator.parameters ?? {}).map(
                  ([name, spec]) => (
                    <ParameterEditor
                      key={name}
                      name={name}
                      spec={spec}
                      value={parameters[name]}
                      tip={guide.parameterTips[name]}
                      onChange={(value) => {
                        setParameters((current) => ({
                          ...current,
                          [name]: value,
                        }));
                        setDirty(true);
                      }}
                    />
                  ),
                )
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
