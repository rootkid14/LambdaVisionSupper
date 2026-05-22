import React, { useState, useEffect } from 'react';
import { Settings2, X, Database, Trash2, Plus, Cpu, Network, HelpCircle, Info, Braces, TerminalSquare, ArrowRight, ArrowLeft, Server, Layout, Download } from 'lucide-react';
import { useSequencerStore, NodeProcessConfig } from '../UIEngineStores/SequencerStores';
import { useTagDb } from '../UIEngineStores/GlobalTagsStore';
import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { DBEngineAPI } from '../../api/dbEngineApi';
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/themes/prism-tomorrow.css';
import { SCRIPT_API_DOCS_MD } from './ScriptApiDocs';

// ĐỒNG BỘ: Cập nhật hàm inferType khớp với GlobalTagsStore
const inferType = (value: any): string => {
  if (value === null || value === undefined) return 'any';
  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'number';
  
  if (Array.isArray(value)) return 'list';
  if (typeof value === 'object') return 'dict';
  
  if (typeof value === 'string') {
      if (value.startsWith('data:image/')) return 'base64';
      if (value.length > 200 && !value.includes(' ') && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
          return 'base64';
      }
      return 'string';
  }
  return 'any';
};

const NodeNameHeader = ({ nodeId, currentName }: { nodeId: string, currentName: string }) => {
    const updateNodeData = useSequencerStore(state => state.updateNodeData);
    
    return (
        <div className="p-4 border-b border-[#3c4043] bg-[#28292c]">
            <label className="text-[10px] font-bold text-[#4fd1c5] uppercase tracking-widest mb-1 block">
                Scripting Identity (Node Address)
            </label>
            <input 
                value={currentName || ""} 
                onChange={(e) => updateNodeData(nodeId, { name: e.target.value.replace(/\s+/g, '_') })}
                placeholder="e.g. TRAM_CAN_1, KHO_A..."
                className="w-full bg-[#171717] border border-[#3c4043] focus:border-[#4fd1c5] text-[#e8eaed] text-sm p-2 rounded outline-none font-mono"
            />
            <p className="text-[8px] text-[#9aa0a6] mt-1 italic">* Dùng tên này để gọi lệnh ENGINE.spawnAt("{currentName || '...'}")</p>
        </div>
    );
};

