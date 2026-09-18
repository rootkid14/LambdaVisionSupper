import { useEffect, useState } from 'react';
import { X } from 'lucide-react';

const INFO:Record<string,{title:string;body:string;formula?:string}>={
 channels:{title:'Image channels',body:'A channel is one numerical view of the same image. Gray represents brightness. RGB isolates red/green/blue. HSV separates hue, saturation and brightness. LAB separates perceptual lightness from two color axes.'},
 mean:{title:'Mean',body:'The mean is the average sampled value. It answers: where is the center of this distribution?',formula:'μ = (1/N) Σ xᵢ'},
 std:{title:'Standard deviation',body:'STD measures how spread out sampled values are around their mean. A flat region tends to have small STD; a mixed/rough region tends to have larger STD.',formula:'σ = √[(1/N) Σ(xᵢ − μ)²]'},
 min:{title:'Minimum',body:'The smallest sampled value in the selected domain or sampling path.'},
 max:{title:'Maximum',body:'The largest sampled value in the selected domain or sampling path.'},
 median:{title:'Median',body:'The middle value after sorting samples. It is less sensitive to a few extreme outliers than the mean.'},
 histogram:{title:'Histogram',body:'A histogram converts many sample values into a distribution: each bar stores how much data falls into one value interval.'},
 histogram_bins:{title:'Histogram bins',body:'Bins control resolution. Fewer bins give a coarse, compact distribution. More bins preserve finer intensity/color detail but create a longer vector.'},
 sampling_density:{title:'Sampling density',body:'Choose how many numerical samples are taken along each ray/cross/ring. Fixed count gives model-stable vector sizes; fixed step preserves physical spacing; full density follows source pixels.'},
 sampling_step:{title:'Sampling step',body:'Step is the spatial distance between neighboring samples along a path. Smaller step = denser sampling and longer vectors.'},
};

const Demo=({topic}:{topic:string})=>{
 if(topic==='mean'||topic==='std')return <svg viewBox="0 0 360 120" className="h-32 w-full rounded bg-[#111]"><polyline points="10,90 45,75 80,80 115,25 150,70 185,52 220,60 255,18 290,65 340,45" fill="none" stroke="#8ab4f8" strokeWidth="3"/><line x1="10" y1="58" x2="340" y2="58" stroke="#fdd663" strokeDasharray="6 4"/><text x="15" y="52" fill="#fdd663" fontSize="10">mean</text>{topic==='std'?<><line x1="300" y1="30" x2="300" y2="86" stroke="#81c995"/><text x="306" y="59" fill="#81c995" fontSize="9">spread ≈ STD</text></>:null}</svg>;
 if(topic==='histogram'||topic==='histogram_bins')return <svg viewBox="0 0 360 120" className="h-32 w-full rounded bg-[#111]">{[28,55,92,72,38,18,10,5].map((h,i)=><rect key={i} x={20+i*40} y={108-h} width="30" height={h} fill="#8ab4f8"/>)}<line x1="15" y1="108" x2="350" y2="108" stroke="#5f6368"/><text x="18" y="118" fill="#80868b" fontSize="8">low value</text><text x="300" y="118" fill="#80868b" fontSize="8">high</text></svg>;
 if(topic==='sampling_density'||topic==='sampling_step')return <svg viewBox="0 0 360 120" className="h-32 w-full rounded bg-[#111]"><line x1="20" y1="45" x2="340" y2="45" stroke="#8ab4f8" strokeWidth="2"/>{Array.from({length:17},(_,i)=><circle key={`a${i}`} cx={20+i*20} cy="45" r="3" fill="#fdd663"/>)}<text x="20" y="30" fill="#bdc1c6" fontSize="9">dense / small step</text><line x1="20" y1="90" x2="340" y2="90" stroke="#8ab4f8" strokeWidth="2"/>{Array.from({length:5},(_,i)=><circle key={`b${i}`} cx={20+i*80} cy="90" r="4" fill="#fdd663"/>)}<text x="20" y="78" fill="#bdc1c6" fontSize="9">sparse / large step</text></svg>;
 return null;
};

export const SamplingConceptHelpModal=({topic,channelPreviewUrl,onClose}:{topic:string;channelPreviewUrl?:string|null;onClose:()=>void;})=>{
 const info=INFO[topic]??{title:topic,body:'This parameter changes how Sampling LAB converts image data into structured numerical features.'};
 return <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/70 p-6"><div className="max-h-[90vh] w-[760px] overflow-y-auto rounded border border-[#5f6368] bg-[#202124] shadow-2xl"><div className="flex items-center border-b border-[#3c4043] px-4 py-3"><div><div className="text-xs font-black">{info.title}</div><div className="text-[8px] uppercase tracking-[.13em] text-[#8ab4f8]">Interactive Sampling Guide</div></div><button onClick={onClose} className="ml-auto"><X size={17}/></button></div><div className="grid gap-4 p-4 md:grid-cols-2"><div><p className="text-[10px] leading-5 text-[#bdc1c6]">{info.body}</p>{info.formula?<div className="mt-3 rounded border border-[#3c4043] bg-[#111] p-3 font-mono text-sm text-[#fdd663]">{info.formula}</div>:null}<div className="mt-4"><Demo topic={topic}/></div></div><div className="rounded border border-[#3c4043] bg-[#18191b] p-3"><div className="mb-2 text-[8px] font-black uppercase tracking-[.12em] text-[#81c995]">Image-grounded view</div>{channelPreviewUrl?<img src={channelPreviewUrl} className="max-h-[360px] w-full object-contain"/>:<div className="flex h-[260px] items-center justify-center text-center text-[9px] leading-5 text-[#80868b]">For channel help, use the eye button beside Gray/R/G/B/H/S/V/L*/a*/b* to extract that channel from the actual inspected image.</div>}</div></div></div></div>;
};
