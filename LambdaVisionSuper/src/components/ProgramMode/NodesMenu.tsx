import { useState, useMemo, useEffect } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { useFlowStore, NodeManifest } from '../../Stores/FlowStore'; // Sửa lại đường dẫn import cho đúng với dự án của bạn

interface NodeContextMenuProps {
    isOpen: boolean;
    screenX: number;
    screenY: number;
    onSelectNode: (template: NodeManifest) => void;
}

export const NodeContextMenu = ({ isOpen, screenX, screenY, onSelectNode }: NodeContextMenuProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  
  // Rút dữ liệu trực tiếp từ SSOT FlowStore
  const { nodeCatalogueList, isLoading, errorMessage } = useFlowStore();

  // Reset thanh tìm kiếm mỗi khi mở menu
  useEffect(() => { 
    if (isOpen) setSearchQuery(''); 
  }, [isOpen]);

  // Lọc Node dựa trên searchQuery
  const filteredCatalog = useMemo(() => {
    return nodeCatalogueList.filter((item) =>
      item.label?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [searchQuery, nodeCatalogueList]);

  if (!isOpen) return null;

  return (
    <div 
      className="absolute z-50 flex flex-col w-64 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-lg shadow-xl overflow-hidden" 
      style={{ top: screenY, left: screenX }}
    >
      <div className="flex items-center gap-2 p-3 border-b border-slate-700/50 bg-slate-950/50">
        <Search size={16} className="text-slate-400" />
        <input 
          autoFocus 
          placeholder="Tìm node..." 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
          className="w-full bg-transparent text-sm text-white outline-none" 
        />
      </div>

      <div className="flex flex-col max-h-75 overflow-y-auto p-1 custom-scrollbar">
        {isLoading ? (
          <div className="p-4 flex items-center justify-center text-slate-400">
            <Loader2 className="animate-spin mr-2" size={16} /> Đang tải...
          </div>
        ) : errorMessage ? (
          <div className="p-4 text-center text-xs text-red-500">{errorMessage}</div>
        ) : filteredCatalog.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500">Không tìm thấy Node nào</div>
        ) : (
          filteredCatalog.map((item) => (
            <button 
              key={item.class} 
              onClick={() => onSelectNode(item)} 
              className="flex items-center gap-3 p-2 text-left rounded hover:bg-purple-600/30 transition-colors group"
            >
              <div className={`w-2 h-2 rounded-full ${item.color}`}></div>
              <div>
                <div className="text-sm font-bold text-slate-200 group-hover:text-white">{item.label}</div>
                <div className="text-[10px] text-slate-500 group-hover:text-purple-200">{item.description}</div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
};