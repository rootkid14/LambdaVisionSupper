import React, { useState } from 'react';
import { useDBEngineStore } from '../../Stores/DatabaseEngineStore';
import { DBEngineAPI } from '../../api/dbEngineApi';
import { X, AlertCircle, Download, Database, Plus, Trash2 } from 'lucide-react';

export const DBErrorModal = () => {
    const { errorModal, closeErrorModal } = useDBEngineStore();
    if (!errorModal.isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center font-sans">
            <div className="bg-[#28292c] border border-[#f28b82] rounded-xl shadow-2xl w-96 overflow-hidden">
                <div className="bg-[#f28b82]/20 px-4 py-3 border-b border-[#f28b82]/30 flex items-center gap-2">
                    <AlertCircle className="text-[#f28b82]" size={18} />
                    <h3 className="text-[#f28b82] font-bold text-sm">Database Error</h3>
                </div>
                <div className="p-5 text-[#e8eaed] text-sm">
                    {errorModal.ErrorMessage}
                </div>
                <div className="px-4 py-3 bg-[#171717] flex justify-end">
                    <button onClick={closeErrorModal} className="px-4 py-1.5 rounded-lg text-xs font-bold bg-[#f28b82]/20 text-[#f28b82] hover:bg-[#f28b82]/30 transition-colors">CLOSE</button>
                </div>
            </div>
        </div>
    );
};

export const DBImageModal = () => {
    const { imageModal, closeImageViewModal, selectedServerId, downloadImage } = useDBEngineStore();
    
    if (!imageModal.isOpen || !imageModal.imageFileName || !selectedServerId) return null;

    const isMaster = selectedServerId === "master_gateway";

    // CLEAN CODE: Gọi API để tạo chuỗi URL thay vì hardcode thủ công
    const imageUrl = isMaster 
        ? DBEngineAPI.master_getImageUrl(imageModal.imageFileName)
        : DBEngineAPI.proxy_getImageUrl(selectedServerId, imageModal.imageFileName);

    return (
        <div className="fixed inset-0 z-[90] bg-black/90 flex flex-col items-center justify-center font-sans">
            <div className="absolute top-4 right-4 flex gap-3">
                {/* Nút Download gọi trực tiếp hàm trong Store */}
                <button onClick={() => downloadImage(imageModal.imageFileName as string)} className="p-2 bg-[#303134] hover:bg-[#3c4043] rounded-full text-[#8ab4f8] transition-colors" title="Download Image">
                    <Download size={20} />
                </button>
                <button onClick={closeImageViewModal} className="p-2 bg-[#303134] hover:bg-[#f28b82]/20 rounded-full text-[#e8eaed] hover:text-[#f28b82] transition-colors" title="Close Preview">
                    <X size={20} />
                </button>
            </div>
            
            <div className="relative max-w-[90vw] max-h-[85vh] rounded border border-[#3c4043] overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.8)]">
                {/* Dùng URL sạch từ API */}
                <img 
                    src={imageUrl} 
                    alt="Inspection Defect" 
                    className="w-full h-full object-contain bg-[#171717]"
                    // Xử lý chống vỡ UI nếu ảnh lỗi / không tồn tại
                    onError={(e) => {
                        (e.target as HTMLImageElement).src = "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%235f6368' stroke-width='1' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='18' height='18' rx='2' ry='2'%3E%3C/rect%3E%3Ccircle cx='8.5' cy='8.5' r='1.5'%3E%3C/circle%3E%3Cpolyline points='21 15 16 10 5 21'%3E%3C/polyline%3E%3C/svg%3E";
                    }}
                />
            </div>
            <div className="mt-4 text-[#9aa0a6] font-mono text-sm">
                File: {imageModal.imageFileName}
            </div>
        </div>
    );
};

