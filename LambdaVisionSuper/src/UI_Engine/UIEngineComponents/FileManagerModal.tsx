import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Search, FileJson, Trash2, Download, UploadCloud, FolderOpen } from 'lucide-react';

interface FileManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  folder: 'projects' | 'models' | 'graphs' | 'plugins'; // Hỗ trợ đa mục đích
  mode: 'load' | 'save' | 'manage'; // load: Chọn file, save: Lưu file mới, manage: Chỉ quản lý
  onFileSelect?: (filename: string, fileContent?: any) => void;
  onSaveAs?: (filename: string) => void;
}

export function FileManagerModal({ isOpen, onClose, folder, mode, onFileSelect, onSaveAs }: FileManagerModalProps) {
  const [files, setFiles] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [saveName, setSaveName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Fetch danh sách file mỗi khi mở Modal
  useEffect(() => {
    if (isOpen) fetchFiles();
  }, [isOpen, folder]);

  const fetchFiles = async () => {
    setIsLoading(true);
    try {
      const res = await axios.get(`/resources/status`);
      setFiles(res.data.files || []);
    } catch (error) {
      console.error(`Lỗi tải danh sách ${folder}:`, error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (filename: string) => {
    if (!confirm(`Bạn có chắc muốn xóa file ${filename}?`)) return;
    try {
      await axios.delete(`/resources/delete/${folder}/${filename}`);
      fetchFiles(); // Refresh lại list
    } catch (error) {
      console.error("Lỗi khi xóa file:", error);
    }
  };

  const handleAction = async (filename: string) => {
    if (mode === 'load' && onFileSelect) {
      setIsLoading(true);
      try {
        // Nếu là project, gọi API để lấy thẳng nội dung JSON
        if (folder === 'projects') {
          // Bạn cần thêm endpoint get file content trên infra_api (nếu chưa có)
          // Hoặc API trả về URL file để fetch
          const res = await axios.get(`/resources/files/${folder}/${filename}/content`);
          onFileSelect(filename, res.data);
        } else {
          onFileSelect(filename); // Chỉ cần tên file (cho Model/Plugin)
        }
        onClose();
      } catch (error) {
        console.error("Lỗi khi đọc nội dung file:", error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  if (!isOpen) return null;

  const filteredFiles = files.filter(f => f.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 w-full max-w-4xl rounded-xl shadow-2xl border border-slate-700 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-800/50">
          <div className="flex items-center gap-3">
            <FolderOpen className="text-blue-400 w-6 h-6" />
            <h2 className="text-xl font-bold text-slate-100 uppercase tracking-wider">
              {mode === 'save' ? `Lưu vào ${folder}` : `Quản lý ${folder}`}
            </h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-full text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar (Search & Save Input) */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/20 flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder={`Tìm kiếm trong ${folder}...`}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          {mode === 'save' && (
            <div className="flex gap-2 flex-1">
              <input 
                type="text" 
                placeholder="Nhập tên file mới..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:border-green-500 focus:ring-1 focus:ring-green-500 outline-none transition"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
              />
              <button 
                onClick={() => onSaveAs?.(saveName)}
                disabled={!saveName}
                className="bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition"
              >
                <UploadCloud className="w-4 h-4" /> Lưu
              </button>
            </div>
          )}
        </div>

        {/* File List / Grid */}
        <div className="flex-1 p-6 overflow-y-auto max-h-[60vh] bg-slate-900/50">
          {isLoading ? (
            <div className="flex justify-center items-center h-40 text-slate-400">Đang tải dữ liệu...</div>
          ) : filteredFiles.length === 0 ? (
            <div className="flex flex-col justify-center items-center h-40 text-slate-500">
              <FileJson className="w-12 h-12 mb-3 opacity-20" />
              <p>Chưa có file nào trong thư mục này.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {filteredFiles.map((file) => (
                <div 
                  key={file}
                  className="group bg-slate-800 border border-slate-700 hover:border-blue-500 hover:bg-slate-800/80 rounded-xl p-4 flex flex-col gap-3 transition cursor-pointer"
                  onClick={() => mode === 'load' && handleAction(file)}
                >
                  <div className="flex items-start justify-between">
                    <div className="p-2 bg-slate-700 rounded-lg group-hover:bg-blue-500/20 group-hover:text-blue-400 text-slate-300 transition">
                      <FileJson className="w-6 h-6" />
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleDelete(file); }}
                      className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded-md transition opacity-0 group-hover:opacity-100"
                      title="Xóa file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <h3 className="text-sm font-medium text-slate-200 truncate" title={file}>{file}</h3>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}