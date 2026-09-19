#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys

VERSION = "v0.15.0"
TITLE = "COMPUTER VISION V0.15.0 — UTILITIES / DATA GATHERING"

MODELS_BLOCK = 'class UtilityGatherRoi(BaseModel):\n    roi_id: str\n    name: str = ""\n    rect: NormalizedRect\n\n\nclass UtilityGatherRoute(BaseModel):\n    output_id: str\n    destination: str\n    enabled: bool = True\n\n\nclass UtilityGatherPlan(BaseModel):\n    base_dir: str = ""\n    routes: list[UtilityGatherRoute] = Field(default_factory=list)\n    rois: list[UtilityGatherRoi] = Field(default_factory=list)\n    image_format: Literal["jpg", "png"] = "jpg"\n    jpeg_quality: int = Field(default=94, ge=50, le=100)\n\n\nclass UtilityBatchRequest(UtilityGatherPlan):\n    source_dir: str = ""\n\n\n'
API_BLOCK = '@router.get("/programs/{program_id}/workspaces/{workspace_alias}/utilities/gather/folder-info", summary="Inspect an offline Utilities image folder")\ndef utility_gather_folder_info(program_id: str, workspace_alias: str, source_dir: str):\n    try:\n        repository.get(program_id)\n        return {"success": True, **utilities_runtime.folder_info(source_dir)}\n    except Exception as exc:\n        raise _error(exc)\n\n\n@router.get("/programs/{program_id}/workspaces/{workspace_alias}/utilities/gather/folder-preview", summary="Preview one offline Utilities source image")\ndef utility_gather_folder_preview(program_id: str, workspace_alias: str, source_dir: str, index: int = 0, quality: int = 90):\n    try:\n        repository.get(program_id)\n        image, path, resolved, count = utilities_runtime.folder_image(source_dir, index)\n        from urllib.parse import quote\n        return Response(\n            content=_encode_jpeg(image, quality),\n            media_type="image/jpeg",\n            headers={\n                "X-Image-Index": str(resolved),\n                "X-Image-Count": str(count),\n                "X-Image-Name": quote(path.name, safe=""),\n            },\n        )\n    except Exception as exc:\n        raise _error(exc)\n\n\n@router.post("/programs/{program_id}/workspaces/{workspace_alias}/utilities/gather/capture", summary="Capture active Workspace camera and persist routed full-frame/ROI samples")\ndef utility_gather_capture(program_id: str, workspace_alias: str, plan: UtilityGatherPlan):\n    try:\n        program = repository.get(program_id)\n        workspace = workspace_by_alias(program, workspace_alias)\n        if not workspace.camera_id:\n            raise RuntimeError("Workspace has no assigned camera")\n        camera = next((item for item in workspace.cameras.devices if item.declaration_id == workspace.camera_id), None)\n        if camera is None:\n            raise RuntimeError(f"Workspace camera declaration not found: {workspace.camera_id}")\n        image = automation_manager.camera_resources.capture(program_id, camera)\n        alias = safe_alias(workspace.alias, workspace.workspace_id)\n        automation_manager.set_latest_frame(program_id, image, workspace_alias=alias, announce=False)\n        result = utilities_runtime.save_frame(image, plan)\n        return {"success": True, "workspace": alias, "camera": safe_alias(camera.alias, camera.declaration_id), **result}\n    except Exception as exc:\n        raise _error(exc)\n\n\n@router.post("/programs/{program_id}/workspaces/{workspace_alias}/utilities/gather/batch", summary="Batch-extract full-frame/ROI samples from an offline image folder")\ndef utility_gather_batch(program_id: str, workspace_alias: str, request: UtilityBatchRequest):\n    try:\n        repository.get(program_id)\n        return {"success": True, **utilities_runtime.process_folder(request)}\n    except Exception as exc:\n        raise _error(exc)\n\n\n'
FE_TYPES = "export interface UtilityGatherRoi { roi_id:string; name:string; rect:NormalizedRect; }\nexport interface UtilityGatherRoute { output_id:string; destination:string; enabled:boolean; }\nexport interface UtilityGatherPlan { base_dir:string; routes:UtilityGatherRoute[]; rois:UtilityGatherRoi[]; image_format:'jpg'|'png'; jpeg_quality:number; }\nexport interface UtilityBatchRequest extends UtilityGatherPlan { source_dir:string; }\nexport interface UtilityGatherResult { success:boolean; workspace:string; camera:string; stem:string; saved_count:number; failed_count:number; saved:{output_id:string;path:string;width:number;height:number}[]; failed:{output_id:string;error:string}[]; }\nexport interface UtilityBatchResult { success:boolean; source_dir:string; source_count:number; processed_count:number; saved_count:number; failed_count:number; errors:{source?:string;output_id?:string;error:string}[]; }\nexport interface UtilityFolderInfo { success:boolean; source_dir:string; count:number; first_name:string; last_name:string; }\n"
FE_METHODS = "  utilityFolderInfo: async (id:string,workspaceAlias:string,sourceDir:string):Promise<UtilityFolderInfo> => (await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/workspaces/${encodeURIComponent(workspaceAlias)}/utilities/gather/folder-info`,{params:{source_dir:sourceDir}})).data,\n  utilityFolderPreview: async (id:string,workspaceAlias:string,sourceDir:string,index:number):Promise<{blob:Blob;index:number;count:number;name:string}> => {\n    const r=await axiosClient.get(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/workspaces/${encodeURIComponent(workspaceAlias)}/utilities/gather/folder-preview`,{params:{source_dir:sourceDir,index},responseType:'blob'});\n    return {blob:r.data,index:Number(r.headers?.['x-image-index']??index),count:Number(r.headers?.['x-image-count']??0),name:decodeURIComponent(String(r.headers?.['x-image-name']??''))};\n  },\n  utilityGatherCapture: async (id:string,workspaceAlias:string,plan:UtilityGatherPlan):Promise<UtilityGatherResult> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/workspaces/${encodeURIComponent(workspaceAlias)}/utilities/gather/capture`,plan,{timeout:120000})).data,\n  utilityGatherBatch: async (id:string,workspaceAlias:string,request:UtilityBatchRequest):Promise<UtilityBatchResult> => (await axiosClient.post(`${api_version}/computer-vision/programs/${encodeURIComponent(id)}/workspaces/${encodeURIComponent(workspaceAlias)}/utilities/gather/batch`,request,{timeout:0})).data,\n"
UTILITIES_RUNTIME = 'from __future__ import annotations\n\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom threading import Lock\nfrom typing import Iterable\nimport re\n\nimport cv2\nimport numpy as np\n\nfrom app.services.vision_app.models import UtilityBatchRequest, UtilityGatherPlan, UtilityGatherRoi\n\n\n_IMAGE_SUFFIXES = {\'.jpg\', \'.jpeg\', \'.png\', \'.bmp\', \'.tif\', \'.tiff\', \'.webp\'}\n_SAFE_STEM = re.compile(r\'[^A-Za-z0-9_.-]+\')\n\n\nclass UtilityGatherRuntime:\n    """Filesystem-oriented image/ROI harvesting for Vision App Utilities.\n\n    This runtime deliberately does not know AI classes, datasets, training, Working\n    Logic, or inspection decisions.  It receives one image plus an explicit\n    extraction/routing plan and persists the requested visual samples.\n    """\n\n    FULL_OUTPUT_ID = \'__full__\'\n\n    def __init__(self) -> None:\n        self._counter = 0\n        self._lock = Lock()\n\n    @staticmethod\n    def _folder(path: str) -> Path:\n        value = str(path or \'\').strip()\n        if not value:\n            raise ValueError(\'Folder path is empty\')\n        return Path(value).expanduser()\n\n    @classmethod\n    def _images(cls, source_dir: str) -> list[Path]:\n        root = cls._folder(source_dir)\n        if not root.exists():\n            raise FileNotFoundError(f\'Image source folder not found: {root}\')\n        if not root.is_dir():\n            raise NotADirectoryError(f\'Image source is not a folder: {root}\')\n        return sorted(\n            (item for item in root.iterdir() if item.is_file() and item.suffix.lower() in _IMAGE_SUFFIXES),\n            key=lambda item: item.name.lower(),\n        )\n\n    def folder_info(self, source_dir: str) -> dict:\n        images = self._images(source_dir)\n        return {\n            \'source_dir\': str(self._folder(source_dir)),\n            \'count\': len(images),\n            \'first_name\': images[0].name if images else \'\',\n            \'last_name\': images[-1].name if images else \'\',\n        }\n\n    def folder_image(self, source_dir: str, index: int) -> tuple[np.ndarray, Path, int, int]:\n        images = self._images(source_dir)\n        if not images:\n            raise FileNotFoundError(f\'No supported images in source folder: {source_dir}\')\n        resolved = max(0, min(int(index), len(images) - 1))\n        path = images[resolved]\n        image = cv2.imread(str(path), cv2.IMREAD_COLOR)\n        if image is None:\n            raise ValueError(f\'Could not decode image: {path}\')\n        return image, path, resolved, len(images)\n\n    @staticmethod\n    def _crop(image: np.ndarray, roi: UtilityGatherRoi) -> np.ndarray:\n        height, width = image.shape[:2]\n        rect = roi.rect\n        x0 = max(0, min(width - 1, int(round(rect.x * width))))\n        y0 = max(0, min(height - 1, int(round(rect.y * height))))\n        x1 = max(x0 + 1, min(width, int(round((rect.x + rect.w) * width))))\n        y1 = max(y0 + 1, min(height, int(round((rect.y + rect.h) * height))))\n        crop = image[y0:y1, x0:x1]\n        if crop.size == 0:\n            raise ValueError(f\'ROI produced an empty crop: {roi.roi_id}\')\n        return np.ascontiguousarray(crop)\n\n    @staticmethod\n    def _safe_stem(value: str) -> str:\n        stem = _SAFE_STEM.sub(\'_\', value.strip()).strip(\'._-\')\n        return (stem or \'sample\')[:120]\n\n    def _capture_stem(self) -> str:\n        with self._lock:\n            self._counter += 1\n            counter = self._counter\n        now = datetime.now(timezone.utc).astimezone()\n        return f"capture_{now.strftime(\'%Y%m%d_%H%M%S_%f\')}_{counter:06d}"\n\n    @staticmethod\n    def _destination(plan: UtilityGatherPlan, destination: str) -> Path:\n        value = str(destination or \'\').strip()\n        if not value:\n            raise ValueError(\'Enabled output has no destination folder\')\n        target = Path(value).expanduser()\n        if target.is_absolute():\n            return target\n        base = str(plan.base_dir or \'\').strip()\n        if not base:\n            raise ValueError(f\'Relative destination requires a base folder: {value}\')\n        return Path(base).expanduser() / target\n\n    @staticmethod\n    def _next_path(folder: Path, stem: str, extension: str) -> Path:\n        candidate = folder / f\'{stem}.{extension}\'\n        if not candidate.exists():\n            return candidate\n        index = 1\n        while True:\n            candidate = folder / f\'{stem}_{index:03d}.{extension}\'\n            if not candidate.exists():\n                return candidate\n            index += 1\n\n    @staticmethod\n    def _encode(image: np.ndarray, plan: UtilityGatherPlan) -> tuple[str, bytes]:\n        extension = \'png\' if plan.image_format == \'png\' else \'jpg\'\n        params: list[int] = []\n        if extension == \'jpg\':\n            params = [int(cv2.IMWRITE_JPEG_QUALITY), int(plan.jpeg_quality)]\n        ok, encoded = cv2.imencode(f\'.{extension}\', image, params)\n        if not ok:\n            raise RuntimeError(f\'Failed to encode gathered image as {extension}\')\n        return extension, encoded.tobytes()\n\n    @staticmethod\n    def _roi_map(rois: Iterable[UtilityGatherRoi]) -> dict[str, UtilityGatherRoi]:\n        result: dict[str, UtilityGatherRoi] = {}\n        for roi in rois:\n            if roi.roi_id in result:\n                raise ValueError(f\'Duplicate gather ROI id: {roi.roi_id}\')\n            result[roi.roi_id] = roi\n        return result\n\n    def save_frame(self, image: np.ndarray, plan: UtilityGatherPlan, *, stem: str | None = None) -> dict:\n        arr = np.asarray(image)\n        if arr.ndim not in {2, 3} or arr.size == 0:\n            raise ValueError(\'Gather source image is empty or invalid\')\n        roi_by_id = self._roi_map(plan.rois)\n        active_routes = [route for route in plan.routes if route.enabled]\n        if not active_routes:\n            raise ValueError(\'At least one gather output must be enabled\')\n\n        seen: set[str] = set()\n        for route in active_routes:\n            if route.output_id in seen:\n                raise ValueError(f\'Duplicate gather route: {route.output_id}\')\n            seen.add(route.output_id)\n            if route.output_id != self.FULL_OUTPUT_ID and route.output_id not in roi_by_id:\n                raise KeyError(f\'Gather route refers to unknown ROI: {route.output_id}\')\n\n        sample_stem = self._safe_stem(stem or self._capture_stem())\n        saved: list[dict] = []\n        failed: list[dict] = []\n        for route in active_routes:\n            try:\n                payload = arr if route.output_id == self.FULL_OUTPUT_ID else self._crop(arr, roi_by_id[route.output_id])\n                folder = self._destination(plan, route.destination)\n                folder.mkdir(parents=True, exist_ok=True)\n                extension, encoded = self._encode(payload, plan)\n                path = self._next_path(folder, sample_stem, extension)\n                temporary = path.with_name(path.name + \'.tmp\')\n                temporary.write_bytes(encoded)\n                temporary.replace(path)\n                saved.append({\n                    \'output_id\': route.output_id,\n                    \'path\': str(path),\n                    \'width\': int(payload.shape[1]),\n                    \'height\': int(payload.shape[0]),\n                })\n            except Exception as exc:\n                failed.append({\'output_id\': route.output_id, \'error\': str(exc)})\n\n        return {\n            \'stem\': sample_stem,\n            \'saved_count\': len(saved),\n            \'failed_count\': len(failed),\n            \'saved\': saved,\n            \'failed\': failed,\n        }\n\n    def process_folder(self, request: UtilityBatchRequest) -> dict:\n        images = self._images(request.source_dir)\n        if not images:\n            raise FileNotFoundError(f\'No supported images in source folder: {request.source_dir}\')\n\n        processed = 0\n        saved_count = 0\n        failed_count = 0\n        errors: list[dict] = []\n        for path in images:\n            image = cv2.imread(str(path), cv2.IMREAD_COLOR)\n            if image is None:\n                failed_count += 1\n                errors.append({\'source\': str(path), \'error\': \'decode failed\'})\n                continue\n            try:\n                result = self.save_frame(image, request, stem=f\'{self._safe_stem(path.stem)}__gathered\')\n                processed += 1\n                saved_count += int(result[\'saved_count\'])\n                failed_count += int(result[\'failed_count\'])\n                for item in result[\'failed\']:\n                    if len(errors) < 50:\n                        errors.append({\'source\': str(path), **item})\n            except Exception as exc:\n                failed_count += 1\n                if len(errors) < 50:\n                    errors.append({\'source\': str(path), \'error\': str(exc)})\n\n        return {\n            \'source_dir\': str(self._folder(request.source_dir)),\n            \'source_count\': len(images),\n            \'processed_count\': processed,\n            \'saved_count\': saved_count,\n            \'failed_count\': failed_count,\n            \'errors\': errors,\n        }\n'
UTILITIES_WORKSPACE = 'import { Camera, ChevronLeft, ChevronRight, FolderOpen, Image as ImageIcon, Loader2, Plus, RefreshCw, Trash2 } from \'lucide-react\';\nimport { useEffect, useMemo, useState } from \'react\';\nimport { VisionAppAPI, type MasterRoi, type NormalizedRect, type UtilityBatchResult, type UtilityGatherPlan, type UtilityGatherResult, type WorkspaceDefinition } from \'../../api/visionAppApi\';\nimport { VisionViewport } from \'./VisionViewport\';\n\ntype Props={\n  programId:string;\n  workspace:WorkspaceDefinition;\n  workspaceAlias:string;\n  onSaveProgram:()=>Promise<void>;\n  onError:(message:string)=>void;\n};\n\ntype SourceMode=\'camera\'|\'folder\';\ntype RouteState={enabled:boolean;destination:string};\nconst FULL=\'__full__\';\nconst safeFolder=(value:string)=>value.trim().replace(/[^A-Za-z0-9_.-]+/g,\'_\').replace(/^[_\\.-]+|[_\\.-]+$/g,\'\')||\'roi\';\nconst absolutePath=(value:string)=>/^(?:[A-Za-z]:[\\\\/]|\\\\\\\\|\\/)/.test(value.trim());\nconst manualRoi=(rect:NormalizedRect,index:number):MasterRoi=>({roi_id:`utility_${Date.now()}_${Math.random().toString(36).slice(2,6)}`,name:`Utility ROI ${index+1}`,alias:`UTILITY_${index+1}`,rect,enabled:true});\n\nexport const UtilitiesWorkspace=({programId,workspace,workspaceAlias,onSaveProgram,onError}:Props)=>{\n const [mode,setMode]=useState<SourceMode>(\'camera\');const [baseDir,setBaseDir]=useState(\'\');const [sourceDir,setSourceDir]=useState(\'\');const [folderCount,setFolderCount]=useState(0);const [folderIndex,setFolderIndex]=useState(0);const [folderName,setFolderName]=useState(\'\');const [previewUrl,setPreviewUrl]=useState<string|null>(null);const [busy,setBusy]=useState(false);const [status,setStatus]=useState(\'Ready\');const [lastResult,setLastResult]=useState<UtilityGatherResult|UtilityBatchResult|null>(null);const [useMaster,setUseMaster]=useState(true);const [manual,setManual]=useState<MasterRoi[]>([]);const [drawMode,setDrawMode]=useState(false);const [selectedId,setSelectedId]=useState<string|null>(null);const [routes,setRoutes]=useState<Record<string,RouteState>>({[FULL]:{enabled:true,destination:\'full\'}});\n const allRois=useMemo(()=>[...(useMaster?workspace.master.rois:[]),...manual],[useMaster,workspace.master.rois,manual]);\n const camera=workspace.cameras.devices.find(item=>item.declaration_id===workspace.camera_id)??null;\n const outputRows=useMemo(()=>[{id:FULL,name:\'Full Frame\',kind:\'frame\'},...allRois.map(roi=>({id:roi.roi_id,name:roi.name,kind:roi.roi_id.startsWith(\'utility_\')?\'manual\':\'master\'}))],[allRois]);\n useEffect(()=>{setRoutes(current=>{const next={...current};for(const row of outputRows){if(!next[row.id])next[row.id]={enabled:true,destination:row.id===FULL?\'full\':safeFolder(row.name)};}for(const id of Object.keys(next)){if(!outputRows.some(row=>row.id===id))delete next[id];}return next;});},[outputRows]);\n useEffect(()=>()=>{if(previewUrl)URL.revokeObjectURL(previewUrl);},[previewUrl]);\n const showBlob=(blob:Blob,name:string)=>{setFolderName(name);setPreviewUrl(old=>{if(old)URL.revokeObjectURL(old);return URL.createObjectURL(blob);});};\n const plan=():UtilityGatherPlan=>({base_dir:baseDir,routes:outputRows.map(row=>({output_id:row.id,enabled:routes[row.id]?.enabled??true,destination:routes[row.id]?.destination??\'\'})),rois:allRois.map(roi=>({roi_id:roi.roi_id,name:roi.name,rect:roi.rect})),image_format:\'jpg\',jpeg_quality:94});\n const validate=()=>{const active=outputRows.filter(row=>routes[row.id]?.enabled!==false);if(!active.length)throw new Error(\'Enable at least one output.\');for(const row of active){if(!(routes[row.id]?.destination??\'\').trim())throw new Error(`${row.name} has no destination folder.`);}if(active.some(row=>!absolutePath(routes[row.id]?.destination??\'\'))&&!baseDir.trim())throw new Error(\'Set a base output folder when using relative destinations.\');};\n const loadFolder=async(index=0)=>{if(!sourceDir.trim())return;try{setBusy(true);const info=await VisionAppAPI.utilityFolderInfo(programId,workspaceAlias,sourceDir.trim());setFolderCount(info.count);if(!info.count){setPreviewUrl(old=>{if(old)URL.revokeObjectURL(old);return null;});setFolderName(\'\');setStatus(\'No supported images in folder\');return;}const target=Math.max(0,Math.min(index,info.count-1));const preview=await VisionAppAPI.utilityFolderPreview(programId,workspaceAlias,sourceDir.trim(),target);setFolderIndex(preview.index);showBlob(preview.blob,preview.name);setStatus(`${preview.index+1} / ${preview.count}`);}catch(e:any){onError(e?.response?.data?.detail||e?.message||\'Folder preview failed\');}finally{setBusy(false);}};\n const capture=async()=>{try{validate();if(!camera)throw new Error(\'Assign an enabled camera to this Workspace first.\');setBusy(true);setStatus(\'Capturing and saving...\');await onSaveProgram();const result=await VisionAppAPI.utilityGatherCapture(programId,workspaceAlias,plan());setLastResult(result);const blob=await VisionAppAPI.automationLatestFrame(programId,workspaceAlias);showBlob(blob,result.stem+\'.jpg\');setStatus(`Saved ${result.saved_count} output(s)${result.failed_count?` · ${result.failed_count} failed`:\'\'}`);}catch(e:any){onError(e?.response?.data?.detail||e?.message||\'Utility capture failed\');setStatus(\'Capture failed\');}finally{setBusy(false);}};\n const runBatch=async()=>{try{validate();if(!sourceDir.trim())throw new Error(\'Set an image source folder.\');setBusy(true);setStatus(\'Running folder batch...\');const result=await VisionAppAPI.utilityGatherBatch(programId,workspaceAlias,{...plan(),source_dir:sourceDir.trim()});setLastResult(result);setStatus(`Processed ${result.processed_count}/${result.source_count} image(s) · saved ${result.saved_count}`);}catch(e:any){onError(e?.response?.data?.detail||e?.message||\'Utility folder batch failed\');setStatus(\'Batch failed\');}finally{setBusy(false);}};\n const addManual=(rect:NormalizedRect)=>{const roi=manualRoi(rect,manual.length);setManual(items=>[...items,roi]);setSelectedId(roi.roi_id);setDrawMode(false);};\n const removeManual=(id:string)=>{setManual(items=>items.filter(item=>item.roi_id!==id));if(selectedId===id)setSelectedId(null);};\n const updateManualName=(id:string,name:string)=>setManual(items=>items.map(item=>item.roi_id===id?{...item,name,alias:safeFolder(name).toUpperCase()}:item));\n return <div className="flex h-full min-h-0 bg-[#202124]">\n  <section className="relative min-w-0 flex-1"><VisionViewport imageUrl={previewUrl} rois={allRois} selectedId={selectedId} drawMode={drawMode} onSelect={setSelectedId} onDraw={addManual}/><div className="absolute left-3 top-3 z-20 rounded border border-[#3c4043] bg-[#202124]/95 px-2 py-1 text-[8px] text-[#9aa0a6]">{mode===\'camera\'?(camera?`Camera: ${camera.alias}`:\'No camera assigned\'):(folderName||\'Folder source\')}</div></section>\n  <aside className="w-[500px] shrink-0 overflow-y-auto border-l border-[#3c4043] bg-[#292a2d] p-3 text-[8px]">\n   <div className="mb-3"><div className="text-[10px] font-black text-[#c58af9]">UTILITIES · DATA GATHERING</div><div className="mt-1 leading-4 text-[#9aa0a6]">Harvest full frames and ROI crops. Routing is filesystem-only; no AI/dataset semantics are imposed here.</div></div>\n   <div className="mb-3 grid grid-cols-2 gap-2"><button onClick={()=>setMode(\'camera\')} className={`cv-btn justify-center ${mode===\'camera\'?\'border-[#8ab4f8] bg-[#174ea6]\':\'\'}`}><Camera size={11}/>Camera Collection</button><button onClick={()=>setMode(\'folder\')} className={`cv-btn justify-center ${mode===\'folder\'?\'border-[#8ab4f8] bg-[#174ea6]\':\'\'}`}><FolderOpen size={11}/>Offline Folder</button></div>\n   {mode===\'folder\'?<div className="mb-3 rounded-lg border border-[#3c4043] bg-[#242528] p-2"><div className="mb-1 font-black">SOURCE FOLDER</div><div className="flex gap-1"><input value={sourceDir} onChange={e=>setSourceDir(e.target.value)} placeholder="/path/to/raw_images" className="cv-field !mt-0 flex-1 font-mono"/><button disabled={busy||!sourceDir.trim()} onClick={()=>void loadFolder(0)} className="cv-icon"><RefreshCw size={11}/></button></div><div className="mt-2 flex items-center gap-1"><button disabled={busy||folderIndex<=0} onClick={()=>void loadFolder(folderIndex-1)} className="cv-icon"><ChevronLeft size={11}/></button><button disabled={busy||!folderCount||folderIndex>=folderCount-1} onClick={()=>void loadFolder(folderIndex+1)} className="cv-icon"><ChevronRight size={11}/></button><span className="font-mono text-[#9aa0a6]">{folderCount?`${folderIndex+1}/${folderCount}`:\'0 images\'}</span><span className="ml-auto truncate font-mono text-[#65d1ff]">{folderName}</span></div></div>:<div className="mb-3 rounded-lg border border-[#3c4043] bg-[#242528] p-2"><div className="font-black">WORKSPACE CAMERA</div><div className="mt-1 font-mono text-[#65d1ff]">{camera?`${camera.alias} · ${camera.driver}`:\'No camera assigned\'}</div><div className="mt-1 text-[#80868b]">Capture saves the full frame and every enabled output route in one transaction.</div></div>}\n   <div className="mb-3 rounded-lg border border-[#3c4043] bg-[#242528] p-2"><div className="flex items-center gap-2"><b className="flex-1">EXTRACTION ROI</b><label className="flex items-center gap-1"><input type="checkbox" checked={useMaster} onChange={e=>setUseMaster(e.target.checked)}/>Master ROIs ({workspace.master.rois.length})</label><button disabled={!previewUrl} onClick={()=>setDrawMode(v=>!v)} className={`cv-btn ${drawMode?\'border-[#81c995] text-[#81c995]\':\'\'}`}><Plus size={10}/>Draw ROI</button></div>{manual.length?<div className="mt-2 space-y-1">{manual.map(roi=><div key={roi.roi_id} className="flex items-center gap-1"><input className="cv-field !mt-0 flex-1" value={roi.name} onChange={e=>updateManualName(roi.roi_id,e.target.value)} onFocus={()=>setSelectedId(roi.roi_id)}/><button onClick={()=>removeManual(roi.roi_id)} className="cv-icon text-[#f28b82]"><Trash2 size={10}/></button></div>)}</div>:null}</div>\n   <div className="mb-2 rounded-lg border border-[#3c4043] bg-[#242528] p-2"><div className="mb-1 flex items-center gap-2"><b className="flex-1">OUTPUT ROUTING</b><span className="text-[#80868b]">relative paths use Base folder</span></div><input value={baseDir} onChange={e=>setBaseDir(e.target.value)} placeholder="Base output folder, e.g. /data/vision_collection" className="cv-field !mt-0 w-full font-mono"/></div>\n   <div className="space-y-1">{outputRows.map(row=>{const route=routes[row.id]??{enabled:true,destination:\'\'};return <div key={row.id} className={`rounded border p-2 ${selectedId===row.id?\'border-[#fdd663] bg-[#3a3524]\':\'border-[#3c4043] bg-[#242528]\'}`} onClick={()=>row.id!==FULL&&setSelectedId(row.id)}><div className="flex items-center gap-2"><input type="checkbox" checked={route.enabled} onChange={e=>setRoutes(s=>({...s,[row.id]:{...route,enabled:e.target.checked}}))}/><ImageIcon size={10} className={row.kind===\'frame\'?\'text-[#8ab4f8]\':row.kind===\'master\'?\'text-[#81c995]\':\'text-[#fdd663]\'}/><b className="w-[120px] truncate">{row.name}</b><input value={route.destination} onChange={e=>setRoutes(s=>({...s,[row.id]:{...route,destination:e.target.value}}))} onClick={e=>e.stopPropagation()} className="cv-field !mt-0 flex-1 font-mono" placeholder="destination folder"/></div></div>;})}</div>\n   <div className="mt-3 flex items-center gap-2 border-t border-[#3c4043] pt-3">{mode===\'camera\'?<button disabled={busy||!camera} onClick={()=>void capture()} className="cv-btn border-[#81c995] bg-[#1f6b38] text-white"><Camera size={11}/>{busy?<Loader2 size={11} className="animate-spin"/>:\'Capture + Save\'}</button>:<button disabled={busy||!sourceDir.trim()} onClick={()=>void runBatch()} className="cv-btn border-[#81c995] bg-[#1f6b38] text-white"><FolderOpen size={11}/>{busy?<Loader2 size={11} className="animate-spin"/>:\'Run Folder Batch\'}</button>}<span className="flex-1 truncate text-[#9aa0a6]">{status}</span></div>\n   {lastResult?<div className="mt-2 rounded border border-[#3c4043] bg-[#202124] p-2 font-mono text-[7px] text-[#9aa0a6]">{\'processed_count\' in lastResult?<>source={lastResult.source_count} processed={lastResult.processed_count} saved={lastResult.saved_count} failed={lastResult.failed_count}</>:<>stem={lastResult.stem} saved={lastResult.saved_count} failed={lastResult.failed_count}</>}</div>:null}\n  </aside>\n </div>;\n};\n'
REGRESSION_TEST = "from pathlib import Path\n\nimport cv2\nimport numpy as np\n\nfrom app.services.vision_app.models import NormalizedRect, UtilityBatchRequest, UtilityGatherPlan, UtilityGatherRoi, UtilityGatherRoute\nfrom app.services.vision_app.utilities_runtime import UtilityGatherRuntime\n\n\ndef _image() -> np.ndarray:\n    image = np.zeros((100, 200, 3), dtype=np.uint8)\n    image[20:60, 50:110] = (10, 120, 240)\n    return image\n\n\ndef _plan(root: Path) -> UtilityGatherPlan:\n    return UtilityGatherPlan(\n        base_dir=str(root),\n        routes=[\n            UtilityGatherRoute(output_id='__full__', destination='full'),\n            UtilityGatherRoute(output_id='pem', destination='pem_ok'),\n        ],\n        rois=[UtilityGatherRoi(roi_id='pem', name='PEM', rect=NormalizedRect(x=.25, y=.2, w=.3, h=.4))],\n    )\n\n\ndef test_utilities_gather_saves_full_frame_and_roi(tmp_path: Path):\n    runtime = UtilityGatherRuntime()\n    result = runtime.save_frame(_image(), _plan(tmp_path), stem='sample')\n    assert result['saved_count'] == 2\n    full = cv2.imread(str(tmp_path / 'full' / 'sample.jpg'))\n    roi = cv2.imread(str(tmp_path / 'pem_ok' / 'sample.jpg'))\n    assert full.shape[:2] == (100, 200)\n    assert roi.shape[:2] == (40, 60)\n\n\ndef test_utilities_offline_batch_reuses_one_extraction_plan(tmp_path: Path):\n    source = tmp_path / 'raw'\n    source.mkdir()\n    cv2.imwrite(str(source / 'a.jpg'), _image())\n    cv2.imwrite(str(source / 'b.png'), _image())\n    plan = _plan(tmp_path / 'out')\n    payload = plan.model_dump() if hasattr(plan, 'model_dump') else plan.dict()\n    request = UtilityBatchRequest(source_dir=str(source), **payload)\n    result = UtilityGatherRuntime().process_folder(request)\n    assert result['source_count'] == 2\n    assert result['processed_count'] == 2\n    assert result['saved_count'] == 4\n    assert len(list((tmp_path / 'out' / 'pem_ok').glob('*.jpg'))) == 2\n"
CONTEXT_NOTE = "# Computer Vision v0.15.0 — Utilities / Data Gathering\n\n## Purpose\n\nAdd the first **Utilities** tool to the Computer Vision application: a manual, controllable image-harvesting workspace for collecting full camera frames and ROI crops without running inspection or introducing Dataset/Training/AI infrastructure.\n\n## Architectural boundary\n\nUtilities is a **tooling plane** owned by the current Vision Workspace context, but it is not part of the production `Working` inspection pipeline.\n\n```text\nVision Workspace\n├─ Camera declarations / assigned camera\n├─ Master Sample / ROIs\n├─ Working                  # production inspection\n└─ Utilities\n   └─ Data Gathering        # image/ROI harvesting only\n```\n\nUtilities must not infer OK/NG semantics, model classes, training splits, augmentation, model registry, or deployment behavior. Users route each visual output to filesystem folders of their choice.\n\n## v0.15.0 workflow\n\n### Camera Collection\n\n1. Use the camera assigned to the active Workspace.\n2. Configure a base output folder and one destination for each output.\n3. Outputs are:\n   - full captured frame;\n   - every Master ROI currently selected for extraction;\n   - optional manual utility ROIs drawn in the Utilities viewport.\n4. `Capture + Save` captures once and writes every enabled route from that same frozen frame.\n5. Repeat capture without reconfiguring routes.\n\nThis supports operator flows such as configuring an `ALL_OK` directory layout, capturing tens of products, changing routes for an NG condition, then continuing collection.\n\n### Offline Folder\n\n1. Point Utilities at an existing server/local image folder.\n2. Preview images by index.\n3. Reuse Workspace Master ROIs and/or draw temporary utility ROIs on the preview.\n4. Configure output routing once.\n5. Run the whole folder through the same extraction engine.\n\nThis allows raw full-frame images collected at the factory to be taken elsewhere and converted into ROI samples later without requiring camera access.\n\n## Extraction semantics\n\n- v0.15.0 uses **fixed normalized rectangles** from the current Master ROI definitions plus optional manual utility ROIs.\n- Full-frame and ROI outputs from one source image share the same source stem/token so they can be correlated by filename.\n- Relative destination paths resolve under the configured base folder; absolute destination folders are also allowed.\n- Existing files are never overwritten. A numeric suffix is added on collision.\n- Image writing is filesystem-only and does not mutate Vision Program inspection state.\n- Camera capture reuses the Workspace-owned camera declaration and writes the frame into that Workspace's latest-frame context for preview.\n- Offline folder enumeration is non-recursive in v0.15.0.\n\nLocator-aware extraction can be added later, but must reuse the existing Workspace locator contract rather than creating a second ROI-location algorithm inside Utilities.\n\n## Backend files\n\n- `app/services/vision_app/models.py`\n  - Adds non-persistent Utilities request contracts: `UtilityGatherRoi`, `UtilityGatherRoute`, `UtilityGatherPlan`, `UtilityBatchRequest`.\n- `app/services/vision_app/utilities_runtime.py`\n  - New filesystem-oriented extraction engine.\n  - Folder discovery/preview.\n  - Normalized ROI cropping.\n  - Collision-safe JPEG/PNG writes.\n  - Full-folder batch extraction.\n- `app/api/v1/endpoints/vision_app_api.py`\n  - Adds Workspace-scoped Utilities routes for folder info/preview, camera capture+save, and offline batch extraction.\n- `tests/vision_app/test_vision_app_v1500.py`\n  - Regression coverage for full-frame + ROI extraction and offline batch reuse of one extraction plan.\n\n## Frontend files\n\n- `src/components/ComputerVision/UtilitiesWorkspace.tsx`\n  - New Utilities/Data Gathering UI.\n  - Camera Collection and Offline Folder modes.\n  - Base-folder + per-output routing.\n  - Master ROI reuse and temporary manual ROI drawing.\n- `src/api/visionAppApi.ts`\n  - Utilities contracts and API helpers.\n- `src/Pages/ComputerVisionPage.tsx`\n  - Adds the Utilities top-level module for the active Workspace.\n  - Version footer becomes v0.15.0.\n\n## API routes\n\n```text\nGET  /programs/<id>/workspaces/<workspace>/utilities/gather/folder-info\nGET  /programs/<id>/workspaces/<workspace>/utilities/gather/folder-preview\nPOST /programs/<id>/workspaces/<workspace>/utilities/gather/capture\nPOST /programs/<id>/workspaces/<workspace>/utilities/gather/batch\n```\n\n## Invariants\n\n1. Utilities never falls back to another Workspace's camera or ROI state.\n2. Camera acquisition uses the camera assigned to the route Workspace.\n3. Utilities does not execute Working Filter/Logic/Decision in v0.15.0.\n4. Utilities does not create AI/Dataset/Training abstractions.\n5. Master ROI definitions remain owned by Master; temporary utility ROIs are session-local frontend state.\n6. Offline and camera modes share the same extraction/routing contract.\n7. No output file is overwritten by a gathering operation.\n\n## Recommended minimal context for future Utilities work\n\n- `FE:src/Pages/ComputerVisionPage.tsx`\n- `FE:src/components/ComputerVision/UtilitiesWorkspace.tsx`\n- `FE:src/components/ComputerVision/VisionViewport.tsx`\n- `FE:src/api/visionAppApi.ts`\n- `BE:app/services/vision_app/models.py`\n- `BE:app/services/vision_app/utilities_runtime.py`\n- `BE:app/services/vision_app/camera_resource_runtime.py`\n- `BE:app/services/vision_app/workspace_runtime.py`\n- `BE:app/api/v1/endpoints/vision_app_api.py`\n- `BE:tests/vision_app/test_vision_app_v1500.py`\n"

