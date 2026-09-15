import { useMemo, useState } from 'react';
import { ChevronDown, ChevronRight, LockKeyhole, Plus, Search } from 'lucide-react';
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
    <aside className="w-[292px] min-w-[250px] border-r border-[#3c4043] bg-[#202124] flex flex-col overflow-hidden">
      <div className="p-3 border-b border-[#3c4043] bg-[#292a2d]">
        <div className="flex items-center justify-between mb-2">
          <div className="text-[11px] font-black tracking-[0.18em] text-[#e8eaed] uppercase">Operator Library</div>
          <span className="rounded bg-[#3c4043] px-2 py-0.5 text-[9px] font-bold text-[#bdc1c6]">{operators.length}</span>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-2.5 text-[#9aa0a6]" />
          <input
            value={query}
            onChange={(event: any) => setQuery(event.target.value)}
            placeholder="Search algorithms..."
            className="w-full rounded-md border border-[#5f6368] bg-[#202124] pl-8 pr-2 py-2 text-xs text-[#e8eaed] outline-none placeholder:text-[#80868b] focus:border-[#8ab4f8]"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {grouped.map(([category, items]) => {
          const isOpen = openCategories[category] ?? true;
          return (
            <div key={category} className="rounded-md border border-[#3c4043] overflow-hidden bg-[#292a2d]">
              <button
                onClick={() => setOpenCategories((current) => ({ ...current, [category]: !isOpen }))}
                className="w-full flex items-center justify-between px-3 py-2 text-left text-xs font-semibold text-[#e8eaed] hover:bg-[#35363a]"
              >
                <span className="flex items-center gap-2">
                  {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  {category}
                </span>
                <span className="text-[10px] text-[#9aa0a6]">{items.length}</span>
              </button>

              {isOpen && (
                <div className="border-t border-[#3c4043]">
                  {items.map((operator) => {
                    const compatibility = canAppend(operator);
                    return (
                      <button
                        key={operator.id}
                        onClick={() => compatibility.ok && onAdd(operator)}
                        title={compatibility.ok ? operator.description : compatibility.reason}
                        className={`w-full px-3 py-2.5 flex items-start gap-2 text-left border-b last:border-b-0 border-[#3c4043] transition-colors ${
                          compatibility.ok
                            ? 'hover:bg-[#35363a] text-[#e8eaed]'
                            : 'opacity-45 cursor-not-allowed text-[#80868b]'
                        }`}
                      >
                        <span className={`mt-0.5 flex items-center justify-center w-6 h-6 rounded ${compatibility.ok ? 'bg-[#3c4043] text-[#8ab4f8]' : 'bg-[#35363a] text-[#80868b]'}`}>
                          {compatibility.ok ? <Plus size={13} /> : <LockKeyhole size={12} />}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block text-xs font-semibold truncate">{operator.label}</span>
                          <span className="block text-[10px] text-[#9aa0a6] mt-0.5 line-clamp-2">
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
