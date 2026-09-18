import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Boxes,
  CircleDot,
  FlaskConical,
  GitBranch,
  ImagePlus,
  Loader2,
  Play,
  Save,
  Share2,
  Upload,
  Waves,
} from 'lucide-react';
import { SamplingOperatorLibrary } from '../components/VisionLabs/SamplingGeometry/SamplingOperatorLibrary';
import { SamplingStack } from '../components/VisionLabs/SamplingGeometry/SamplingStack';
import { SamplingWorkbench } from '../components/VisionLabs/SamplingGeometry/SamplingWorkbench';
import { useSamplingGeometryController } from '../components/VisionLabs/SamplingGeometry/useSamplingGeometryController';
import type { SamplingWorkspace } from '../components/VisionLabs/SamplingGeometry/types';

const tabs: Array<{ id: SamplingWorkspace; label: string; subtitle: string; icon: any }> = [
  { id: 'geometry', label: 'Geometry', subtitle: 'Contour · curve · measurement', icon: GitBranch },
  { id: 'spatial', label: 'Spatial Sampling', subtitle: 'Ray · ring · patch · profile', icon: CircleDot },
  { id: 'spectral', label: 'Spectral / Statistics', subtitle: 'Histogram · FFT · descriptors', icon: Waves },
];

export const SamplingGeometryLabPage = () => {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement | null>(null);
  const c = useSamplingGeometryController();

  const selectedUpstream = c.upstreamServices.find((service) => service.service_id === c.inputBinding.serviceId);
  const usableOutputs = Object.entries(selectedUpstream?.outputs ?? {}).filter(([, output]) => ['image', 'binary_mask'].includes(output.type));

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#202124] text-[#e8eaed]">
      <header className="shrink-0 border-b border-[#3c4043] bg-[#292a2d]">
        <div className="flex h-14 items-center gap-3 px-3">
          <button onClick={() => navigate('/labs')} className="flex h-8 w-8 items-center justify-center rounded border border-[#5f6368] bg-[#35363a] text-[#bdc1c6] hover:bg-[#3c4043]"><ArrowLeft size={15}/></button>
          <FlaskConical size={18} className="text-[#8ab4f8]" />
          <div className="mr-3"><div className="text-xs font-black tracking-[0.16em]">SAMPLING / GEOMETRY LAB</div><div className="text-[9px] text-[#80868b]">Geometry · spatial signals · spectral descriptors</div></div>

          <div className="flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124] p-1">
            {tabs.map((tab) => { const Icon=tab.icon; const active=c.workspace===tab.id; return <button key={tab.id} onClick={()=>c.switchWorkspace(tab.id)} className={`flex min-w-[155px] items-center gap-2 rounded px-3 py-1.5 text-left ${active?'bg-[#3c4043] text-[#e8eaed]':'text-[#9aa0a6] hover:bg-[#303134]'}`}><Icon size={14} className={active?'text-[#8ab4f8]':''}/><span><span className="block text-[10px] font-black">{tab.label}</span><span className="block text-[8px]">{tab.subtitle}</span></span></button>; })}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <div className="flex rounded border border-[#5f6368] bg-[#202124] p-0.5"><button onClick={()=>c.setExecutionMode('live')} className={`rounded px-2 py-1 text-[9px] font-black ${c.executionMode==='live'?'bg-[#174ea6] text-[#d2e3fc]':'text-[#9aa0a6]'}`}>LIVE</button><button onClick={()=>c.setExecutionMode('manual')} className={`rounded px-2 py-1 text-[9px] font-black ${c.executionMode==='manual'?'bg-[#3c4043] text-[#e8eaed]':'text-[#9aa0a6]'}`}>MANUAL</button></div>
            <button onClick={()=>void c.runNow()} disabled={!c.sourceLoaded||!c.stack.length||c.busy} className="flex items-center gap-1.5 rounded border border-[#8ab4f8] bg-[#174ea6] px-3 py-1.5 text-[10px] font-black text-[#d2e3fc] disabled:opacity-35">{c.busy?<Loader2 size={12} className="animate-spin"/>:<Play size={12}/>}Run{c.pending?<span className="rounded bg-[#fdd663] px-1 text-[8px] text-[#202124]">PENDING</span>:null}</button>
          </div>
        </div>

        <div className="flex min-h-[62px] items-center gap-3 border-t border-[#3c4043] px-3 py-2">
          <div className="flex items-center gap-2 rounded border border-[#3c4043] bg-[#202124] p-2">
            <div className="text-[9px] font-black tracking-wider text-[#8ab4f8]">INPUT SOURCE</div>
            <select value={c.inputBinding.mode} onChange={(e)=>c.setInputBinding((current:any)=>({...current,mode:e.target.value as any,serviceId:'',serviceOutput:''}))} className="rounded border border-[#5f6368] bg-[#292a2d] px-2 py-1 text-[10px] text-[#e8eaed]"><option value="upload">Upload</option><option value="lab_service">Lab Service</option></select>
            {c.inputBinding.mode==='upload'?<select value={c.inputBinding.inputType} onChange={(e)=>c.setInputBinding((current:any)=>({...current,inputType:e.target.value as any}))} className="rounded border border-[#5f6368] bg-[#292a2d] px-2 py-1 text-[10px] text-[#e8eaed]"><option value="image">Image</option><option value="binary_mask">BinaryMask</option></select>:<><select value={c.inputBinding.serviceId} onChange={(e)=>{const service=c.upstreamServices.find((s)=>s.service_id===e.target.value);const output=Object.entries(service?.outputs??{}).find(([,o])=>['image','binary_mask'].includes(o.type));c.setInputBinding((current:any)=>({...current,serviceId:e.target.value,serviceOutput:output?.[0]??''}));}} className="max-w-[210px] rounded border border-[#5f6368] bg-[#292a2d] px-2 py-1 text-[10px] text-[#e8eaed]"><option value="">Select upstream service…</option>{c.upstreamServices.map((service)=><option key={service.service_id} value={service.service_id}>{service.name} · v{service.version}</option>)}</select><select value={c.inputBinding.serviceOutput} onChange={(e)=>c.setInputBinding((current:any)=>({...current,serviceOutput:e.target.value}))} className="max-w-[180px] rounded border border-[#5f6368] bg-[#292a2d] px-2 py-1 text-[10px] text-[#e8eaed]"><option value="">Output…</option>{usableOutputs.map(([name,output])=><option key={name} value={name}>{name}:{output.type}</option>)}</select></>}
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e)=>{const file=e.target.files?.[0]??null;c.setInputBinding((current:any)=>({...current,file}));e.currentTarget.value='';}}/>
            <button onClick={()=>fileRef.current?.click()} className="flex items-center gap-1 rounded border border-[#5f6368] bg-[#35363a] px-2 py-1 text-[9px] font-bold"><Upload size={10}/>{c.inputBinding.file?.name??'Choose image'}</button>
            <button onClick={()=>void c.loadSource()} disabled={!c.inputBinding.file||c.busy} className="flex items-center gap-1 rounded border border-[#81c995] bg-[#1e3828] px-2 py-1 text-[9px] font-black text-[#81c995] disabled:opacity-35"><ImagePlus size={10}/>Load Source</button>
            <span className="font-mono text-[8px] text-[#80868b]">→ {c.currentInputType}</span>
          </div>

          <div className="ml-auto flex items-center gap-2 rounded border border-[#3c4043] bg-[#202124] p-2">
            <Share2 size={12} className="text-[#81c995]"/><input value={c.serviceName} onChange={(e)=>c.setServiceName(e.target.value)} className="w-[220px] rounded border border-[#5f6368] bg-[#292a2d] px-2 py-1 text-[10px] text-[#e8eaed]"/>
            <span className="text-[8px] text-[#80868b]">{c.stack.filter((item)=>item.exposedName).length} outputs</span>
            <button onClick={()=>void c.deploy(false)} disabled={c.busy||!c.stack.some((item)=>item.exposedName)} className="rounded border border-[#81c995] bg-[#1e3828] px-2 py-1 text-[9px] font-black text-[#81c995] disabled:opacity-35">{c.editingService?'Update Service':'Deploy Service'}</button>
            {c.editingService?<button onClick={()=>void c.deploy(true)} className="rounded border border-[#5f6368] bg-[#35363a] px-2 py-1 text-[9px] font-bold text-[#bdc1c6]">Save As New</button>:null}
          </div>
        </div>
      </header>

      {c.error?<div className="shrink-0 border-b border-[#f28b82]/40 bg-[#5f2120] px-3 py-1.5 text-[10px] text-[#f28b82]">{c.error}<button onClick={()=>c.setError('')} className="ml-3 font-bold">DISMISS</button></div>:null}

      <main className="flex min-h-0 flex-1">
        <SamplingOperatorLibrary operators={c.operators} onAdd={c.addOperator} canAppend={c.canAppend}/>
        <SamplingWorkbench workspace={c.workspace} sourceUrl={c.sourceUrl} artifact={c.artifact} artifactPreviewUrl={c.artifactPreviewUrl}/>
        <SamplingStack stack={c.stack} selectedNodeId={c.selectedNodeId} timings={c.timings} onSelect={(id)=>void c.fetchArtifactFor(id)} onParameter={c.updateParameter} onMove={c.moveOperator} onRemove={c.removeOperator} onToggleExpose={c.toggleExpose} onExposeName={c.setExposeName}/>
      </main>
    </div>
  );
};
