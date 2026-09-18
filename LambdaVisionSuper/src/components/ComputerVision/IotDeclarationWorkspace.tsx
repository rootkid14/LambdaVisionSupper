import { useMemo, useState } from 'react';
import { Activity, ChevronDown, ChevronRight, Cpu, Database, Plus, Trash2, Wifi } from 'lucide-react';
import type { IotDeclarationConfig, ModbusDeviceDeclaration, ModbusPointDeclaration, ModbusPointKind } from '../../api/visionAppApi';

type Props={config:IotDeclarationConfig;onChange:(next:IotDeclarationConfig)=>void};

const makePoint=(index:number,kind:ModbusPointKind='coil'):ModbusPointDeclaration=>({
 point_id:`point_${Date.now()}_${Math.random().toString(36).slice(2,6)}`,
 alias:`P${index}`,
 enabled:true,
 kind,
 address:0,
 description:'',
 pulse_seconds:1,
});
const makeDevice=(index:number):ModbusDeviceDeclaration=>({
 declaration_id:`modbus_${Date.now()}_${Math.random().toString(36).slice(2,6)}`,
 alias:`modbus_${index}`,
 enabled:true,
 driver:'modbus_tcp',
 host:'192.168.1.177',
 port:502,
 unit_id:1,
 points:[],
});
const safeAlias=(value:string)=>value.trim().replace(/[^A-Za-z0-9_]+/g,'_').replace(/^([0-9])/,'_$1')||'unnamed';
const kindMeta:Record<ModbusPointKind,{label:string;color:string;rw:string}>={
 coil:{label:'Coil',color:'#81c995',rw:'R/W'},
 discrete_input:{label:'Discrete Input',color:'#8ab4f8',rw:'R'},
 holding_register:{label:'Holding Register',color:'#fdd663',rw:'R/W'},
 input_register:{label:'Input Register',color:'#c58af9',rw:'R'},
};

