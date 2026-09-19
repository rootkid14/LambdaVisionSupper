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

type PreviewMode='raw'|'gray'|'mask'|'overlay';
const safe=(v:string)=>v.trim().replace(/[^A-Za-z0-9_]+/g,'_').replace(/^([0-9])/,'_$1')||'camera';

export const StreamingWorkspace=({programId,workspace,camera,onWorkspace,onError}:Props)=>{
  const [previewing,setPreviewing]=useState(false);
  const [previewMode,setPreviewMode]=useState<PreviewMode>('overlay');
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
        const frame=previewMode==='raw'
          ?await VisionAppAPI.streamLatestFrame(programId,wsAlias,lastSequence.current)
          :await VisionAppAPI.softTriggerPreview(programId,wsAlias,softConfigRef.current,previewMode,lastSequence.current);
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
    const id=window.setInterval(()=>void refreshStatus(),350);
    void refreshStatus();
    return()=>{
      mounted.current=false;
      window.clearInterval(id);
      setPreviewUrl(old=>{if(old)URL.revokeObjectURL(old);return null;});
      if(previewingRef.current&&camera)void VisionAppAPI.streamStop(programId,wsAlias).catch(()=>{});
    };
  },[programId,camera?.declaration_id,workspace.workspace_id,previewMode]);

  useEffect(()=>{
    lastSequence.current=0;
  },[previewMode,workspace.soft_trigger.pixel_threshold,workspace.soft_trigger.threshold_mode,workspace.soft_trigger.roi]);

  const start=async()=>{
    if(!camera)return;
    if(camera.driver!=='basler'){
      onError('Streaming currently supports Basler native streaming only. HTTP/Raspberry Pi stream transport remains pending.');
      return;
    }
    try{
      const response=await VisionAppAPI.streamStart(programId,wsAlias);
      setStatus(response.stream);
      setSoftRuntime(response.soft_trigger??null);
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
      setSoftRuntime(response.soft_trigger??null);
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
  const policy=workspace.soft_trigger.backpressure_policy??'skip';
  const capacity=policy==='skip'?0:policy==='latest'?1:Math.max(1,workspace.soft_trigger.queue_capacity??3);
  const queueDepth=softRuntime?.queue_depth??0;
  const queuePercent=capacity>0?Math.min(100,(queueDepth/capacity)*100):0;

  return <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_410px] bg-[#14171b] text-[#e8eaed]">
    <section className="flex min-h-0 flex-col border-r border-[#34383f]">
      <div className="flex min-h-10 shrink-0 flex-wrap items-center gap-2 border-b border-[#34383f] bg-[#1d2126] px-3 py-1 text-[8px]">
        <Activity size={12} className="text-[#65d1ff]"/><b>STREAMING FRAME</b>
        <span className="rounded bg-[#20252b] px-2 py-1 font-mono text-[#81c995]">camera.{alias}.{camera.stream_slot}</span>
        <span className={`rounded px-2 py-1 font-black ${status?.running?'bg-[#173c29] text-[#81c995]':'bg-[#402323] text-[#f28b82]'}`}>{status?.running?'RUNNING':'STOPPED'}</span>
        <span className="text-[#9aa0a6]">{(status?.fps??0).toFixed(1)} fps · seq {status?.sequence??0}</span>
        <div className="ml-auto flex items-center gap-1 rounded border border-[#34383f] bg-[#171a1f] p-1">
          <Activity size={10} className="mx-1 text-[#8ab4f8]"/>
          {(['raw','gray','mask','overlay'] as PreviewMode[]).map(mode=><button key={mode} onClick={()=>setPreviewMode(mode)} className={`rounded px-2 py-1 text-[7px] font-black uppercase ${previewMode===mode?'bg-[#31506f] text-white':'text-[#9aa0a6] hover:bg-[#252a31]'}`}>{mode==='mask'?'Threshold':mode}</button>)}
        </div>
        <button disabled={!supported||previewing} onClick={()=>void start()} className="cv-btn border-[#65d1ff] text-[#65d1ff]"><CirclePlay size={10}/>Start Preview</button>
        <button disabled={!previewing} onClick={()=>void stop()} className="cv-btn border-[#f28b82] text-[#f28b82]"><CircleStop size={10}/>Stop Preview</button>
      </div>

      {!supported?<div className="border-b border-[#6b5b2f] bg-[#352d18] px-3 py-2 text-[8px] text-[#fdd663]">
        HTTP/Raspberry Pi streaming transport is pending. The workspace/stream contract is already prepared for a later URL/TCP implementation.
      </div>:null}

      <div className="relative min-h-0 flex-1">
        <VisionViewport imageUrl={previewUrl} rois={triggerRois} selectedId="__soft_trigger__" drawMode={draw} onDraw={rect=>{patchSoft({roi:rect});setDraw(false);}}/>
        {previewing&&previewMode!=='raw'?<div className="pointer-events-none absolute bottom-4 left-4 rounded border border-[#405266] bg-[#111820]/90 px-2 py-1 text-[7px] text-[#b8c7d3]">
          {previewMode==='mask'?'White = threshold-active pixel · Black = inactive':previewMode==='overlay'?'Green = active threshold pixels · dim = inactive':'Grayscale source used by the trigger'} · same threshold logic as backend Soft Trigger
        </div>:null}
        {!previewing?<div className="pointer-events-none absolute bottom-4 left-4 max-w-[430px] rounded border border-[#38414a] bg-[#111820]/90 p-2 text-[7px] leading-4 text-[#9fb7c8]">
          Browser preview is lazy. No JPEG is requested until <b>Start Preview</b>. ONLINE Soft Trigger can continue entirely in backend memory.
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
          Draw one small sensor ROI. Threshold view uses the exact backend rule, so tune it until the product is clearly separated from conveyor/background before choosing the trigger count.
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

      <div className="mt-3 rounded-xl border border-[#564c34] bg-[#251f15] p-3">
        <div className="flex items-center gap-2"><Activity size={11} className="text-[#fdd663]"/><b>BACKPRESSURE / BUSY POLICY</b></div>
        <div className="mt-2 text-[7px] leading-4 text-[#c8b98f]">What should happen when another product triggers while an inspection is still running?</div>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <label className="col-span-2">Policy<select className="cv-field" value={policy} onChange={e=>patchSoft({backpressure_policy:e.target.value as any})}>
            <option value="skip">Skip new trigger while busy</option>
            <option value="latest">Keep only latest waiting frame</option>
            <option value="fifo">FIFO cache</option>
          </select></label>
          {policy==='fifo'?<><label>Queue capacity<input className="cv-field" type="number" min={1} max={128} value={workspace.soft_trigger.queue_capacity??3} onChange={e=>patchSoft({queue_capacity:Math.max(1,Number(e.target.value))})}/></label>
          <label>When full<select className="cv-field" value={workspace.soft_trigger.overflow_policy??'drop_oldest'} onChange={e=>patchSoft({overflow_policy:e.target.value as any})}><option value="drop_oldest">Drop oldest cached</option><option value="drop_newest">Drop newest trigger</option></select></label></>:null}
        </div>
        <div className="mt-3">
          <div className="flex justify-between text-[6px] text-[#a99c79]"><span>QUEUE PRESSURE</span><span>{queueDepth}/{capacity||0}</span></div>
          <div className="mt-1 h-2 overflow-hidden rounded bg-[#111]"><div className="h-full bg-[#fdd663] transition-all" style={{width:`${queuePercent}%`}}/></div>
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2 text-[7px]">
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">INSPECTION</div><b className={softRuntime?.inspection_busy?'text-[#fdd663]':'text-[#81c995]'}>{softRuntime?.inspection_busy?'BUSY':'IDLE'}</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">PROCESSED</div><b>{softRuntime?.processed_total??0}</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">QUEUED</div><b>{softRuntime?.queued_total??0}</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">SKIPPED BUSY</div><b className="text-[#f28b82]">{softRuntime?.skipped_busy??0}</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">DROPPED</div><b className="text-[#f28b82]">{softRuntime?.dropped_overflow??0}</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">LATEST REPLACED</div><b>{softRuntime?.replaced_latest??0}</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">MAX DEPTH</div><b>{softRuntime?.max_queue_depth??0}</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">AVG WAIT</div><b>{(softRuntime?.avg_queue_wait_ms??0).toFixed(0)} ms</b></div>
          <div className="rounded bg-[#17130d] p-2"><div className="text-[6px] text-[#93876c]">LAST ACTION</div><b className="break-all">{softRuntime?.last_action||'—'}</b></div>
        </div>
      </div>

      <div className="mt-3 rounded-xl border border-[#4f455f] bg-[#211b29] p-3">
        <div className="flex items-center gap-2"><Gauge size={11} className="text-[#c58af9]"/><b>LIVE SENSOR METRICS</b></div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">ACTIVE PIXELS</div><div className="text-lg font-black text-[#fdd663]">{count}</div></div>
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">ACTIVE RATIO</div><div className="text-lg font-black text-[#65d1ff]">{(ratio*100).toFixed(1)}%</div></div>
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">RUNTIME</div><div className={`font-black ${softRuntime?.armed?'text-[#81c995]':'text-[#9aa0a6]'}`}>{softRuntime?.armed?'ARMED':workspace.soft_trigger.enabled?'WAITING / OFFLINE':'DISABLED'}</div></div>
          <div className="rounded bg-[#17131d] p-2"><div className="text-[6px] text-[#8b8296]">THRESHOLD FIRES</div><div className="font-black">{softRuntime?.fires??0}</div></div>
        </div>
        <div className="mt-2 text-[6px] text-[#8b8296]">Trigger ≥ {workspace.soft_trigger.trigger_pixel_count}px · Rearm ≤ {workspace.soft_trigger.reset_pixel_count}px</div>
      </div>
    </aside>
  </div>;
};
