// src/components/Inspection/InspectionSidebar.tsx
import React from 'react';
import { MonitorPlay, Plus } from 'lucide-react';

export const InspectionSidebar = () => {
  const screens = [
    { id: 1, name: 'Main Dashboard', active: true },
    { id: 2, name: 'Cam Detail Loop', active: false },
    { id: 3, name: 'Alarm View', active: false },
  ];

  return (
    <div className="w-64 h-full bg-slate-800 border-r border-slate-700 flex flex-col z-10 shadow-2xl">
      <div className="p-4 border-b border-slate-700 flex items-center justify-between">
        <h3 className="font-bold text-slate-400 uppercase tracking-widest text-[10px] flex items-center gap-2">
          <MonitorPlay size={14} className="text-emerald-400" /> Active Screens
        </h3>
        <button className="text-slate-400 hover:text-white bg-slate-700 p-1 rounded-md">
          <Plus size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 custom-scrollbar">
        {screens.map((s, idx) => (
          <div key={s.id} className="cursor-pointer">
            <div className={`aspect-video rounded-xl border-2 transition-all flex flex-col items-center justify-center p-2 ${s.active ? 'border-emerald-500 bg-emerald-500/10' : 'border-slate-700 bg-slate-700/30 hover:border-slate-500'}`}>
              <MonitorPlay size={20} className={s.active ? 'text-emerald-400' : 'text-slate-600'} />
              <p className={`text-[10px] mt-2 font-bold uppercase ${s.active ? 'text-white' : 'text-slate-500'}`}>{s.name}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};