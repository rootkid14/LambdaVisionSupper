import { Plus, Trash2 } from 'lucide-react';
import type { WorkspaceDefinition } from '../../api/visionAppApi';

type Props={
  workspaces:WorkspaceDefinition[];
  activeId:string;
  onActive:(id:string)=>void;
  onAdd:()=>void;
  onRemove:(id:string)=>void;
};

export const WorkspaceTabs=({workspaces,activeId,onActive,onAdd,onRemove}:Props)=>{
 return <div className="flex h-9 shrink-0 items-center gap-1 border-b border-[#3c4043] bg-[#1d2024] px-2">
  <span className="mr-1 text-[7px] font-black tracking-[.12em] text-[#80868b]">WORKSPACES</span>
  {workspaces.map(w=><div key={w.workspace_id} className={`flex items-center rounded-t border px-2 py-1 text-[8px] ${activeId===w.workspace_id?'border-[#65d1ff] bg-[#25323a] text-[#e8eaed]':'border-[#353940] bg-[#24272c] text-[#8f969e]'}`}><button onClick={()=>onActive(w.workspace_id)} className="max-w-[150px] truncate font-black">{w.name}</button><button onClick={()=>onRemove(w.workspace_id)} className="ml-2 text-[#6f7882] hover:text-[#f28b82]" title="Remove workspace"><Trash2 size={9}/></button></div>)}
  <button className="cv-mini ml-1 text-[#65d1ff]" onClick={onAdd}><Plus size={9}/>Workspace</button>
 </div>;
};
