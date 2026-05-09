// components/ProgramMode/DebugPanel.tsx
import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Save, FolderOpen, Bug, ChevronRight, Upload, Eye, X, ArrowLeft, RefreshCcw, Timer, CloudUpload } from 'lucide-react';
import { useFlowStore } from '../../Stores/FlowStore';
import { ImageProcessing } from '../../utils/imageUtils';
import { FlowCompiler } from '../../utils/FlowCompiler';
import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { FleetAPI } from '../../api/fleetApi';

export const DebugPanel = () => {

  const store = useFlowStore();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fleetStore = useFleetStore();
  const remoteGraphName = store.editing_remote_graph_name;

  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  // COMPONENT MỚI CHO GRAPH TIMEOUT
  const [graphTimeout, setGraphTimeout] = useState<number>(store.timeout || 30.0); 

  // TÌM NODE DATA IN (ReceivePayloadNode)
  const receiveNode = store.nodes.find(n => n.data?.className === 'ReceivePayloadNode');
  const inputConfigs = receiveNode?.data?.outputs || [];
  
  const isBase64Image = (val: any) => typeof val === 'string' && val.startsWith('data:image/');

  const handleRun = async () => {
    if ((inputConfigs as any).length === 0 && !store.nodes.find(n => n.data?.className === 'SendResponseNode')) {
        alert("Đồ thị cần có ít nhất Data In (Receive Payload) hoặc Data Out (Send Response) để chạy test.");
        return;
    }

    // ÉP FLOW COMPILER KIỂM TRA TRƯỚC KHI CHẠY
    const compileResult = FlowCompiler.compile(store.nodes, store.edges, graphTimeout);
    if (!compileResult.success) {
      for (const [nodeId, msg] of Object.entries(compileResult.errors || {})) {
        store.updateNodeData(nodeId, { errorMessage: msg });
      }
      alert("Đồ thị có lỗi (Thiếu kết nối bắt buộc hoặc Node lơ lửng). Vui lòng kiểm tra các Node bị viền đỏ!");
      return;
    }

    store.setGraphTimeout(graphTimeout); // Nạp timeout vào Store
    setIsTesting(true);
    await store.preflight_run();
    setIsTesting(false);
  };

  const handleSave = () => {
    // ÉP FLOW COMPILER KIỂM TRA TRƯỚC KHI LƯU
    const compileResult = FlowCompiler.compile(store.nodes, store.edges, graphTimeout);
    if (!compileResult.success) {
      for (const [nodeId, msg] of Object.entries(compileResult.errors || {})) {
        store.updateNodeData(nodeId, { errorMessage: msg });
      }
      console.log(compileResult)
      alert(`Warning, Logic Graph has Flaw at node. Be cautious! ${compileResult.toString()}`);
    }

    store.setGraphTimeout(graphTimeout);
    store.saveGraphtoFile(`lambda_ui_graph_${Date.now()}.json`);
  };

  const handleLoad = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = JSON.parse(event.target?.result as string);
        if (content.timeout) setGraphTimeout(content.timeout);
        store.loadGraphfromFile(content);
      } catch (err) { 
        alert("Lỗi đọc file JSON"); 
      } finally { 
        if (fileInputRef.current) fileInputRef.current.value = ''; 
      }
    };
    reader.readAsText(file);
  };

  const updateInput = (id: string, val: any) => store.updateInputSimulatorData(id, val);

  // NÂNG CẤP XỬ LÝ UPLOAD: Kiểm tra dataType để lưu đúng định dạng
  const handleImageUpload = async (id: string, file: File, dataType: string) => {
    try {
       const optimized = await ImageProcessing.processImageForUpload(file, 1920, 0.8, 'image/jpeg');
       
       if (dataType === 'base64') {
           // Chuyển file thành dạng chuỗi Base64
           const reader = new FileReader();
           reader.onloadend = () => {
               updateInput(id, reader.result); // reader.result là chuỗi data:image/jpeg;base64,...
           };
           reader.readAsDataURL(optimized as Blob);
       } else {
           // Nếu là numpy_array / image, giữ nguyên dạng File để gửi FormData (tuỳ kiến trúc BE)
           updateInput(id, optimized);
       }
    } catch { 
       alert("Lỗi xử lý ảnh"); 
    }
  };

  const simulatorData = store.input_simulator_data || {};
  const inspectorData = store.result_inspector_data;

  // HÀM HELPER: Lấy URL để preview ảnh bất kể nó là File hay Base64
  const getPreviewImageUrl = (val: any) => {
      if (val instanceof File) return URL.createObjectURL(val);
      if (isBase64Image(val)) return val;
      return null;
  };

  const handleCloudSave = async () => {
    let name = remoteGraphName;
    
    // Nếu chưa có tên, hỏi người dùng
    if (!name) {
        name = prompt("Nhập tên File Graph muốn lưu lên Cloud (Server):", `graph_${Date.now()}.json`);
        if (!name) return;
        if (!name.endsWith('.json')) name += '.json';
    }

    // ÉP FLOW COMPILER KIỂM TRA TRƯỚC KHI LƯU
    const compileResult = FlowCompiler.compile(store.nodes, store.edges, graphTimeout);
    if (!compileResult.success) {
      for (const [nodeId, msg] of Object.entries(compileResult.errors || {})) {
        store.updateNodeData(nodeId, { errorMessage: msg });
      }
      alert("Hệ thống phát hiện lỗi Nối dây / Cấu hình. Xin hãy sửa trước khi tải lên Cloud!");
      return;
    }

    // LẤY ID WORKER TỪ FLOW STORE (Không lấy từ Fleet Store để tránh bị null)
    const workerId = store.this_worker_infor?.selected_worker_id;
    if (!workerId) {
        alert("Lỗi: Không tìm thấy ID của Worker hiện tại để upload!");
        return;
    }

    // Tạo file từ Graph hiện tại
    const payload = { timeout: graphTimeout, nodes: store.nodes, edges: store.edges };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const file = new File([blob], name, { type: "application/json" });

    // Đẩy thẳng lên API (Bỏ qua FleetStore)
    try {
        let resp;
        if (workerId === "master_gateway") {
            resp = await FleetAPI.master_uploadFile(file, 'graph');
        } else {
            resp = await FleetAPI.proxy_uploadFile(workerId, file, 'graph');
        }
        
        // Kiểm tra Response thực tế từ Backend
        if (resp && resp.success) {
            store.setEditingRemoteGraphName(name); // Đánh dấu tên để lần sau overwrite tiếp
            alert(`Thành công! Đã ghi đè dữ liệu lên File [${name}] trên Server.`);
        } else {
            alert(`Lỗi từ Server: ${resp?.message || "Upload thất bại"}`);
        }
    } catch (e: any) {
        alert(`Lỗi khi kết nối đến Server: ${e?.response?.data?.detail || e.message}`);
    }
  };

  return (
    <>
      <div className="relative w-[400px] h-full bg-[#202124] border-r border-[#202124] flex flex-col z-10 shadow-2xl">
        {/* HEADER & GLOBAL BUTTONS (EXIT & REFRESH) */}
        <div className="p-4 border-b border-slate-700 bg-[#202124] flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* NÚT EXIT VỀ FLEET */}
            <button
              onClick={() => navigate('/fleet')}
              className="p-1.5 bg-[#202124] hover:bg-slate-700 rounded-md transition-colors border border-slate-700 text-slate-300"
              title="Exit to Fleet Dashboard"
            >
              <ArrowLeft size={16} />
            </button>
            <div className="flex items-center gap-2">
              <Bug size={18} className="text-blue-400" />
              <h2 className="font-bold text-slate-200 uppercase tracking-wider text-xs">Debug Panel</h2>
            </div>
          </div>
          {/* NÚT REFRESH CATALOGUE */}
          <button
            onClick={() => store.loadNodeCatalogue()}
            disabled={store.isLoading}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-md transition-colors border border-slate-700 text-slate-300"
            title="Refresh Node Catalogue"
          >
            <RefreshCcw size={16} className={store.isLoading ? "animate-spin text-blue-400" : ""} />
          </button>
        </div>

        <div className="p-4 border-b border-slate-700 bg-[#202124] flex justify-around">
          <button onClick={handleRun} disabled={isTesting} className="flex flex-col items-center p-2 hover:bg-slate-700 rounded transition-colors group">
            <Play size={18} className={`mb-1 text-emerald-400 ${isTesting ? 'animate-ping' : 'group-hover:scale-110 transition-transform'}`} />
            <span className="text-[10px] font-bold tracking-wider text-emerald-100">{isTesting ? 'RUNNING...' : 'TEST'}</span>
          </button>
          
          <button onClick={handleCloudSave} className="flex flex-col items-center p-2 hover:bg-[#202124] rounded transition-colors group" title={remoteGraphName ? `Ghi đè file: ${remoteGraphName}` : "Lưu mới lên Server"}>
            <CloudUpload size={18} className="mb-1 text-purple-400 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold tracking-wider text-purple-100">BE SAVE</span>
          </button>

          <button onClick={handleSave} className="flex flex-col items-center p-2 hover:bg-[#202124] rounded transition-colors group" title="Lưu về Máy tính">
            <Save size={18} className="mb-1 text-blue-400 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold tracking-wider text-blue-100">LOCAL</span>
          </button>
          
          <button onClick={() => fileInputRef.current?.click()} className="flex flex-col items-center p-2 hover:bg-[#202124] rounded transition-colors group" title="Mở File từ Máy tính">
            <FolderOpen size={18} className="mb-1 text-amber-400 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold tracking-wider text-amber-100">LOAD</span>
          </button>
          <input type="file" ref={fileInputRef} className="hidden" accept=".json" onChange={handleLoad} />
        </div>
        
        {/* GRAPH TIMEOUT CONFIG */}
        <div className="px-4 py-3 border-b border-slate-700 bg-[#202124] flex items-center justify-between">
           <div className="flex items-center gap-2 text-slate-300">
             <Timer size={14} className="text-amber-500" />
             <span className="text-xs font-bold uppercase tracking-wider">Graph Timeout (s)</span>
           </div>
           <input 
             type="number" 
             step="0.1"
             value={graphTimeout} 
             onChange={(e) => setGraphTimeout(Number(e.target.value) || 0)} 
             className="bg-slate-950 text-slate-200 px-2 py-1 text-xs rounded border border-slate-600 focus:border-blue-500 outline-none w-20 text-center font-mono"
           />
        </div>

        {/* KHU VỰC CUỘN ĐƯỢC: INPUT & OUTPUT */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar bg-[#202124]">
          
          {/* INPUT SIMULATOR */}
          <section>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-1">
              <ChevronRight size={14}/> Input Simulator
            </h3>
            <div className="space-y-3">
              {(inputConfigs as any).length === 0 ? (
                <div className="p-4 border border-dashed border-slate-600 rounded bg-slate-800/50">
                  <p className="text-xs text-slate-500 italic text-center">Empty Inputs</p>
                </div>
              ) : (inputConfigs as any).map((cfg: any) => (
                <div key={cfg.id} className="bg-slate-800/80 p-3 rounded border border-slate-700">
                  
                  {/* CẬP NHẬT: Hỗ trợ numpy_array, image VÀ base64 */}
                  {['numpy_array', 'image', 'base64'].includes(cfg.dataType) ? (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-slate-300 font-mono">{cfg.label || cfg.id}</span>
                        <label className="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/50 rounded transition-colors text-blue-400">
                          <Upload size={14} />
                          <span className="text-[10px] font-bold uppercase tracking-wider">Upload</span>
                          {/* Truyền dataType vào hàm để xử lý riêng biệt */}
                          <input type="file" accept="image/*" onChange={(e) => e.target.files && handleImageUpload(cfg.id, e.target.files[0], cfg.dataType)} className="hidden" />
                        </label>
                      </div>
                      
                      {/* Hiển thị Preview Ảnh (Hỗ trợ cả File lẫn chuỗi Base64) */}
                      {getPreviewImageUrl(simulatorData[cfg.id]) && (
                        <div className="relative mt-3 group w-24 h-24 rounded border border-slate-600 overflow-hidden">
                          <img src={getPreviewImageUrl(simulatorData[cfg.id])!} className="w-full h-full object-cover" alt="preview" />
                          <div onClick={() => setEnlargedImage(getPreviewImageUrl(simulatorData[cfg.id])!)} className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity backdrop-blur-sm">
                            <Eye size={20} className="text-white"/>
                          </div>
                        </div>
                      )}
                    </div>
                  
                  // Boolean Input
                  ) : cfg.dataType === 'boolean' ? (
                    <label className="flex items-center justify-between cursor-pointer group">
                      <span className="text-xs font-bold text-slate-300 font-mono">{cfg.label || cfg.id}</span>
                      <div className="relative flex items-center">
                        <input type="checkbox" className="sr-only peer" checked={simulatorData[cfg.id] || false} onChange={(e) => updateInput(cfg.id, e.target.checked)} />
                        <div className="w-9 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500"></div>
                      </div>
                    </label>
                  
                  // Text/Number Input
                  ) : (
                    <div>
                      <span className="text-xs font-bold text-slate-300 font-mono mb-2 block">{cfg.label || cfg.id}</span>
                      <input
                        type={cfg.dataType === 'number' ? 'number' : 'text'}
                        step="any"
                        className="w-full bg-slate-900 text-slate-200 px-3 py-2 text-xs rounded border border-slate-600 focus:border-blue-500 outline-none"
                        value={simulatorData[cfg.id] ?? ''}
                        onChange={(e) => {
                          const rawValue = e.target.value;
                          if (cfg.dataType === 'number') {
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

          {/* RESULT INSPECTOR */}
          <section className="border-t border-slate-700 pt-6">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-1">
              <ChevronRight size={14}/> Result Inspector
            </h3>
            {isTesting ? (
              <div className="flex flex-col items-center justify-center p-8 text-blue-400">
                <Play className="animate-ping mb-3 opacity-50" size={24}/> Running Logic...
              </div>
            ) : !inspectorData || Object.keys(inspectorData).length === 0 ? (
              <div className="p-4 border border-dashed border-slate-600 rounded bg-slate-800/50">
                <p className="text-xs text-slate-500 italic text-center">No Result Generated</p>
              </div>
            ) : (
              <div className="bg-slate-900 rounded border border-slate-700 overflow-hidden">
                {inspectorData.success ? (
                  inspectorData.data && typeof inspectorData.data === 'object' ? (
                    Object.entries(inspectorData.data).map(([key, value]) => (
                      <div key={key} className="border-b border-slate-700/50 last:border-0 p-3">
                        <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider mb-1 block">{key}</span>
                        {isBase64Image(value) ? (
                          <div className="relative mt-2 group w-24 h-24 rounded border border-slate-600 overflow-hidden">
                            <img src={value as string} alt={key} className="w-full h-full object-cover" />
                            <div onClick={() => setEnlargedImage(value as string)} className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity backdrop-blur-sm">
                              <Eye size={20} className="text-white"/>
                            </div>
                          </div>
                        ) : (
                          <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap break-all">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </pre>
                        )}
                      </div>
                    ))
                  ) : (
                    <pre className="text-xs text-slate-300 font-mono p-3 break-all">{JSON.stringify(inspectorData.data, null, 2)}</pre>
                  )
                ) : (
                  <div className="text-red-400 p-3">
                    <p className="font-bold flex items-center gap-2 text-sm mb-2"><X size={16}/> Lỗi tại: {inspectorData.failed_node_id || "Hệ thống"}</p>
                    <p className="text-xs bg-red-500/10 border border-red-500/20 p-2 rounded">{inspectorData.error_message}</p>
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
            <button onClick={() => setEnlargedImage(null)} className="absolute -top-12 right-0 p-2 bg-red-600 hover:bg-red-500 text-white rounded-full transition-colors shadow-lg">
              <X size={24}/>
            </button>
            <img src={enlargedImage} alt="Enlarged" className="max-w-[90vw] max-h-[85vh] object-contain rounded-lg shadow-2xl border border-slate-700 bg-slate-900" />
          </div>
        </div>
      )}
    </>
  );
};