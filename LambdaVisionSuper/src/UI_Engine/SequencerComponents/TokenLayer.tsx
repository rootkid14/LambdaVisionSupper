import { useViewport } from '@xyflow/react';
import { useSequencerStore } from '../UIEngineStores/SequencerStores';

export const TokenLayer = () => {
  const tokens = useSequencerStore(state => state.run_time_token_list);
  const { x, y, zoom } = useViewport();

  return (
    <div className="absolute inset-0 pointer-events-none z-50 overflow-hidden">
      {Object.entries(tokens).map(([id, token]) => {
        // Tính toán tọa độ thực tế trên màn hình dựa vào transform của React Flow
        const screenX = token.x * zoom + x;
        const screenY = token.y * zoom + y;

        return (
          <div
            key={id}
            className={`absolute w-4 h-4 rounded-full shadow-[0_0_15px_currentColor] transition-all duration-300 ease-out flex items-center justify-center ${token.color} text-${token.color.split('-')[1]}-400`}
            style={{
              transform: `translate(${screenX}px, ${screenY}px) scale(${zoom})`,
              transformOrigin: 'center center',
            }}
          >
            {/* Đốm sáng lõi của Token */}
            <div className="w-2 h-2 bg-white rounded-full animate-pulse" />

            {/* ========================================================= */}
            {/* TÍNH NĂNG MỚI: HOLOGRAPHIC LABELS (HIỂN THỊ NHÃN DÁN ĐỘNG) */}
            {/* ========================================================= */}
            {token.labels && token.labels.length > 0 && (
              <div className="absolute bottom-6 flex flex-col items-center gap-0.5 whitespace-nowrap">
                {token.labels.map((label, idx) => (
                  <span 
                    key={idx} 
                    className="px-1.5 py-[2px] bg-[#171717]/80 backdrop-blur-md border border-[#3c4043] rounded text-[6px] font-bold text-[#e8eaed] font-mono shadow-sm tracking-wider uppercase"
                    // Hiệu ứng viền phát sáng nhẹ trùng màu với token
                    style={{ borderColor: 'currentColor', opacity: 0.9 }}
                  >
                    {label}
                  </span>
                ))}
              </div>
            )}
            
          </div>
        );
      })}
    </div>
  );
};