export const IotDeclarationWorkspace=({config,onChange}:Props)=>{
 const [selectedId,setSelectedId]=useState<string|null>(config.devices[0]?.declaration_id??null);
 const [expanded,setExpanded]=useState<Record<string,boolean>>({});
 const selected=config.devices.find(d=>d.declaration_id===selectedId)??config.devices[0]??null;
 const patchDevice=(id:string,patch:Partial<ModbusDeviceDeclaration>)=>onChange({...config,devices:config.devices.map(d=>d.declaration_id===id?{...d,...patch}:d)});
 const patchPoint=(deviceId:string,pointId:string,patch:Partial<ModbusPointDeclaration>)=>onChange({...config,devices:config.devices.map(d=>d.declaration_id===deviceId?{...d,points:d.points.map(p=>p.point_id===pointId?{...p,...patch}:p)}:d)});
 const addDevice=()=>{const d=makeDevice(config.devices.length+1);onChange({...config,devices:[...config.devices,d]});setSelectedId(d.declaration_id);};
 const removeDevice=(id:string)=>{const devices=config.devices.filter(d=>d.declaration_id!==id);onChange({...config,devices});setSelectedId(devices[0]?.declaration_id??null);};
 const addPoint=(device:ModbusDeviceDeclaration,kind:ModbusPointKind)=>patchDevice(device.declaration_id,{points:[...device.points,makePoint(device.points.length+1,kind)]});
 const enabledPoints=useMemo(()=>config.devices.reduce((n,d)=>n+d.points.filter(p=>p.enabled).length,0),[config.devices]);
 return <div className="flex h-full min-h-0 flex-col bg-[#17191d] text-[#e8eaed]">
  <div className="flex h-11 items-center gap-3 border-b border-[#34363a] bg-[#22252a] px-4">
   <Wifi size={15} className="text-[#65d1ff]"/><div><div className="text-[10px] font-black tracking-[.14em]">IOT DECLARATION ENGINE</div><div className="text-[7px] text-[#8b949e]">Declarations belong to the active Workspace. Automation IDE receives only this Workspace's typed live endpoints.</div></div>
   <div className="ml-auto flex items-center gap-2 text-[7px]"><span className="rounded bg-[#14354a] px-2 py-1 text-[#65d1ff]">{config.devices.length} device(s)</span><span className="rounded bg-[#203525] px-2 py-1 text-[#81c995]">{enabledPoints} endpoint(s)</span><button className="cv-btn border-[#65d1ff] text-[#65d1ff]" onClick={addDevice}><Plus size={10}/>Declare Modbus TCP</button></div>
  </div>
  <div className="grid min-h-0 flex-1 grid-cols-[290px_minmax(0,1fr)]">
   <aside className="overflow-y-auto border-r border-[#34363a] bg-[#1d2025]">
    <div className="p-2 text-[7px] font-black uppercase tracking-[.14em] text-[#8b949e]">Declared Devices</div>
    {config.devices.map(d=>{const active=(selected?.declaration_id===d.declaration_id);return <button key={d.declaration_id} onClick={()=>setSelectedId(d.declaration_id)} className={`mx-2 mb-2 w-[calc(100%-16px)] rounded-lg border p-3 text-left transition ${active?'border-[#65d1ff] bg-[#183243] shadow-[0_0_0_1px_rgba(101,209,255,.15)]':'border-[#34363a] bg-[#24272d] hover:border-[#56606a]'}`}><div className="flex items-center gap-2"><Cpu size={13} className={active?'text-[#65d1ff]':'text-[#8b949e]'}/><b className="truncate text-[10px]">{d.alias}</b><span className={`ml-auto h-2 w-2 rounded-full ${d.enabled?'bg-[#81c995]':'bg-[#5f6368]'}`}/></div><div className="mt-1 font-mono text-[7px] text-[#8b949e]">{d.host}:{d.port} · unit {d.unit_id}</div><div className="mt-2 flex gap-1"><span className="rounded bg-[#202124] px-1.5 py-0.5 text-[6px] text-[#c58af9]">MODBUS TCP</span><span className="rounded bg-[#202124] px-1.5 py-0.5 text-[6px] text-[#fdd663]">{d.points.length} point(s)</span></div></button>})}
    {!config.devices.length?<div className="p-8 text-center text-[8px] leading-5 text-[#6f7782]">No IOT device declared.<br/>Declare a Modbus TCP device to create real <span className="font-mono text-[#65d1ff]">device.*</span> objects.</div>:null}
   </aside>
   <main className="min-w-0 overflow-y-auto p-4">
    {selected?<div className="mx-auto max-w-[1050px] space-y-4">
     <section className="rounded-xl border border-[#34363a] bg-[#22252a] shadow-xl"><div className="flex items-center gap-2 border-b border-[#34363a] px-4 py-3"><Activity size={14} className="text-[#65d1ff]"/><b className="text-[10px]">DEVICE DECLARATION</b><label className="ml-auto flex items-center gap-2 text-[8px]"><input type="checkbox" checked={selected.enabled} onChange={e=>patchDevice(selected.declaration_id,{enabled:e.target.checked})}/>Enabled</label><button className="cv-icon text-[#f28b82]" onClick={()=>removeDevice(selected.declaration_id)}><Trash2 size={11}/></button></div><div className="grid grid-cols-5 gap-3 p-4 text-[8px]"><label>Object alias<input className="cv-field" value={selected.alias} onChange={e=>patchDevice(selected.declaration_id,{alias:e.target.value})}/><div className="mt-1 font-mono text-[6px] text-[#65d1ff]">device.{safeAlias(selected.alias)}</div></label><label>Driver<select className="cv-field" value={selected.driver} onChange={e=>patchDevice(selected.declaration_id,{driver:e.target.value as any})}><option value="modbus_tcp">Modbus TCP</option>{selected.driver==='simulated'?<option value="simulated" disabled>Simulated (legacy hidden)</option>:null}</select></label><label>Host<input className="cv-field" value={selected.host} onChange={e=>patchDevice(selected.declaration_id,{host:e.target.value})}/></label><label>Port<input type="number" className="cv-field" value={selected.port} onChange={e=>patchDevice(selected.declaration_id,{port:Number(e.target.value)})}/></label><label>Unit ID<input type="number" className="cv-field" value={selected.unit_id} onChange={e=>patchDevice(selected.declaration_id,{unit_id:Number(e.target.value)})}/></label></div></section>
     <section className="rounded-xl border border-[#34363a] bg-[#22252a] shadow-xl"><div className="flex items-center gap-2 border-b border-[#34363a] px-4 py-3"><Database size={14} className="text-[#c58af9]"/><div><b className="text-[10px]">POINT DECLARATIONS</b><div className="text-[7px] text-[#8b949e]">Each alias becomes an actual Endpoint Registry object immediately.</div></div><div className="ml-auto flex gap-1"><button className="cv-mini text-[#81c995]" onClick={()=>addPoint(selected,'coil')}>+ Coil</button><button className="cv-mini text-[#8ab4f8]" onClick={()=>addPoint(selected,'discrete_input')}>+ DI</button><button className="cv-mini text-[#fdd663]" onClick={()=>addPoint(selected,'holding_register')}>+ Holding</button><button className="cv-mini text-[#c58af9]" onClick={()=>addPoint(selected,'input_register')}>+ Input Reg</button></div></div>
      <div className="p-3">{selected.points.map(point=>{const meta=kindMeta[point.kind];const open=expanded[point.point_id]??true;const endpoint=`device.${safeAlias(selected.alias)}.${safeAlias(point.alias)}`;return <div key={point.point_id} className="mb-2 overflow-hidden rounded-lg border border-[#34363a] bg-[#1c1f24]"><button onClick={()=>setExpanded(x=>({...x,[point.point_id]:!open}))} className="flex w-full items-center gap-2 px-3 py-2 text-left"><span style={{color:meta.color}}>{open?<ChevronDown size={12}/>:<ChevronRight size={12}/>}</span><Activity size={10} style={{color:meta.color}}/><b className="text-[9px]">{point.alias}</b><span className="rounded px-1.5 py-0.5 text-[6px] font-black" style={{background:`${meta.color}18`,color:meta.color}}>{meta.label}</span><span className="rounded bg-[#2b2f35] px-1.5 py-0.5 text-[6px] text-[#9da7b1]">{meta.rw}</span><span className="ml-auto font-mono text-[7px] text-[#65d1ff]">{endpoint}</span><input onClick={e=>e.stopPropagation()} type="checkbox" checked={point.enabled} onChange={e=>patchPoint(selected.declaration_id,point.point_id,{enabled:e.target.checked})}/></button>{open?<div className="grid grid-cols-[180px_170px_130px_1fr_30px] gap-2 border-t border-[#2d3137] p-3 text-[7px]"><label>Alias<input className="cv-field" value={point.alias} onChange={e=>patchPoint(selected.declaration_id,point.point_id,{alias:e.target.value})}/></label><label>Type<select className="cv-field" value={point.kind} onChange={e=>patchPoint(selected.declaration_id,point.point_id,{kind:e.target.value as ModbusPointKind})}><option value="coil">Coil</option><option value="discrete_input">Discrete Input</option><option value="holding_register">Holding Register</option><option value="input_register">Input Register</option></select></label><label>Address<input type="number" className="cv-field" value={point.address} onChange={e=>patchPoint(selected.declaration_id,point.point_id,{address:Number(e.target.value)})}/></label><label>Description<input className="cv-field" value={point.description} onChange={e=>patchPoint(selected.declaration_id,point.point_id,{description:e.target.value})}/>{point.kind==='coil'?<div className="mt-1 text-[6px] text-[#81c995]">Action: <span className="font-mono">{endpoint}.pulse(seconds)</span></div>:null}</label><button className="cv-icon mt-[13px] text-[#f28b82]" onClick={()=>patchDevice(selected.declaration_id,{points:selected.points.filter(p=>p.point_id!==point.point_id)})}><Trash2 size={10}/></button></div>:null}</div>})}{!selected.points.length?<div className="rounded border border-dashed border-[#3c4043] p-8 text-center text-[8px] text-[#6f7782]">Declare points such as X1, Y_OK, pressure, temperature...<br/>They will appear in Automation IDE IntelliSense without hard-coded instructions.</div>:null}</div>
     </section>
    </div>:<div className="flex h-full items-center justify-center text-center"><div><Wifi size={38} className="mx-auto mb-3 text-[#3f4c57]"/><div className="text-[11px] font-black">IOT Declaration Engine</div><div className="mt-2 text-[8px] text-[#6f7782]">Declare your first device to create typed hardware objects.</div></div></div>}
   </main>
  </div>
 </div>;
};
