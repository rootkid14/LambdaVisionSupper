import { useMemo, useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  CircleHelp,
  LockKeyhole,
  Plus,
  Search,
} from 'lucide-react';
import type { OperatorManifest } from './types';
import { FilterGuideModal } from './FilterGuideModal';

interface Props {
  operators: OperatorManifest[];
  onAdd: (operator: OperatorManifest) => void;
  canAppend: (operator: OperatorManifest) => { ok: boolean; reason?: string };
}

export const OperatorLibrary = ({
  operators,
  onAdd,
  canAppend,
}: Props) => {
  const [query, setQuery] = useState('');
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({});
  const [guideOperator, setGuideOperator] = useState<OperatorManifest | null>(null);

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
    <>
      <aside className="w-[292px] min-w-[250px] border-r border-[#3c4043] bg-[#202124] flex flex-col overflow-hidden">
        <div className="p-3 border-b border-[#3c4043] bg-[#292a2d]">
          <div className="flex items-center justify-between mb-2">
            <div className="text-[11px] font-black tracking-[0.18em] text-[#e8eaed] uppercase">
              Operator Library
            </div>

            <span className="rounded bg-[#3c4043] px-2 py-0.5 text-[9px] font-bold text-[#bdc1c6]">
              {operators.length}
            </span>
          </div>

          <div className="relative">
            <Search
              size={14}
              className="absolute left-2.5 top-2.5 text-[#9aa0a6]"
            />

            <input
              value={query}
              onChange={(event: any) => setQuery(event.target.value)}
              placeholder="Search filters..."
              className="w-full rounded-md border border-[#5f6368] bg-[#202124] py-2 pl-8 pr-2 text-xs text-[#e8eaed] outline-none placeholder:text-[#80868b] focus:border-[#8ab4f8]"
            />
          </div>

          <p className="mt-2 text-[9px] leading-4 text-[#80868b]">
            <CircleHelp size={10} className="mr-1 inline text-[#8ab4f8]" />
            Use the info button to learn and test a filter without changing the current stack.
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {grouped.map(([category, categoryOperators]) => {
            const isOpen = openCategories[category] ?? true;

            return (
              <div
                key={category}
                className="mb-2 overflow-hidden rounded-md border border-[#3c4043] bg-[#292a2d]"
              >
                <button
                  onClick={() => {
                    setOpenCategories((current) => ({
                      ...current,
                      [category]: !isOpen,
                    }));
                  }}
                  className="w-full flex items-center gap-2 px-2.5 py-2 text-left hover:bg-[#35363a]"
                >
                  {isOpen ? (
                    <ChevronDown size={13} className="text-[#9aa0a6]" />
                  ) : (
                    <ChevronRight size={13} className="text-[#9aa0a6]" />
                  )}

                  <span className="min-w-0 flex-1 truncate text-[10px] font-black uppercase tracking-wider text-[#bdc1c6]">
                    {category}
                  </span>

                  <span className="text-[9px] text-[#80868b]">
                    {categoryOperators.length}
                  </span>
                </button>

                {isOpen && (
                  <div className="border-t border-[#3c4043]">
                    {categoryOperators.map((operator) => {
                      const compatibility = canAppend(operator);

                      return (
                        <div
                          key={operator.id}
                          className="group border-b border-[#3c4043] last:border-b-0 px-2.5 py-2 hover:bg-[#35363a]"
                        >
                          <div className="flex items-start gap-2">
                            <div className="min-w-0 flex-1">
                              <div className="truncate text-[11px] font-semibold text-[#e8eaed]">
                                {operator.label}
                              </div>

                              {operator.description && (
                                <div className="mt-0.5 line-clamp-2 text-[9px] leading-4 text-[#9aa0a6]">
                                  {operator.description}
                                </div>
                              )}
                            </div>

                            <button
                              onClick={() => setGuideOperator(operator)}
                              title={`Guide / standalone test: ${operator.label}`}
                              className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded border border-[#5f6368] bg-[#202124] text-[#8ab4f8] hover:border-[#8ab4f8] hover:bg-[#3c4043]"
                            >
                              <CircleHelp size={14} />
                            </button>

                            <button
                              disabled={!compatibility.ok}
                              onClick={() => compatibility.ok && onAdd(operator)}
                              title={
                                compatibility.ok
                                  ? `Add ${operator.label}`
                                  : compatibility.reason
                              }
                              className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded border ${
                                compatibility.ok
                                  ? 'border-[#5f6368] bg-[#202124] text-[#8ab4f8] hover:border-[#8ab4f8] hover:bg-[#3c4043]'
                                  : 'border-[#3c4043] bg-[#202124] text-[#5f6368] cursor-not-allowed'
                              }`}
                            >
                              {compatibility.ok ? (
                                <Plus size={14} />
                              ) : (
                                <LockKeyhole size={13} />
                              )}
                            </button>
                          </div>

                          {!compatibility.ok && compatibility.reason && (
                            <div className="mt-1 text-[8px] leading-3 text-[#80868b]">
                              {compatibility.reason}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </aside>

      {guideOperator && (
        <FilterGuideModal
          operator={guideOperator}
          onClose={() => setGuideOperator(null)}
        />
      )}
    </>
  );
};
