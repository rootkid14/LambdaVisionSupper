import { Activity, Camera, CirclePlay, CircleStop, Crosshair, Gauge } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  VisionAppAPI,
  type CameraDeclaration,
  type CameraStreamStatus,
  type MasterRoi,
  type SoftTriggerAnalysis,
  type SoftTriggerRuntimeStatus,
  type WorkspaceDefinition,
} from '../../api/visionAppApi';
import { VisionViewport } from './VisionViewport';

type Props={
  programId:string;
  workspace:WorkspaceDefinition;
  camera:CameraDeclaration|null;
  onWorkspace:(workspace:WorkspaceDefinition)=>void;
  onError:(message:string)=>void;
};

const safe=(v:string)=>v.trim().replace(/[^A-Za-z0-9_]+/g,'_').replace(/^([0-9])/,'_$1')||'camera';

export const StreamingWorkspace=({programId,workspace,camera,onWorkspace,onError}:Props)=>{
  const [previewing,setPreviewing]=useState(false);
  const [previewUrl,setPreviewUrl]=useState<string|null>(null);
  const [status,setStatus]=useState<CameraStreamStatus|null>(null);
  const [softRuntime,setSoftRuntime]=useState<SoftTriggerRuntimeStatus|null>(null);
  const [analysis,setAnalysis]=useState<SoftTriggerAnalysis|null>(null);
  const [draw,setDraw]=useState(false);
  const lastSequence=useRef(0);
  const mounted=useRef(true);
  const previewingRef=useRef(false);
  const softConfigRef=useRef(workspace.soft_trigger);
  softConfigRef.current=workspace.soft_trigger;
  const alias=camera?safe(camera.alias):'';
  const wsAlias=safe(workspace.alias);

  const patchSoft=(patch:Partial<WorkspaceDefinition['soft_trigger']>)=>{
    onWorkspace({...workspace,soft_trigger:{...workspace.soft_trigger,...patch}});
  };

  const triggerRois=useMemo<MasterRoi[]>(()=>workspace.soft_trigger.roi?[{
    roi_id:'__soft_trigger__',
    name:`Soft Trigger · ${analysis?.pixel_count??softRuntime?.pixel_count??0}px`,
    alias:'soft_trigger',
    rect:workspace.soft_trigger.roi,
    enabled:true,
  }]:[],[workspace.soft_trigger.roi,analysis?.pixel_count,softRuntime?.pixel_count]);

  const refreshStatus=async()=>{
    if(!camera)return;
    try{
      const response=await VisionAppAPI.streamStatus(programId,wsAlias);
      if(!mounted.current)return;
      setStatus(response.stream);
      setSoftRuntime(response.soft_trigger??null);
      if(previewingRef.current && response.stream.sequence>lastSequence.current){
        const frame=await VisionAppAPI.streamLatestFrame(programId,wsAlias,lastSequence.current);
        if(!mounted.current)return;
        lastSequence.current=Math.max(frame.sequence,response.stream.sequence);
        if(frame.blob){
          setPreviewUrl(old=>{if(old)URL.revokeObjectURL(old);return URL.createObjectURL(frame.blob!);});
          if(softConfigRef.current.roi){
            try{
              const metrics=await VisionAppAPI.analyzeSoftTrigger(programId,wsAlias,softConfigRef.current);
              if(mounted.current)setAnalysis(metrics);
            }catch{}
          }
        }
      }
    }catch(e:any){
      if(mounted.current)setStatus(s=>s?{...s,last_error:e?.response?.data?.detail||e?.message||'Stream status failed'}:s);
    }
  };

  useEffect(()=>{
    mounted.current=true;
    const id=window.setInterval(()=>void refreshStatus(),500);
    void refreshStatus();
    return()=>{
      mounted.current=false;
      window.clearInterval(id);
      setPreviewUrl(old=>{if(old)URL.revokeObjectURL(old);return null;});
      if(previewingRef.current&&camera)void VisionAppAPI.streamStop(programId,wsAlias).catch(()=>{});
    };
  },[programId,camera?.declaration_id,workspace.workspace_id]);

  const start=async()=>{
    if(!camera)return;
    if(camera.driver!=='basler'){
      onError('Streaming v0.14 currently supports Basler native streaming only. HTTP/Raspberry Pi stream transport is declared but pending.');
      return;
    }
    try{
      const response=await VisionAppAPI.streamStart(programId,wsAlias);
      setStatus(response.stream);
      lastSequence.current=0;
      previewingRef.current=true;
      setPreviewing(true);
    }catch(e:any){onError(e?.response?.data?.detail||e?.message||'Unable to start stream');}
  };
  const stop=async()=>{
    if(!camera)return;
    try{
      const response=await VisionAppAPI.streamStop(programId,wsAlias);
      setStatus(response.stream);
    }catch{}
    previewingRef.current=false;
    setPreviewing(false);
    setPreviewUrl(old=>{if(old)URL.revokeObjectURL(old);return null;});
  };

  if(!camera)return <div className="flex h-full items-center justify-center bg-[#14171b] text-[10px] text-[#8b949e]">
    Assign one camera to this workspace before using Streaming.
  </div>;

  const supported=camera.driver==='basler';
  const count=analysis?.pixel_count??softRuntime?.pixel_count??0;
  const ratio=analysis?.active_ratio??softRuntime?.active_ratio??0;

  return <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_390px] bg-[#14171b] text-[#e8eaed]">
    <section className="flex min-h-0 flex-col border-r border-[#34383f]">
      <div className="flex h-10 shrink-0 items-center gap-2 border-b border-[#34383f] bg-[#1d2126] px-3 text-[8px]">
        <Activity size={12} className="text-[#65d1ff]"/><b>STREAMING FRAME</b>
        <span className="rounded bg-[#20252b] px-2 py-1 font-mono text-[#81c995]">camera.{alias}.{camera.stream_slot}</span>
        <span className={`rounded px-2 py-1 font-black ${status?.running?'bg-[#173c29] text-[#81c995]':'bg-[#402323] text-[#f28b82]'}`}>{status?.running?'RUNNING':'STOPPED'}</span>
        <span className="text-[#9aa0a6]">{(status?.fps??0).toFixed(1)} fps · seq {status?.sequence??0}</span>
        <button disabled={!supported||previewing} onClick={()=>void start()} className="cv-btn ml-auto border-[#65d1ff] text-[#65d1ff]"><CirclePlay size={10}/>Start Preview</button>
        <button disabled={!previewing} onClick={()=>void stop()} className="cv-btn border-[#f28b82] text-[#f28b82]"><CircleStop size={10}/>Stop Preview</button>
      </div>
      {!supported?<div className="border-b border-[#6b5b2f] bg-[#352d18] px-3 py-2 text-[8px] text-[#fdd663]">
        HTTP/Raspberry Pi streaming is intentionally pending in v0.14. The declaration already keeps a stream slot/path so a future URL/TCP transport can plug into this workspace without changing Soft Trigger or IDE objects.
      </div>:null}
      <div className="relative min-h-0 flex-1">
        <VisionViewport imageUrl={previewUrl} rois={triggerRois} selectedId="__soft_trigger__" drawMode={draw} onDraw={rect=>{patchSoft({roi:rect});setDraw(false);}}/>
        {!previewing?<div className="pointer-events-none absolute bottom-4 left-4 max-w-[430px] rounded border border-[#38414a] bg-[#111820]/90 p-2 text-[7px] leading-4 text-[#9fb7c8]">
          Browser preview is lazy. No stream JPEG is requested until <b>Start Preview</b> is pressed. Backend streaming can still stay alive for an ONLINE Soft Trigger.
        </div>:null}
      </div>
    </section>
    <aside className="overflow-y-auto bg-[#20242a] p-3 text-[8px]">
      <div className="rounded-xl border border-[#394049] bg-[#181c21] p-3">
        <div className="flex items-center gap-2"><Camera size={11} className="text-[#81c995]"/><b>ASSIGNED CAMERA</b></div>
        <div className="mt-2 grid grid-cols-2 gap-2 text-[7px]">
          <div><span className="text-[#7d8791]">Object</span><div className="font-mono text-[#65d1ff]">camera.{alias}</div></div>
          <div><span className="text-[#7d8791]">Driver</span><div>{camera.driver}</div></div>
          <div><span className="text-[#7d8791]">Stream slot</span><div className="font-mono">{camera.stream_slot}</div></div>
          <div><span className="text-[#7d8791]">Backend cap</span><div>{camera.stream_max_fps} fps</div></div>
        </div>
        {status?.last_error?<div className="mt-2 rounded bg-[#4b2020] p-2 text-[#f28b82]">{status.last_error}</div>:null}
      </div>

      <div className="mt-3 rounded-xl border border-[#405266] bg-[#17212b] p-3">
        <div className="flex items-center gap-2"><Crosshair size={11} className="text-[#65d1ff]"/><b>SOFT TRIGGER</b>
          <label className="ml-auto flex items-center gap-1"><input type="checkbox" checked={workspace.soft_trigger.enabled} onChange={e=>patchSoft({enabled:e.target.checked})}/>Arm when ONLINE</label>
        </div>
        <div className="mt-2 rounded border border-[#31495b] bg-[#111a22] p-2 text-[7px] leading-4 text-[#9fb7c8]">
          The backend evaluates only this ROI from <span className="font-mono text-[#65d1ff]">{camera.stream_slot}</span>. When active pixels cross the trigger count, the current stream frame is snapshotted to <span className="font-mono text-[#81c995]">{camera.image_slot}</span> and this workspace can inspect it. It rearms only after pixel count falls below Reset count.
        </div>
        <button className={`cv-btn mt-2 ${draw?'border-[#fdd663] text-[#fdd663]':'border-[#65d1ff] text-[#65d1ff]'}`} onClick={()=>setDraw(v=>!v)}><Crosshair size={10}/>{draw?'Draw trigger ROI…':'Draw / Replace ROI'}</button>
        <button className="cv-btn mt-2 ml-2" onClick={()=>patchSoft({roi:null})}>Clear ROI</button>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <label>Threshold mode<select className="cv-field" value={workspace.soft_trigger.threshold_mode} onChange={e=>patchSoft({threshold_mode:e.target.value as any})}><option value="bright">Bright pixels ≥ threshold</option><option value="dark">Dark pixels ≤ threshold</option></select></label>
          <label>Pixel threshold (0–255)<input type="number" min={0} max={255} className="cv-field" value={workspace.soft_trigger.pixel_threshold} onChange={e=>patchSoft({pixel_threshold:Number(e.target.value)})}/></label>
          <label>Trigger pixel count<input type="number" min={1} className="cv-field" value={workspace.soft_trigger.trigger_pixel_count} onChange={e=>patchSoft({trigger_pixel_count:Math.max(1,Number(e.target.value))})}/></label>
          <label>Reset pixel count<input type="number" min={0} className="cv-field" value={workspace.soft_trigger.reset_pixel_count} onChange={e=>patchSoft({reset_pixel_count:Math.max(0,Number(e.target.value))})}/></label>
          <label>Check every N frames<input type="number" min={1} className="cv-field" value={workspace.soft_trigger.frame_stride} onChange={e=>patchSoft({frame_stride:Math.max(1,Number(e.target.value))})}/></label>
          <label>Cooldown ms<input type="number" min={0} className="cv-field" value={workspace.soft_trigger.cooldown_ms} onChange={e=>patchSoft({cooldown_ms:Math.max(0,Number(e.target.value))})}/></label>
        </div>
        <div className="mt-2 flex gap-3 text-[7px]"><label className="flex items-center gap-1"><input type="checkbox" checked={workspace.soft_trigger.snapshot_to_image_slot} onChange={e=>patchSoft({snapshot_to_image_slot:e.target.checked})}/>Snapshot → Current_image</label><label className="flex items-center gap-1"><input type="checkbox" checked={workspace.soft_trigger.run_inspection} onChange={e=>patchSoft({run_inspection:e.target.checked})}/>Run inspection</label></div>
      </div>

      <div className="mt-3 rounded-xl border border-[#4f455f] bg-[#211b29] p-3">
        <div className="flex items-center gap-2"><Gauge size={11} className="text-[#c58af9]"/><b>LIVE SENSOR METRICS</b></div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">ACTIVE PIXELS</div><div className="text-lg font-black text-[#fdd663]">{count}</div></div>
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">ACTIVE RATIO</div><div className="text-lg font-black text-[#65d1ff]">{(ratio*100).toFixed(1)}%</div></div>
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">RUNTIME</div><div className={`font-black ${softRuntime?.armed?'text-[#81c995]':'text-[#9aa0a6]'}`}>{softRuntime?.armed?'ARMED':workspace.soft_trigger.enabled?'WAITING / OFFLINE':'DISABLED'}</div></div>
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">FIRES</div><div className="font-black">{softRuntime?.fires??0}</div></div>
        </div>
        <div className="mt-2 text-[6px] text-[#8b8296]">Trigger ≥ {workspace.soft_trigger.trigger_pixel_count}px · Rearm ≤ {workspace.soft_trigger.reset_pixel_count}px</div>
      </div>
    </aside>
  </div>;
};
