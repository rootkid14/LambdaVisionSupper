import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CircleDot, FlaskConical, GitBranch, Loader2, Play, Share2, Waves } from 'lucide-react';
import { SamplingOperatorLibrary } from '../components/VisionLabs/SamplingGeometry/SamplingOperatorLibrary';
import { SamplingStack } from '../components/VisionLabs/SamplingGeometry/SamplingStack';
import { SamplingWorkbench } from '../components/VisionLabs/SamplingGeometry/SamplingWorkbench';
import { SourceBoard } from '../components/VisionLabs/SamplingGeometry/SourceBoard';
import { ArtifactInspectorModal } from '../components/VisionLabs/SamplingGeometry/ArtifactInspectorModal';
import { useSamplingGeometryController } from '../components/VisionLabs/SamplingGeometry/useSamplingGeometryController';
import type { SamplingWorkspace } from '../components/VisionLabs/SamplingGeometry/types';

const tabs: Array<{ id: SamplingWorkspace; label: string; subtitle: string; icon: any }> = [
  { id: 'geometry', label: 'Geometry', subtitle: 'Contour discovery & selection', icon: GitBranch },
  { id: 'spatial', label: 'Spatial Sampling', subtitle: 'Housing + data extraction', icon: CircleDot },
  { id: 'spectral', label: 'Spectral / Statistics', subtitle: 'Data & frequency representation', icon: Waves },
];

