import { useEffect, useRef, useState } from 'react';
import { Minus, Plus, RotateCcw } from 'lucide-react';
import type { SamplingDomain, SamplingMethodDefinition, SamplingProgramDefinition } from './types';

const countFor=(method:SamplingMethodDefinition,length:number)=>method.sampling_mode==='step'?Math.max(2,Math.min(60,Math.floor(length/Math.max(.25,method.sample_step))+1)):method.sampling_mode==='full'?Math.max(2,Math.min(60,Math.floor(length))):Math.max(2,Math.min(60,method.sample_count));

const PointsOnLine=({x1,y1,x2,y2,n}:{x1:number;y1:number;x2:number;y2:number;n:number})=><>{Array.from({length:n},(_,i)=>{const t=n<=1?0:i/(n-1);return <circle key={i} cx={x1+(x2-x1)*t} cy={y1+(y2-y1)*t} r="2.4" fill="#fdd663" vectorEffect="non-scaling-stroke"/>;})}</>;

const MethodOverlay=({method,rect}:{method:SamplingMethodDefinition;rect:{x:number;y:number;w:number;h:number}})=>{
 const stroke="#8ab4f8";const parts:any[]=[];
 if(method.kind==='rays'){
  const axis=String(method.parameters.axis??'x'),n=Math.max(1,Number(method.parameters.ray_count??5));
  if(axis==='x'||axis==='both')for(let i=0;i<n;i++){const y=rect.y+(i+.5)*rect.h/n;const dots=countFor(method,rect.w);parts.push(<g key={`xh${i}`}><line x1={rect.x} y1={y} x2={rect.x+rect.w} y2={y} stroke={stroke} strokeWidth="2" vectorEffect="non-scaling-stroke"/><PointsOnLine x1={rect.x} y1={y} x2={rect.x+rect.w} y2={y} n={dots}/></g>);}
  if(axis==='y'||axis==='both')for(let i=0;i<n;i++){const x=rect.x+(i+.5)*rect.w/n;const dots=countFor(method,rect.h);parts.push(<g key={`yv${i}`}><line x1={x} y1={rect.y} x2={x} y2={rect.y+rect.h} stroke={stroke} strokeWidth="2" vectorEffect="non-scaling-stroke"/><PointsOnLine x1={x} y1={rect.y} x2={x} y2={rect.y+rect.h} n={dots}/></g>);}
 }
 if(method.kind==='cross'){
  const centers=method.placement.mode==='auto_grid'?Array.from({length:method.placement.rows*method.placement.cols},(_,i)=>({cx:(i%method.placement.cols+.5)/method.placement.cols,cy:(Math.floor(i/method.placement.cols)+.5)/method.placement.rows})):[{cx:method.placement.center_x,cy:method.placement.center_y}];
  const ratio=Number(method.parameters.length_ratio??.8);
  centers.forEach((c,i)=>{const cx=rect.x+c.cx*rect.w,cy=rect.y+c.cy*rect.h,hx=rect.w*ratio*.5,hy=rect.h*ratio*.5;const x1=Math.max(rect.x,cx-hx),x2=Math.min(rect.x+rect.w,cx+hx),y1=Math.max(rect.y,cy-hy),y2=Math.min(rect.y+rect.h,cy+hy);parts.push(<g key={`c${i}`}><line x1={x1} y1={cy} x2={x2} y2={cy} stroke={stroke} strokeWidth="2" vectorEffect="non-scaling-stroke"/><line x1={cx} y1={y1} x2={cx} y2={y2} stroke={stroke} strokeWidth="2" vectorEffect="non-scaling-stroke"/><PointsOnLine x1={x1} y1={cy} x2={x2} y2={cy} n={countFor(method,x2-x1)}/><PointsOnLine x1={cx} y1={y1} x2={cx} y2={y2} n={countFor(method,y2-y1)}/></g>);});
 }
 if(method.kind==='rings'){
  const centers=method.placement.mode==='auto_grid'?Array.from({length:method.placement.rows*method.placement.cols},(_,i)=>({cx:(i%method.placement.cols+.5)/method.placement.cols,cy:(Math.floor(i/method.placement.cols)+.5)/method.placement.rows})):[{cx:method.placement.center_x,cy:method.placement.center_y}];
  const ringCount=Math.max(1,Number(method.parameters.ring_count??3)),maxR=Math.min(rect.w,rect.h)*Number(method.parameters.max_radius_ratio??.4);
  centers.forEach((c,ci)=>{const cx=rect.x+c.cx*rect.w,cy=rect.y+c.cy*rect.h;for(let ri=1;ri<=ringCount;ri++){const r=maxR*ri/ringCount,n=countFor(method,2*Math.PI*r);parts.push(<g key={`r${ci}-${ri}`}><circle cx={cx} cy={cy} r={r} fill="none" stroke={stroke} strokeWidth="1.5" vectorEffect="non-scaling-stroke"/>{Array.from({length:Math.min(n,48)},(_,i)=>{const a=2*Math.PI*i/Math.min(n,48);return <circle key={i} cx={cx+Math.cos(a)*r} cy={cy+Math.sin(a)*r} r="2" fill="#fdd663"/>;})}</g>);}});
 }
 if(method.kind==='histogram'||method.kind==='statistics')parts.push(<rect key="domain" x={rect.x+2} y={rect.y+2} width={Math.max(0,rect.w-4)} height={Math.max(0,rect.h-4)} fill="#8ab4f8" fillOpacity=".08" stroke="#8ab4f8" strokeDasharray="5 4" vectorEffect="non-scaling-stroke"/>);
 return <>{parts}</>;
};