// ==============================================================
// MODAL HƯỚNG DẪN SỬ DỤNG SCRIPT
// ==============================================================
const GuideModal = ({ onClose }: { onClose: () => void }) => (
  <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center font-sans">
    <div className="bg-[#28292c] w-full max-w-2xl rounded-xl border border-[#3c4043] shadow-2xl overflow-hidden flex flex-col">
      <div className="px-6 py-4 bg-[#303134] border-b border-[#3c4043] flex items-center justify-between">
        <div className="flex items-center gap-3 text-[#8ab4f8]">
          <HelpCircle size={20} />
          <h2 className="font-bold text-base uppercase tracking-wider">Hướng dẫn cú pháp JSON Script</h2>
        </div>
        <button onClick={onClose} className="text-[#9aa0a6] hover:text-[#f28b82] transition-colors"><X size={20}/></button>
      </div>
      
      <div className="p-6 overflow-y-auto custom-scrollbar flex flex-col gap-6 text-[#e8eaed] text-sm">
        <div className="bg-[#8ab4f8]/10 border border-[#8ab4f8]/30 p-4 rounded-lg flex gap-3 text-[#8ab4f8]">
          <Info size={24} className="shrink-0 mt-0.5" />
          <p className="leading-relaxed">Hệ thống sử dụng cơ chế <b className="text-[#fcd663]">Template Mapping</b>. Bạn chỉ cần viết một cấu trúc JSON chuẩn, sau đó thế các giá trị bằng <b className="text-[#fcd663]">Alias Variables</b> (Biến ánh xạ) để hệ thống tự động điền hoặc bóc tách dữ liệu.</p>
        </div>

        <div>
          <h3 className="text-[#81c995] font-bold mb-2 text-base">1. Quy tắc bắt buộc</h3>
          <ul className="list-disc pl-5 space-y-2 text-[#9aa0a6]">
            <li>Cú pháp gõ vào phải là <b>JSON hợp lệ 100%</b>.</li>
            <li>Các biến Alias khi đưa vào template <b>bắt buộc phải nằm trong dấu ngoặc kép</b>. Ví dụ: <code className="text-[#f28b82] bg-[#202124] px-1 rounded">"data": "@my_data"</code> (Sai cú pháp: <span className="line-through">"data": @my_data</span>).</li>
          </ul>
        </div>

        <div>
          <h3 className="text-[#81c995] font-bold mb-2 text-base">2. Biến Đặc Biệt: @ignore</h3>
          <p className="text-[#9aa0a6] mb-2">Dùng để đánh dấu các Key mà bạn không quan tâm (Bỏ qua khi trích xuất) hoặc muốn hệ thống tự động lược bỏ (Khi build).</p>
        </div>

        <div>
          <h3 className="text-[#81c995] font-bold mb-2 text-base">3. Ví dụ thực tế</h3>
          <div className="bg-[#171717] border border-[#3c4043] rounded-lg p-4 font-mono text-xs leading-relaxed">
            <span className="text-[#e8eaed]">{`{`}</span><br/>
            <span className="text-[#e8eaed]">  </span><span className="text-[#8ab4f8]">"system_name"</span><span className="text-[#e8eaed]">{`: `}</span><span className="text-[#fcd663]">"@name"</span><span className="text-[#e8eaed]">{`,`}</span><br/>
            <span className="text-[#e8eaed]">  </span><span className="text-[#8ab4f8]">"payload"</span><span className="text-[#e8eaed]">{`: `}</span><span className="text-[#fcd663]">"@data"</span><span className="text-[#e8eaed]">{`,`}</span><br/>
            <span className="text-[#e8eaed]">  </span><span className="text-[#8ab4f8]">"metadata"</span><span className="text-[#e8eaed]">{`: {`}</span><br/>
            <span className="text-[#e8eaed]">    </span><span className="text-[#8ab4f8]">"version"</span><span className="text-[#e8eaed]">{`: `}</span><span className="text-[#5f6368]">"@ignore"</span><span className="text-[#e8eaed]">{`,`}</span><br/>
            <span className="text-[#e8eaed]">    </span><span className="text-[#8ab4f8]">"id"</span><span className="text-[#e8eaed]">{`: `}</span><span className="text-[#fcd663]">"@id"</span><br/>
            <span className="text-[#e8eaed]">  {`}`}</span><br/>
            <span className="text-[#e8eaed]">{`}`}</span>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-[#3c4043] bg-[#202124] flex justify-end">
        <button onClick={onClose} className="px-6 py-2 bg-[#8ab4f8] text-[#202124] font-bold rounded hover:bg-[#a8c7fa] transition-colors">ĐÃ HIỂU</button>
      </div>
    </div>
  </div>
);

const ScriptGuideModal = ({ onClose }: { onClose: () => void }) => {
  
  // Hàm tải file cực kỳ gọn gàng nhờ tách biến
  const handleDownloadDocs = () => {
    const blob = new Blob([SCRIPT_API_DOCS_MD], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'Lambda_Script_API_Docs.md'; 
    document.body.appendChild(link);
    link.click();
    
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center font-sans">
      <div className="bg-[#28292c] w-full max-w-5xl rounded-xl border border-[#3c4043] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 bg-[#303134] border-b border-[#3c4043] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3 text-[#4fd1c5]">
            <TerminalSquare size={20} />
            <h2 className="font-bold text-base uppercase tracking-wider">Tài liệu API Javascript & Agentic</h2>
          </div>
          <button onClick={onClose} className="text-[#9aa0a6] hover:text-[#f28b82] transition-colors"><X size={20}/></button>
        </div>
        
        <div className="p-6 overflow-y-auto custom-scrollbar flex flex-col gap-8 text-[#e8eaed] text-sm">
          
          {/* KHU VỰC 1: GIỚI THIỆU CHUNG */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#171717] p-4 rounded-lg border border-[#3c4043]">
              <h3 className="text-[#4fd1c5] font-bold mb-2 flex items-center gap-2"><ArrowRight size={14}/> 1. Đọc Data (IN)</h3>
              <p className="text-[#9aa0a6] text-xs">Đọc giá trị từ Global Tags.<br/><code className="text-[#e8eaed] bg-[#202124] px-1 py-0.5 rounded mt-1 inline-block">let v = IN.my_var;</code></p>
            </div>
            <div className="bg-[#171717] p-4 rounded-lg border border-[#3c4043]">
              <h3 className="text-[#c58af9] font-bold mb-2 flex items-center gap-2"><ArrowLeft size={14}/> 2. Ghi Data (OUT)</h3>
              <p className="text-[#9aa0a6] text-xs">Xuất giá trị ra Global Tags.<br/><code className="text-[#e8eaed] bg-[#202124] px-1 py-0.5 rounded mt-1 inline-block">OUT.result = 100;</code></p>
            </div>
            <div className="bg-[#171717] p-4 rounded-lg border border-[#3c4043]">
              <h3 className="text-[#8ab4f8] font-bold mb-2 flex items-center gap-2"><Layout size={14}/> 3. Thao tác UI</h3>
              <p className="text-[#9aa0a6] text-xs">Can thiệp Component trực tiếp.<br/><code className="text-[#e8eaed] bg-[#202124] px-1 py-0.5 rounded mt-1 inline-block">UI.set("Box1", {"{w: 10}"})</code></p>
            </div>
            <div className="bg-[#171717] p-4 rounded-lg border border-[#fcd663]/50 relative overflow-hidden shadow-[0_0_15px_rgba(252,214,99,0.05)]">
              <div className="absolute top-0 right-0 w-16 h-16 bg-[#fcd663] opacity-10 rounded-bl-full"></div>
              <h3 className="text-[#fcd663] font-bold mb-2 flex items-center gap-2"><Network size={14}/> 4. Token Engine</h3>
              <p className="text-[#9aa0a6] text-xs">Điều phối luồng Agentic.<br/><code className="text-[#e8eaed] bg-[#202124] px-1 py-0.5 rounded mt-1 inline-block">ENGINE.addLabel("A")</code></p>
            </div>
          </div>
  
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* KHU VỰC 2A: TỪ ĐIỂN UI */}
              <div>
                <h3 className="text-[#8ab4f8] font-bold mb-3 text-base flex items-center gap-2">
                  <Database size={18}/> Thuộc tính UI (UI Properties)
                </h3>
                <div className="overflow-x-auto border border-[#3c4043] rounded-lg">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-[#202124] text-[#9aa0a6] border-b border-[#3c4043]">
                      <tr>
                        <th className="p-3 font-bold w-[35%]">Nhóm Component</th>
                        <th className="p-3 font-bold">Các Key (Props) có thể Get / Set</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#3c4043] text-[#e8eaed] bg-[#171717]">
                      <tr className="hover:bg-[#202124] transition-colors">
                        <td className="p-3 font-bold text-[#e8eaed]">Tất cả (Common)</td>
                        <td className="p-3 font-mono text-[11px] leading-relaxed">
                          <span className="text-[#fcd663]">x, y, w, h, rotation, isVisible</span>
                        </td>
                      </tr>
                      <tr className="hover:bg-[#202124] transition-colors">
                        <td className="p-3 font-bold text-[#81c995]">Style (Màu, Viền)</td>
                        <td className="p-3 font-mono text-[11px] leading-relaxed text-[#fcd663]">
                          {"style: { strokeColor, fillColor, fontColor... }"}
                        </td>
                      </tr>
                      <tr className="hover:bg-[#202124] transition-colors">
                        <td className="p-3 font-bold text-[#4fd1c5]">Text / Button</td>
                        <td className="p-3 font-mono text-[11px] leading-relaxed text-[#fcd663]">content</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
  
              {/* KHU VỰC 2B: TỪ ĐIỂN ENGINE API */}
              <div>
                <h3 className="text-[#fcd663] font-bold mb-3 text-base flex items-center gap-2">
                  <Cpu size={18}/> Thao tác Token (Engine API)
                </h3>
                <div className="overflow-x-auto border border-[#fcd663]/30 rounded-lg">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-[#202124] text-[#fcd663] border-b border-[#fcd663]/30">
                      <tr>
                        <th className="p-3 font-bold w-[35%]">Nhóm Lệnh</th>
                        <th className="p-3 font-bold">Cú pháp & Chức năng</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#3c4043] text-[#e8eaed] bg-[#171717]">
                      <tr className="hover:bg-[#202124] transition-colors">
                        <td className="p-3 font-bold text-[#e8eaed]">Nhãn dán (Label)</td>
                        <td className="p-3 font-mono text-[11px] leading-relaxed">
                          ENGINE.addLabel("Tên"); <br/>
                          ENGINE.removeLabel("Tên"); <br/>
                          <span className="text-[#9aa0a6]">{"// bool = ENGINE.hasLabel(\"Tên\")"}</span>
                        </td>
                      </tr>
                      <tr className="hover:bg-[#202124] transition-colors">
                        <td className="p-3 font-bold text-[#81c995]">Truy vấn (Query)</td>
                        <td className="p-3 font-mono text-[11px] leading-relaxed">
                          ENGINE.queryByLabel("Tên"); <br/>
                          ENGINE.queryByHistory("Node_ID");<br/>
                          <span className="text-[#9aa0a6]">{"// Trả về mảng string [Token_IDs]"}</span>
                        </td>
                      </tr>
                      <tr className="hover:bg-[#202124] transition-colors">
                        <td className="p-3 font-bold text-[#f28b82]">Can thiệp (Action)</td>
                        <td className="p-3 font-mono text-[11px] leading-relaxed">
                          ENGINE.kill(id); <br/>
                          ENGINE.killAllByLabel("Tên"); <br/>
                          ENGINE.hijack(id, "Target_Node_ID");
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
          </div>
  
          {/* KHU VỰC 3: CODE MẪU */}
          <div>
            <h3 className="text-[#e8eaed] font-bold mb-3 text-base">Code Mẫu (Snippets)</h3>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="bg-[#171717] border border-[#3c4043] rounded-lg p-4 font-mono text-xs leading-relaxed text-[#e8eaed]">
                <span className="text-[#5f6368]">{"// 1. Tính toán & Xuất Tag"}</span><br/>
                <span className="text-[#4fd1c5]">{"let "}</span>{"cnt = IN.arr ? IN.arr.length : "}<span className="text-[#fcd663]">{"0"}</span>{";"}<br/>
                <span className="text-[#c58af9]">{"OUT"}</span>{".status = (cnt > "}<span className="text-[#fcd663]">{"10"}</span>{") ? "}<span className="text-[#fcd663]">{"\"ERR\""}</span>{" : "}<span className="text-[#fcd663]">{"\"OK\""}</span>{";"}
              </div>
              <div className="bg-[#171717] border border-[#3c4043] rounded-lg p-4 font-mono text-xs leading-relaxed text-[#e8eaed]">
                <span className="text-[#5f6368]">{"// 2. Can thiệp UI Component"}</span><br/>
                <span className="text-[#4fd1c5]">{"let "}</span>{"box = "}<span className="text-[#8ab4f8]">{"UI.get"}</span>{"("}<span className="text-[#fcd663]">{"\"Face_Box\""}</span>{");"}<br/>
                <span className="text-[#4fd1c5]">{"if "}</span>{"(box) {"}<br/>
                &nbsp;&nbsp;<span className="text-[#8ab4f8]">{"UI.set"}</span>{"("}<span className="text-[#fcd663]">{"\"Face_Box\""}</span>{", { style: { strokeColor: "}<span className="text-[#fcd663]">{"'#ff0000'"}</span>{" } });"}<br/>
                {"}"}
              </div>
              <div className="bg-[#171717] border border-[#fcd663]/30 rounded-lg p-4 font-mono text-xs leading-relaxed text-[#e8eaed]">
                <span className="text-[#5f6368]">{"// 3. Giải cứu Token (Agentic)"}</span><br/>
                <span className="text-[#fcd663]">{"ENGINE"}</span>{".addLabel("}<span className="text-[#fcd663]">{"\"Tracked\""}</span>{");"}<br/>
                <span className="text-[#4fd1c5]">{"let "}</span>{"errs = "}<span className="text-[#fcd663]">{"ENGINE"}</span>{".queryByLabel("}<span className="text-[#fcd663]">{"\"Error\""}</span>{");"}<br/>
                <span className="text-[#4fd1c5]">{"for "}</span>{"(let id of errs) {"}<br/>
                &nbsp;&nbsp;<span className="text-[#fcd663]">{"ENGINE"}</span>{".hijack(id, "}<span className="text-[#fcd663]">{"\"Node_Alarm_1\""}</span>{");"}<br/>
                {"}"}
              </div>
            </div>
          </div>
        </div>
  
        <div className="p-4 border-t border-[#3c4043] bg-[#202124] flex justify-between items-center shrink-0">
          <button 
            onClick={handleDownloadDocs} 
            className="flex items-center gap-2 px-4 py-2 bg-[#8ab4f8]/10 text-[#8ab4f8] font-bold text-xs rounded hover:bg-[#8ab4f8]/20 border border-[#8ab4f8]/30 transition-colors"
          >
            <Download size={14} /> DOWNLOAD FULL DOCS (.MD)
          </button>
          
          <button 
            onClick={onClose} 
            className="px-6 py-2 bg-[#4fd1c5] text-[#202124] font-bold rounded hover:bg-[#81e6d9] transition-colors shadow-lg"
          >
            ĐÃ HIỂU
          </button>
        </div>
      </div>
    </div>
  );
};

export const PropertiesSidebar = ({ nodeId, onClose }: { nodeId: string, onClose: () => void }) => {
  const store = useSequencerStore();
  const node = store.nodes.find(n => n.id === nodeId);
  
  const [showGuide, setShowGuide] = useState(false);
  const [showScriptGuide, setShowScriptGuide] = useState(false);

  if (!node) return null;
  const config = (node.data?.sequencer_data as any)?.config as any || {};

  const renderPanel = () => {
    switch (node.type) {
      case 'start':
      case 'end':
        return <StartEndPanel nodeId={nodeId} config={config} isStart={node.type === 'start'} />;
      case 'proc':
        return <ProcessPanel nodeId={nodeId} config={config} />;
      case 'exjson':
        return <JsonScriptPanel nodeId={nodeId} config={config} isExtract={true} />;
      case 'buildjson':
        return <JsonScriptPanel nodeId={nodeId} config={config} isExtract={false} />;
      case 'script':
        return <ScriptPanel nodeId={nodeId} config={config} />; // Đã rút NodeNameHeader ra
      case 'writedb':
        return <WriteDbPanel nodeId={nodeId} config={config} />
      default:
        return (
          <div className="p-6 text-[#9aa0a6] text-sm italic text-center">
            No advanced properties available for {node.type?.toUpperCase() || 'THIS'} node.
          </div>
        );
    }
  };

  return (
    <aside className="flex flex-col h-full w-[480px] bg-[#28292c] border-l border-[#3c4043] shadow-2xl transition-all z-40">
      <div className="p-4 bg-[#303134] border-b border-[#3c4043] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 font-bold text-[#e8eaed]">
          <Settings2 size={18} className="text-[#8ab4f8]" /> 
          <span className="uppercase tracking-wider text-xs text-[#9aa0a6] mt-0.5">
            {node.type || 'Node'} Properties
          </span>
            {(node.type === 'exjson' || node.type === 'buildjson') && (
              <button onClick={() => setShowGuide(true)} className="ml-2 text-[#8ab4f8] hover:text-[#a8c7fa] bg-[#8ab4f8]/10 p-1 rounded transition-colors">
                <HelpCircle size={16} />
              </button>
            )}
            {node.type === 'script' && (
              <button onClick={() => setShowScriptGuide(true)} className="ml-2 text-[#4fd1c5] hover:text-[#81e6d9] bg-[#4fd1c5]/10 p-1 rounded transition-colors">
                <HelpCircle size={16} />
              </button>
            )}
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-[#3c4043] rounded text-[#9aa0a6] hover:text-[#f28b82] transition-colors">
          <X size={18} />
        </button>
      </div>

      {/* ĐÂY LÀ CHÌA KHÓA: Đặt thẻ NameHeader ở đây để Node nào cũng có thể đặt tên Identity */}
      <NodeNameHeader nodeId={nodeId} currentName={node.data.name as any} />

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {renderPanel()}
      </div>

      {showGuide && <GuideModal onClose={() => setShowGuide(false)} />}
      {showScriptGuide && <ScriptGuideModal onClose={() => setShowScriptGuide(false)} />}
    </aside>
  );
};

// ==============================================================
// COMPONENT 1: START / END PANEL
// ==============================================================
const StartEndPanel = ({ nodeId, config, isStart }: { nodeId: string, config: any, isStart: boolean }) => {
  const setFieldValue = useSequencerStore(state => state.setFieldValue);
  const tags = useTagDb(state => state.tags);
  const globalTags = Object.keys(tags);
  
  const mapKey = isStart ? 'on_begin_map' : 'on_end_map';
  const currentMap = config[mapKey] || {};
  
  const [rows, setRows] = useState<{ tag: string, type: string, val: any }[]>(() => 
    Object.entries(currentMap).map(([k, v]) => ({
      tag: k,
      type: inferType(tags[k]), 
      val: v
    }))
  );

  const saveConfig = (newRows: typeof rows) => {
    const newMap: Record<string, any> = {};
    newRows.forEach(r => {
      if (r.tag) newMap[r.tag] = r.type === 'number' ? Number(r.val) : r.type === 'boolean' ? (r.val === 'true' || r.val === true) : String(r.val);
    });
    setFieldValue(nodeId, mapKey, newMap);
  };

  const updateRow = (idx: number, field: string, value: any) => {
    const newRows = [...rows];
    newRows[idx] = { ...newRows[idx], [field]: value };
    
    if (field === 'tag') {
       const inferredType = inferType(tags[value]);
       newRows[idx].type = inferredType;
       newRows[idx].val = inferredType === 'boolean' ? false : inferredType === 'number' ? 0 : "";
    }
    setRows(newRows);
    saveConfig(newRows);
  };

  const addRow = () => {
    const newRows = [...rows, { tag: '', type: 'string', val: '' }];
    setRows(newRows);
    saveConfig(newRows);
  };

  const removeRow = (idx: number) => {
    const newRows = rows.filter((_, i) => i !== idx);
    setRows(newRows);
    saveConfig(newRows);
  };

  return (
    <div className="p-5 flex flex-col gap-4">
      {/* TĂNG SIZE: text-[10px] -> text-xs */}
      <div className="text-xs text-[#9aa0a6] uppercase font-bold border-b border-[#3c4043] pb-2 flex items-center gap-2">
        <Database size={16} className="text-[#81c995]" /> 
        {isStart ? "Initialization Data" : "Cleanup Data"}
      </div>
      
        {rows.map((row, i) => (
          <div key={i} className="flex gap-2 items-center bg-[#202124] p-2.5 rounded border border-[#3c4043]">
            {/* TĂNG SIZE: text-[10px] p-1.5 -> text-sm p-2.5 */}
            <select value={row.tag} onChange={(e) => updateRow(i, 'tag', e.target.value)} className="w-1/3 bg-[#171717] border border-[#3c4043] text-[#8ab4f8] text-sm p-2.5 rounded outline-none cursor-pointer">
              <option value="">Select Tag...</option>
              {globalTags.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            
            <div className="w-1/5 bg-[#171717] border border-[#3c4043] text-[#fcd663] text-xs p-2.5 rounded text-center uppercase tracking-wider font-bold">
              {row.tag ? row.type : "--"}
            </div>

            {row.type === 'boolean' ? (
              <select value={String(row.val)} onChange={(e) => updateRow(i, 'val', e.target.value)} className="flex-1 bg-[#171717] border border-[#3c4043] text-[#81c995] text-sm p-2.5 rounded outline-none cursor-pointer">
                  <option value="true">True</option>
                  <option value="false">False</option>
              </select>
            ) : row.type === 'number' ? (
              <input type="number" value={row.val} onChange={(e) => updateRow(i, 'val', e.target.value)} placeholder="0" className="flex-1 bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm p-2.5 rounded outline-none min-w-0" />
            ) : (
              <input type="text" value={row.val} onChange={(e) => updateRow(i, 'val', e.target.value)} placeholder="Value..." className="flex-1 bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm p-2.5 rounded outline-none min-w-0" />
            )}
            <button onClick={() => removeRow(i)} className="text-[#5f6368] hover:text-[#f28b82] p-1.5"><Trash2 size={16}/></button>
          </div>
        ))}
        <button onClick={addRow} className="w-full py-2.5 border border-dashed border-[#5f6368] text-[#9aa0a6] rounded text-xs font-bold hover:border-[#8ab4f8] hover:text-[#8ab4f8] transition-colors flex items-center justify-center gap-2">
          <Plus size={14}/> ADD RECORD
        </button>
      </div>
    );
};

// ==============================================================
// COMPONENT 2: PROCESS PANEL
// ==============================================================
const ProcessPanel = ({ nodeId, config }: { nodeId: string, config: NodeProcessConfig }) => {
  const onSelectWorker = useSequencerStore(state => state.onSelectWorker);
  const onSelectLogicObject = useSequencerStore(state => state.onSelectLogicObject);
  const setFieldValue = useSequencerStore(state => state.setFieldValue);
  const tags = useTagDb(state => state.tags);
  const globalTags = Object.keys(tags);
  
  const masterWorker = useFleetStore(state => state.master_worker);
  const fleetWorkers = useFleetStore(state => state.fleet_worker);

  const safeLogicInfo = config.logic_object_info || { worker_id: '', logic_object_id: '' };
  
  const [title, setTitle] = useState(config.node_title || 'Process');
  const [workerId, setWorkerId] = useState(safeLogicInfo.worker_id);
  const [logicId, setLogicId] = useState(safeLogicInfo.logic_object_id);
  
  const [availableLogics, setAvailableLogics] = useState<string[]>([]);
  const [schemas, setSchemas] = useState<{input: Record<string, string>, output: Record<string, string>}>({ input: {}, output: {} });
  const [tab, setTab] = useState<'begin'|'end'>('begin');

  useEffect(() => {
    if (!workerId) {
        setAvailableLogics([]);
        return;
    }
    onSelectWorker(workerId).then(logics => {
      if(logics) setAvailableLogics(logics);
    });
  }, [workerId, onSelectWorker]);

  useEffect(() => {
    if (!workerId || !logicId) {
        setSchemas({ input: {}, output: {} });
        return;
    }
    onSelectLogicObject(workerId, logicId).then((res: any) => {
      if (res) {
        setSchemas({
           input: res.input_schema || {},
           output: res.output_schema || {}
        });
      }
    });
  }, [workerId, logicId, onSelectLogicObject]);

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(e.target.value);
    setFieldValue(nodeId, 'node_title', e.target.value);
  };

  const handleWorkerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newWorker = e.target.value;
    setWorkerId(newWorker);
    setLogicId(''); 
    setFieldValue(nodeId, 'logic_object_info', { worker_id: newWorker, logic_object_id: '' });
  };

  const handleLogicChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLogic = e.target.value;
    setLogicId(newLogic);
    setFieldValue(nodeId, 'logic_object_info', { worker_id: workerId, logic_object_id: newLogic });
  };

  const handleMappingChange = (type: 'begin' | 'end', path: string, val: any, inputMode: 'tag' | 'const' = 'tag') => {
     const targetField = type === 'begin' ? 'payload_formation_map' : 'response_receive_map';
     const currentMap = { ...(config[targetField] || {}) };
     
     if (type === 'begin') {
         // --- ĐÃ SỬA LỖI Ở ĐÂY ---
         if (val !== undefined && val !== '') {
             // Có giá trị thì lưu bình thường
             currentMap[path] = { type: inputMode, value: val };
         } else {
             if (inputMode === 'const') {
                 // Nếu user vừa bấm sang nút C (Const) nhưng chưa gõ gì, 
                 // BẮT BUỘC phải lưu object này để UI giữ được trạng thái nút màu vàng
                 currentMap[path] = { type: 'const', value: '' };
             } else {
                 // Nếu là Tag và bị bỏ trống thì xóa khỏi map cho sạch bộ nhớ
                 delete currentMap[path];
             }
         }
     } else {
         if (val) currentMap[path] = val;
         else delete currentMap[path];
     }
     
     setFieldValue(nodeId, targetField, currentMap);
  };

  const renderSchemaRows = (type: 'begin' | 'end') => {
    const currentSchema = type === 'begin' ? schemas.input : schemas.output;
    const currentMap = type === 'begin' ? (config.payload_formation_map || {}) : (config.response_receive_map || {});
    const schemaEntries = Object.entries(currentSchema);

    if (schemaEntries.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-10 text-[#5f6368] italic border border-dashed border-[#3c4043] rounded bg-[#171717]">
                <Database size={28} className="mb-3 opacity-30" />
                <span className="text-xs font-bold mb-1">No Schema Found</span>
                <span className="text-[10px]">Select a Logic Object to auto-fetch schema.</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-3 mt-3">
            {schemaEntries.map(([path, feType]) => {
                // ĐỒNG BỘ LUẬT KIỂM DUYỆT TAG KHẮT KHE
                const validTags = globalTags.filter(t => {
                    if (feType === 'any') return true;
                    const tagType = inferType(tags[t]);
                    
                    if (feType === 'image' || feType === 'base64') return tagType === 'base64';
                    if (feType === 'numpy_array') return tagType === 'list';
                    if (feType === 'json') return tagType === 'dict';
                    
                    return tagType === feType;
                });

                return (
                  <div key={path} className="flex gap-2 items-center bg-[#202124] p-2.5 rounded border border-[#3c4043] hover:border-[#5f6368] transition-colors">
                      <div className="w-[40%] flex flex-col overflow-hidden shrink-0">
                          <span className="text-sm text-[#fcd663] font-mono truncate" title={path}>{path}</span>
                          <span className="text-[10px] text-[#9aa0a6] uppercase font-bold tracking-widest mt-0.5">{feType as string}</span>
                      </div>
                      
                      <span className="text-[#5f6368] text-sm px-1 shrink-0">{type === 'begin' ? '⟵' : '⟶'}</span>
                      
                      {type === 'end' ? (
                          // ==========================================
                          // LUỒNG ON END (Nhận từ Backend -> Ép buộc lưu vào Tag)
                          // ==========================================
                          <select 
                              value={currentMap[path] as any|| ''}
                              onChange={(e) => handleMappingChange(type, path, e.target.value)}
                              className="flex-1 bg-[#171717] border border-[#3c4043] focus:border-[#8ab4f8] text-[#8ab4f8] text-sm p-2.5 rounded outline-none cursor-pointer min-w-0 transition-colors"
                          >
                              <option value="">-- Ignored / Empty --</option>
                              {validTags.map(t => <option key={t} value={t}>{t}</option>)}
                          </select>
                      ) : (
                          // ==========================================
                          // LUỒNG ON BEGIN (Gửi lên Backend -> Dual Mode: Tag / Const)
                          // ==========================================
                          <div className="flex-1 flex gap-1.5 items-center min-w-0">
                              {(() => {
                                  // Đọc config hiện tại xem người dùng đang lưu dạng gì
                                  const mapData = currentMap[path];
                                  const isConst = (mapData as any)?.type === 'const';
                                  
                                  // Xử lý tương thích ngược: Nếu dữ liệu cũ là string trơn -> coi như là Tag
                                  const val = (mapData as any)?.value !== undefined 
                                      ? (mapData as any).value 
                                      : (typeof mapData === 'string' ? mapData : '');

                                  return (
                                      <>
                                          {/* Nút Toggle C (Constant) và T (Tag) */}
                                          <button 
                                              onClick={() => handleMappingChange(type, path, '', isConst ? 'tag' : 'const')}
                                              className={`p-1.5 rounded border shrink-0 text-[10px] font-bold w-8 text-center transition-colors ${
                                                  isConst 
                                                  ? 'bg-[#fcd663]/20 text-[#fcd663] border-[#fcd663]/50 hover:bg-[#fcd663]/30' 
                                                  : 'bg-[#8ab4f8]/20 text-[#8ab4f8] border-[#8ab4f8]/50 hover:bg-[#8ab4f8]/30'
                                              }`}
                                              title={isConst ? "Nhập Hằng số cố định" : "Lấy giá trị động từ Tag"}
                                          >
                                              {isConst ? 'C' : 'T'}
                                          </button>
                                          
                                          {/* Hiển thị Input hoặc Select tùy theo Mode */}
                                          {isConst ? (
                                              <input 
                                                  type={feType === 'number' ? 'number' : 'text'}
                                                  value={val}
                                                  onChange={(e) => handleMappingChange(type, path, feType === 'number' ? Number(e.target.value) : e.target.value, 'const')}
                                                  placeholder={feType === 'number' ? "0" : "Enter value..."}
                                                  className="w-full bg-[#171717] border border-[#3c4043] focus:border-[#fcd663] text-[#fcd663] text-sm p-2 rounded outline-none min-w-0 transition-colors"
                                              />
                                          ) : (
                                              <select 
                                                  value={val} 
                                                  onChange={(e) => handleMappingChange(type, path, e.target.value, 'tag')}
                                                  className="w-full bg-[#171717] border border-[#3c4043] focus:border-[#8ab4f8] text-[#8ab4f8] text-sm p-2 rounded outline-none cursor-pointer min-w-0 transition-colors"
                                              >
                                                  <option value="">-- Select Tag --</option>
                                                  {validTags.map(t => <option key={t} value={t}>{t}</option>)}
                                              </select>
                                          )}
                                      </>
                                  );
                              })()}
                          </div>
                      )}
                  </div>
                );
            })}
        </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-5 border-b border-[#3c4043] bg-[#202124]">
        {/* TĂNG SIZE: text-[9px] -> text-xs */}
        <label className="text-xs font-bold text-[#9aa0a6] uppercase block mb-1.5">Process Title</label>
        <input 
            type="text" value={title} onChange={handleTitleChange} 
            className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] font-bold text-sm p-2.5 rounded outline-none focus:border-[#8ab4f8] mb-5" 
            placeholder="Name this process..."
        />

        <div className="flex items-center gap-2 mb-1.5">
            <Network size={14} className="text-[#8ab4f8]" />
            <label className="text-xs font-bold text-[#9aa0a6] uppercase">Target Worker</label>
        </div>
        <select 
              value={workerId} onChange={handleWorkerChange} 
              className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm p-2.5 rounded outline-none mb-5 cursor-pointer"
          >
            <option value="">-- Select Target Worker --</option>
            {masterWorker && <option value="master_gateway">Master Gateway (Local)</option>}
            {fleetWorkers.map((w: any, idx: number) => {
                const wId = w.server_id;
                const wName = w.server_id ? `${w.server_id} (${w.host})` : `Unknown Server ${idx}`;
                return <option key={`worker-${wId || idx}`} value={wId}>{wName}</option>;
            })}
          </select>

        <div className="flex items-center gap-2 mb-1.5">
            <Cpu size={14} className="text-[#81c995]" />
            <label className="text-xs font-bold text-[#9aa0a6] uppercase">Logic Object ID</label>
        </div>
        <select 
            value={logicId} onChange={handleLogicChange} disabled={!workerId || availableLogics.length === 0}
            className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm p-2.5 rounded outline-none cursor-pointer font-mono disabled:opacity-50"
        >
          <option value="">-- Select Logic Object --</option>
          {availableLogics.map(id => <option key={id} value={id}>{id}</option>)}
        </select>
      </div>

      <div className="flex bg-[#28292c] border-b border-[#3c4043] p-2 gap-1.5 shrink-0">
        <button onClick={() => setTab('begin')} className={`flex-1 py-2 text-xs font-bold uppercase rounded transition-colors ${tab === 'begin' ? 'bg-[#81c995]/20 text-[#81c995]' : 'text-[#9aa0a6] hover:bg-[#303134]'}`}>On Begin (Request)</button>
        <button onClick={() => setTab('end')} className={`flex-1 py-2 text-xs font-bold uppercase rounded transition-colors ${tab === 'end' ? 'bg-[#8ab4f8]/20 text-[#8ab4f8]' : 'text-[#9aa0a6] hover:bg-[#303134]'}`}>On End (Response)</button>
      </div>

      <div className="p-5 flex-1">
        <p className="text-[11px] text-[#8ab4f8] bg-[#8ab4f8]/10 p-3 rounded border border-[#8ab4f8]/20 italic mb-5 leading-relaxed">
           {tab === 'begin' 
            ? "Mỗi dòng tương ứng với 1 trường Schema mà Backend yêu cầu. Hãy chọn một Tag để lấy dữ liệu nạp vào Payload." 
            : "Mỗi dòng là một dữ liệu Backend trả về. Hãy chọn một Tag để hệ thống tự động bóc tách và lưu trữ."}
        </p>
        {renderSchemaRows(tab)}
      </div>
    </div>
  );
};

// ==============================================================
// COMPONENT 3: JSON SCRIPT PANEL
// ==============================================================
const JsonScriptPanel = ({ nodeId, config, isExtract }: { nodeId: string, config: any, isExtract: boolean }) => {
  const setFieldValue = useSequencerStore(state => state.setFieldValue);
  const tags = useTagDb(state => state.tags);
  const globalTags = Object.keys(tags);

  const mainTagField = isExtract ? 'source_tag_id' : 'target_tag_id';
  const mainTagVal = config[mainTagField] || '';
  const aliases = config.aliases || {};
  const script = config.script || "{\n  \n}";

  const [aliasList, setAliasList] = useState<{name: string, tag: string}[]>(() => 
    Object.entries(aliases).map(([k, v]) => ({ name: k, tag: v as string }))
  );

  const updateAliasList = (newList: {name: string, tag: string}[]) => {
    setAliasList(newList);
    const newAliases: Record<string, string> = {};
    newList.forEach(item => {
      if (item.name.startsWith('@') && item.name.length > 1) {
        newAliases[item.name] = item.tag;
      }
    });
    setFieldValue(nodeId, 'aliases', newAliases);
  };

  const addAlias = () => updateAliasList([...aliasList, { name: '@', tag: '' }]);
  const removeAlias = (idx: number) => updateAliasList(aliasList.filter((_, i) => i !== idx));
  const updateAlias = (idx: number, field: 'name'|'tag', val: string) => {
    const newList = [...aliasList];
    newList[idx][field] = val;
    // Tự động ép tiền tố @
    if (field === 'name' && !val.startsWith('@')) newList[idx].name = '@' + val;
    updateAliasList(newList);
  };

  // Chỉ cho phép chọn Tag có định dạng là DICT (tức là JSON) cho Target/Source Tag
  const validJsonTags = globalTags.filter(t => inferType(tags[t]) === 'dict');

  return (
    <div className="flex flex-col h-full">
      {/* 1. KHU VỰC CHỌN TAG CHÍNH */}
      <div className="p-5 border-b border-[#3c4043] bg-[#202124]">
        {/* TĂNG SIZE */}
        <label className="text-xs font-bold text-[#9aa0a6] uppercase flex items-center gap-2 mb-2.5">
          <Database size={16} className={isExtract ? "text-[#f28b82]" : "text-[#81c995]"} />
          {isExtract ? "Source JSON Tag (Parse from)" : "Target JSON Tag (Save to)"}
        </label>
        <select 
          value={mainTagVal} 
          onChange={(e) => setFieldValue(nodeId, mainTagField, e.target.value)}
          className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm p-2.5 rounded outline-none focus:border-[#8ab4f8] cursor-pointer"
        >
          <option value="">-- Select Target JSON Tag --</option>
          {validJsonTags.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* 2. KHU VỰC TẠO ALIAS */}
      <div className="p-5 border-b border-[#3c4043]">
        <div className="flex items-center justify-between mb-3">
           <label className="text-xs font-bold text-[#9aa0a6] uppercase">Variables (Aliases)</label>
           {/* KHÔI PHỤC NÚT ADD */}
           <button onClick={addAlias} className="flex items-center gap-1 text-[#8ab4f8] hover:text-[#202124] bg-[#8ab4f8]/10 hover:bg-[#8ab4f8] px-3 py-1.5 rounded transition-colors text-xs font-bold"><Plus size={14}/> ADD</button>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex gap-2 items-center bg-[#28292c] p-2.5 rounded border border-[#3c4043] opacity-60">
             <span className="w-1/3 text-xs text-[#fcd663] font-mono px-2">@ignore</span>
             <span className="flex-1 text-xs text-[#9aa0a6] italic">Built-in (Skip field)</span>
          </div>
          {aliasList.map((al, idx) => (
            <div key={idx} className="flex gap-2 items-center bg-[#202124] p-2.5 rounded border border-[#3c4043]">
              <input type="text" value={al.name} onChange={(e) => updateAlias(idx, 'name', e.target.value)} className="w-1/3 bg-[#171717] border border-[#3c4043] text-[#fcd663] text-sm p-2.5 rounded font-mono outline-none focus:border-[#8ab4f8]" placeholder="@var" />
              <select value={al.tag} onChange={(e) => updateAlias(idx, 'tag', e.target.value)} className="flex-1 bg-[#171717] border border-[#3c4043] text-[#8ab4f8] text-sm p-2.5 rounded outline-none cursor-pointer">
                <option value="">Link to Tag...</option>
                {globalTags.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <button onClick={() => removeAlias(idx)} className="text-[#5f6368] hover:text-[#f28b82] p-2"><Trash2 size={18}/></button>
            </div>
          ))}
        </div>
      </div>

      {/* 3. KHU VỰC VIẾT SCRIPT */}
      <div className="p-5 flex-1 flex flex-col min-h-[300px]">
        <label className="text-xs font-bold text-[#9aa0a6] uppercase mb-3 flex items-center gap-2">
          <Braces size={16} /> JSON Script Template
        </label>
        <textarea 
           value={script} 
           onChange={(e) => setFieldValue(nodeId, 'script', e.target.value)}
           spellCheck={false}
           className="w-full flex-1 bg-[#171717] border border-[#3c4043] text-[#81c995] font-mono text-sm p-4 rounded outline-none focus:border-[#8ab4f8] custom-scrollbar whitespace-pre"
        />
      </div>
    </div>
  );
};


// ==============================================================
// COMPONENT 4: SCRIPT PANEL (VANILLA JS SANDBOX)
// ==============================================================
const ScriptPanel = ({ nodeId, config }: { nodeId: string, config: any }) => {
  const setFieldValue = useSequencerStore(state => state.setFieldValue);
  const globalTags = Object.keys(useTagDb(state => state.tags));

  const inputAliases = config.input_aliases || {};
  const outputAliases = config.output_aliases || {};
  const scriptContent = config.script_content || "";

  const [inList, setInList] = useState<{name: string, tag: string}[]>(() => 
    Object.entries(inputAliases).map(([k, v]) => ({ name: k, tag: v as string }))
  );
  
  const [outList, setOutList] = useState<{name: string, tag: string}[]>(() => 
    Object.entries(outputAliases).map(([k, v]) => ({ name: k, tag: v as string }))
  );

  const updateList = (type: 'in' | 'out', newList: {name: string, tag: string}[]) => {
    if (type === 'in') setInList(newList);
    else setOutList(newList);
    
    const newAliases: Record<string, string> = {};
    newList.forEach(item => {
      const validName = item.name.replace(/[^a-zA-Z0-9_]/g, '');
      if (validName && item.tag) newAliases[validName] = item.tag;
    });
    setFieldValue(nodeId, type === 'in' ? 'input_aliases' : 'output_aliases', newAliases);
  };

  const addVar = (type: 'in' | 'out') => {
    const list = type === 'in' ? inList : outList;
    updateList(type, [...list, { name: '', tag: '' }]);
  };

  const removeVar = (type: 'in' | 'out', idx: number) => {
    const list = type === 'in' ? inList : outList;
    updateList(type, list.filter((_, i) => i !== idx));
  };

  const updateVar = (type: 'in' | 'out', idx: number, field: 'name'|'tag', val: string) => {
    const list = type === 'in' ? [...inList] : [...outList];
    if (field === 'name') {
        list[idx][field] = val.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
    } else {
        list[idx][field] = val;
    }
    updateList(type, list);
  };

  return (
    <div className="flex flex-col h-full bg-[#202124]">
      {/* KHU VỰC 1: INPUTS (Đọc từ Tag vào IN.xxx) */}
      <div className="p-4 border-b border-[#3c4043] bg-[#28292c]">
        <div className="flex items-center justify-between mb-2">
           <label className="text-xs font-bold text-[#4fd1c5] uppercase flex items-center gap-2">
             <ArrowRight size={14} /> [ IN ] Variables (Read Tag)
           </label>
           <button onClick={() => addVar('in')} className="text-[#4fd1c5] hover:bg-[#4fd1c5]/20 px-2 py-1 rounded transition-colors text-[10px] font-bold">+ ADD</button>
        </div>
        <div className="flex flex-col gap-2">
          {inList.map((al, idx) => (
            <div key={idx} className="flex gap-2 items-center">
              <span className="text-[#9aa0a6] font-mono text-xs">IN.</span>
              <input type="text" value={al.name} onChange={(e) => updateVar('in', idx, 'name', e.target.value)} className="w-1/3 bg-[#171717] border border-[#3c4043] text-[#4fd1c5] text-sm p-2 rounded font-mono outline-none" placeholder="var_name" />
              <span className="text-[#5f6368] text-xs">⟵</span>
              <select value={al.tag} onChange={(e) => updateVar('in', idx, 'tag', e.target.value)} className="flex-1 bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs p-2 rounded outline-none cursor-pointer">
                <option value="">Map to Tag...</option>
                {globalTags.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <button onClick={() => removeVar('in', idx)} className="text-[#5f6368] hover:text-[#f28b82] p-1"><Trash2 size={16}/></button>
            </div>
          ))}
        </div>
      </div>

      {/* KHU VỰC 2: OUTPUTS (Lưu từ OUT.xxx ra Tag) */}
      <div className="p-4 border-b border-[#3c4043] bg-[#28292c]">
        <div className="flex items-center justify-between mb-2">
           <label className="text-xs font-bold text-[#c58af9] uppercase flex items-center gap-2">
             <ArrowLeft size={14} /> [ OUT ] Variables (Write Tag)
           </label>
           <button onClick={() => addVar('out')} className="text-[#c58af9] hover:bg-[#c58af9]/20 px-2 py-1 rounded transition-colors text-[10px] font-bold">+ ADD</button>
        </div>
        <div className="flex flex-col gap-2">
          {outList.map((al, idx) => (
            <div key={idx} className="flex gap-2 items-center">
              <span className="text-[#9aa0a6] font-mono text-xs">OUT.</span>
              <input type="text" value={al.name} onChange={(e) => updateVar('out', idx, 'name', e.target.value)} className="w-1/3 bg-[#171717] border border-[#3c4043] text-[#c58af9] text-sm p-2 rounded font-mono outline-none" placeholder="var_name" />
              <span className="text-[#5f6368] text-xs">⟶</span>
              <select value={al.tag} onChange={(e) => updateVar('out', idx, 'tag', e.target.value)} className="flex-1 bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs p-2 rounded outline-none cursor-pointer">
                <option value="">Map to Tag...</option>
                {globalTags.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <button onClick={() => removeVar('out', idx)} className="text-[#5f6368] hover:text-[#f28b82] p-1"><Trash2 size={16}/></button>
            </div>
          ))}
        </div>
      </div>

      {/* KHU VỰC 3: CODE EDITOR */}
      <div className="p-4 flex-1 flex flex-col min-h-[350px]">
        <label className="text-xs font-bold text-[#4fd1c5] uppercase mb-2 flex items-center gap-2">
          <TerminalSquare size={16} /> Javascript Sandbox
        </label>
        
        {/* KHU VỰC CHEATSHEET HƯỚNG DẪN ĐÃ ĐƯỢC BỔ SUNG ENGINE */}
        <div className="text-[12px] text-[#9aa0a6] bg-[#171717] border border-[#3c4043] rounded p-2 mb-2 font-mono flex flex-col gap-1 shrink-0">
            <span><b className="text-[#4fd14f]">IN.var</b> : Đọc dữ liệu từ biến đầu vào</span>
            <span><b className="text-[#9230e7]">OUT.var</b> : Ghi dữ liệu ra biến đầu ra</span>
            <span><b className="text-[#8ab4f8]">UI.get(name_or_id)</b> / <b className="text-[#0058e6]">UI.set(...)</b> : Can thiệp UI Component</span>
            <span className="mt-1 pt-1 border-t border-[#3c4043]"><b className="text-[#fcd663]">ENGINE</b> : .addLabel(), .queryByLabel(), .kill(), .hijack(), <b className="text-[#81c995]">.log(msg)</b></span>
            
        </div>

        <div className="flex-1 w-full bg-[#1d1f21] border border-[#3c4043] focus-within:border-[#4fd1c5] transition-colors rounded overflow-y-auto custom-scrollbar relative">
          <Editor
            value={scriptContent}
            onValueChange={(code) => setFieldValue(nodeId, 'script_content', code)}
            highlight={(code) => Prism.highlight(code, Prism.languages.javascript, 'javascript')}
            padding={16}
            tabSize={4}
            textareaClassName="focus:outline-none"
            className="min-h-full font-mono text-sm leading-relaxed"
            style={{
              fontFamily: '"Fira Code", "Consolas", monospace',
              backgroundColor: 'transparent',
              color: '#e8eaed',
            }}
          />
        </div>
      </div>
    </div>
  );
};


const WriteDbPanel = ({ nodeId, config }: { nodeId: string, config: any }) => {
  const setFieldValue = useSequencerStore(state => state.setFieldValue);
  const tags = useTagDb(state => state.tags);
  const globalTags = Object.keys(tags);
  const { master_worker, fleet_worker } = useFleetStore();
  
  const workerId = config.worker_id || "";
  const tableName = config.table_name || "";
  const mapping = config.mapping || {};
  const imgCols = config.image_columns || {};

  const [availableTables, setAvailableTables] = useState<string[]>([]);
  const [schema, setSchema] = useState<any>({});

  // Lấy danh sách bảng
  useEffect(() => {
    if (!workerId) return;
    const isMaster = workerId === "master_gateway";
    (isMaster ? DBEngineAPI.master_getTables() : DBEngineAPI.proxy_getTables(workerId))
      .then(res => setAvailableTables(Array.isArray(res) ? res : []));
  }, [workerId]);

  // Lấy Schema
  useEffect(() => {
    if (!workerId || !tableName) return;
    const isMaster = workerId === "master_gateway";
    (isMaster ? DBEngineAPI.master_getSchema(tableName) : DBEngineAPI.proxy_getSchema(workerId, tableName))
      .then(res => setSchema(res || {}));
  }, [workerId, tableName]);

  // ====================================================
  // PHÉP THUẬT AUTO-MAP DATETIME
  // Tự động gán keyword __AUTO_TIME__ cho các cột Datetime
  // ====================================================
  useEffect(() => {
    let changed = false;
    const newMapping = { ...mapping };
    
    Object.entries(schema).forEach(([col, cfg]: any) => {
        if (cfg.dataType === 'datetime' && newMapping[col] !== '__AUTO_TIME__') {
            newMapping[col] = '__AUTO_TIME__';
            changed = true;
        }
    });
    
    if (changed) {
        setFieldValue(nodeId, 'mapping', newMapping);
    }
  }, [schema]); // Chỉ chạy lại khi Schema thay đổi

  const handleWorkerChange = (e: any) => { setFieldValue(nodeId, 'worker_id', e.target.value); setFieldValue(nodeId, 'table_name', ''); };
  const handleTableChange = (e: any) => setFieldValue(nodeId, 'table_name', e.target.value);
  const handleMapChange = (col: string, tag: string) => setFieldValue(nodeId, 'mapping', { ...mapping, [col]: tag });
  const handleImgToggle = (col: string, val: boolean) => setFieldValue(nodeId, 'image_columns', { ...imgCols, [col]: val });

  return (
    <div className="flex flex-col h-full bg-[#202124]">
      <div className="p-5 border-b border-[#3c4043] bg-[#28292c]">
        <label className="text-xs font-bold text-[#e580ff] uppercase flex items-center gap-2 mb-2"><Server size={14} /> Target Database</label>
        <select value={workerId} onChange={handleWorkerChange} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm p-2.5 rounded outline-none mb-3 cursor-pointer">
            <option value="">-- Select Worker --</option>
            {master_worker && <option value="master_gateway">Master Gateway</option>}
            {fleet_worker.map((w: any) => <option key={w.server_id} value={w.server_id}>{w.server_id}</option>)}
        </select>
        <select value={tableName} onChange={handleTableChange} disabled={!workerId} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-sm p-2.5 rounded outline-none cursor-pointer disabled:opacity-50 font-mono">
            <option value="">-- Select Table --</option>
            {availableTables.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div className="p-5 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3">
        <label className="text-xs font-bold text-[#e8eaed] uppercase">Column Mapping</label>
        {Object.entries(schema).filter(([col, cfg]: any) => col !== 'id').map(([col, cfg]: any) => {
            
            const isImgChecked = imgCols[col] || false;
            const isDatetime = cfg.dataType === 'datetime';
            
            // Logic lọc Tag (Trả về mảng rỗng nếu là Datetime vì đằng nào cũng bị Khóa UI)
            const validTags = isDatetime ? [] : globalTags.filter(t => {
                const tagType = inferType(tags[t]);
                const dbType = cfg.dataType;
                if (isImgChecked) return tagType === 'base64';
                if (dbType === 'number') return tagType === 'number';
                if (dbType === 'boolean') return tagType === 'boolean';
                if (dbType === 'text') return tagType === 'string' || tagType === 'base64';
                return true;
            });

            return (
              <div key={col} className="flex gap-2 items-center bg-[#28292c] p-2.5 rounded border border-[#3c4043]">
                  <div className="w-1/3 flex flex-col overflow-hidden">
                      <span className="text-sm font-mono text-[#fcd663] truncate" title={col}>{col}</span>
                      <span className="text-[10px] text-[#9aa0a6] uppercase font-bold">{cfg.dataType}</span>
                  </div>
                  
                  {/* NẾU LÀ DATETIME -> HIỂN THỊ LABEL KHÓA AUTO TIME */}
                  {isDatetime ? (
                      <div className="flex-1 bg-[#171717] border border-[#3c4043] text-[#81c995] text-xs p-2.5 rounded flex items-center justify-center font-bold tracking-wider opacity-80 cursor-not-allowed">
                          [ AUTO: CURRENT TIME ]
                      </div>
                  ) : (
                      <select value={mapping[col] || ''} onChange={(e) => handleMapChange(col, e.target.value)} className="flex-1 bg-[#171717] border border-[#3c4043] focus:border-[#8ab4f8] text-[#8ab4f8] text-xs p-2.5 rounded outline-none cursor-pointer min-w-0 transition-colors">
                          <option value="">(NULL)</option>
                          {validTags.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                  )}
                  
                  <div className="w-14 flex flex-col items-center justify-center gap-1.5 border-l border-[#3c4043] pl-2 shrink-0">
                      {/* Disable checkbox Is IMG nếu là Datetime */}
                      <span className={`text-[8px] uppercase font-bold text-center ${isDatetime ? 'text-[#5f6368]' : 'text-[#9aa0a6]'}`}>Is IMG</span>
                      <input type="checkbox" checked={isImgChecked} disabled={isDatetime} onChange={e => handleImgToggle(col, e.target.checked)} className="accent-[#e580ff] w-4 h-4 cursor-pointer disabled:opacity-20" />
                  </div>
              </div>
            );
        })}
      </div>
    </div>
  );
};