CONTEXT_DOCS = [
    "docs/llm_context/SYSTEM_CONTEXT_INDEX.md",
    "docs/llm_context/SYSTEM_ARCHITECTURE.md",
    "docs/llm_context/SYSTEM_CONTEXT_BUNDLES.md",
    "docs/llm_context/SYSTEM_FILE_MAP.md",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _candidate_roots() -> list[Path]:
    starts = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    seen: set[Path] = set()
    result: list[Path] = []
    for start in starts:
        for parent in [start, *start.parents]:
            for candidate in (parent, parent / "LambdaVisionSuper", parent / "LambdaVisionSuperBackEnd"):
                try:
                    resolved = candidate.resolve()
                except Exception:
                    continue
                if resolved not in seen:
                    seen.add(resolved); result.append(resolved)
    return result


def find_roots() -> tuple[Path, Path]:
    fe = None; be = None
    env_fe = os.environ.get("LAMBDA_VISION_FRONTEND")
    env_be = os.environ.get("LAMBDA_VISION_BACKEND")
    if env_fe:
        p = Path(env_fe).expanduser().resolve()
        if (p / "src/Pages/ComputerVisionPage.tsx").exists(): fe = p
    if env_be:
        p = Path(env_be).expanduser().resolve()
        if (p / "app/services/vision_app/models.py").exists(): be = p
    for candidate in _candidate_roots():
        if fe is None and (candidate / "src/Pages/ComputerVisionPage.tsx").exists(): fe = candidate
        if be is None and (candidate / "app/services/vision_app/models.py").exists(): be = candidate
    if fe is None or be is None:
        raise RuntimeError("Could not locate LambdaVisionSuper frontend/backend roots. Set LAMBDA_VISION_FRONTEND and LAMBDA_VISION_BACKEND if needed.")
    return fe, be


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _partial(text: str, markers: list[str]) -> bool:
    hits = sum(1 for marker in markers if marker in text)
    return 0 < hits < len(markers)


def patch_models(text: str) -> str:
    markers = ["class UtilityGatherRoi(BaseModel):", "class UtilityBatchRequest(UtilityGatherPlan):"]
    if all(marker in text for marker in markers): return text
    if _partial(text, markers): raise RuntimeError("models.py contains a partial Utilities v0.15.0 patch")
    anchor = "class WorkspaceDefinition(BaseModel):\n"
    if anchor not in text or "class SoftTriggerConfig(BaseModel):" not in text:
        raise RuntimeError("models.py baseline anchor not found")
    return text.replace(anchor, MODELS_BLOCK + anchor, 1)


def patch_api(text: str) -> str:
    markers = ["utilities_runtime = UtilityGatherRuntime()", "/utilities/gather/capture", "/utilities/gather/batch"]
    if all(marker in text for marker in markers): return text
    if _partial(text, markers): raise RuntimeError("vision_app_api.py contains a partial Utilities v0.15.0 patch")
    old = "from app.services.vision_app.models import SoftTriggerConfig, VisionProgramDefinition, model_to_dict"
    new = "from app.services.vision_app.models import SoftTriggerConfig, UtilityBatchRequest, UtilityGatherPlan, VisionProgramDefinition, model_to_dict"
    if old not in text: raise RuntimeError("vision_app_api.py model import anchor not found")
    text = text.replace(old, new, 1)
    anchor = "from app.services.vision_app.runtime import VisionProgramRuntime\n"
    if anchor not in text: raise RuntimeError("vision_app_api.py runtime import anchor not found")
    text = text.replace(anchor, anchor + "from app.services.vision_app.utilities_runtime import UtilityGatherRuntime\n", 1)
    anchor = "runner_manager = VisionTriggerRunnerManager(repository, runtime, camera_controller, io_controller)\n"
    if anchor not in text: raise RuntimeError("vision_app_api.py manager anchor not found")
    text = text.replace(anchor, anchor + "utilities_runtime = UtilityGatherRuntime()\n", 1)
    anchor = "def _workspace_stream_resource(program, workspace_alias: str):\n"
    if anchor not in text: raise RuntimeError("vision_app_api.py stream-resource anchor not found")
    return text.replace(anchor, API_BLOCK + anchor, 1)


def patch_fe_api(text: str) -> str:
    markers = ["export interface UtilityGatherPlan", "utilityGatherCapture:", "utilityGatherBatch:"]
    if all(marker in text for marker in markers): return text
    if _partial(text, markers): raise RuntimeError("visionAppApi.ts contains a partial Utilities v0.15.0 patch")
    anchor = "export interface SimulatorConfig { enabled:boolean; camera_sequence_mode:'fixed'|'next'|'loop'; stream_fps:number; }\n"
    if anchor not in text: raise RuntimeError("visionAppApi.ts type anchor not found")
    text = text.replace(anchor, FE_TYPES + anchor, 1)
    anchor = "  uploadSimCameraFrame: async (id:string,cameraAlias:string,file:Blob) =>"
    if anchor not in text: raise RuntimeError("visionAppApi.ts method anchor not found")
    return text.replace(anchor, FE_METHODS + anchor, 1)


def patch_page(text: str) -> str:
    markers = ["UtilitiesWorkspace", "'utilities'|'ide'", "label:'Utilities'", "Vision App v0.15.0"]
    if all(marker in text for marker in markers): return text
    if any(marker in text for marker in ["UtilitiesWorkspace", "label:'Utilities'", "Vision App v0.15.0"]):
        raise RuntimeError("ComputerVisionPage.tsx contains a partial Utilities v0.15.0 patch")
    old = "import { Activity, ArrowLeft, Box, Braces, Camera, ChevronLeft, ChevronRight, Cpu, CirclePlay, CircleStop, Image as ImageIcon, Loader2, Play, Save, Sparkles, Trash2, Upload } from 'lucide-react';"
    new = "import { Activity, ArrowLeft, Box, Braces, Camera, ChevronLeft, ChevronRight, Cpu, CirclePlay, CircleStop, Image as ImageIcon, Loader2, Play, Save, Sparkles, Trash2, Upload, Wrench } from 'lucide-react';"
    if old not in text: raise RuntimeError("ComputerVisionPage.tsx Lucide import anchor not found")
    text = text.replace(old, new, 1)
    anchor = "import { StreamingWorkspace } from '../components/ComputerVision/StreamingWorkspace';\n"
    if anchor not in text: raise RuntimeError("ComputerVisionPage.tsx Streaming import anchor not found")
    text = text.replace(anchor, anchor + "import { UtilitiesWorkspace } from '../components/ComputerVision/UtilitiesWorkspace';\n", 1)
    old = "type ModuleKey='iot'|'camera'|'streaming'|'master'|'working'|'ide';"
    new = "type ModuleKey='iot'|'camera'|'streaming'|'master'|'working'|'utilities'|'ide';"
    if old not in text: raise RuntimeError("ComputerVisionPage.tsx ModuleKey anchor not found")
    text = text.replace(old, new, 1)
    old = "{key:'working',label:'Working',icon:Box},{key:'ide',label:'Automation IDE',icon:Braces}"
    new = "{key:'working',label:'Working',icon:Box},{key:'utilities',label:'Utilities',icon:Wrench},{key:'ide',label:'Automation IDE',icon:Braces}"
    if old not in text: raise RuntimeError("ComputerVisionPage.tsx module list anchor not found")
    text = text.replace(old, new, 1)
    old = "module==='streaming'?<StreamingWorkspace key={`streaming-${activeWorkspace.workspace_id}`} programId={program.program_id} workspace={activeWorkspace} camera={activeCamera} onWorkspace={next=>patchWorkspace(()=>next)} onError={setError}/>:<VisionViewport"
    new = "module==='streaming'?<StreamingWorkspace key={`streaming-${activeWorkspace.workspace_id}`} programId={program.program_id} workspace={activeWorkspace} camera={activeCamera} onWorkspace={next=>patchWorkspace(()=>next)} onError={setError}/>:module==='utilities'?<UtilitiesWorkspace key={`utilities-${activeWorkspace.workspace_id}`} programId={program.program_id} workspace={activeWorkspace} workspaceAlias={wsAlias} onSaveProgram={save} onError={setError}/>:<VisionViewport"
    if old not in text: raise RuntimeError("ComputerVisionPage.tsx render-chain anchor not found")
    text = text.replace(old, new, 1)
    if "<span>Vision App v0.14.2</span>" not in text: raise RuntimeError("ComputerVisionPage.tsx v0.14.2 footer anchor not found")
    return text.replace("<span>Vision App v0.14.2</span>", "<span>Vision App v0.15.0</span>", 1)


def targets(fe: Path, be: Path) -> list[tuple[str, Path, str, object]]:
    return [
        ("backend/app/services/vision_app/models.py", be / "app/services/vision_app/models.py", "patch", patch_models),
        ("backend/app/api/v1/endpoints/vision_app_api.py", be / "app/api/v1/endpoints/vision_app_api.py", "patch", patch_api),
        ("frontend/src/api/visionAppApi.ts", fe / "src/api/visionAppApi.ts", "patch", patch_fe_api),
        ("frontend/src/Pages/ComputerVisionPage.tsx", fe / "src/Pages/ComputerVisionPage.tsx", "patch", patch_page),
        ("backend/app/services/vision_app/utilities_runtime.py", be / "app/services/vision_app/utilities_runtime.py", "create", UTILITIES_RUNTIME),
        ("frontend/src/components/ComputerVision/UtilitiesWorkspace.tsx", fe / "src/components/ComputerVision/UtilitiesWorkspace.tsx", "create", UTILITIES_WORKSPACE),
        ("backend/tests/vision_app/test_vision_app_v1500.py", be / "tests/vision_app/test_vision_app_v1500.py", "create", REGRESSION_TEST),
        ("frontend/docs/llm_context/updates/v1500_utilities_data_gathering.md", fe / "docs/llm_context/updates/v1500_utilities_data_gathering.md", "create", CONTEXT_NOTE),
    ]


def status_for(label: str, path: Path, kind: str, payload: object) -> tuple[str, str]:
    if kind == "create":
        expected = str(payload)
        if not path.exists(): return "CREATE", ""
        current = _read(path)
        if current == expected: return "OK", ""
        return "CONFLICT", "generated v0.15.0 file already exists with different content"
    if not path.exists(): return "ERROR", "file missing"
    try:
        current = _read(path); updated = payload(current)  # type: ignore[misc]
    except Exception as exc:
        return "CONFLICT", str(exc)
    return ("OK", "") if updated == current else ("PATCH", "")


def print_banner(fe: Path, be: Path, verify: bool = False) -> None:
    print("=" * 116)
    print(("VERIFY " if verify else "") + TITLE)
    print("=" * 116)
    if not verify:
        print(f"Frontend : {fe}")
        print(f"Backend  : {be}")
        print()


def scan(fe: Path, be: Path, *, echo: bool = True) -> bool:
    if echo: print_banner(fe, be)
    blockers = 0
    rows = []
    for label, path, kind, payload in targets(fe, be):
        status, detail = status_for(label, path, kind, payload)
        rows.append((status, label, detail))
        if status in {"CONFLICT", "ERROR"}: blockers += 1
    if echo:
        for status, label, detail in rows:
            print(f"  [{status:<12}] {label}{' — ' + detail if detail else ''}")
        print()
        print("v0.15.0:")
        print("  New Utilities top-level module in the active Workspace")
        print("  Camera Collection: capture once -> full frame + routed ROI crops")
        print("  Offline Folder: preview/draw ROIs -> automatic batch extraction")
        print("  Per-output filesystem routing; no Dataset/Training/AI semantics")
        print("  Master ROIs are reused without mutating Master; manual utility ROIs are session-local")
        print("  Fixed normalized ROI extraction in v0.15.0; locator-aware harvesting remains future work")
        if blockers:
            print(f"[BLOCKED] {blockers} blocking issue(s). Do not apply.")
        else:
            print("[OK] Safe to apply.")
    return blockers == 0


def _backup(fe: Path, be: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = fe / ".lambda_updater_backups" / f"computer_vision_v1500_{stamp}"
    for label, path, _, _ in targets(fe, be):
        if path.exists():
            dest = root / label
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    for rel in CONTEXT_DOCS:
        path = fe / rel
        if path.exists():
            dest = root / "frontend" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    return root


def _regenerate_context(fe: Path, be: Path, *, strict: bool) -> bool:
    generator = fe / "tools/generate_llm_context_map.py"
    if not generator.exists():
        print(f"[WARN] Context generator not found: {generator}")
        return not strict
    print("[INFO] Regenerating LLM context docs...")
    sys.stdout.flush()
    result = subprocess.run([sys.executable, str(generator), "--frontend", str(fe), "--backend", str(be)], cwd=fe)
    if result.returncode != 0:
        print("[ERROR] LLM context regeneration failed")
        return False
    return True


def apply(fe: Path, be: Path) -> int:
    print_banner(fe, be)
    if not scan(fe, be, echo=False):
        scan(fe, be, echo=True)
        return 2
    for label, path, kind, payload in targets(fe, be):
        status, _ = status_for(label, path, kind, payload)
        print(f"  [{status:<12}] {label}")
    print()
    print("v0.15.0:")
    print("  Camera + Offline-folder Data Gathering share one extraction/routing contract")
    print("  Full frame + all configured ROI outputs can be routed independently")
    print("  Utility harvesting is deliberately separate from Working inspection and AI infrastructure")
    print("[OK] Safe to apply.")
    backup = _backup(fe, be)
    for label, path, kind, payload in targets(fe, be):
        if kind == "patch":
            current = _read(path); updated = payload(current)  # type: ignore[misc]
            if updated != current:
                _write(path, updated); print(f"[PATCH ] {label}")
        else:
            expected = str(payload)
            if not path.exists():
                _write(path, expected); print(f"[CREATE] {label}")
    _regenerate_context(fe, be, strict=False)
    print(f"[OK] Backup: {backup}")
    print("Run verify next.")
    return 0


def _check(name: str, condition: bool) -> bool:
    print(f"[{'OK' if condition else 'FAIL'}] {name}")
    return condition


def _run(name: str, command: list[str], cwd: Path) -> bool:
    result = subprocess.run(command, cwd=cwd)
    ok = result.returncode == 0
    print(f"[{'OK' if ok else 'FAIL'}] {name}")
    return ok


def verify(fe: Path, be: Path) -> int:
    print_banner(fe, be, verify=True)
    ok = True
    py_files = [
        be / "app/services/vision_app/models.py",
        be / "app/services/vision_app/utilities_runtime.py",
        be / "app/api/v1/endpoints/vision_app_api.py",
        be / "tests/vision_app/test_vision_app_v1500.py",
    ]
    ok &= _run("Python syntax", [sys.executable, "-m", "py_compile", *map(str, py_files)], be)
    models = _read(be / "app/services/vision_app/models.py")
    api = _read(be / "app/api/v1/endpoints/vision_app_api.py")
    runtime = _read(be / "app/services/vision_app/utilities_runtime.py")
    fe_api = _read(fe / "src/api/visionAppApi.ts")
    page = _read(fe / "src/Pages/ComputerVisionPage.tsx")
    component = _read(fe / "src/components/ComputerVision/UtilitiesWorkspace.tsx")
    ok &= _check("Utilities request contracts", all(x in models for x in ["class UtilityGatherRoi", "class UtilityGatherPlan", "class UtilityBatchRequest"]))
    ok &= _check("Filesystem gather runtime", all(x in runtime for x in ["class UtilityGatherRuntime", "def save_frame", "def process_folder", "FULL_OUTPUT_ID = '__full__'"]))
    ok &= _check("Workspace-scoped Utilities API", all(x in api for x in ["/utilities/gather/folder-info", "/utilities/gather/folder-preview", "/utilities/gather/capture", "/utilities/gather/batch"]))
    ok &= _check("Frontend Utilities API", all(x in fe_api for x in ["UtilityGatherPlan", "utilityGatherCapture", "utilityGatherBatch", "utilityFolderPreview"]))
    ok &= _check("Utilities top-level module", all(x in page for x in ["UtilitiesWorkspace", "label:'Utilities'", "Vision App v0.15.0"]))
    ok &= _check("Camera + Offline Folder UI", all(x in component for x in ["Camera Collection", "Offline Folder", "OUTPUT ROUTING", "Run Folder Batch", "Capture + Save"]))
    ok &= _check("Master + manual ROI extraction UI", all(x in component for x in ["Master ROIs", "Draw ROI", "Utility ROI"]))
    ok &= _run("Utilities regression test", [sys.executable, "-m", "pytest", "-q", "tests/vision_app/test_vision_app_v1500.py"], be)
    ok &= _run("Full Vision App regression suite", [sys.executable, "-m", "pytest", "-q", "tests/vision_app"], be)
    ok &= _run("Frontend npm build", ["npm", "run", "build"], fe)
    context_ok = _regenerate_context(fe, be, strict=True)
    ok &= context_ok
    print(f"[{'OK' if context_ok else 'FAIL'}] LLM context regeneration")
    if ok:
        print("[OK] Computer Vision v0.15.0 Utilities/Data Gathering verified.")
        return 0
    print("[FAIL] Verification failed. Review output above; backup is under frontend/.lambda_updater_backups/.")
    return 1


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"scan", "apply", "verify"}:
        print(f"Usage: {Path(sys.argv[0]).name} [scan|apply|verify]")
        return 2
    try:
        fe, be = find_roots()
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 2
    command = sys.argv[1]
    if command == "scan": return 0 if scan(fe, be) else 2
    if command == "apply": return apply(fe, be)
    return verify(fe, be)


if __name__ == "__main__":
    raise SystemExit(main())
