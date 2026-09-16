import { useMemo, useState } from 'react';
import { RotateCcw, X } from 'lucide-react';
import type { SamplingOperatorManifest, SamplingParameterManifest } from './types';
import { SyntheticGuideVisual } from './SamplingVisuals';

const defaultsFor = (operator: SamplingOperatorManifest) => Object.fromEntries(
  Object.entries(operator.parameters ?? {}).map(([name, spec]) => [name, spec.default]),
);

const ParamEditor = ({
  name,
  spec,
  value,
  onChange,
}: {
  name: string;
  spec: SamplingParameterManifest;
  value: any;
  onChange: (value: any) => void;
}) => {
  const label = spec.label || name.replaceAll('_', ' ');
  if (spec.type === 'boolean') {
    return (
      <div className="rounded border border-[#3c4043] bg-[#292a2d] p-2">
        <div className="mb-1 text-[10px] font-black uppercase text-[#e8eaed]">{label}</div>
        <button onClick={() => onChange(!Boolean(value))} className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-xs text-[#bdc1c6]">{value ? 'Enabled' : 'Disabled'}</button>
      </div>
    );
  }
  if (spec.type === 'enum') {
    const choices = spec.choices ?? [];
    let selected = choices.findIndex((choice) => Object.is(choice, value));
    if (selected < 0) selected = choices.findIndex((choice) => String(choice) === String(value));
    return (
      <div className="rounded border border-[#3c4043] bg-[#292a2d] p-2">
        <div className="mb-1 text-[10px] font-black uppercase text-[#e8eaed]">{label}</div>
        <select value={selected} onChange={(e) => onChange(choices[Number(e.target.value)])} className="w-full rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-xs text-[#e8eaed]">
          {choices.map((choice, i) => <option key={`${i}:${String(choice)}`} value={i}>{String(choice)}</option>)}
        </select>
      </div>
    );
  }
  if (spec.type === 'integer' || spec.type === 'float') {
    const min = spec.min ?? 0;
    const max = spec.max ?? (spec.type === 'integer' ? 255 : 1);
    const step = spec.odd ? 2 : spec.type === 'integer' ? 1 : Math.max(0.001, (Number(max) - Number(min)) / 200);
    return (
      <div className="rounded border border-[#3c4043] bg-[#292a2d] p-2">
        <div className="mb-1 flex items-center justify-between gap-2"><span className="text-[10px] font-black uppercase text-[#e8eaed]">{label}</span><span className="font-mono text-[9px] text-[#8ab4f8]">{String(value)}</span></div>
        <div className="grid grid-cols-[1fr_80px] gap-2">
          <input type="range" min={min ?? undefined} max={max ?? undefined} step={step} value={Number(value)} onChange={(e) => onChange(Number(e.target.value))} className="accent-[#8ab4f8]" />
          <input type="number" min={min ?? undefined} max={max ?? undefined} step={step} value={Number(value)} onChange={(e) => onChange(Number(e.target.value))} className="rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-xs text-[#e8eaed]" />
        </div>
        {spec.description && <div className="mt-1 text-[9px] leading-4 text-[#9aa0a6]">{spec.description}</div>}
      </div>
    );
  }
  return null;
};

export const SamplingGuideModal = ({ operator, onClose }: { operator: SamplingOperatorManifest; onClose: () => void }) => {
  const initial = useMemo(() => defaultsFor(operator), [operator.id]);
  const [params, setParams] = useState<Record<string, any>>(initial);
  const guide = operator.guide ?? {};
  return (
    <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/75 p-4">
      <div className="flex h-[90vh] w-[96vw] max-w-[1700px] flex-col overflow-hidden rounded-xl border border-[#5f6368] bg-[#202124] shadow-2xl">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-[#3c4043] bg-[#292a2d] px-4">
          <div className="min-w-0 flex-1"><div className="text-[10px] font-black tracking-[0.18em] text-[#8ab4f8]">OPERATOR GUIDE / INTERACTIVE MODEL</div><div className="truncate text-sm font-bold text-[#e8eaed]">{operator.label} <span className="font-normal text-[#9aa0a6]">· {operator.category}</span></div></div>
          <button onClick={onClose} className="rounded p-2 text-[#9aa0a6] hover:bg-[#3c4043] hover:text-white"><X size={17}/></button>
        </header>
        <div className="grid min-h-0 flex-1 grid-cols-[340px_minmax(0,1fr)_360px]">
          <section className="overflow-y-auto border-r border-[#3c4043] bg-[#292a2d] p-4">
            <div className="text-[10px] font-black uppercase tracking-wider text-[#8ab4f8]">What it does</div><p className="mt-2 text-xs leading-5 text-[#e8eaed]">{guide.overview || operator.description}</p>
            <div className="mt-5 text-[10px] font-black uppercase tracking-wider text-[#bdc1c6]">How it works</div><p className="mt-2 text-xs leading-5 text-[#bdc1c6]">{guide.how_it_works || operator.description}</p>
            <div className="mt-5 text-[10px] font-black uppercase tracking-wider text-[#bdc1c6]">Tuning tips</div><ul className="mt-2 space-y-2 text-[11px] leading-4 text-[#bdc1c6]">{(guide.tips ?? []).map((tip) => <li key={tip} className="flex gap-2"><span className="text-[#8ab4f8]">•</span>{tip}</li>)}</ul>
            <div className="mt-5 text-[10px] font-black uppercase tracking-wider text-[#bdc1c6]">Notes</div><ul className="mt-2 space-y-2 text-[11px] leading-4 text-[#9aa0a6]">{(guide.notes ?? []).map((note) => <li key={note} className="flex gap-2"><span>•</span>{note}</li>)}</ul>
            <div className="mt-5 rounded border border-[#3c4043] bg-[#202124] p-3 text-[9px] font-mono text-[#9aa0a6]"><div>IN  {Object.entries(operator.inputs).map(([name, p]) => `${name}:${p.type}`).join(', ')}</div><div className="mt-1">OUT {Object.entries(operator.outputs).map(([name, p]) => `${name}:${p.type}`).join(', ')}</div></div>
          </section>
          <section className="min-w-0 bg-[#171717] p-4"><SyntheticGuideVisual visualization={guide.visualization} workspace={operator.workspace} params={params} /></section>
          <section className="overflow-y-auto border-l border-[#3c4043] bg-[#202124] p-3">
            <div className="mb-3 flex items-center justify-between"><div><div className="text-[10px] font-black uppercase tracking-wider text-[#e8eaed]">Interactive parameters</div><div className="text-[9px] text-[#80868b]">These controls affect only the guide model.</div></div><button onClick={() => setParams(initial)} className="rounded border border-[#5f6368] bg-[#292a2d] p-1.5 text-[#9aa0a6] hover:text-white"><RotateCcw size={13}/></button></div>
            <div className="space-y-2">{Object.entries(operator.parameters).length ? Object.entries(operator.parameters).map(([name, spec]) => <ParamEditor key={name} name={name} spec={spec} value={params[name]} onChange={(value) => setParams((current) => ({ ...current, [name]: value }))} />) : <div className="rounded border border-dashed border-[#5f6368] p-4 text-center text-xs text-[#9aa0a6]">No adjustable parameters.</div>}</div>
          </section>
        </div>
      </div>
    </div>
  );
};
