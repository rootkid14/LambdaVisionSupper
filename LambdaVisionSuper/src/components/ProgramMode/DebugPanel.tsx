// components/DebugPanel.tsx
import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Save, FolderOpen, Bug, ChevronRight, Upload, Eye, X, ArrowLeft, RefreshCcw } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore'; 
import { ImageProcessing } from '../../utils/imageUtils'; 

export const DebugPanel = () => {
  const store = useFlowStore();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // 1. TÌM NODE DATA IN (ReceivePayloadNode)
  const receiveNode = store.nodes.find(n => n.data?.className === 'ReceivePayloadNode');
  const inputConfigs = receiveNode?.data?.outputs || [];

  const isBase64Image = (val: any) => typeof val === 'string' && val.startsWith('data:image/');

  // 2. CÁC HÀM XỬ LÝ SỰ KIỆN
  const handleRun = async () => {
    if ((inputConfigs as any).length === 0 && !store.nodes.find(n => n.data?.className === 'SendResponseNode')) {
        alert("Đồ thị cần có ít nhất Data In (Receive Payload) hoặc Data Out (Send Response) để chạy test.");
        return;
    }
    setIsTesting(true);
    await store.preflight_run();
    setIsTesting(false);
  };

  const handleSave = () => {
    store.saveGraphtoFile(`lambda_ui_graph_${Date.now()}.json`);
  };

  const handleLoad = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = JSON.parse(event.target?.result as string);
        store.loadGraphfromFile(content);
      } catch (err) { alert("Lỗi đọc file JSON"); }
      finally { if (fileInputRef.current) fileInputRef.current.value = ''; }
    };
    reader.readAsText(file);
  };

  const updateInput = (id: string, val: any) => store.updateInputSimulatorData(id, val);

  const handleImageUpload = async (id: string, file: File) => {
    try {
       const optimized = await ImageProcessing.processImageForUpload(file, 1920, 0.8, 'image/jpeg');
       updateInput(id, optimized);
    } catch { alert("Lỗi xử lý ảnh"); }
  };

  const simulatorData = store.input_simulator_data || {};
  const inspectorData = store.result_inspector_data;

  return (
    <>
      <div className="relative w-[400px] h-full bg-[#28292c] border-r border-[#3c4043] shadow-[15px_0_40px_rgba(0,0,0,0.3)] flex flex-col shrink-0 z-40 font-sans">
        
        {/* HEADER & GLOBAL BUTTONS (EXIT & REFRESH) */}
        <div className="p-4 border-b border-[#3c4043] flex items-center justify-between bg-[#303134]">
          <div className="flex items-center gap-3">
            {/* NÚT EXIT VỀ FLEET */}
            <button 
              onClick={() => navigate('/fleet')} 
              className="p-1.5 bg-[#202124] hover:bg-[#3c4043] text-[#9aa0a6] hover:text-[#e8eaed] rounded-md border border-[#3c4043] transition-colors shadow-sm"
              title="Exit to Fleet Dashboard"
            >
              <ArrowLeft size={16} />
            </button>
            <div className="flex items-center gap-2">
              <Bug size={18} className="text-[#8ab4f8]" />
              <h2 className="font-bold text-[#e8eaed] tracking-wide text-sm">COMMAND & DEBUG</h2>
            </div>
          </div>
          
          {/* NÚT REFRESH CATALOGUE */}
          <button 
            onClick={() => store.loadNodeCatalogue()} 
            disabled={store.isLoading}
            className="p-1.5 bg-[#202124] hover:bg-[#81c995]/20 text-[#9aa0a6] hover:text-[#81c995] rounded-md border border-[#3c4043] hover:border-[#81c995]/50 transition-colors disabled:opacity-50 shadow-sm"
            title="Refresh Node Catalogue"
          >
            <RefreshCcw size={16} className={store.isLoading ? "animate-spin text-[#81c995]" : ""} />
          </button>
        </div>

        <div className="p-4 border-b border-[#3c4043] bg-[#28292c] grid grid-cols-3 gap-2">
          <button onClick={handleRun} disabled={isTesting} className="flex flex-col items-center p-2 bg-[#81c995]/10 hover:bg-[#81c995]/20 border border-[#81c995]/30 hover:border-[#81c995]/50 rounded-lg text-[#81c995] transition-all group disabled:opacity-50">
            <Play size={18} className={`mb-1 ${isTesting ? 'animate-ping' : 'group-hover:scale-110 transition-transform'}`} /> 
            <span className="text-[10px] font-bold tracking-wider">{isTesting ? 'RUNNING...' : 'COMPILE/TEST'}</span>
          </button>
          <button onClick={handleSave} className="flex flex-col items-center p-2 bg-[#8ab4f8]/10 hover:bg-[#8ab4f8]/20 border border-[#8ab4f8]/30 hover:border-[#8ab4f8]/50 rounded-lg text-[#8ab4f8] transition-all group">
            <Save size={18} className="mb-1 group-hover:scale-110 transition-transform" /> 
            <span className="text-[10px] font-bold tracking-wider">SAVE</span>
          </button>
          <button onClick={() => fileInputRef.current?.click()} className="flex flex-col items-center p-2 bg-[#fcd663]/10 hover:bg-[#fcd663]/20 border border-[#fcd663]/30 hover:border-[#fcd663]/50 rounded-lg text-[#fcd663] transition-all group">
            <FolderOpen size={18} className="mb-1 group-hover:scale-110 transition-transform" /> 
            <span className="text-[10px] font-bold tracking-wider">LOAD</span>
          </button>
          <input type="file" ref={fileInputRef} className="hidden" accept=".json" onChange={handleLoad} />
        </div>

        {/* KHU VỰC CUỘN ĐƯỢC */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar bg-[#202124]">
          
          {/* PHẦN 2: INPUT SIMULATOR */}
          <section>
            <h3 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest mb-4 flex items-center gap-2">
              <ChevronRight size={14}/> Input Simulator
            </h3>
            <div className="space-y-3">
              {(inputConfigs as any).length === 0 ? (
                <div className="p-4 border border-dashed border-[#3c4043] rounded-lg text-center bg-[#171717]">
                  <p className="text-xs text-[#5f6368] font-medium">Use Node Data In for debugging</p>
                </div>
              ) : (inputConfigs as any).map((cfg: any) => (
                <div key={cfg.id} className="bg-[#28292c] p-3 rounded-lg border border-[#3c4043] transition-colors hover:border-[#5f6368]">
                  
                  {/* Image Input */}
                  {cfg.dataType === 'numpy_array' || cfg.dataType === 'image' ? (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-[#e8eaed]">{cfg.label} <span className="text-[#5f6368] font-mono font-normal">({cfg.dataType})</span></span>
                        <label className="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 bg-[#3c4043] hover:bg-[#5f6368] border border-[#5f6368] rounded text-[10px] font-bold uppercase text-[#e8eaed] transition-colors shadow-sm">
                          <Upload size={14} className="text-[#8ab4f8]"/> Upload
                          <input type="file" onChange={(e) => e.target.files && handleImageUpload(cfg.id, e.target.files[0])} className="hidden" />
                        </label>
                      </div>
                      {simulatorData[cfg.id] && simulatorData[cfg.id] instanceof File && (
                        <div className="relative mt-3 group w-24 h-24 rounded border border-[#3c4043] overflow-hidden bg-[#171717] shadow-inner">
                          <img src={URL.createObjectURL(simulatorData[cfg.id])} className="w-full h-full object-cover" alt="preview" />
                          <div onClick={() => setEnlargedImage(URL.createObjectURL(simulatorData[cfg.id]))} className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity backdrop-blur-sm">
                            <Eye size={20} className="text-white"/>
                          </div>
                        </div>
                      )}
                    </div>

                  // Boolean Input
                  ) : cfg.dataType === 'boolean' ? (
                    <label className="flex items-center justify-between cursor-pointer group">
                      <span className="text-xs font-bold text-[#e8eaed] group-hover:text-[#8ab4f8] transition-colors">{cfg.label}</span>
                      <div className="relative flex items-center">
                        <input type="checkbox" className="sr-only peer" checked={simulatorData[cfg.id] || false} onChange={(e) => updateInput(cfg.id, e.target.checked)} />
                        <div className="w-9 h-5 bg-[#3c4043] rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-[#8ab4f8] after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#e8eaed] after:rounded-full after:h-4 after:w-4 after:transition-all after:shadow-sm box-border"></div>
                      </div>
                    </label>

                  // Text/Number Input
                  ) : (
                    <div>
                      <span className="text-xs font-bold text-[#e8eaed] block mb-1.5">{cfg.label}</span>
                      <input 
                        type={cfg.dataType === 'number' ? 'number' : 'text'} 
                        // FIX 1: Thêm step="any" để cho phép nhập số thập phân (float)
                        step="any"
                        className="w-full bg-[#171717] border border-[#3c4043] p-2 rounded text-xs text-[#e8eaed] outline-none focus:border-[#8ab4f8] transition-all shadow-inner font-mono"
                        
                        // FIX 2: Sử dụng toán tử ?? (nullish coalescing) thay vì || 
                        // Để số 0 vẫn được hiển thị thay vì biến thành chuỗi rỗng
                        value={simulatorData[cfg.id] ?? ''}
                        
                        onChange={(e) => {
                          const rawValue = e.target.value;
                          if (cfg.dataType === 'number') {
                            // FIX 3: Xử lý khi xóa trắng ô nhập để không bị biến thành số 0 ngay lập tức
                            updateInput(cfg.id, rawValue === '' ? '' : Number(rawValue));
                          } else {
                            updateInput(cfg.id, rawValue);
                          }
                        }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* PHẦN 3: RESULT INSPECTOR */}
          <section className="border-t border-[#3c4043] pt-6">
            <h3 className="text-xs font-bold text-[#9aa0a6] uppercase tracking-widest mb-4 flex items-center gap-2">
              <ChevronRight size={14}/> Result Inspector
            </h3>
            
            {isTesting ? (
              <div className="flex flex-col items-center justify-center p-8 text-[#8ab4f8] italic text-sm bg-[#8ab4f8]/5 rounded-lg border border-[#8ab4f8]/20">
                <Play className="animate-ping mb-3 opacity-50" size={24}/> Running Logic...
              </div>
            ) : !inspectorData || Object.keys(inspectorData).length === 0 ? (
              <div className="p-4 border border-dashed border-[#3c4043] rounded-lg text-center bg-[#171717]">
                <p className="text-xs text-[#5f6368] font-medium">Use Node Data Out for debugging</p>
              </div>
            ) : (
              <div className="bg-[#28292c] p-4 rounded-lg border border-[#3c4043] shadow-inner space-y-4">
                {inspectorData.success ? (
                  inspectorData.data && typeof inspectorData.data === 'object' ? (
                    Object.entries(inspectorData.data).map(([key, value]) => (
                      <div key={key} className="border-b border-[#3c4043] pb-3 last:border-0 last:pb-0">
                        <span className="text-[10px] text-[#81c995] uppercase font-bold block mb-1.5 tracking-wider">Output: {key}</span>
                        {isBase64Image(value) ? (
                          <div className="relative mt-2 group w-24 h-24 rounded border border-[#3c4043] overflow-hidden bg-black shadow-inner">
                            <img src={value as string} alt={key} className="w-full h-full object-cover" />
                            <div onClick={() => setEnlargedImage(value as string)} className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity backdrop-blur-sm">
                              <Eye size={20} className="text-white"/>
                            </div>
                          </div>
                        ) : (
                          <pre className="text-[#9aa0a6] font-mono text-xs whitespace-pre-wrap break-all bg-[#171717] p-2 rounded border border-[#3c4043]">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </pre>
                        )}
                      </div>
                    ))
                  ) : (
                    <pre className="text-[#9aa0a6] font-mono text-xs whitespace-pre-wrap break-all bg-[#171717] p-2 rounded border border-[#3c4043]">{JSON.stringify(inspectorData, null, 2)}</pre>
                  )
                ) : (
                  <div className="text-[#f28b82]">
                    <p className="font-bold flex items-center gap-2 text-sm mb-2"><X size={16}/> Lỗi tại: {inspectorData.failed_node_id || "Hệ thống"}</p>
                    <p className="text-xs bg-[#f28b82]/10 p-3 rounded border border-[#f28b82]/30 leading-relaxed font-mono">{inspectorData.error_message || "Đã xảy ra lỗi không xác định."}</p>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </div>

      {/* MODAL XEM ẢNH */}
      {enlargedImage && (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center p-8">
          <div className="relative max-w-full max-h-full">
            <button onClick={() => setEnlargedImage(null)} className="absolute -top-12 right-0 p-2 bg-[#202124] hover:bg-[#f28b82] text-[#9aa0a6] hover:text-[#202124] rounded-full transition-colors border border-[#3c4043] hover:border-transparent"><X size={24} /></button>
            <img src={enlargedImage} alt="Enlarged" className="max-w-[90vw] max-h-[85vh] object-contain rounded-lg shadow-2xl border border-[#3c4043] bg-black" />
          </div>
        </div>
      )}
    </>
  );
};