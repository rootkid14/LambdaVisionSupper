import { useDBEngineStore } from '../../Stores/DatabaseEngineStore';
import { Image as ImageIcon } from 'lucide-react';

export const DBResultGrid = () => {
    const { queryResults, schemaConfig, openImageViewModal, isLoading } = useDBEngineStore();
    const visibleColumns = Object.values(schemaConfig).filter(col => col.isVisible);

    if (isLoading) {
        return <div className="flex-1 flex items-center justify-center text-[#5f6368] font-bold bg-[#171717]">Lấy dữ liệu từ Database...</div>;
    }

    if (queryResults.length === 0) {
        return <div className="flex-1 flex items-center justify-center text-[#5f6368] italic bg-[#171717]">No results to display. Execute a query.</div>;
    }

    return (
        <div className="flex-1 bg-[#171717] p-6 overflow-y-auto custom-scrollbar">
            {/* 1. LAYOUT DẸT (FLEX COLUMN LIST) */}
            <div className="flex flex-col gap-3">
                {queryResults.map((row, index) => (
                    <div key={index} className="bg-[#28292c] border border-[#3c4043] rounded-lg overflow-hidden flex flex-row items-stretch shadow-md hover:border-[#5f6368] transition-colors">
                        
                        {/* Cột đánh số ID dọc */}
                        <div className="bg-[#303134] w-16 flex items-center justify-center border-r border-[#3c4043] shrink-0">
                            <span className="text-[10px] font-bold text-[#8ab4f8] whitespace-nowrap">
                                REC #{index + 1}
                            </span>
                        </div>
                        
                        {/* 2. CHỐNG OUT OF BOUND: Cuộn ngang bên trong nếu có quá nhiều cột */}
                        <div className="flex-1 p-3 flex flex-row flex-nowrap gap-6 overflow-x-auto custom-scrollbar items-center">
                            {visibleColumns.map(col => {
                                const val = row[col.originalName];
                                return (
                                    <div key={col.originalName} className="flex flex-col gap-1 min-w-[120px] shrink-0 border-l border-[#3c4043]/50 pl-4 first:border-0 first:pl-0">
                                        <span className="text-[9px] font-bold text-[#9aa0a6] uppercase tracking-wider">{col.displayName}</span>
                                        
                                        {/* Xử lý ảnh vs Text */}
                                        {col.isImage ? (
                                            <button 
                                                onClick={() => openImageViewModal(val)}
                                                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#fcd663]/10 text-[#fcd663] rounded border border-[#fcd663]/30 hover:bg-[#fcd663]/20 text-[10px] font-bold transition-colors w-max"
                                            >
                                                <ImageIcon size={12}/> XEM ẢNH
                                            </button>
                                        ) : (
                                            <span className="text-xs font-mono text-[#e8eaed] truncate max-w-[200px]" title={val !== null ? String(val) : 'null'}>
                                                {val !== null ? String(val) : 'null'}
                                            </span>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};