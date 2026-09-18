import type { SamplingArtifact, SamplingWorkspace } from './types';

const palette = ['#8ab4f8', '#81c995', '#fdd663', '#f28b82', '#c58af9', '#78d9ec'];

export const LineChart = ({
  series,
  labels,
}: {
  series: number[][];
  labels?: string[];
}) => {
  const flat = series.flat().filter(Number.isFinite);
  const min = flat.length ? Math.min(...flat) : 0;
  const max = flat.length ? Math.max(...flat) : 1;
  const span = Math.max(1e-9, max - min);
  const width = 1000;
  const height = 500;
  const pad = 40;

  return (
    <div className="h-full w-full p-3">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full rounded border border-[#3c4043] bg-[#171717]">
        <rect x={pad} y={pad} width={width - pad * 2} height={height - pad * 2} fill="none" stroke="#3c4043" />
        {series.slice(0, 16).map((row, rowIndex) => {
          if (row.length < 2) return null;
          const points = row.map((value, i) => {
            const x = pad + (i / Math.max(1, row.length - 1)) * (width - pad * 2);
            const y = height - pad - ((value - min) / span) * (height - pad * 2);
            return `${x},${y}`;
          }).join(' ');
          return (
            <polyline
              key={rowIndex}
              points={points}
              fill="none"
              stroke={palette[rowIndex % palette.length]}
              strokeWidth="2"
            />
          );
        })}
        <text x={pad} y={22} fill="#bdc1c6" fontSize="16">max {max.toFixed(3)}</text>
        <text x={pad} y={height - 10} fill="#9aa0a6" fontSize="14">min {min.toFixed(3)}</text>
      </svg>
      {labels?.length ? (
        <div className="mt-1 flex flex-wrap gap-2 text-[9px] text-[#9aa0a6]">
          {labels.slice(0, 12).map((label, i) => (
            <span key={label} style={{ color: palette[i % palette.length] }}>{label}</span>
          ))}
        </div>
      ) : null}
    </div>
  );
};

export const FeatureBars = ({ values, names }: { values: number[]; names: string[] }) => {
  const finite = values.filter(Number.isFinite);
  const min = finite.length ? Math.min(...finite) : 0;
  const max = finite.length ? Math.max(...finite) : 1;
  const span = Math.max(1e-9, max - min);
  return (
    <div className="h-full overflow-auto p-4">
      <div className="mb-3 text-[10px] font-black tracking-wider text-[#8ab4f8]">FEATURE VECTOR · {values.length}D</div>
      <div className="space-y-1">
        {values.map((value, i) => (
          <div key={`${names[i] ?? i}`} className="grid grid-cols-[180px_1fr_90px] items-center gap-2 text-[10px]">
            <div className="truncate font-mono text-[#bdc1c6]">{names[i] ?? `f${i}`}</div>
            <div className="h-3 rounded bg-[#292a2d] overflow-hidden">
              <div className="h-full bg-[#8ab4f8]" style={{ width: `${Math.max(1, ((value - min) / span) * 100)}%` }} />
            </div>
            <div className="text-right font-mono text-[#9aa0a6]">{Number(value).toFixed(5)}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const FeatureMatrixView = ({ artifact }: { artifact: any }) => {
  const values: number[][] = artifact.values ?? [];
  const flat = values.flat().filter(Number.isFinite);
  const min = flat.length ? Math.min(...flat) : 0;
  const max = flat.length ? Math.max(...flat) : 1;
  const span = Math.max(1e-9, max - min);
  return (
    <div className="h-full overflow-auto p-4">
      <div className="mb-3 text-[10px] font-black tracking-wider text-[#8ab4f8]">FEATURE MATRIX · {values.length}×{artifact.feature_names?.length ?? 0}</div>
      <div className="inline-grid gap-[2px] rounded border border-[#3c4043] bg-[#202124] p-2" style={{ gridTemplateColumns: `repeat(${Math.max(1, artifact.feature_names?.length ?? 1)}, 34px)` }}>
        {values.flatMap((row, r) => row.map((value, c) => {
          const t = Math.max(0, Math.min(1, (value - min) / span));
          return (
            <div
              key={`${r}:${c}`}
              title={`${artifact.row_labels?.[r] ?? r} · ${artifact.feature_names?.[c] ?? c} = ${value}`}
              className="h-8 w-8 rounded-sm border border-black/20"
              style={{ background: `rgba(138,180,248,${0.12 + t * 0.88})` }}
            />
          );
        }))}
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-[9px] text-[#9aa0a6]">
        {(artifact.feature_names ?? []).map((name: string) => <span key={name}>{name}</span>)}
      </div>
    </div>
  );
};

export const MeasurementTableView = ({ artifact }: { artifact: any }) => (
  <div className="h-full overflow-auto p-4">
    <table className="w-full border-collapse text-[10px]">
      <thead className="sticky top-0 bg-[#292a2d] text-[#8ab4f8]">
        <tr>{(artifact.columns ?? []).map((column: string) => <th key={column} className="border border-[#3c4043] px-2 py-1 text-left">{column}</th>)}</tr>
      </thead>
      <tbody>
        {(artifact.rows ?? []).map((row: any, i: number) => (
          <tr key={i} className="odd:bg-[#202124] even:bg-[#242528]">
            {(artifact.columns ?? []).map((column: string) => <td key={column} className="border border-[#3c4043] px-2 py-1 font-mono text-[#bdc1c6]">{String(row[column] ?? '')}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export const SyntheticGuideVisual = ({
  visualization,
  workspace,
  params,
}: {
  visualization?: string;
  workspace: SamplingWorkspace;
  params: Record<string, any>;
}) => {
  if (workspace === 'spatial') {
    const count = Math.max(1, Number(params.ray_count ?? params.rings ?? 5));
    const cx = Number(params.center_x ?? 0.5) * 800;
    const cy = Number(params.center_y ?? 0.5) * 500;
    return (
      <svg viewBox="0 0 800 500" className="h-full w-full rounded border border-[#3c4043] bg-[#171717]">
        <defs>
          <linearGradient id="sample-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#202124"/><stop offset="0.5" stopColor="#5f6368"/><stop offset="1" stopColor="#292a2d"/></linearGradient>
        </defs>
        <rect width="800" height="500" fill="url(#sample-bg)" />
        {visualization === 'rings' ? Array.from({ length: count }).map((_, i) => (
          <circle key={i} cx={cx} cy={cy} r={35 + i * Math.min(45, 180 / count)} fill="none" stroke="#8ab4f8" strokeWidth="2" opacity={0.9} />
        )) : visualization === 'patch_grid' ? (
          <g>{Array.from({ length: Number(params.rows ?? 4) }).flatMap((_, r) => Array.from({ length: Number(params.cols ?? 4) }).map((__, c) => (
            <rect key={`${r}:${c}`} x={c * 800 / Number(params.cols ?? 4)} y={r * 500 / Number(params.rows ?? 4)} width={800 / Number(params.cols ?? 4)} height={500 / Number(params.rows ?? 4)} fill="none" stroke="#8ab4f8" strokeWidth="2" />
          )))}</g>
        ) : visualization === 'cross' ? (
          <g><line x1="0" y1={cy} x2="800" y2={cy} stroke="#8ab4f8" strokeWidth="3"/><line x1={cx} y1="0" x2={cx} y2="500" stroke="#81c995" strokeWidth="3"/><circle cx={cx} cy={cy} r="6" fill="#fdd663"/></g>
        ) : (
          <g>{Array.from({ length: count }).map((_, i) => {
            const y = ((i + 1) / (count + 1)) * 500;
            return <line key={i} x1="0" y1={y} x2="800" y2={y} stroke="#8ab4f8" strokeWidth="2" />;
          })}</g>
        )}
      </svg>
    );
  }

  if (workspace === 'spectral') {
    if (visualization === 'fft2d' || visualization === 'radial_bands' || visualization === 'angular_bands') {
      return (
        <svg viewBox="0 0 800 500" className="h-full w-full rounded border border-[#3c4043] bg-[#050505]">
          <defs><radialGradient id="spec"><stop offset="0" stopColor="#fff"/><stop offset="0.15" stopColor="#8ab4f8" stopOpacity="0.9"/><stop offset="0.45" stopColor="#c58af9" stopOpacity="0.35"/><stop offset="1" stopColor="#000" stopOpacity="0"/></radialGradient></defs>
          <rect width="800" height="500" fill="#050505"/>
          <ellipse cx="400" cy="250" rx="320" ry="210" fill="url(#spec)"/>
          <line x1="120" y1="420" x2="680" y2="80" stroke="#fdd663" strokeWidth="8" opacity="0.35"/>
          <line x1="160" y1="450" x2="640" y2="50" stroke="#fdd663" strokeWidth="4" opacity="0.55"/>
          {visualization === 'radial_bands' ? Array.from({length: Number(params.bands ?? 8)}).map((_,i)=><circle key={i} cx="400" cy="250" r={20+i*25} fill="none" stroke="#81c995" strokeWidth="1" opacity="0.8"/>) : null}
          {visualization === 'angular_bands' ? Array.from({length: Number(params.sectors ?? 12)}).map((_,i)=>{ const a=Math.PI*i/Number(params.sectors ?? 12); return <line key={i} x1="400" y1="250" x2={400+300*Math.cos(a)} y2={250+300*Math.sin(a)} stroke="#81c995" strokeWidth="1"/>;}) : null}
        </svg>
      );
    }
    const bins = Number(params.bins ?? 32);
    const bars = Array.from({ length: Math.min(64, bins) }).map((_, i) => 0.15 + 0.85 * Math.exp(-Math.pow((i / Math.max(1, Math.min(64,bins)-1) - 0.55) * 3, 2)) * (0.7 + 0.3 * Math.sin(i * 1.7) ** 2));
    return <FeatureBars values={bars} names={bars.map((_,i)=>`bin_${i}`)} />;
  }

  const count = Math.max(12, Number(params.samples ?? 48));
  const points = Array.from({ length: count }).map((_, i) => {
    const a = (Math.PI * 2 * i) / count;
    const radius = 150 + 30 * Math.sin(a * 3) + 12 * Math.cos(a * 7);
    return [400 + Math.cos(a) * radius, 250 + Math.sin(a) * radius];
  });
  return (
    <svg viewBox="0 0 800 500" className="h-full w-full rounded border border-[#3c4043] bg-[#171717]">
      <polyline points={points.map(p=>p.join(',')).join(' ')} fill="rgba(138,180,248,0.08)" stroke="#8ab4f8" strokeWidth="3" />
      {points.filter((_,i)=>i%Math.max(1,Math.floor(count/24))===0).map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r="4" fill="#fdd663"/>)}
    </svg>
  );
};

export const ArtifactDataView = ({ artifact }: { artifact: SamplingArtifact | null }) => {
  if (!artifact) return <div className="flex h-full items-center justify-center text-sm text-[#80868b]">Run the pipeline to inspect an artifact.</div>;
  if (artifact.type === 'contour_set') return <MeasurementTableView artifact={{ columns: ['id','area_px2','perimeter_px','point_count','aspect_ratio','circularity','solidity'], rows: (artifact as any).metrics ?? [] }} />;
  if (artifact.type === 'sampling_housing') return <div className="h-full overflow-auto p-4"><div className="text-sm font-black text-[#e8eaed]">{(artifact as any).kind} · {(artifact as any).element_count} elements</div><pre className="mt-3 text-[10px] text-[#bdc1c6]">{JSON.stringify((artifact as any).elements ?? [], null, 2)}</pre></div>;
  if (artifact.type === 'profile_set') return <LineChart series={(artifact as any).series ?? []} labels={(artifact as any).labels ?? []} />;
  if (artifact.type === 'histogram_1d') return <LineChart series={[((artifact as any).values ?? [])]} labels={[(artifact as any).channel ?? 'histogram']} />;
  if (artifact.type === 'data_block_set') return <div className="h-full overflow-auto p-4"><div className="mb-3 text-[10px] font-black text-[#8ab4f8]">DATA BLOCKS · {(artifact as any).count ?? 0}</div><div className="grid grid-cols-2 gap-2">{((artifact as any).blocks ?? []).map((block:any)=><div key={block.block_id} className="rounded border border-[#5f6368] bg-[#292a2d] p-2"><div className="text-[9px] font-black text-[#d2e3fc]">{block.label}</div><div className="mt-1 text-[8px] text-[#9aa0a6]">{block.kind} · shape [{block.shape?.join('×')}]</div><div className="mt-1 text-[8px] text-[#80868b]">{block.description}</div><div className="mt-2 max-h-24 overflow-auto font-mono text-[7px] text-[#bdc1c6]">{(block.values ?? []).slice(0,64).map((v:number)=>Number(v).toFixed(3)).join(', ')}</div></div>)}</div></div>;
  if (artifact.type === 'composed_data') { const values:any=(artifact as any).values??[]; const shape=(artifact as any).shape??[]; return shape.length<=1 ? <FeatureBars values={values as number[]} names={(values as number[]).map((_,i)=>`d${i}`)} /> : <FeatureMatrixView artifact={{values,feature_names:Array.from({length:shape[1]??0},(_,i)=>`c${i}`),row_labels:Array.from({length:shape[0]??0},(_,i)=>`r${i}`)}}/>; }
  if (artifact.type === 'feature_vector') return <FeatureBars values={(artifact as any).values ?? []} names={(artifact as any).names ?? []} />;
  if (artifact.type === 'feature_matrix') return <FeatureMatrixView artifact={artifact} />;
  if (artifact.type === 'measurement_table') return <MeasurementTableView artifact={artifact} />;
  return <pre className="h-full overflow-auto p-4 text-[10px] text-[#bdc1c6]">{JSON.stringify(artifact, null, 2)}</pre>;
};
