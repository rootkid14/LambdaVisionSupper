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
