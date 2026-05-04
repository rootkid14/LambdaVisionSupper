import { useDBEngineStore, DBFilter } from '../../Stores/DatabaseEngineStore';
import { useFleetStore } from '../../Stores/FleetDashboardStores';
import { Server, Table2, Plus, Trash2, Eye, EyeOff } from 'lucide-react';

// ... (DBLeftPanel giữ nguyên không thay đổi) ...
export const DBLeftPanel = () => { /* Giữ nguyên như phiên bản trước */ 
    const { tables, selectedServerId, selectedTable, setSelectedServer, setSelectedTable } = useDBEngineStore();
    const { master_worker, fleet_worker } = useFleetStore();
    const availableServers = [];
    if (master_worker) availableServers.push({ id: "master_gateway", label: `Master (${master_worker.host})` });
    fleet_worker.forEach(w => availableServers.push({ id: w.server_id, label: `Worker: ${w.server_id} (${w.host})` }));

    return (
        <aside className="w-64 bg-[#28292c] border-r border-[#3c4043] flex flex-col font-sans shrink-0">
            <div className="p-4 border-b border-[#3c4043]">
                <label className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest flex items-center gap-2 mb-2"><Server size={14}/> Server Pool</label>
                <select value={selectedServerId || ''} onChange={(e) => setSelectedServer(e.target.value)} className="w-full bg-[#171717] border border-[#5f6368] rounded px-3 py-2 text-[#e8eaed] text-sm outline-none focus:border-[#8ab4f8] cursor-pointer">
                    <option value="" disabled>-- Select a Server --</option>
                    {availableServers.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                </select>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
                <div className="flex justify-between items-center px-2 mt-2 mb-2">
                    <label className="text-[10px] font-bold text-[#9aa0a6] uppercase tracking-widest flex items-center gap-2"><Table2 size={14}/> Database Tables</label>
                    <button onClick={() => useDBEngineStore.getState().openCreateTableModal()} className="text-[#8ab4f8] hover:bg-[#8ab4f8]/20 p-1 rounded transition-colors"><Plus size={14}/></button>
                </div>
                <div className="flex flex-col gap-1">
                    {tables.map(table => (
                        <button key={table} onClick={() => setSelectedTable(table)} className={`text-left px-3 py-2 rounded text-xs font-mono transition-colors ${selectedTable === table ? 'bg-[#8ab4f8]/20 text-[#8ab4f8] border border-[#8ab4f8]/30' : 'text-[#e8eaed] hover:bg-[#3c4043] border border-transparent'}`}>{table}</button>
                    ))}
                </div>
            </div>
        </aside>
    );
};

export const DBCenterPanel = () => {
    const { schemaConfig, filters, updateColumnConfig, addFilter, updateFilter, removeFilter, executeQuery, isLoading } = useDBEngineStore();
    const columns = Object.values(schemaConfig);

    // Xử lý khi người dùng đổi cột -> Reset operator và value cho chuẩn với Type mới
    const handleColumnChange = (filterId: string, newColName: string) => {
        const type = schemaConfig[newColName]?.dataType || 'text';
        let defaultOp: any = '==';
        let defaultVal: any = '';
        if (type === 'datetime') defaultOp = '>';
        if (type === 'boolean') defaultVal = true;
        updateFilter(filterId, { column: newColName, operator: defaultOp, value: defaultVal });
    };

    // Hàm ma thuật render UI tương ứng với Từng loại Filter
    const renderFilterInput = (f: DBFilter) => {
        const type = schemaConfig[f.column]?.dataType || 'text';

        // 1. Dạng BOOLEAN
        if (type === 'boolean') {
            return (
                <select value={String(f.value)} onChange={e => updateFilter(f.id, { value: e.target.value === 'true' })} className="w-1/3 bg-[#28292c] border border-[#5f6368] rounded px-2 text-[#e8eaed] text-[10px] outline-none">
                    <option value="true">True</option>
                    <option value="false">False</option>
                </select>
            );
        }

        // 2. Dạng DATETIME (Hỗ trợ BETWEEN = From To)
        if (type === 'datetime') {
            if (f.operator === 'BETWEEN') {
                const valArr = Array.isArray(f.value) ? f.value : ['', ''];
                return (
                    <div className="w-1/3 flex gap-1 items-center">
                        <input type="date" value={valArr[0]} onChange={e => updateFilter(f.id, { value: [e.target.value, valArr[1]] })} className="w-1/2 bg-[#28292c] border border-[#5f6368] rounded px-1 py-1 text-[#e8eaed] text-[9px] outline-none" title="From Date" />
                        <span className="text-[#5f6368]">-</span>
                        <input type="date" value={valArr[1]} onChange={e => updateFilter(f.id, { value: [valArr[0], e.target.value] })} className="w-1/2 bg-[#28292c] border border-[#5f6368] rounded px-1 py-1 text-[#e8eaed] text-[9px] outline-none" title="To Date" />
                    </div>
                );
            }
            return <input type="datetime-local" value={f.value as string} onChange={e => updateFilter(f.id, { value: e.target.value })} className="w-1/3 bg-[#28292c] border border-[#5f6368] rounded px-2 py-1 text-[#e8eaed] text-[10px] outline-none" />;
        }

        // 3. Dạng NUMBER
        if (type === 'number') {
            return <input type="number" value={f.value as string} onChange={e => updateFilter(f.id, { value: Number(e.target.value) })} className="w-1/3 bg-[#28292c] border border-[#5f6368] rounded px-2 py-1 text-[#e8eaed] text-[10px] outline-none" placeholder="Num..." />;
        }

        // 4. Mặc định TEXT
        return <input type="text" value={f.value as string} onChange={e => updateFilter(f.id, { value: e.target.value })} className="w-1/3 bg-[#28292c] border border-[#5f6368] rounded px-2 py-1 text-[#e8eaed] text-[10px] outline-none" placeholder="Text..." />;
    };

    return (
        <div className="w-[500px] bg-[#202124] border-r border-[#3c4043] flex flex-col font-sans shrink-0">
            {/* Section 1: Cấu hình Column */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-4 border-b border-[#3c4043]">
                <h3 className="text-[#8ab4f8] font-bold text-xs uppercase tracking-wider mb-3">1. Column Configuration</h3>
                <div className="bg-[#171717] rounded-lg border border-[#3c4043] overflow-hidden">
                    <table className="w-full text-left text-xs">
                        <thead className="bg-[#28292c] border-b border-[#3c4043]">
                            <tr>
                                <th className="p-2 text-[#9aa0a6] font-bold text-[10px] w-8 text-center">Vis</th>
                                <th className="p-2 text-[#9aa0a6] font-bold text-[10px] w-[35%]">Col Name</th>
                                <th className="p-2 text-[#9aa0a6] font-bold text-[10px]">Alias</th>
                                <th className="p-2 text-[#9aa0a6] font-bold text-[10px] text-center">Type</th>
                                <th className="p-2 text-[#9aa0a6] font-bold text-[10px] text-center w-16">Img Path</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#3c4043]">
                            {columns.length === 0 ? <tr><td colSpan={5} className="p-4 text-center text-[#5f6368] italic">Select a table first</td></tr> : null}
                            {columns.map(col => (
                                <tr key={col.originalName} className="hover:bg-[#202124]">
                                    <td className="p-2 text-center">
                                        <button onClick={() => updateColumnConfig(col.originalName, { isVisible: !col.isVisible })} className={`p-1 rounded ${col.isVisible ? 'text-[#81c995]' : 'text-[#5f6368]'}`}>
                                            {col.isVisible ? <Eye size={14}/> : <EyeOff size={14}/>}
                                        </button>
                                    </td>
                                    <td className="p-2 font-mono text-[#e8eaed] text-[10px] truncate max-w-[120px]" title={col.originalName}>
                                        {col.originalName}
                                    </td>
                                    <td className="p-2">
                                        <input value={col.displayName} onChange={(e) => updateColumnConfig(col.originalName, { displayName: e.target.value })} className="w-full bg-transparent border-b border-transparent hover:border-[#5f6368] focus:border-[#8ab4f8] text-[#8ab4f8] outline-none text-[10px]" />
                                    </td>
                                    {/* CỘT TYPE */}
                                    <td className="p-2 text-center text-[#9aa0a6] text-[9px] uppercase font-bold">{col.dataType}</td>
                                    {/* CỘT IMG PATH (Chỉ hiện checkbox nếu là dạng Text) */}
                                    <td className="p-2 text-center">
                                        {col.dataType === 'text' && (
                                            <input type="checkbox" checked={col.isImage} onChange={e => updateColumnConfig(col.originalName, { isImage: e.target.checked })} className="accent-[#fcd663] w-3 h-3 cursor-pointer" />
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Section 2: Filters Builder */}
            <div className="h-[250px] p-4 flex flex-col">
                <div className="flex justify-between items-center mb-3">
                    <h3 className="text-[#8ab4f8] font-bold text-xs uppercase tracking-wider">2. Query Filters</h3>
                    <button onClick={addFilter} className="flex items-center gap-1 px-2 py-1 bg-[#8ab4f8]/10 text-[#8ab4f8] rounded text-[10px] font-bold hover:bg-[#8ab4f8]/20"><Plus size={12}/> ADD</button>
                </div>
                <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2 custom-scrollbar">
                    {filters.map(f => {
                        const type = schemaConfig[f.column]?.dataType || 'text';
                        return (
                            <div key={f.id} className="flex items-stretch gap-2 bg-[#171717] p-2 rounded border border-[#3c4043]">
                                <select value={f.column} onChange={e => handleColumnChange(f.id, e.target.value)} className="w-1/3 bg-[#28292c] border border-[#5f6368] rounded px-1 py-1 text-[#e8eaed] text-[10px] outline-none">
                                    <option value="">- Col -</option>
                                    {columns.map(c => <option key={c.originalName} value={c.originalName}>{c.originalName}</option>)}
                                </select>
                                
                                <select value={f.operator} onChange={e => updateFilter(f.id, { operator: e.target.value as any, value: e.target.value === 'BETWEEN' ? ['',''] : '' })} className="w-1/4 bg-[#28292c] border border-[#5f6368] rounded px-1 text-[#fcd663] font-bold text-[9px] outline-none text-center text-center">
                                    {/* Render options dựa theo Type */}
                                    {type === 'boolean' && <option value="==">==</option>}
                                    {type === 'number' && <><option value="==">==</option><option value="!=">!=</option><option value=">">&gt;</option><option value="<">&lt;</option></>}
                                    {type === 'datetime' && <><option value=">">&gt;</option><option value="<">&lt;</option><option value="BETWEEN">BETWEEN</option></>}
                                    {type === 'text' && <><option value="==">==</option><option value="!=">!=</option><option value="CONTAINS">LIKE</option></>}
                                </select>
                                
                                {/* Gọi hàm ma thuật render input */}
                                {renderFilterInput(f)}

                                <button onClick={() => removeFilter(f.id)} className="text-[#5f6368] hover:text-[#f28b82] flex items-center justify-center px-1"><Trash2 size={14}/></button>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Section 3: Execute */}
            <div className="p-4 bg-[#171717] border-t border-[#3c4043]">
                <button onClick={executeQuery} disabled={isLoading} className="w-full py-3 bg-[#81c995] text-[#202124] font-bold rounded-lg hover:bg-[#a8dab5] disabled:opacity-50 transition-colors flex justify-center items-center">
                    {isLoading ? 'EXECUTING SCRIPT...' : 'EXECUTE QUERY'}
                </button>
            </div>
        </div>
    );
};