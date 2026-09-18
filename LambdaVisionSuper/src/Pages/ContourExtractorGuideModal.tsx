import { X } from 'lucide-react';

const RoadmapCard = ({title, body}:{title:string; body:string}) => (
  <div className="rounded-lg border border-[#3c4043] bg-[#202124] p-3">
    <div className="text-[9px] font-black uppercase tracking-[.14em] text-[#8ab4f8]">{title}</div>
    <div className="mt-1 text-[9px] leading-4 text-[#bdc1c6]">{body}</div>
  </div>
);

export const ContourExtractorGuideModal = ({onClose}:{onClose:()=>void}) => (
  <div className="fixed inset-0 z-[180] flex items-center justify-center bg-black/80 p-4">
    <div className="grid h-[90vh] w-[94vw] max-w-[1580px] grid-cols-[390px_minmax(0,1fr)_390px] overflow-hidden rounded-xl border border-[#5f6368] bg-[#202124] text-[#e8eaed] shadow-2xl">
      <section className="overflow-y-auto border-r border-[#3c4043] p-4">
        <div className="text-[9px] font-black uppercase tracking-[.18em] text-[#81c995]">Contour Extractor LAB · System Guide</div>
        <h2 className="mt-2 text-xl font-black">Find the shapes that matter</h2>
        <p className="mt-3 text-[10px] leading-5 text-[#bdc1c6]">
          The LAB is not primarily a measurement tool. Its job is to turn a noisy field of candidate boundaries into a small, meaningful and inspectable <b>ContourSet</b> that other LABs can consume.
        </p>

        <div className="mt-4 rounded-lg border border-[#5f6368] bg-[#292a2d] p-3 text-[9px] leading-4 text-[#bdc1c6]">
          <div className="font-black text-[#fdd663]">MANDATORY MEMORY GATE</div>
          <div className="mt-1">Candidate coordinates are cheap-filtered immediately after extraction. Rejected contours are discarded before the retained ContourStore is created. Later stages keep only contour IDs; they do not clone geometry.</div>
        </div>

        <div className="mt-4 space-y-3 text-[9px] text-[#9aa0a6]">
          <div><b className="text-[#d2e3fc]">Source mode</b><br/>Binary masks are best treated as boundaries directly. Natural/grayscale images usually need Canny or another edge-producing source.</div>
          <div><b className="text-[#d2e3fc]">Base Memory Filter</b><br/>Area, perimeter, bounding-box size and point count are deliberately simple because they run before geometry enters the long-lived store.</div>
          <div><b className="text-[#d2e3fc]">max retained</b><br/>A hard safety cap for pathological images. If a normal inspection needs thousands of retained shapes, first ask whether the source/edge stage is too noisy.</div>
          <div><b className="text-[#d2e3fc]">Stage Registry</b><br/>Every advanced contour algorithm is a registered stage with a manifest, parameters, guide and ID-in/ID-out execution contract. This is the extension point for future shape algorithms.</div>
          <div><b className="text-[#d2e3fc]">Inspect ≠ Filter</b><br/>Inspection visualizes and explains retained contours; stages change which contour IDs survive. The UI should always make that distinction visible.</div>
        </div>
      </section>

      <section className="flex min-h-0 flex-col bg-[#111] p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[9px] font-black uppercase tracking-[.14em] text-[#8ab4f8]">LONG-TERM WORKBENCH MODEL</div>
            <div className="mt-1 text-[10px] text-[#9aa0a6]">A contour discovery system, not a row of tiny filter buttons.</div>
          </div>
        </div>

        <div className="mt-3 grid flex-1 min-h-0 grid-rows-[minmax(0,1fr)_auto] gap-3">
          <div className="min-h-0 rounded-xl border border-[#3c4043] bg-[#171717] p-3">
            <svg viewBox="0 0 820 500" className="h-full w-full">
              <defs>
                <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#8ab4f8"/></marker>
              </defs>
              <rect x="20" y="20" width="780" height="460" rx="18" fill="#151515" stroke="#3c4043"/>
              <text x="55" y="68" fill="#e8eaed" fontSize="18" fontWeight="700">Candidate field</text>
              {Array.from({length:54}).map((_,i)=>{const x=55+(i*97)%245;const y=88+(i*53)%300;const r=2+(i%5);return <circle key={i} cx={x} cy={y} r={r} fill="none" stroke="#80868b" opacity=".45"/>;})}
              <path d="M92 145 C120 92 240 100 258 173 C280 251 181 292 110 247 C65 216 61 175 92 145Z" fill="none" stroke="#81c995" strokeWidth="4"/>
              <path d="M144 341 C185 305 249 315 272 365 C286 399 248 431 199 424 C153 418 125 378 144 341Z" fill="none" stroke="#81c995" strokeWidth="4"/>
              <line x1="322" y1="245" x2="390" y2="245" stroke="#8ab4f8" strokeWidth="3" markerEnd="url(#arrow)"/>
              <rect x="405" y="75" width="175" height="330" rx="14" fill="#202124" stroke="#5f6368"/>
              <text x="430" y="112" fill="#fdd663" fontSize="15" fontWeight="700">Contour Stage Registry</text>
              {[
                ['Metric / region filters', '#bdc1c6'],
                ['Largest / topology', '#bdc1c6'],
                ['Simplification', '#bdc1c6'],
                ['Master-shape matching', '#81c995'],
                ['Fourier descriptors', '#81c995'],
                ['Future topology graph', '#8ab4f8'],
                ['Future learned descriptor', '#8ab4f8'],
              ].map(([label,color],i)=><g key={label}><rect x="430" y={135+i*34} width="125" height="24" rx="6" fill="#292a2d"/><text x="440" y={152+i*34} fill={color} fontSize="11">{label}</text></g>)}
              <line x1="590" y1="245" x2="655" y2="245" stroke="#8ab4f8" strokeWidth="3" markerEnd="url(#arrow)"/>
              <path d="M680 153 C721 111 773 137 773 192 C771 244 726 280 682 253 C648 232 648 187 680 153Z" fill="none" stroke="#81c995" strokeWidth="6"/>
              <text x="658" y="320" fill="#e8eaed" fontSize="15" fontWeight="700">Meaningful ContourSet</text>
              <text x="658" y="343" fill="#9aa0a6" fontSize="11">stable IDs · lazy geometry</text>
              <text x="658" y="363" fill="#9aa0a6" fontSize="11">deployable service output</text>
            </svg>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <RoadmapCard title="Master / Reference Shapes" body="Select a master contour or master library, compare descriptors, and retain candidates that share the desired shape family."/>
            <RoadmapCard title="Fourier Shape Space" body="Represent an ordered contour as x(s)+iy(s), decompose it into harmonics, compare descriptors and visualize low-harmonic reconstruction."/>
            <RoadmapCard title="Future Advanced Stages" body="Topology, convex decomposition, graph structure, local curvature signatures, learned shape embeddings and hybrid rule/descriptor stages plug into the same stage registry."/>
          </div>
        </div>
      </section>

      <section className="overflow-y-auto border-l border-[#3c4043] p-4">
        <button onClick={onClose} className="float-right rounded p-1 hover:bg-[#3c4043]"><X size={17}/></button>
        <div className="text-[9px] font-black uppercase tracking-[.14em] text-[#fdd663]">Recommended workflow</div>
        <ol className="mt-3 list-decimal space-y-3 pl-4 text-[9px] leading-4 text-[#bdc1c6]">
          <li><b>Choose the cleanest source.</b> Prefer a BinaryMask from Image Processing LAB when possible; otherwise tune the edge source.</li>
          <li><b>Look at the Memory Funnel first.</b> A huge candidate count is acceptable only when the retained geometry collapses immediately.</li>
          <li><b>Tune the Base Memory Filter conservatively.</b> Remove obvious fragments without destroying meaningful small shapes.</li>
          <li><b>Build a discovery funnel.</b> Add large, explainable stages: metric/region → topology/shape → master-pattern stages.</li>
          <li><b>Inspect, do not guess.</b> Use contour table + canvas hit-test + stage before/after counts. Geometry should load lazily.</li>
          <li><b>Use Fourier/master matching only after candidates are sane.</b> Expensive shape analysis belongs after the cheap memory gate.</li>
          <li><b>Deploy the final ContourSet.</b> Comparison/Rule, Sampling or Global Vision should consume the stable service contract rather than reimplement contour discovery.</li>
        </ol>

        <div className="mt-5 rounded-lg border border-[#5f6368] bg-[#292a2d] p-3 text-[9px] leading-4 text-[#9aa0a6]">
          <div className="font-black text-[#81c995]">Fourier mental model</div>
          <div className="mt-1">Low harmonics describe the broad outline; higher harmonics restore finer shape detail. Translation and scale are normalized before descriptor comparison. The current Fourier stage is the first advanced pattern primitive, not the final limit of the LAB.</div>
        </div>

        <div className="mt-3 rounded-lg border border-[#5f6368] bg-[#292a2d] p-3 text-[9px] leading-4 text-[#9aa0a6]">
          <div className="font-black text-[#8ab4f8]">Design rule for future algorithms</div>
          <div className="mt-1">A new contour algorithm should register a stage manifest, consume retained contour IDs, avoid cloning geometry, provide an explanation/guide, expose meaningful before→after diagnostics, and reuse the standard contour inspector whenever possible.</div>
        </div>
      </section>
    </div>
  </div>
);
