import { Activity, CheckCircle2, XCircle } from 'lucide-react';
import type { ModbusIOConfig } from '../../api/visionAppApi';

type Props={config:ModbusIOConfig;onChange:(next:ModbusIOConfig)=>void;onRead:()=>void;onPulse:(result:'ok'|'ng')=>void;triggerState:boolean|null;busy:boolean};
export const IotModulePanel=({config,onChange,onRead,onPulse,triggerState,busy}:Props)=>{
 const patch=(p:Partial<ModbusIOConfig>)=>onChange({...config,...p});
 const num=(name:keyof ModbusIOConfig,value:string)=>patch({[name]:Number(value)} as any);
 return <div className="space-y-3 p-3 text-[9px]">
  <div className="rounded-lg border border-[#3c4043] bg-[#242528] p-3"><div className="flex items-center gap-2 text-[10px] font-black"><Activity size={13} className="text-[#8ab4f8]"/>MODBUS TCP I/O</div><div className="mt-1 text-[8px] leading-4 text-[#9aa0a6]">Trigger input starts the Vision Program. Final OK/NG pulses the configured output coil for the selected duration.</div></div>
  <label className="flex items-center gap-2"><input type="checkbox" checked={config.enabled} onChange={e=>patch({enabled:e.target.checked})}/>Enable I/O</label>
  <div className="grid grid-cols-2 gap-2">
   <label>Host<input value={config.host} onChange={e=>patch({host:e.target.value})} className="cv-field"/></label>
   <label>Port<input type="number" value={config.port} onChange={e=>num('port',e.target.value)} className="cv-field"/></label>
   <label>Device ID<input type="number" value={config.device_id} onChange={e=>num('device_id',e.target.value)} className="cv-field"/></label>
   <label>Trigger type<select value={config.trigger_kind} onChange={e=>patch({trigger_kind:e.target.value as any})} className="cv-field"><option value="discrete_input">Discrete input</option><option value="coil">Coil</option></select></label>
   <label>Trigger address<input type="number" value={config.trigger_address} onChange={e=>num('trigger_address',e.target.value)} className="cv-field"/></label>
   <label>Poll ms<input type="number" value={config.poll_interval_ms} onChange={e=>num('poll_interval_ms',e.target.value)} className="cv-field"/></label>
   <label>OK coil<input type="number" value={config.ok_coil} onChange={e=>num('ok_coil',e.target.value)} className="cv-field"/></label>
   <label>NG coil<input type="number" value={config.ng_coil} onChange={e=>num('ng_coil',e.target.value)} className="cv-field"/></label>
   <label>Pulse seconds<input type="number" step="0.1" value={config.pulse_seconds} onChange={e=>num('pulse_seconds',e.target.value)} className="cv-field"/></label>
   <label className="flex items-end gap-2 pb-1"><input type="checkbox" checked={config.trigger_active_high} onChange={e=>patch({trigger_active_high:e.target.checked})}/>Active HIGH</label>
  </div>
  <div className="grid grid-cols-3 gap-2"><button disabled={busy} onClick={onRead} className="cv-btn">Read Trigger</button><button disabled={busy} onClick={()=>onPulse('ok')} className="cv-btn border-[#81c995] text-[#81c995]"><CheckCircle2 size={11}/>Pulse OK</button><button disabled={busy} onClick={()=>onPulse('ng')} className="cv-btn border-[#f28b82] text-[#f28b82]"><XCircle size={11}/>Pulse NG</button></div>
  <div className="rounded border border-[#3c4043] bg-[#202124] p-2">Trigger state: <b className={triggerState?'text-[#81c995]':'text-[#9aa0a6]'}>{triggerState==null?'not read':triggerState?'ACTIVE':'inactive'}</b></div>
 </div>;
};
