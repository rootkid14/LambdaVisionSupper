import { useState, useMemo } from 'react';
import { Search, Plus, Trash2, Edit3, Database, X, Upload, Download } from 'lucide-react';
import { useTagDb, TagValue, inferTagType } from '../UIEngineStores/GlobalTagsStore';

const getTypeColor = (type: string) => {
    if (type === 'boolean') return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    if (type === 'number') return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (type === 'string') return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    if (type === 'list') return 'text-purple-400 bg-purple-500/10 border-purple-500/30';
    if (type === 'dict' || type === 'json') return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    if (type === 'base64') return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
};

const MonitorCell = ({ value, type }: { value: any, type: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  let displayValue = String(value);
  if (type === 'list') displayValue = `List [ ${(value as any[]).length} items ]`;
  else if (type === 'dict') displayValue = `Dict { ${Object.keys(value).length} keys }`;
  else if (type === 'base64') {
      if (value === 'data:image/empty') displayValue = `[Image: Empty / Fallback]`;
      else displayValue = `[Base64 Data: ~${((value as string).length / 1024).toFixed(2)} KB]`;
  }
  
  if (isExpanded && type !== 'base64') {
    return (
      <input 
        autoFocus type="text" readOnly 
        value={type === 'list' || type === 'dict' ? JSON.stringify(value) : displayValue} 
        onBlur={() => setIsExpanded(false)}
        className="w-full bg-[#171717] text-[#e8eaed] text-[10px] font-mono p-1 rounded border border-[#8ab4f8] outline-none"
      />
    );
  }

  return (
    <div 
      className="cursor-text hover:bg-[#171717] rounded px-1 -ml-1 transition-colors truncate w-full"
      onClick={() => setIsExpanded(true)} title="Click to view details"
    >
       {type === 'boolean' ? (
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold inline-block ${value ? 'bg-[#81c995]/20 text-[#81c995]' : 'bg-[#f28b82]/20 text-[#f28b82]'}`}>
            {value ? 'TRUE' : 'FALSE'}
          </span>
       ) : type === 'list' || type === 'dict' ? (
          <span className="text-[#c58af9] italic font-bold truncate block">{displayValue}</span>
       ) : type === 'base64' ? (
          <span className="text-[#fcd663] truncate block" title={displayValue}>{displayValue}</span>
       ) : (
          <span className="text-[#8ab4f8] truncate block">{displayValue}</span>
       )}
    </div>
  );
};

export const TagManagerTable = ({ onClose, mode = 'edit' }: { onClose?: () => void, mode?: 'edit' | 'view' }) => {
  const { tags, writeTag, deleteTag } = useTagDb();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagType, setNewTagType] = useState('string');
  const [newTagValue, setNewTagValue] = useState('');

  const filteredTags = useMemo(() => {
    return Object.entries(tags).filter(([key]) => key.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [tags, searchTerm]);

  const handleAddTag = () => {
    if (!newTagName.trim()) return;
    let val: TagValue = newTagValue;
    try {
        if (newTagType === 'number') val = Number(newTagValue);
        else if (newTagType === 'boolean') val = newTagValue.toLowerCase() === 'true';
        else if (newTagType === 'base64') val = newTagValue ? newTagValue : 'data:image/empty';
        else if (newTagType === 'dict' || newTagType === 'json') val = JSON.parse(newTagValue);
        else if (newTagType === 'list') {
            val = JSON.parse(newTagValue);
            if(!Array.isArray(val)) throw new Error("Not an array");
        }
    } catch (err) {
        // TẠO THÔNG BÁO LỖI THÔNG MINH
        const isJsonType = ['list', 'dict', 'json'].includes(newTagType);
        let errorMsg = `❌ LỖI CÚ PHÁP: Dữ liệu bạn nhập không đúng chuẩn định dạng ${newTagType.toUpperCase()}`;
        
        if (isJsonType) {
            errorMsg += `\n\n⚠️ HỆ THỐNG YÊU CẦU CHUẨN STRICT JSON:\n` +
                        ` Bắt buộc phải dùng NGOẶC KÉP (" ") cho TẤT CẢ các Key và Chuỗi.\n` +
                        ` KHÔNG dùng ngoặc đơn (' ') hoặc để Key trần (không có ngoặc).\n\n` +
                        ` VÍ DỤ ĐÚNG:\n` +
                        `- List chữ: ["apple", "banana"]\n` +
                        `- List số: [1, 2, 3]\n` +
                        `- Dict/JSON: {"id": 1, "status": "running"}`;
        }
        
        alert(errorMsg);
        return;
    }
    writeTag(newTagName.trim(), val);
    setNewTagName(''); setNewTagValue(''); setIsAdding(false);
  };

  const handleForceValue = (key: string, currentType: string, newValue: string) => {
    let parsedValue: any = newValue;
    try {
        if (currentType === 'number') parsedValue = Number(newValue);
        else if (currentType === 'boolean') parsedValue = newValue === 'true';
        else if (currentType === 'dict' || currentType === 'list') parsedValue = JSON.parse(newValue);
    } catch {
        alert("Force Failed: Định dạng JSON/Mảng không hợp lệ!");
        return;
    }
    writeTag(key, parsedValue);
  };

  const handleDownloadImage = (key: string, value: any) => {
    if (!value || value === 'data:image/empty') {
      alert("Không có dữ liệu ảnh để tải xuống!"); return;
    }
    const a = document.createElement('a');
    a.href = value; 
    a.download = `Tag_${key}_${Date.now()}.jpg`;
    document.body.appendChild(a); a.click(); a.remove();
  };

  return (
    <div className="flex flex-col h-full bg-[#28292c] text-[#e8eaed] border-l border-[#3c4043] shadow-2xl font-sans">
      <div className="flex items-center justify-between p-4 bg-[#303134] border-b border-[#3c4043] shrink-0">
        <div className="flex items-center gap-3">
          <Database className="text-[#8ab4f8]" size={20} />
          <div className="flex flex-col">
            <h2 className="font-bold tracking-wide uppercase text-sm text-[#e8eaed]">Global Data Tags</h2>
            {mode === 'view' && <span className="text-[9px] text-[#fcd663] italic">Read-only (Force allowed)</span>}
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1.5 hover:bg-[#3c4043] rounded-md transition-colors">
            <X size={18} className="text-[#9aa0a6] hover:text-[#f28b82]" />
          </button>
        )}
      </div>

      <div className="p-3 bg-[#202124] border-b border-[#3c4043] flex items-center gap-3 shrink-0">
        <div className="flex-1 flex items-center bg-[#171717] rounded border border-[#3c4043] px-3 py-1.5 focus-within:border-[#8ab4f8] transition-colors">
          <Search size={14} className="text-[#5f6368] mr-2" />
          <input 
            type="text" placeholder="Search tags..." 
            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent text-xs outline-none w-full text-[#e8eaed] placeholder-[#5f6368]"
          />
        </div>
        {/* CHÚ Ý: Nút Add Tag giờ luôn xuất hiện ở mọi Mode */}
        <button onClick={() => setIsAdding(true)} className="flex items-center gap-2 bg-[#8ab4f8]/10 text-[#8ab4f8] border border-[#8ab4f8]/30 hover:bg-[#8ab4f8]/20 px-3 py-1.5 rounded text-[11px] font-bold transition-colors whitespace-nowrap">
          <Plus size={14} /> ADD
        </button>
      </div>

      <div className="flex-1 overflow-auto bg-[#28292c] custom-scrollbar">
        <table className="w-full table-fixed text-left border-collapse">
          <thead className="sticky top-0 bg-[#303134] z-10 border-b border-[#3c4043] shadow-sm">
            <tr>
              <th className="p-2 text-[10px] font-bold text-[#9aa0a6] uppercase w-[120px] truncate">Name</th>
              <th className="p-2 text-[10px] font-bold text-[#9aa0a6] uppercase text-center w-[70px] shrink-0">Type</th>
              <th className="p-2 text-[10px] font-bold text-[#9aa0a6] uppercase truncate">Value</th>
              <th className="p-2 text-[10px] font-bold text-[#9aa0a6] uppercase text-right w-[160px] shrink-0">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#3c4043]">
            {isAdding && (
              <tr className="bg-[#8ab4f8]/5">
                <td className="p-2">
                  <input autoFocus type="text" placeholder="Name" value={newTagName} onChange={e => setNewTagName(e.target.value)} className="w-full bg-[#171717] text-xs text-[#e8eaed] p-1.5 rounded border border-[#3c4043] outline-none focus:border-[#8ab4f8]" />
                </td>
                <td className="p-2">
                  <select value={newTagType} onChange={e => setNewTagType(e.target.value)} className="bg-[#171717] text-[10px] text-[#fcd663] font-bold uppercase p-1.5 rounded border border-[#3c4043] outline-none w-full cursor-pointer">
                    <option value="string">Str</option>
                    <option value="number">Num</option>
                    <option value="boolean">Bool</option>
                    <option value="dict">Dict</option>
                    <option value="list">List</option>
                    <option value="json">JSON</option>
                    {/* CHỈ CÒN ĐÚNG 1 LỰA CHỌN BASE64 */}
                    <option value="base64">Base64</option> 
                    <option value="any">Any</option>
                  </select>
                </td>
                <td className="p-2">
                  {newTagType === 'base64' ? (
                     <input type="file" accept="image/*" onChange={e => {
                        const file = e.target.files?.[0];
                        if(file) {
                            const reader = new FileReader();
                            reader.onload = (ev) => setNewTagValue(ev.target?.result as string);
                            reader.readAsDataURL(file);
                        }
                     }} className="w-full bg-[#171717] text-[10px] text-[#e8eaed] p-1 rounded border border-[#3c4043] outline-none" />
                  ) : (
                     <input type="text" placeholder={newTagType === 'list' ? '[1, 2]' : newTagType === 'dict' ? '{"a": 1}' : 'Value'} value={newTagValue} onChange={e => setNewTagValue(e.target.value)} className="w-full bg-[#171717] text-xs text-[#e8eaed] p-1.5 rounded border border-[#3c4043] outline-none focus:border-[#8ab4f8]" />
                  )}
                </td>
                <td className="p-2 flex justify-end gap-1">
                  <button onClick={handleAddTag} className="text-[10px] bg-[#81c995] text-[#202124] px-2 py-1.5 rounded font-bold hover:bg-[#a8dab5] transition-colors">SAVE</button>
                  <button onClick={() => setIsAdding(false)} className="text-[10px] text-[#9aa0a6] font-bold px-2 py-1.5 hover:text-[#e8eaed] transition-colors">CANCEL</button>
                </td>
              </tr>
            )}
            
            {filteredTags.map(([key, value]) => {
              const type = inferTagType(value);
              return (
                <tr key={key} className="hover:bg-[#303134] transition-colors group">
                  <td className="p-2 font-mono text-[11px] text-[#e8eaed] truncate" title={key}>{key}</td>
                  
                  <td className="p-2 text-center">
                    <span className={`text-[9px] border px-1.5 py-0.5 rounded uppercase font-bold tracking-wider ${getTypeColor(type)}`}>
                      {type === 'base64' ? 'B64' : type}
                    </span>
                  </td>
                  
                  <td className="p-2 font-mono text-[11px]">
                     <div className="truncate w-full block">
                        <MonitorCell value={value} type={type} />
                     </div>
                  </td>

                  <td className="p-2">
                      <div className="flex items-center justify-end gap-1 w-full">
                          {['boolean', 'number', 'string', 'base64', 'list', 'dict', 'json', 'any'].includes(type) && (
                              <div className="flex bg-[#171717] border border-[#3c4043] rounded overflow-hidden opacity-40 group-hover:opacity-100 transition-opacity focus-within:opacity-100 flex-1">
                                  
                                  {type === 'boolean' ? (
                                      <select 
                                          className="bg-transparent text-[9px] font-bold uppercase text-[#e8eaed] p-1.5 outline-none cursor-pointer w-full"
                                          onChange={(e) => handleForceValue(key, type, e.target.value)}
                                          value={String(value)}
                                      >
                                          <option value="true">True</option>
                                          <option value="false">False</option>
                                      </select>
                                  ) : type === 'base64' ? (
                                      <div className="flex gap-1 w-full">
                                          <label className="flex-1 bg-transparent flex justify-center gap-1 items-center text-[9px] font-bold uppercase text-[#e8eaed] p-1.5 outline-none cursor-pointer text-center hover:bg-[#8ab4f8] hover:text-[#202124] transition-colors border-r border-[#3c4043]">
                                              <Upload size={12} /> FILE
                                              <input type="file" accept="image/*" className="hidden" onChange={(e) => {
                                                  const file = e.target.files?.[0];
                                                  if(file) {
                                                      const reader = new FileReader();
                                                      reader.onload = (ev) => handleForceValue(key, 'base64', ev.target?.result as string);
                                                      reader.readAsDataURL(file);
                                                  }
                                              }}/>
                                          </label>
                                          <button onClick={() => handleDownloadImage(key, value)} className="px-2 text-[#81c995] hover:bg-[#81c995] hover:text-[#202124] transition-colors border-r border-[#3c4043]" title="Download Image"><Download size={14}/></button>
                                          <button onClick={() => writeTag(key, 'data:image/empty')} className="px-2 text-[#f28b82] hover:bg-[#f28b82] hover:text-[#202124] transition-colors" title="Clear Image Data"><X size={14}/></button>
                                      </div>
                                  ) : (
                                      <>
                                          <input 
                                              type={type === 'number' ? 'number' : 'text'} 
                                              placeholder="Force..." 
                                              className="bg-transparent text-[10px] text-[#e8eaed] p-1 w-full min-w-0 outline-none px-1.5"
                                              onKeyDown={(e) => {
                                                  if (e.key === 'Enter') { handleForceValue(key, type, e.currentTarget.value); e.currentTarget.value = '';}
                                              }}
                                          />
                                          <button className="bg-[#3c4043] text-[#e8eaed] px-1.5 hover:bg-[#8ab4f8] hover:text-[#202124] transition-colors" title="Press Enter to apply">
                                              <Edit3 size={10}/>
                                          </button>
                                      </>
                                  )}
                              </div>
                          )}

                          {!key.startsWith('SYS_') ? (
                              <button onClick={() => deleteTag(key)} className="text-[#f28b82] p-1.5 hover:bg-white/10 rounded transition-colors" title="Delete Tag">
                                  <Trash2 size={14} />
                              </button>
                          ) : (
                              <div className="p-1.5 cursor-not-allowed" title="System Tag - Protected">
                                  {/* Hiện chữ SYS mờ mờ thay vì nút Xóa */}
                                  <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">SYS</span>
                              </div>
                          )}
                      </div>
                  </td>
                </tr>
              );
            })}
            
            {filteredTags.length === 0 && !isAdding && (
              <tr>
                <td colSpan={4} className="p-8">
                  <div className="text-center text-[#5f6368] text-xs border-dashed border border-[#3c4043] p-6 rounded-xl bg-[#202124] flex flex-col items-center gap-2">
                    <Database size={24} className="opacity-20" />
                    No tags found.
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};