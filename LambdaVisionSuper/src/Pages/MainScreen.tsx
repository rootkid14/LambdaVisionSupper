import { useState, useEffect } from 'react';
import { Search, Database, ChevronUp, Server, User, Network } from 'lucide-react'; 
import { TbLambda } from "react-icons/tb"; 
import { useNavigate } from 'react-router-dom';
import { NeonActionBar, ActionItem } from '../Commons/NeonActionBar';

// =========================================
// COMPONENT: HIỆU ỨNG GÕ CHỮ KIỂU AI (LLM)
// =========================================
const TypewriterMessage = () => {
  const [text, setText] = useState('');
  
  // Dòng chữ hệ thống sẽ tự động gõ
  const fullText = 
  "> LAMBDA AGENTIC READY\n\n" + 
  "> Orchestrating Distributed | Agentic AI | Computer Vision | Industrial Automation";

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      setText(fullText.slice(0, i));
      i++;
      if (i > fullText.length) clearInterval(timer);
    }, 20); // Tốc độ gõ chữ (ms)
    
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="mt-8 text-[#8ab4f8] font-mono text-xs sm:text-sm max-w-2xl text-center bg-[#171717]/60 border border-[#3c4043] px-6 py-3 rounded-lg shadow-[0_0_20px_rgba(138,180,248,0.1)] backdrop-blur-sm h-auto min-h-[46px] flex items-center justify-center">
      <p>
        {text}<span className="animate-pulse text-[#e8eaed]">█</span>
      </p>
    </div>
  );
};

export const MainScreen = () => {
  const navigate = useNavigate();

  const homeActions: ActionItem[] = [
    { id: 'fleet', label: 'Resources', icon: Server, activeColor: 'cyan', onClick: () => navigate('/fleet') },
    { id: 'inspection', label: 'App Builder', icon: Search, activeColor: 'emerald', onClick: () => navigate('/inspection') },
    { id: 'data', label: 'DataBase', icon: Database, activeColor: 'orange', onClick: () => navigate('/data') }
  ];

  return (
    <div className="relative min-h-screen bg-[#0d0e12] flex flex-col items-center justify-center overflow-hidden font-sans selection:bg-[#b026ff]/30">
      
      {/* ========================================= */}
      {/* LỚP 0: THÔNG TIN CONTACT (TOP RIGHT)        */}
      {/* ========================================= */}
      <div className="absolute top-6 right-8 flex flex-col items-end opacity-40 hover:opacity-100 transition-opacity duration-500 font-mono text-xs text-[#9aa0a6] z-50 cursor-default">
         <span className="text-[#d08ef7] font-bold mb-1.5 uppercase tracking-widest flex items-center gap-2 drop-shadow-[0_0_10px_rgba(176,38,255,0.5)]">
           <User size={18}/> Developer Contact
         </span>
         <span className="text-[#e8eaed] font-bold text-sm tracking-wider">Harry - Hieu Do</span>
         <span className="mt-0.5">Tel: 84 366971242</span>
         <span className="mt-0.5">Email: lambda.tech@outlook.com</span>
      </div>

      {/* ========================================= */}
      {/* LỚP 1: HIỆU ỨNG NỀN (GRID & GLOWING)      */}
      {/* ========================================= */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#3c404330_1px,transparent_1px),linear-gradient(to_bottom,#3c404330_1px,transparent_1px)] bg-[size:48px_48px]"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#0d0e12_80%)] pointer-events-none"></div>
      <div className="absolute bottom-0 left-0 right-0 h-[50vh] bg-gradient-to-t from-[#8ab4f8]/10 via-[#b026ff]/5 to-transparent pointer-events-none blur-3xl"></div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#b026ff]/10 blur-[120px] rounded-full pointer-events-none"></div>

      {/* ========================================= */}
      {/* LỚP 2: CỤM LOGO & TIÊU ĐỀ CHÍNH           */}
      {/* ========================================= */}
      <div className="z-10 flex flex-col items-center justify-center -translate-y-16">
        
        {/* Vòng sáng xoay mờ ảo sau Logo */}
        <div className="relative flex items-center justify-center">
           <div className="absolute w-48 h-48 bg-[#b026ff]/20 rounded-full blur-2xl animate-pulse"></div>
           
           {/* LOGO LAMBDA: Béo hơn (strokeWidth={3.5}) và màu tím Neon rực rỡ */}
           <TbLambda 
              strokeWidth={2.5} 
              className="relative text-[220px] sm:text-[260px] text-[#c56bfa] drop-shadow-[0_0_60px_rgba(176,38,255,0.9)] filter transition-all duration-700 hover:scale-105 hover:drop-shadow-[0_0_100px_rgba(176,38,255,1)]" 
           />
        </div>
        
        {/* Tên Ứng Dụng (Đã được buff Neon cực mạnh) */}
        <h1 
          className="mt-4 text-transparent bg-clip-text bg-gradient-to-r from-[#e8eaed] via-[#d946ef] to-[#8ab4f8] font-bold font-mono tracking-[0.25em] uppercase text-2xl sm:text-4xl select-none text-center"
          style={{
            // Xếp chồng 2 lớp drop-shadow: Lớp tím đậm tỏa gần + Lớp xanh dương tỏa xa
            filter: 'drop-shadow(0 0 15px rgba(217,70,239,0.9)) drop-shadow(0 0 40px rgba(138,180,248,0.6))'
          }}
        >
          LAMBDA AGENTIC
        </h1>

        {/* Cụm Phiên Bản: Text to hơn (text-sm sm:text-base) */}
        <div className="mt-6 flex items-center gap-4 opacity-70">
          <div className="h-[1px] w-20 bg-gradient-to-r from-transparent to-[#9aa0a6]"></div>
          <span className="flex items-center gap-2 text-[#9aa0a6] font-mono tracking-[0.4em] uppercase text-sm sm:text-base font-bold select-none">
            <Network size={22} className="text-[#8ab4f8]" /> AGENTIC AI ENGINE
          </span>
          <div className="h-[1px] w-20 bg-gradient-to-l from-transparent to-[#9aa0a6]"></div>
        </div>

        {/* ========================================= */}
        {/* COMPONENT: GỌI HIỆU ỨNG CHẠY CHỮ Ở ĐÂY    */}
        {/* ========================================= */}
        <TypewriterMessage />

      </div>

      {/* ========================================= */}
      {/* LỚP 3: KHU VỰC CẢM BIẾN TRIGGER ZONE      */}
      {/* ========================================= */}
      <div className="group absolute bottom-0 left-0 w-full h-56 flex flex-col items-center justify-end pb-8 z-20 cursor-pointer">
        

        <div className=" scale-95 transition-all duration-700 group-hover:translate-y-0 mb-2">
          <NeonActionBar items={homeActions} activeId={null} />
        </div>

      </div>
    </div>
  );
};