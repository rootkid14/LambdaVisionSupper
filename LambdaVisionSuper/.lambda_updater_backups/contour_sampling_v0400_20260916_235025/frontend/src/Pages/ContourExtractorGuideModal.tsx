import { X } from 'lucide-react';

export const ContourExtractorGuideModal = ({onClose}:{onClose:()=>void}) => (
  <div className="fixed inset-0 z-[180] flex items-center justify-center bg-black/80 p-4">
    <div className="grid h-[86vh] w-[92vw] max-w-[1500px] grid-cols-[360px_minmax(0,1fr)_360px] overflow-hidden rounded-xl border border-[#5f6368] bg-[#202124] text-[#e8eaed]">
      <section className="overflow-y-auto border-r border-[#3c4043] p-4">
        <div className="text-[9px] font-black uppercase tracking-[.18em] text-[#81c995]">Contour Extractor Guide</div>
        <h2 className="mt-2 text-lg font-black">From contour mess to meaningful shapes</h2>
        <p className="mt-3 text-[10px] leading-5 text-[#bdc1c6]">Candidate generation can create thousands of tiny contours. The default contour filter runs immediately after candidate extraction. Rejected coordinates are not retained. Surviving geometry is stored once; later stages keep only contour IDs.</p>
        <div className="mt-4 space-y-3 text-[9px] text-[#9aa0a6]">
          <div><b className="text-[#d2e3fc]">Auto source</b><br/>BinaryMask → direct mask boundary. Normal image → Canny edges.</div>
          <div><b className="text-[#d2e3fc]">min area / perimeter / bbox / points</b><br/>Cheap early gates for removing tiny edge fragments before they enter the retained ContourStore.</div>
          <div><b className="text-[#d2e3fc]">max retained</b><br/>Safety cap for pathological images. Increase only when the meaningful contour population genuinely requires it.</div>
          <div><b className="text-[#d2e3fc]">Metric Filter</b><br/>Filter the retained candidates by area, perimeter, circularity, solidity or aspect ratio.</div>
          <div><b className="text-[#d2e3fc]">Largest N</b><br/>Keep only the largest N contours by area or perimeter.</div>
          <div><b className="text-[#d2e3fc]">Region Filter</b><br/>Keep contours whose centroids fall inside a normalized image region.</div>
          <div><b className="text-[#d2e3fc]">Simplify</b><br/>Reduce contour point count with polygon approximation while keeping the same contour identity.</div>
        </div>
      </section>
      <section className="flex min-h-0 flex-col bg-[#111] p-4">
        <div className="text-[9px] font-black text-[#8ab4f8]">INTERACTIVE MENTAL MODEL</div>
        <div className="mt-3 flex flex-1 items-center justify-center">
          <svg viewBox="0 0 720 460" className="h-full max-h-[620px] w-full">
            <rect x="20" y="20" width="680" height="420" rx="18" fill="#171717" stroke="#3c4043"/>
            {Array.from({length:80}).map((_,i)=>{const x=45+(i*83)%620;const y=55+(i*47)%330;const r=2+(i%4);return <circle key={i} cx={x} cy={y} r={r} fill="none" stroke="#80868b" opacity=".45"/>;})}
            <path d="M120 115 C160 55 280 70 300 150 C320 235 210 285 135 230 C80 188 80 145 120 115Z" fill="none" stroke="#81c995" strokeWidth="5"/>
            <path d="M430 105 C525 85 625 155 590 260 C555 365 415 350 382 248 C355 165 382 118 430 105Z" fill="none" stroke="#81c995" strokeWidth="5"/>
            <text x="42" y="410" fill="#80868b" fontSize="18">gray = rejected before store</text>
            <text x="390" y="410" fill="#81c995" fontSize="18">green = retained candidates</text>
          </svg>
        </div>
      </section>
      <section className="overflow-y-auto border-l border-[#3c4043] p-4">
        <button onClick={onClose} className="float-right rounded p-1 hover:bg-[#3c4043]"><X size={17}/></button>
        <div className="text-[9px] font-black text-[#fdd663]">HOW TO TUNE</div>
        <ol className="mt-3 list-decimal space-y-3 pl-4 text-[9px] leading-4 text-[#bdc1c6]">
          <li>Choose the source. Prefer a clean BinaryMask when an Image Processing Service can provide one.</li>
          <li>Run once and inspect the <b>Memory Funnel</b>: candidate count versus retained geometry.</li>
          <li>Raise the default early thresholds until obvious junk is removed, but keep meaningful small shapes.</li>
          <li>Use filter stages to answer the semantic question: “which shapes do I actually want?”</li>
          <li>Inspect `edge_map` and `contour_image` as real black/white artifacts, then inspect selected contour metrics/geometry.</li>
          <li>Deploy only after the final `ContourSet` is stable.</li>
        </ol>
        <div className="mt-5 rounded border border-[#5f6368] bg-[#292a2d] p-3 text-[9px] text-[#9aa0a6]">Performance rule: do not solve a 20,000-contour problem by sending 20,000 coordinate arrays to the browser. Use early rejection + paged metrics + lazy geometry inspection.</div>
      </section>
    </div>
  </div>
);
