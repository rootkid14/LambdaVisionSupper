import { Plus, Trash2 } from 'lucide-react';
import type { WorkspaceDefinition } from '../../api/visionAppApi';

type Props={workspaces:WorkspaceDefinition[];activeId:string;onActive:(id:string)=>void;onChange:(next:WorkspaceDefinition[])=>void};
const makeWorkspace=(index:number):WorkspaceDefinition=>({
 workspace_id:`workspace_${Date.now()}_${Math.random().toString(36).slice(2,6)}`,
 name:`Workspace ${index}`,
 alias:`workspace_${index}`,
 enabled:true,
 camera_id:'',
 input_binding:'',
 master:{rois:[],master_shape:[],locator:{method:'manual',blur_kernel:9,template_threshold:.65,geometry:{enabled:true,search_margin_px:80,max_shift_px:120}}},
 working:{global_scope:{enable_filter:true,filter_services:[],enable_logic:true,logic_services:[],enable_decision:false,decision:{script:''}},station_scopes:{},station_execution:'sequential',global_services:[],station_services:{}},
});
export const WorkspaceTabs=({workspaces,activeId,onActive,onChange}:Props)=>{
 const add=()=>{const w=makeWorkspace(workspaces.length+1);onChange([...workspaces,w]);onActive(w.workspace_id);};
 const remove=(id:string)=>{if(workspaces.length<=1)return;const next=workspaces.filter(w=>w.workspace_id!==id);onChange(next);if(activeId===id)onActive(next[0].workspace_id);};
 return <div className="flex h-9 shrink-0 items-center gap-1 border-b border-[#3c4043] bg-[#1d2024] px-2">
  <span className="mr-1 text-[7px] font-black tracking-[.12em] text-[#80868b]">WORKSPACES</span>
  {workspaces.map(w=><div key={w.workspace_id} className={`flex items-center rounded-t border px-2 py-1 text-[8px] ${activeId===w.workspace_id?'border-[#65d1ff] bg-[#25323a] text-[#e8eaed]':'border-[#353940] bg-[#24272c] text-[#8f969e]'}`}><button onClick={()=>onActive(w.workspace_id)} className="max-w-[150px] truncate font-black">{w.name}</button><button onClick={()=>remove(w.workspace_id)} className="ml-2 text-[#6f7882] hover:text-[#f28b82]" title="Remove workspace"><Trash2 size={9}/></button></div>)}
  <button className="cv-mini ml-1 text-[#65d1ff]" onClick={add}><Plus size={9}/>Workspace</button>
 </div>;
};
