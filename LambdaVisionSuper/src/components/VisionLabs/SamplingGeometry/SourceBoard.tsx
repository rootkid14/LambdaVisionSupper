import { Eye, ImagePlus, Play, Workflow } from 'lucide-react';
import type { LabServiceDefinition } from '../../../api/labServiceApi';
import type { SourceBoardConfig, SourceBoardManifest } from './types';

export const SourceBoard = ({file,onFile,config,onConfig,services,manifest,busy,onBuild,onInspect}:{
  file:File|null; onFile:(file:File|null)=>void; config:SourceBoardConfig; onConfig:(config:SourceBoardConfig)=>void;
  services:LabServiceDefinition[]; manifest:SourceBoardManifest|null; busy:boolean; onBuild:()=>void; onInspect:(name:string)=>void;
}) => {
  const selected=services.find((s)=>s.service_id===config.image_service.service_id);
  return <div className="border-t border-[#3c4043] bg-[#242528] px-3 py-2">
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 min-w-[160px]"><Workflow size={13} className="text-[#8ab4f8]"/><div><div className="text-[9px] font-black">SAMPLING SOURCE</div><div className="text-[8px] text-[#80868b]">one raw image for every unit</div></div></div>
      <label className="flex items-center gap-2 rounded border border-[#5f6368] bg-[#303134] px-2 py-1.5 text-[9px] cursor-pointer"><ImagePlus size={11}/>{file?.name??'Choose image'}<input type="file" accept="image/*" className="hidden" onChange={(e)=>onFile(e.target.files?.[0]??null)}/></label>
      <div className="text-[10px] text-[#5f6368]">→</div>
      <div className="flex items-center gap-2">
        <span className="text-[8px] font-black uppercase text-[#9aa0a6]">Image Processing Service</span>
        <select value={config.image_service.service_id} onChange={(e)=>onConfig({...config,image_service:{service_id:e.target.value,version:null,output_name:''}})} className="max-w-[190px] rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px]"><option value="">Blank = raw image</option>{services.map((s)=><option key={s.service_id} value={s.service_id}>{s.name} · v{s.version}</option>)}</select>
        {selected?<select value={config.image_service.output_name} onChange={(e)=>onConfig({...config,image_service:{...config.image_service,output_name:e.target.value}})} className="max-w-[170px] rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px]"><option value="">Select output</option>{Object.entries(selected.outputs).filter(([,o])=>o.type==='image').map(([name])=><option key={name}>{name}</option>)}</select>:null}
      </div>
      <button disabled={!file||busy} onClick={onBuild} className="ml-auto flex items-center gap-1 rounded border border-[#8ab4f8] bg-[#174ea6] px-2 py-1.5 text-[9px] font-black disabled:opacity-40"><Play size={11}/>Build Source</button>
    </div>
    {manifest?<div className="mt-2 flex gap-1.5 border-t border-[#3c4043] pt-2">{manifest.entries.map((entry)=><button key={entry.name} onClick={()=>onInspect(entry.name)} className="flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124] px-2 py-1 text-[8px] text-[#bdc1c6] hover:border-[#8ab4f8]"><Eye size={9}/>{entry.name}<span className="text-[#5f6368]">{entry.type}</span></button>)}</div>:null}
  </div>;
};
