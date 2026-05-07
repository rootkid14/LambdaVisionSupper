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

  // Kiểm tra xem chuỗi màu truyền vào có phải là mã HEX không
  const isHexColor = headerColorClass?.startsWith('#');
  
  // Nếu là lỗi -> Dùng màu đỏ. 
  // Nếu không lỗi và KHÔNG phải HEX -> Dùng Tailwind class.
  // Nếu là HEX -> Để trống class này.
  const headerClass = isError ? 'bg-red-600' : (isHexColor ? '' : headerColorClass);
  
  // Áp dụng Inline Style nếu nó là mã HEX
  const headerStyle = (!isError && isHexColor) ? { backgroundColor: headerColorClass } : {};

  return (
    <div className={`
      flex flex-col ${minW} max-w-[320px] bg-slate-200 rounded-md font-sans text-slate-900
      shadow-lg transition-all relative
      ${isError ? 'border-2 border-red-500 ring-4 ring-red-500/20' : 'border border-slate-400'}
      ${selected && !isError ? `ring-2 ${ringColorClass}` : ''}
    `}>
      {/* HEADER ÁP DỤNG CẢ CLASS LẪN INLINE STYLE */}
      <div 
        className={`${headerClass} rounded-t-md px-3 py-2 border-b border-slate-800 transition-colors flex items-center justify-between`}
        style={headerStyle}
      >
        <div className="flex items-center gap-2 text-white font-bold tracking-wide text-sm flex-1 justify-center">
          {icon} <span>{title}</span>
        </div>
        {headerRight && <div>{headerRight}</div>}
      </div>

      {isError && errorMessage && (
        <div className="bg-red-600 px-3 pb-2 text-[10px] font-bold text-red-100 uppercase break-words leading-tight text-center">
          ⚠️ {errorMessage}
        </div>
      )}

      <div className="flex flex-col gap-2 p-3">
        {children}
      </div>
    </div>
  );
};