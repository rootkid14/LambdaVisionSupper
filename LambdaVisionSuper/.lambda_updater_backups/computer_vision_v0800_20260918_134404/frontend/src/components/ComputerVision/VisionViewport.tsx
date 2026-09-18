import { useRef, useState } from 'react';
import type { LocatedRoi, MasterRoi, NormalizedRect } from '../../api/visionAppApi';

type Props={
  imageUrl:string|null;
  rois?:MasterRoi[];
  located?:LocatedRoi[];
  selectedId?:string|null;
  drawMode?:boolean;
  onSelect?:(id:string)=>void;
  onDraw?:(rect:NormalizedRect)=>void;
};

export const VisionViewport=({imageUrl,rois=[],located=[],selectedId,drawMode=false,onSelect,onDraw}:Props)=>{
 const wrap=useRef<HTMLDivElement|null>(null);const [start,setStart]=useState<{x:number;y:number}|null>(null);const [draft,setDraft]=useState<NormalizedRect|null>(null);
 const pos=(e:React.PointerEvent)=>{const r=wrap.current?.getBoundingClientRect();if(!r)return null;return{x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))};};
 const down=(e:React.PointerEvent)=>{if(!drawMode)return;const p=pos(e);if(!p)return;setStart(p);setDraft({x:p.x,y:p.y,w:.001,h:.001});(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);};
 const move=(e:React.PointerEvent)=>{if(!drawMode||!start)return;const p=pos(e);if(!p)return;setDraft({x:Math.min(start.x,p.x),y:Math.min(start.y,p.y),w:Math.max(.001,Math.abs(p.x-start.x)),h:Math.max(.001,Math.abs(p.y-start.y))});};
 const up=()=>{if(draft&&draft.w>.005&&draft.h>.005)onDraw?.(draft);setStart(null);setDraft(null);};
 const rects=[...rois.map(r=>({id:r.roi_id,name:r.name,rect:r.rect,ok:true,score:1})),...located.map(r=>({id:r.roi_id,name:r.name,rect:r.rect,ok:r.found,score:r.score}))];
 return <div className="flex h-full w-full items-center justify-center overflow-auto bg-[#17181a] p-5">
   {imageUrl?<div ref={wrap} onPointerDown={down} onPointerMove={move} onPointerUp={up} className={`relative inline-block max-h-full max-w-full select-none ${drawMode?'cursor-crosshair':'cursor-default'}`}>
     <img src={imageUrl} draggable={false} className="block max-h-[calc(100vh-190px)] max-w-[calc(100vw-720px)] object-contain"/>
     {rects.map((item,index)=><button key={`${item.id}-${index}`} onClick={(e)=>{e.stopPropagation();onSelect?.(item.id);}} className={`absolute border-2 ${item.ok?'border-[#81c995]':'border-[#f28b82]'} ${selectedId===item.id?'ring-2 ring-[#fdd663]':''}`} style={{left:`${item.rect.x*100}%`,top:`${item.rect.y*100}%`,width:`${item.rect.w*100}%`,height:`${item.rect.h*100}%`}}><span className="absolute -top-5 left-0 whitespace-nowrap bg-black/80 px-1 text-[8px] text-white">{item.name}{item.score!==1?` · ${item.score.toFixed(3)}`:''}</span></button>)}
     {draft?<div className="pointer-events-none absolute border-2 border-dashed border-[#8ab4f8] bg-[#8ab4f8]/10" style={{left:`${draft.x*100}%`,top:`${draft.y*100}%`,width:`${draft.w*100}%`,height:`${draft.h*100}%`}}/>:null}
   </div>:<div className="rounded-xl border border-dashed border-[#5f6368] px-12 py-16 text-center text-[#80868b]"><div className="text-sm font-black">VISION VIEWPORT</div><div className="mt-2 text-[10px]">Upload a Master Sample or a Working test image to begin.</div></div>}
 </div>;
};
