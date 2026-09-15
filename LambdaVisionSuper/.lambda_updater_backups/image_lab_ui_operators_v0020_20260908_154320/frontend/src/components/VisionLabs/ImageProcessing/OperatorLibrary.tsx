import { useMemo, useState } from 'react';
import { ChevronDown, ChevronRight, Search, Plus, LockKeyhole } from 'lucide-react';
import type { OperatorManifest } from './types';

interface Props {
  operators: OperatorManifest[];
  onAdd: (operator: OperatorManifest) => void;
  canAppend: (operator: OperatorManifest) => { ok: boolean; reason?: string };
}

export const OperatorLibrary = ({ operators, onAdd, canAppend }: Props) => {
  const [query, setQuery] = useState('');
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({});

  const grouped = useMemo(() => {
    const result = new Map<string, OperatorManifest[]>();
    operators
      .filter((operator) => {
        const haystack = `${operator.label} ${operator.category} ${operator.description ?? ''}`.toLowerCase();
        return haystack.includes(query.trim().toLowerCase());
      })
      .forEach((operator) => {
        const category = operator.category || 'Other';
        const items = result.get(category) ?? [];
        items.push(operator);
        result.set(category, items);
      });
    return Array.from(result.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [operators, query]);

  return (
    <aside className="w-[270px] min-w-[240px] border-r border-slate-800 bg-slate-950/80 flex flex-col overflow-hidden">
      <div className="p-3 border-b border-slate-800">
        <div className="text-[11px] font-black tracking-[0.22em] text-cyan-400 uppercase mb-2">Operator Library</div>
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-2.5 text-slate-500" />
          <input
            value={query}
            onChange={(event: any) => setQuery(event.target.value)}
            placeholder="Search algorithms..."
            className="w-full rounded-lg border border-slate-700 bg-slate-900/80 pl-8 pr-2 py-2 text-xs text-slate-100 outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {grouped.map(([category, items]) => {
          const isOpen = openCategories[category] ?? true;
          return (
            <div key={category} className="rounded-lg border border-slate-800/80 overflow-hidden bg-slate-900/30">
              <button
                onClick={() => setOpenCategories((current) => ({ ...current, [category]: !isOpen }))}
                className="w-full flex items-center justify-between px-3 py-2 text-left text-xs font-bold text-slate-200 hover:bg-slate-800/70"
              >
                <span className="flex items-center gap-2">
                  {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  {category}
                </span>
                <span className="text-[10px] text-slate-500">{items.length}</span>
              </button>

              {isOpen && (
                <div className="border-t border-slate-800">
                  {items.map((operator) => {
                    const compatibility = canAppend(operator);
                    return (
                      <button
                        key={operator.id}
                        onClick={() => compatibility.ok && onAdd(operator)}
                        title={compatibility.ok ? operator.description : compatibility.reason}
                        className={`w-full px-3 py-2.5 flex items-start gap-2 text-left border-b last:border-b-0 border-slate-800/60 transition-colors ${
                          compatibility.ok
                            ? 'hover:bg-cyan-500/10 text-slate-200'
                            : 'opacity-45 cursor-not-allowed text-slate-500'
                        }`}
                      >
                        <span className={`mt-0.5 flex items-center justify-center w-6 h-6 rounded-md ${compatibility.ok ? 'bg-cyan-500/10 text-cyan-400' : 'bg-slate-800 text-slate-600'}`}>
                          {compatibility.ok ? <Plus size={13} /> : <LockKeyhole size={12} />}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block text-xs font-semibold truncate">{operator.label}</span>
                          <span className="block text-[10px] text-slate-500 mt-0.5 line-clamp-2">
                            {compatibility.ok ? operator.description : compatibility.reason}
                          </span>
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
};