export const SamplingGeometryLabPage = () => {
  const navigate = useNavigate();
  const c = useSamplingGeometryController();
  const state = c.current;
  const exposedCount = c.stack.reduce((sum, item) => sum + Object.keys(item.exposedOutputs ?? {}).length, 0);

  const workspaceSourceOptions = (c.sourceBoard?.entries ?? []).filter((entry) => {
    if (c.workspace === 'geometry') return entry.name === 'master_contours';
    return entry.type === 'image' && ['raw_image', 'inspected_image', 'contour_image', 'geometry_raster'].includes(entry.name);
  });

  const workbenchSourceUrl = c.workspace === 'geometry'
    ? c.sourceUrls.geometry_raster ?? c.sourceUrls.raw_image ?? null
    : c.sourceUrls[state.sourceName] ?? c.sourceUrls.inspected_image ?? null;

  const inspectorSourceUrl = c.workspace === 'geometry'
    ? c.sourceUrls.geometry_raster ?? c.sourceUrls.raw_image ?? null
    : workbenchSourceUrl;

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#202124] text-[#e8eaed]">
      <header className="shrink-0 border-b border-[#3c4043] bg-[#292a2d]">
        <div className="flex h-14 items-center gap-3 px-3">
          <button onClick={() => navigate('/labs')} className="flex h-8 w-8 items-center justify-center rounded border border-[#5f6368] bg-[#35363a] text-[#bdc1c6] hover:bg-[#3c4043]"><ArrowLeft size={15}/></button>
          <FlaskConical size={18} className="text-[#8ab4f8]"/>
          <div className="mr-2"><div className="text-xs font-black tracking-[0.16em]">SAMPLING / GEOMETRY LAB</div><div className="text-[8px] text-[#80868b]">One shared Source Board · three specialized workspaces · typed inspectable artifacts</div></div>

          <div className="flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124] p-1">
            {tabs.map((tab) => { const Icon=tab.icon; const active=c.workspace===tab.id; return <button key={tab.id} onClick={()=>c.switchWorkspace(tab.id)} className={`flex min-w-[155px] items-center gap-2 rounded px-3 py-1.5 text-left ${active?'bg-[#3c4043] text-[#e8eaed]':'text-[#9aa0a6] hover:bg-[#303134]'}`}><Icon size={14} className={active?'text-[#8ab4f8]':''}/><span><span className="block text-[10px] font-black">{tab.label}</span><span className="block text-[8px]">{tab.subtitle}</span></span></button>; })}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <select value={state.sourceName} onChange={(e)=>c.setWorkspaceSource(e.target.value)} disabled={!c.sourceBoard || c.workspace==='geometry'} className="max-w-[175px] rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px] text-[#e8eaed] disabled:opacity-45" title="Workspace source from shared Source Board">
              {workspaceSourceOptions.length ? workspaceSourceOptions.map((entry)=><option key={entry.name} value={entry.name}>{entry.name}:{entry.type}</option>) : <option value={state.sourceName}>{state.sourceName}</option>}
            </select>
            <div className="flex rounded border border-[#5f6368] bg-[#202124] p-0.5"><button onClick={()=>c.setExecutionMode('live')} className={`rounded px-2 py-1 text-[9px] font-black ${c.executionMode==='live'?'bg-[#174ea6] text-[#d2e3fc]':'text-[#9aa0a6]'}`}>LIVE</button><button onClick={()=>c.setExecutionMode('manual')} className={`rounded px-2 py-1 text-[9px] font-black ${c.executionMode==='manual'?'bg-[#3c4043] text-[#e8eaed]':'text-[#9aa0a6]'}`}>MANUAL</button></div>
            <button onClick={()=>void c.runNow()} disabled={!c.sourceBoard||!c.stack.length||c.busy} className="flex items-center gap-1.5 rounded border border-[#8ab4f8] bg-[#174ea6] px-3 py-1.5 text-[10px] font-black text-[#d2e3fc] disabled:opacity-35">{c.busy?<Loader2 size={12} className="animate-spin"/>:<Play size={12}/>}Run{state.pending?<span className="rounded bg-[#fdd663] px-1 text-[8px] text-[#202124]">PENDING</span>:null}</button>
          </div>
        </div>

        <SourceBoard
          file={c.inputFile}
          onFile={c.setInputFile}
          config={c.sourceBoardConfig}
          onConfig={c.setSourceBoardConfig}
          services={c.imageServices}
          manifest={c.sourceBoard}
          busy={c.busy}
          onBuild={()=>void c.buildBoard()}
          onInspect={(name)=>void c.inspectSource(name)}
        />

        <div className="flex h-10 items-center gap-2 border-t border-[#3c4043] px-3">
          <Share2 size={11} className="text-[#81c995]"/>
          <span className="text-[8px] font-black uppercase tracking-wider text-[#80868b]">Deploy current workspace</span>
          <input value={c.serviceName} onChange={(e)=>c.setServiceName(e.target.value)} className="w-[235px] rounded border border-[#5f6368] bg-[#202124] px-2 py-1 text-[9px] text-[#e8eaed]"/>
          <span className="text-[8px] text-[#80868b]">raw Image → Source Board → {c.workspace} · {exposedCount} exposed outputs</span>
          <button onClick={()=>void c.deploy(false)} disabled={c.busy||!exposedCount} className="ml-auto rounded border border-[#81c995] bg-[#1e3828] px-2 py-1 text-[9px] font-black text-[#81c995] disabled:opacity-35">{c.editingService?'Update Service':'Deploy Service'}</button>
          {c.editingService?<button onClick={()=>void c.deploy(true)} className="rounded border border-[#5f6368] bg-[#35363a] px-2 py-1 text-[9px] font-bold text-[#bdc1c6]">Save As New</button>:null}
        </div>
      </header>

      {c.error?<div className="shrink-0 border-b border-[#f28b82]/40 bg-[#5f2120] px-3 py-1.5 text-[10px] text-[#f28b82]">{c.error}<button onClick={()=>c.setError('')} className="ml-3 font-bold">DISMISS</button></div>:null}

      <main className="flex min-h-0 flex-1">
        <SamplingOperatorLibrary operators={c.operators} onAdd={c.addOperator} canAppend={c.canAppend}/>
        <SamplingWorkbench workspace={c.workspace} sourceUrl={workbenchSourceUrl} artifact={c.artifact} artifactPreviewUrl={c.artifactPreviewUrl} masterContours={c.masterContours}/>
        <SamplingStack
          stack={c.stack}
          selectedNodeId={state.selectedNodeId}
          selectedPort={state.selectedPort}
          timings={state.timings}
          sourceEntries={c.sourceBoard?.entries ?? []}
          inspectedArtifact={c.artifact}
          onSelect={(id,port)=>void c.fetchArtifactFor(id,port)}
          onInspect={(id,port)=>void c.inspectOutput(id,port)}
          onParameter={c.updateParameter}
          onReferenceBinding={c.updateReferenceBinding}
          onMove={c.moveOperator}
          onRemove={c.removeOperator}
          onToggleExpose={c.toggleExpose}
          onExposeName={c.setExposeName}
        />
      </main>

      {c.inspector ? <ArtifactInspectorModal title={c.inspector.nodeId.startsWith('source:')?`Source Board · ${c.inspector.port}`:`${c.inspector.nodeId} · ${c.inspector.port}`} artifact={c.artifact} previewUrl={c.artifactPreviewUrl} sourceUrl={inspectorSourceUrl} masterContours={c.masterContours} onClose={()=>c.setInspector(null)}/> : null}
    </div>
  );
};
