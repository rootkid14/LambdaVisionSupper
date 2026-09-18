import { useEffect, useMemo, useRef, useState } from 'react';
import { CirclePlay, Code2, Cpu, Database, Sparkles } from 'lucide-react';
import type { AutomationEndpoint } from '../../api/visionAppApi';

type Props={value:string;onChange:(value:string)=>void;endpoints:AutomationEndpoint[];insertCommand?:{id:number;path:string;callable:boolean}|null};

type Token={text:string;kind:'plain'|'comment'|'string'|'keyword'|'constant'|'number'|'namespace'|'operator'};
const keywords=new Set(['if','else','and','or','not','pass']);
const constants=new Set(['ON','OFF','OK','NG','NONE','True','False','None']);
const namespaces=new Set(['system','device','vision','camera','event']);
const tokenColor:Record<Token['kind'],string>={plain:'#d7dae0',comment:'#6a9955',string:'#ce9178',keyword:'#c586c0',constant:'#4fc1ff',number:'#b5cea8',namespace:'#4ec9b0',operator:'#d4d4d4'};

const tokenize=(line:string):Token[]=>{
 const out:Token[]=[];
 const re=/(#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b|==|!=|>=|<=|>|<|\+|-|\*|\/|%|\(|\)|:|=)/g;
 let last=0;let m:RegExpExecArray|null;
 while((m=re.exec(line))){if(m.index>last)out.push({text:line.slice(last,m.index),kind:'plain'});const t=m[0];let kind:Token['kind']='plain';if(t.startsWith('#'))kind='comment';else if(t.startsWith('"')||t.startsWith("'"))kind='string';else if(/^\d/.test(t))kind='number';else if(keywords.has(t))kind='keyword';else if(constants.has(t))kind='constant';else if(namespaces.has(t))kind='namespace';else if(/^(==|!=|>=|<=|>|<|\+|-|\*|\/|%|=|:|\(|\))$/.test(t))kind='operator';out.push({text:t,kind});last=re.lastIndex;}
 if(last<line.length)out.push({text:line.slice(last),kind:'plain'});return out;
};
const sourceColor=(path:string)=>path.startsWith('device.')?'#fdd663':path.startsWith('vision.roi.')?'#ff8ab4':path.startsWith('vision.')?'#c58af9':path.startsWith('system.')?'#65d1ff':path.startsWith('camera.')?'#81c995':'#9aa0a6';
const endpointIcon=(e:AutomationEndpoint)=>e.kind==='action'?CirclePlay:e.kind==='event'?Sparkles:e.data_type==='object'||e.data_type==='namespace'||e.data_type==='roi'||e.data_type==='logic_service'||e.data_type==='modbus_tcp_device'?Cpu:e.kind==='data'?Database:Code2;

export const AutomationCodeEditor=({value,onChange,endpoints,insertCommand}:Props)=>{
 const textRef=useRef<HTMLTextAreaElement|null>(null);const preRef=useRef<HTMLPreElement|null>(null);const [suggestOpen,setSuggestOpen]=useState(false);const [caret,setCaret]=useState(0);
 const prefix=useMemo(()=>{const left=value.slice(0,caret);return left.match(/[A-Za-z_][A-Za-z0-9_.]*$/)?.[0]??'';},[value,caret]);
 const suggestions=useMemo(()=>{const q=prefix.toLowerCase();return endpoints.filter(e=>!q||e.path.toLowerCase().startsWith(q)).sort((a,b)=>a.path.length-b.path.length).slice(0,40);},[endpoints,prefix]);
 const replacePrefix=(path:string,callable:boolean)=>{const el=textRef.current;if(!el)return;const pos=el.selectionStart;const left=value.slice(0,pos);const m=left.match(/[A-Za-z_][A-Za-z0-9_.]*$/);const start=m?pos-m[0].length:pos;const insert=path+(callable?'()':'');const next=value.slice(0,start)+insert+value.slice(pos);onChange(next);setSuggestOpen(false);requestAnimationFrame(()=>{el.focus();const p=start+insert.length-(callable?1:0);el.setSelectionRange(p,p);setCaret(p);});};
 const syncScroll=()=>{if(preRef.current&&textRef.current){preRef.current.scrollTop=textRef.current.scrollTop;preRef.current.scrollLeft=textRef.current.scrollLeft;}};
 useEffect(()=>{if(insertCommand)replacePrefix(insertCommand.path,insertCommand.callable);},[insertCommand?.id]);
 return <div className="relative h-full overflow-hidden bg-[#111317]">
  <pre ref={preRef} aria-hidden className="pointer-events-none absolute inset-0 m-0 overflow-hidden whitespace-pre-wrap break-words py-3 pl-12 pr-4 font-mono text-[12px] leading-[20px]">{value.split('\n').map((line,i)=><div key={i}>{tokenize(line).map((t,j)=><span key={j} style={{color:tokenColor[t.kind]}}>{t.text}</span>)}{'\n'}</div>)}</pre>
  <textarea ref={textRef} spellCheck={false} value={value} onChange={e=>{onChange(e.target.value);setCaret(e.target.selectionStart);}} onClick={e=>setCaret((e.target as HTMLTextAreaElement).selectionStart)} onKeyUp={e=>setCaret((e.target as HTMLTextAreaElement).selectionStart)} onScroll={syncScroll} onKeyDown={e=>{const el=e.currentTarget;if((e.ctrlKey||e.metaKey)&&e.code==='Space'){e.preventDefault();setCaret(el.selectionStart);setSuggestOpen(true);return;}if(e.key==='.'&&!e.ctrlKey&&!e.metaKey){requestAnimationFrame(()=>{setCaret(el.selectionStart);setSuggestOpen(true);});}if(e.key==='Escape')setSuggestOpen(false);if(e.key==='Tab'){e.preventDefault();const p=el.selectionStart;onChange(value.slice(0,p)+'    '+value.slice(el.selectionEnd));requestAnimationFrame(()=>{el.setSelectionRange(p+4,p+4);setCaret(p+4);});}}} className="absolute inset-0 h-full w-full resize-none overflow-auto bg-transparent py-3 pl-12 pr-4 font-mono text-[12px] leading-[20px] text-transparent caret-[#f8f8f2] outline-none selection:bg-[#264f78]" placeholder="if device.modbus_1.X1 == ON:\n    system.run_inspection()"/>
  <div className="pointer-events-none absolute left-0 top-0 h-full w-10 select-none border-r border-[#2b2f35] bg-[#0e1013] py-3 text-right font-mono text-[11px] leading-[20px] text-[#46505a]">{Array.from({length:Math.max(1,value.split('\n').length)},(_,i)=><div key={i} className="pr-2">{i+1}</div>)}</div>
  {suggestOpen&&suggestions.length?<div className="absolute left-14 top-12 z-30 max-h-[320px] w-[500px] overflow-y-auto rounded-lg border border-[#49515a] bg-[#1d2025] shadow-2xl">{suggestions.map(e=>{const Icon=endpointIcon(e);const c=sourceColor(e.path);return <button key={e.path} className="flex w-full items-start gap-2 border-b border-[#2b2f35] px-3 py-2 text-left hover:bg-[#29313a]" onMouseDown={ev=>{ev.preventDefault();replacePrefix(e.path,e.callable);}}><span className="mt-0.5 rounded p-1" style={{background:`${c}1a`,color:c}}><Icon size={11}/></span><span className="min-w-0 flex-1"><div className="truncate font-mono text-[9px]" style={{color:c}}>{e.path}{e.callable?'()':''}</div><div className="mt-0.5 text-[7px] text-[#89939e]">{e.data_type} · {e.kind}{e.writable?' · writable':''}</div><div className="mt-0.5 truncate text-[7px] text-[#6f7882]">{e.description}</div></span></button>})}</div>:null}
  <div className="pointer-events-none absolute bottom-2 right-3 rounded bg-[#111317cc] px-2 py-1 text-[7px] text-[#59636e]">Ctrl+Space · type <span className="text-[#65d1ff]">device.</span> / <span className="text-[#ff8ab4]">vision.roi.</span></div>
 </div>;
};