export const CreateTableModal = () => {
    const { isCreateTableModalOpen, closeCreateTableModal, createTable } = useDBEngineStore();
    const [tableName, setTableName] = useState('');
    const [columns, setColumns] = useState([{ name: '', type: 'TEXT' }]);

    if (!isCreateTableModalOpen) return null;

    const handleCreate = () => {
        if (!tableName.trim()) return;
        const validColumns = columns.filter(c => c.name.trim() !== '');
        createTable({ table_name: tableName.trim(), columns: validColumns });
        setTableName('');
        setColumns([{ name: '', type: 'TEXT' }]);
    };

    return (
        <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center font-sans">
            <div className="bg-[#28292c] border border-[#3c4043] rounded-xl shadow-2xl w-[500px] overflow-hidden flex flex-col">
                <div className="bg-[#303134] px-5 py-4 border-b border-[#3c4043] flex items-center gap-2">
                    <Database className="text-[#8ab4f8]" size={18} />
                    <h3 className="text-[#e8eaed] font-bold text-sm uppercase tracking-wider">Create New Table</h3>
                </div>
                
                <div className="p-5 flex flex-col gap-4 overflow-y-auto max-h-[60vh] custom-scrollbar">
                    <div>
                        <label className="text-xs font-bold text-[#9aa0a6] uppercase mb-1.5 block">Table Name</label>
                        <input value={tableName} onChange={e => setTableName(e.target.value.replace(/[^a-zA-Z0-9_]/g, ''))} className="w-full bg-[#171717] border border-[#3c4043] text-[#e8eaed] p-2.5 rounded outline-none focus:border-[#8ab4f8]" placeholder="e.g. inspection_logs" />
                    </div>
                    
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-bold text-[#9aa0a6] uppercase flex justify-between items-center">
                            Columns Definition
                            <button onClick={() => setColumns([...columns, { name: '', type: 'TEXT' }])} className="text-[#81c995] hover:bg-[#81c995]/20 px-2 py-1 rounded flex items-center gap-1"><Plus size={12}/> ADD COL</button>
                        </label>
                        <div className="flex gap-2 items-center bg-[#202124] p-2 rounded border border-[#3c4043] opacity-60">
                            <span className="flex-1 text-[#fcd663] text-sm font-mono pl-2">id</span>
                            <span className="w-1/3 text-[#9aa0a6] text-xs font-bold uppercase text-center">INTEGER (PK)</span>
                            <div className="w-6"></div>
                        </div>
                        {columns.map((col, idx) => (
                            <div key={idx} className="flex gap-2 items-center bg-[#202124] p-2 rounded border border-[#3c4043]">
                                <input 
                                    value={col.name} 
                                    onChange={e => { const nc = [...columns]; nc[idx].name = e.target.value.replace(/[^a-zA-Z0-9_]/g, ''); setColumns(nc); }} 
                                    className="flex-1 bg-[#171717] border border-[#3c4043] text-[#8ab4f8] text-sm p-2 rounded outline-none font-mono" 
                                    placeholder="column_name" 
                                />
                                <select 
                                    value={col.type} 
                                    onChange={e => { const nc = [...columns]; nc[idx].type = e.target.value; setColumns(nc); }} 
                                    className="w-1/3 bg-[#171717] border border-[#3c4043] text-[#e8eaed] text-xs p-2 rounded outline-none cursor-pointer"
                                >
                                    <option value="TEXT">TEXT</option>
                                    <option value="REAL">NUMBER (REAL)</option>
                                    <option value="INTEGER">INTEGER</option>
                                    <option value="BOOLEAN">BOOLEAN</option>
                                    {/* THÊM LỰA CHỌN DATETIME VÀO ĐÂY */}
                                    <option value="DATETIME">DATETIME</option>
                                </select>
                                <button onClick={() => setColumns(columns.filter((_, i) => i !== idx))} className="text-[#5f6368] hover:text-[#f28b82] p-2">
                                    <Trash2 size={16}/>
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="px-5 py-4 bg-[#202124] border-t border-[#3c4043] flex justify-end gap-3 shrink-0">
                    <button onClick={closeCreateTableModal} className="px-5 py-2 rounded font-bold text-xs text-[#9aa0a6] hover:bg-[#3c4043] transition-colors">CANCEL</button>
                    <button onClick={handleCreate} disabled={!tableName} className="px-5 py-2 rounded font-bold text-xs bg-[#8ab4f8] text-[#202124] hover:bg-[#a8c7fa] disabled:opacity-50 transition-colors">CREATE TABLE</button>
                </div>
            </div>
        </div>
    );
};