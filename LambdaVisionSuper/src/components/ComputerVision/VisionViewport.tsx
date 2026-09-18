import { Maximize2, Minus, Plus } from 'lucide-react';
import { useRef, useState } from 'react';
import type { LocatedRoi, MasterRoi, NormalizedRect } from '../../api/visionAppApi';

type Props={
  imageUrl:string|null; rois?:MasterRoi[]; located?:LocatedRoi[]; selectedId?:string|null;
  drawMode?:boolean; onSelect?:(id:string)=>void; onDraw?:(rect:NormalizedRect)=>void;
};

export const VisionViewport=({imageUrl,rois=[],located=[],selectedId,drawMode=false,onSelect,onDraw}:Props)=>{
 const imageWrap=useRef<HTMLDivElement|null>(null);const [start,setStart]=useState<{x:number;y:number}|null>(null);const [draft,setDraft]=useState<NormalizedRect|null>(null);const [scale,setScale]=useState(1);const [pan,setPan]=useState({x:0,y:0});const [panStart,setPanStart]=useState<{x:number;y:number;px:number;py:number}|null>(null);
 const pos=(e:React.PointerEvent)=>{const r=imageWrap.current?.getBoundingClientRect();if(!r)return null;return{x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))};};
 const down=(e:React.PointerEvent)=>{if(drawMode){const p=pos(e);if(!p)return;setStart(p);setDraft({x:p.x,y:p.y,w:.001,h:.001});}else setPanStart({x:e.clientX,y:e.clientY,px:pan.x,py:pan.y});(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);};
 const move=(e:React.PointerEvent)=>{if(drawMode&&start){const p=pos(e);if(!p)return;setDraft({x:Math.min(start.x,p.x),y:Math.min(start.y,p.y),w:Math.max(.001,Math.abs(p.x-start.x)),h:Math.max(.001,Math.abs(p.y-start.y))});}else if(panStart)setPan({x:panStart.px+e.clientX-panStart.x,y:panStart.py+e.clientY-panStart.y});};
 const up=()=>{if(drawMode&&draft&&draft.w>.005&&draft.h>.005)onDraw?.(draft);setStart(null);setDraft(null);setPanStart(null);};
 const wheel=(e:React.WheelEvent)=>{e.preventDefault();setScale(s=>Math.max(.2,Math.min(8,s*(e.deltaY<0?1.12:.89))));};
 const fit=()=>{setScale(1);setPan({x:0,y:0});};
 const rects=[...rois.map(r=>({id:r.roi_id,name:r.name,rect:r.rect,ok:true,score:1})),...located.map(r=>({id:r.roi_id,name:r.name,rect:r.rect,ok:r.found,score:r.score}))];
 return <div className="relative flex h-full w-full items-center justify-center overflow-hidden bg-[#17181a]" onWheel={wheel}>
  <div className="absolute right-3 top-3 z-20 flex gap-1 rounded border border-[#3c4043] bg-[#202124]/90 p-1"><button className="cv-icon" onClick={()=>setScale(s=>Math.max(.2,s/1.12))}><Minus size={11}/></button><span className="min-w-[42px] px-1 text-center text-[8px] leading-6 text-[#9aa0a6]">{Math.round(scale*100)}%</span><button className="cv-icon" onClick={()=>setScale(s=>Math.min(8,s*1.12))}><Plus size={11}/></button><button className="cv-icon" onClick={fit}><Maximize2 size={11}/></button></div>
  {imageUrl?<div className="p-5" style={{transform:`translate(${pan.x}px,${pan.y}px) scale(${scale})`,transformOrigin:'center center'}} onPointerDown={down} onPointerMove={move} onPointerUp={up}>
    <div ref={imageWrap} className={`relative inline-block select-none ${drawMode?'cursor-crosshair':'cursor-grab active:cursor-grabbing'}`}>
      <img src={imageUrl} draggable={false} className="block max-h-[calc(100vh-150px)] max-w-[calc(100vw-240px)] object-contain"/>
      {rects.map((item,index)=><button key={`${item.id}-${index}`} onPointerDown={e=>e.stopPropagation()} onClick={e=>{e.stopPropagation();onSelect?.(item.id);}} className={`absolute border-2 ${item.ok?'border-[#81c995]':'border-[#f28b82]'} ${selectedId===item.id?'ring-2 ring-[#fdd663]':''}`} style={{left:`${item.rect.x*100}%`,top:`${item.rect.y*100}%`,width:`${item.rect.w*100}%`,height:`${item.rect.h*100}%`}}><span className="absolute -top-5 left-0 whitespace-nowrap bg-black/80 px-1 text-[8px] text-white">{item.name}{item.score!==1?` · ${item.score.toFixed(3)}`:''}</span></button>)}
      {draft?<div className="pointer-events-none absolute border-2 border-dashed border-[#8ab4f8] bg-[#8ab4f8]/10" style={{left:`${draft.x*100}%`,top:`${draft.y*100}%`,width:`${draft.w*100}%`,height:`${draft.h*100}%`}}/>:null}
    </div>
  </div>:<div className="rounded-xl border border-dashed border-[#5f6368] px-12 py-16 text-center text-[#80868b]"><div className="text-sm font-black">VISION VIEWPORT</div><div className="mt-2 text-[10px]">Upload, capture or select an image to begin.</div></div>}
 </div>;
};
