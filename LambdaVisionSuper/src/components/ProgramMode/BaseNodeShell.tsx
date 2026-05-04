// components/Nodes/BaseNodeShell.tsx
import React from 'react';

interface BaseNodeShellProps {
  isError?: boolean;
  errorMessage?: string;
  selected?: boolean;
  headerColorClass: string;
  ringColorClass: string;
  title: string;
  icon?: React.ReactNode;
  headerRight?: React.ReactNode;
  children: React.ReactNode;
  minW?: string;
}

export const BaseNodeShell = ({
  isError, errorMessage, selected, headerColorClass, ringColorClass, title, icon, headerRight, children, minW = "min-w-[240px]"
}: BaseNodeShellProps) => {
  return (
    <div className={`
      flex flex-col ${minW} max-w-[320px] bg-slate-200 rounded-md font-sans text-slate-900
      shadow-lg transition-all relative
      ${isError ? 'border-2 border-red-500 ring-4 ring-red-500/20' : 'border border-slate-400'}
      ${selected && !isError ? `ring-2 ${ringColorClass}` : ''}
    `}>
      {/* HEADER */}
      <div className={`${isError ? 'bg-red-600' : headerColorClass} rounded-t-md px-3 py-2 border-b border-slate-800 transition-colors flex items-center justify-between`}>
        <div className="flex items-center gap-2 text-white font-bold tracking-wide text-sm flex-1 justify-center">
          {icon} <span>{title}</span>
        </div>
        {headerRight && <div>{headerRight}</div>}
      </div>

      {/* ERROR MESSAGE (Nếu có, gộp ngay dưới header) */}
      {isError && errorMessage && (
        <div className="bg-red-600 px-3 pb-2 text-[10px] font-bold text-red-100 uppercase break-words leading-tight text-center">
          ⚠️ {errorMessage}
        </div>
      )}

      {/* BODY (Children) */}
      <div className="flex flex-col gap-2 p-3">
        {children}
      </div>
    </div>
  );
};