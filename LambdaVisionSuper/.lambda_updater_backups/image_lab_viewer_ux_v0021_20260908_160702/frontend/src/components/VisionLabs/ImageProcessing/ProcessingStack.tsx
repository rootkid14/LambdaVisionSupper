import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
  GripVertical,
  RotateCcw,
  Trash2,
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
  const min = spec.min ?? 0;
  const max = spec.max ?? (spec.type === 'integer' ? 255 : 10);
  const step = spec.odd ? 2 : spec.type === 'integer' ? 1 : Math.max((max - min) / 200, 0.01);
  const normalized = Number.isFinite(Number(value)) ? Number(value) : Number(spec.default ?? min);

  return (
    <div className="grid grid-cols-[1fr_76px] gap-2 items-center">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={normalized}
        onChange={(event: any) => onChange(Number(event.target.value))}
        onPointerUp={(event: any) => onCommit(Number(event.currentTarget.value))}
        className="w-full accent-[#8ab4f8]"
      />
      <input
        type="number"
        min={min}
        max={max}
        step={step}
        value={normalized}
        onChange={(event: any) => onChange(Number(event.target.value))}
        onBlur={(event: any) => onCommit(Number(event.currentTarget.value))}
        className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
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
        <label className="text-[10px] font-bold uppercase tracking-wider text-[#bdc1c6]">{label}</label>
        {spec.description && <span className="text-[9px] text-[#80868b] truncate">{spec.description}</span>}
      </div>

      {(spec.type === 'integer' || spec.type === 'float') && (
        <NumericEditor spec={spec} value={value} onChange={onChange} onCommit={onCommit} />
      )}

      {spec.type === 'boolean' && (
        <button
          onClick={() => {
            const next = !Boolean(value);
            onChange(next);
            window.setTimeout(() => onCommit(next), 0);
          }}
          className={`w-full rounded border px-2 py-1.5 text-xs font-semibold ${
            value
              ? 'border-[#8ab4f8] bg-[#3c4043] text-[#e8eaed]'
              : 'border-[#5f6368] bg-[#202124] text-[#bdc1c6]'
          }`}
        >
          {value ? 'Enabled' : 'Disabled'}
        </button>
      )}

      {spec.type === 'enum' && (
        <select
          value={value ?? spec.default ?? ''}
          onChange={(event: any) => {
            const next = event.target.value;
            onChange(next);
            window.setTimeout(() => onCommit(next), 0);
          }}
          className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1.5 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
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
          className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1.5 text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8]"
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
    <aside className="w-[360px] min-w-[320px] border-l border-[#3c4043] bg-[#202124] flex flex-col overflow-hidden">
      <div className="p-3 border-b border-[#3c4043] bg-[#292a2d]">
        <div className="flex items-center justify-between">
          <div className="text-[11px] font-black tracking-[0.18em] text-[#e8eaed] uppercase">Processing Stack</div>
          <span className="rounded bg-[#3c4043] px-2 py-0.5 text-[9px] font-bold text-[#bdc1c6]">{stack.length}</span>
        </div>
        <p className="mt-1 text-[10px] text-[#9aa0a6]">Drag to reorder · Expand to tune · Eye = bypass where compatible.</p>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {stack.length === 0 && (
          <div className="rounded-md border border-dashed border-[#5f6368] p-5 text-center text-xs text-[#9aa0a6]">
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
              className={`rounded-md border overflow-hidden transition-colors ${
                instance.enabled
                  ? 'border-[#5f6368] bg-[#292a2d]'
                  : 'border-[#3c4043] bg-[#202124] opacity-60'
              }`}
            >
              <div className="flex items-center gap-1.5 px-2 py-2">
                <GripVertical size={14} className="text-[#80868b] cursor-grab" />
                <span className="w-6 h-6 rounded bg-[#3c4043] flex items-center justify-center text-[10px] font-black text-[#bdc1c6]">{index + 1}</span>
                <button
                  onClick={() => onToggleExpanded(instance.id)}
                  className="min-w-0 flex-1 flex items-center gap-1.5 text-left text-[#e8eaed]"
                >
                  {instance.expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <span className="truncate text-xs font-semibold">{manifest.label}</span>
                </button>
                <button onClick={() => onReset(instance.id)} title="Reset parameters" className="p-1 text-[#9aa0a6] hover:text-[#8ab4f8]"><RotateCcw size={13} /></button>
                <button
                  disabled={!canBypass}
                  onClick={() => canBypass && onToggleEnabled(instance.id)}
                  title={canBypass ? 'Enable / bypass' : 'Bypass unavailable when input/output types differ'}
                  className="p-1 text-[#9aa0a6] hover:text-white disabled:opacity-25 disabled:cursor-not-allowed"
                >
                  {instance.enabled ? <Eye size={13} /> : <EyeOff size={13} />}
                </button>
                <button onClick={() => onDelete(instance.id)} title="Delete" className="p-1 text-[#9aa0a6] hover:text-[#f28b82]"><Trash2 size={13} /></button>
              </div>

              {instance.expanded && (
                <div className="border-t border-[#3c4043] px-3 py-3 space-y-3 bg-[#202124]">
                  <div className="flex gap-1.5 text-[9px] text-[#80868b]">
                    {Object.entries(manifest.inputs ?? {}).map(([name, port]) => (
                      <span key={`i-${name}`} className="rounded bg-[#292a2d] px-1.5 py-0.5">IN {name}:{port.type}</span>
                    ))}
                    {Object.entries(manifest.outputs ?? {}).map(([name, port]) => (
                      <span key={`o-${name}`} className="rounded bg-[#292a2d] px-1.5 py-0.5">OUT {name}:{port.type}</span>
                    ))}
                  </div>

                  {Object.keys(manifest.parameters ?? {}).length === 0 ? (
                    <div className="text-[10px] text-[#80868b]">No adjustable parameters.</div>
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
