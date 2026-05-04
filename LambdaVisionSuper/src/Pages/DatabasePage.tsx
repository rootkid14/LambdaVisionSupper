import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Database } from 'lucide-react';
import { DBLeftPanel, DBCenterPanel } from '../components/DataBaseEngine/DBPanels';
import { DBResultGrid } from '../components/DataBaseEngine/DBResultGrid';
import { DBErrorModal, DBImageModal, CreateTableModal } from '../components/DataBaseEngine/DBModals';

export const DatabasePage = () => {
    const navigate = useNavigate();

    return (
        <div className="h-screen w-screen bg-[#202124] text-[#e8eaed] flex flex-col overflow-hidden font-sans">
            
            {/* Header (Tái sử dụng style chuẩn của hệ thống) */}
            <header className="h-16 bg-[#303134] border-b border-[#3c4043] flex items-center px-4 z-30 shrink-0 shadow-lg">
                <button onClick={() => navigate('/')} className="group flex items-center justify-center w-8 h-8 bg-[#202124] border border-[#5f6368] hover:border-[#8ab4f8] hover:bg-[#8ab4f8]/10 text-[#e8eaed] hover:text-[#8ab4f8] rounded-md transition-all mr-4">
                    <ArrowLeft size={18} className="group-hover:-translate-x-0.5 transition-transform duration-200" />
                </button>
                <div className="w-px h-8 bg-[#3c4043] mr-4"></div>
                <div className="flex flex-col justify-center">
                    <h1 className="font-extrabold text-[#e8eaed] text-[13px] tracking-wide leading-tight flex items-baseline gap-1">
                        <span className="text-[#e580ff]">LAMBDA VISION</span>
                        <span className="text-[#81c995] text-[9px] px-1 py-0.5 bg-[#81c995]/10 rounded border border-[#81c995]/20 ml-0.5">TRACEABILITY</span>
                    </h1>
                    <div className="flex items-center gap-1.5 mt-0.5">
                        <Database size={10} className="text-[#8ab4f8]"/>
                        <span className="text-[#9aa0a6] text-[9px] font-bold tracking-[0.2em] uppercase font-mono">DB Explorer Engine</span>
                    </div>
                </div>
            </header>

            {/* Phân khu 3 Panels */}
            <div className="flex-1 flex overflow-hidden">
                <DBLeftPanel />
                <DBCenterPanel />
                <DBResultGrid />
            </div>

            {/* Modals Cấp cao */}
            <DBErrorModal />
            <DBImageModal />
            <CreateTableModal/>
        </div>
    );
};