export const SamplingProgramCanvas=({sourceUrl,domain,program,selectedMethod}:{sourceUrl:string|null;domain:SamplingDomain;program:SamplingProgramDefinition;selectedMethod:SamplingMethodDefinition|null;})=>{
 const hostRef=useRef<HTMLDivElement|null>(null);const [size,setSize]=useState({w:1,h:1});const [fit,setFit]=useState(1);const [zoom,setZoom]=useState(1);const [pan,setPan]=useState({x:0,y:0});const drag=useRef<any>(null);
 const reset=()=>{setZoom(1);setPan({x:0,y:0});};
 useEffect(()=>{const calc=()=>{const host=hostRef.current;if(!host||size.w<2||size.h<2)return;const r=host.getBoundingClientRect();setFit(Math.max(.01,Math.min((r.width-24)/size.w,(r.height-24)/size.h)));};calc();const ro=new ResizeObserver(calc);if(hostRef.current)ro.observe(hostRef.current);return()=>ro.disconnect();},[size]);
 useEffect(()=>reset(),[sourceUrl,domain]);
 const grid=program.local_domain.grid;
 const rects=domain==='global'?[{x:0,y:0,w:size.w,h:size.h,key:'global'}]:Array.from({length:grid.rows*grid.cols},(_,i)=>{const row=Math.floor(i/grid.cols),col=i%grid.cols;const x0=col*size.w/grid.cols,y0=row*size.h/grid.rows,x1=(col+1)*size.w/grid.cols,y1=(row+1)*size.h/grid.rows;return{x:x0,y:y0,w:x1-x0,h:y1-y0,key:`p${row}-${col}`};});
 return <div ref={hostRef} className="relative h-full min-h-0 overflow-hidden bg-[#111] select-none" onWheel={(e)=>{e.preventDefault();setZoom((v)=>Math.min(20,Math.max(.08,v*(e.deltaY<0?1.12:.89))));}} onMouseDown={(e)=>{if(e.button===0)drag.current={x:e.clientX,y:e.clientY,px:pan.x,py:pan.y};}} onMouseMove={(e)=>{if(drag.current)setPan({x:drag.current.px+e.clientX-drag.current.x,y:drag.current.py+e.clientY-drag.current.y});}} onMouseUp={()=>drag.current=null} onMouseLeave={()=>drag.current=null} onDoubleClick={reset}>
  {sourceUrl?<div className="absolute left-1/2 top-1/2 origin-center" style={{width:size.w,height:size.h,transform:`translate(-50%,-50%) translate(${pan.x}px,${pan.y}px) scale(${fit*zoom})`}}><img src={sourceUrl} draggable={false} className="absolute inset-0 h-full w-full" onLoad={(e)=>setSize({w:e.currentTarget.naturalWidth||1,h:e.currentTarget.naturalHeight||1})}/><svg viewBox={`0 0 ${size.w} ${size.h}`} className="absolute inset-0 h-full w-full overflow-visible">{domain==='local'?rects.map((r,i)=><g key={r.key}><rect x={r.x} y={r.y} width={r.w} height={r.h} fill="none" stroke="#81c995" strokeOpacity=".8" strokeWidth="1.2" vectorEffect="non-scaling-stroke"/><text x={r.x+5} y={r.y+13} fill="#81c995" fontSize="9">P{i+1}</text></g>):<rect x="1" y="1" width={Math.max(0,size.w-2)} height={Math.max(0,size.h-2)} fill="none" stroke="#81c995" strokeWidth="2" vectorEffect="non-scaling-stroke"/>}{selectedMethod?rects.map((r)=><MethodOverlay key={`m${r.key}`} method={selectedMethod} rect={r}/>):null}</svg></div>:<div className="absolute inset-0 flex items-center justify-center text-[10px] text-[#5f6368]">Build the shared inspected image first.</div>}
  <div className="absolute left-3 top-3 rounded border border-[#3c4043] bg-[#202124]/90 px-2 py-1"><div className="text-[9px] font-black text-[#e8eaed]">{domain==='global'?'GLOBAL DOMAIN':'LOCAL PATCH DOMAIN'}</div><div className="text-[8px] text-[#80868b]">{selectedMethod?`Visualizing ${selectedMethod.label??selectedMethod.kind}`:domain==='global'?'Whole inspected image = one sampling domain':`${grid.rows} × ${grid.cols} patches · select a method to visualize it inside every patch`}</div></div>
  <div className="absolute right-3 top-3 flex items-center gap-1 rounded border border-[#3c4043] bg-[#202124]/90 p-1"><button onClick={()=>setZoom((v)=>Math.max(.08,v/1.2))} className="p-1"><Minus size={12}/></button><span className="min-w-[48px] text-center font-mono text-[9px] text-[#8ab4f8]">{Math.round(zoom*100)}%</span><button onClick={()=>setZoom((v)=>Math.min(20,v*1.2))} className="p-1"><Plus size={12}/></button><button onClick={reset} className="p-1"><RotateCcw size={12}/></button></div>
  <div className="absolute bottom-2 left-2 rounded bg-[#202124]/90 px-2 py-1 text-[8px] text-[#80868b]">Yellow dots = sampling density · wheel zoom · drag pan · double-click fit</div>
 </div>;
};
