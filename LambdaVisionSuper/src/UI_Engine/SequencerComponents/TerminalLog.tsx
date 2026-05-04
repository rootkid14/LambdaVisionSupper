import { useEffect, useRef } from 'react';
import { Terminal, Trash2 } from 'lucide-react';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';

export const TerminalLog = () => {
  const logs = useSequencerStore(state => state.compiler_log_messages);
  const cleanUpCompilerLog = useSequencerStore(state => state.cleanUpCompilerLog);
  const endOfLogRef = useRef<HTMLDivElement>(null);

  // Tự động cuộn xuống dòng log mới nhất
  useEffect(() => {
    endOfLogRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    // 1. Tăng font chữ tổng thể từ text-[11px] lên text-sm (14px)
    <div className="h-48 bg-[#1e1e1e] border-t border-[#3c4043] flex flex-col shrink-0 font-mono text-sm">
      
      {/* 2. Tăng nhẹ padding py-1.5 -> py-2 để Header thoáng hơn */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#252526] border-b border-[#3c4043] shrink-0">
        
        {/* 3. Tăng cỡ chữ tiêu đề từ text-[10px] lên text-xs (12px), tăng icon Terminal lên 16 */}
        <div className="flex items-center gap-2 text-[#9aa0a6] font-bold uppercase tracking-wider text-xs">
          <Terminal size={16} className="text-[#8ab4f8]" /> Log Terminal
        </div>
        
        <button 
          onClick={cleanUpCompilerLog}
          className="p-1 hover:bg-[#3c4043] rounded text-[#9aa0a6] hover:text-[#f28b82] transition-colors"
          title="Clear Terminal"
        >
          <Trash2 size={18} />
        </button>
      </div>
      
      {/* 4. Tăng padding p-3 -> p-4 để nội dung Log không bị dính vào viền */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar text-[#cccccc] leading-relaxed">
        {logs.length === 0 ? (
          <span className="text-[#5f6368] italic">No logs to display. Waiting for compilation...</span>
        ) : (
          logs.map((log, idx) => (
            // 5. Tăng margin-bottom từ mb-1 lên mb-1.5 để các dòng log tách bạch dễ đọc hơn
            <div key={idx} className={`mb-1.5 ${log.includes('Error') || log.includes('LỖI') ? 'text-[#f28b82]' : log.includes('Warning') ? 'text-[#fcd663]' : log.includes('SUCCESS') ? 'text-[#81c995]' : ''}`}>
              {/* 6. Tăng margin-right của timestamp từ mr-2 lên mr-3 */}
              <span className="text-[#5f6368] mr-3">[{new Date().toLocaleTimeString()}]</span>
              {log}
            </div>
          ))
        )}
        <div ref={endOfLogRef} />
      </div>
    </div>
  );
};