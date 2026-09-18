from __future__ import annotations

from dataclasses import dataclass
from math import pi
from time import perf_counter
from typing import Any

import cv2
import numpy as np

from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.program import SamplingMethodDefinition, SamplingProgramDefinition
from app.services.vision_labs.sampling_geometry.types import ComposedData, DataBlock, DataBlockSet


CHANNELS = {"gray", "r", "g", "b", "h", "s", "v", "l", "a", "lab_b"}
STAT_NAMES = {"mean", "std", "min", "max", "median"}


def _as_bgr(frame: ImageFrame) -> np.ndarray:
    data = np.asarray(frame.data)
    if data.ndim == 2:
        return cv2.cvtColor(data.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    if frame.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
    if frame.color_space == ColorSpace.HSV:
        return cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
    return data[..., :3].astype(np.uint8)


def channel_array(frame: ImageFrame, channel: str) -> np.ndarray:
    channel = str(channel).lower()
    if channel not in CHANNELS:
        raise ValueError(f"Unsupported sampling channel: {channel}")
    bgr = _as_bgr(frame)
    if channel == "gray":
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    if channel == "b":
        return bgr[..., 0].astype(np.float32)
    if channel == "g":
        return bgr[..., 1].astype(np.float32)
    if channel == "r":
        return bgr[..., 2].astype(np.float32)
    if channel in {"h", "s", "v"}:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        return hsv[..., {"h": 0, "s": 1, "v": 2}[channel]].astype(np.float32)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    return lab[..., {"l": 0, "a": 1, "lab_b": 2}[channel]].astype(np.float32)


def _sample_count(mode: str, requested: int, step: float, length: float) -> int:
    if mode == "full":
        return max(2, min(4096, int(round(length)) + 1))
    if mode == "step":
        return max(2, min(4096, int(np.floor(max(1.0, length) / max(1e-6, step))) + 1))
    return max(2, min(4096, int(requested)))


def _sample_polyline(channel: np.ndarray, points: np.ndarray, count: int) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    if len(pts) < 2:
        x = np.clip(np.rint(pts[:, 0] if len(pts) else [0]), 0, channel.shape[1] - 1).astype(int)
        y = np.clip(np.rint(pts[:, 1] if len(pts) else [0]), 0, channel.shape[0] - 1).astype(int)
        return channel[y, x].astype(np.float32)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cumulative = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(cumulative[-1])
    if total <= 1e-9:
        return np.repeat(channel[int(round(pts[0, 1])), int(round(pts[0, 0]))], count).astype(np.float32)
    targets = np.linspace(0.0, total, count, dtype=np.float32)
    x = np.interp(targets, cumulative, pts[:, 0]).astype(np.float32)
    y = np.interp(targets, cumulative, pts[:, 1]).astype(np.float32)
    return cv2.remap(channel.astype(np.float32), x.reshape(1, -1), y.reshape(1, -1), cv2.INTER_LINEAR).reshape(-1)


def _grid_centers(rows: int, cols: int, width: int, height: int) -> list[tuple[float, float]]:
    xs = np.linspace(0.5 / cols, 1.0 - 0.5 / cols, cols) * max(1, width - 1)
    ys = np.linspace(0.5 / rows, 1.0 - 0.5 / rows, rows) * max(1, height - 1)
    return [(float(x), float(y)) for y in ys for x in xs]


def _placement_centers(method: SamplingMethodDefinition, width: int, height: int) -> list[tuple[float, float]]:
    placement = method.placement
    if placement.mode == "auto_grid":
        return _grid_centers(int(placement.rows), int(placement.cols), width, height)
    return [(float(placement.center_x) * max(1, width - 1), float(placement.center_y) * max(1, height - 1))]


def _stat_values(values: np.ndarray, measures: list[str]) -> tuple[list[str], np.ndarray]:
    values = np.asarray(values, dtype=np.float32).reshape(-1)
    selected = [name for name in measures if name in STAT_NAMES]
    out: list[float] = []
    for name in selected:
        if name == "mean": out.append(float(np.mean(values)))
        elif name == "std": out.append(float(np.std(values)))
        elif name == "min": out.append(float(np.min(values)))
        elif name == "max": out.append(float(np.max(values)))
        elif name == "median": out.append(float(np.median(values)))
    return selected, np.asarray(out, dtype=np.float32)


def _block(block_id: str, label: str, values: np.ndarray, source: str, channel: str, kind: str, description: str, **metadata: Any) -> DataBlock:
    return DataBlock(
        block_id=block_id,
        label=label,
        values=np.asarray(values, dtype=np.float32),
        source_element=source,
        channel=channel,
        kind=kind,
        description=description,
        metadata=metadata,
    )


def _blocks_for_samples(method: SamplingMethodDefinition, method_label: str, channel_name: str, element_id: str, samples: np.ndarray) -> list[DataBlock]:
    blocks: list[DataBlock] = []
    measures = list(method.measures or [])
    prefix = f"{method.id}.{element_id}.{channel_name}"
    if "profile" in measures:
        blocks.append(_block(prefix + ".profile", f"{method_label} · {element_id} · {channel_name.upper()} profile", samples, element_id, channel_name, "profile", "Ordered sampled values along this sampling geometry."))
    stat_names, stat_values = _stat_values(samples, measures)
    if len(stat_values):
        blocks.append(_block(prefix + ".statistics", f"{method_label} · {element_id} · {channel_name.upper()} statistics", stat_values, element_id, channel_name, "statistics", "Summary statistics computed from sampled values.", feature_names=stat_names))
    if "histogram" in measures:
        bins = int(method.histogram_bins)
        hist, edges = np.histogram(samples, bins=bins, range=(float(np.min(samples)), float(np.max(samples)) + 1e-6))
        hist = hist.astype(np.float32)
        if hist.sum() > 0: hist /= hist.sum()
        blocks.append(_block(prefix + ".histogram", f"{method_label} · {element_id} · {channel_name.upper()} histogram", hist, element_id, channel_name, "histogram", f"Normalized histogram with {bins} bins.", bin_edges=edges.astype(float).tolist()))
    return blocks


def _whole_domain_blocks(method: SamplingMethodDefinition, frame: ImageFrame, source_prefix: str) -> list[DataBlock]:
    blocks: list[DataBlock] = []
    label = method.label or method.kind.title()
    for ch in method.channels or ["gray"]:
        values = channel_array(frame, ch).reshape(-1)
        if method.kind == "histogram":
            hist, edges = np.histogram(values, bins=int(method.histogram_bins), range=(float(values.min()), float(values.max()) + 1e-6))
            hist = hist.astype(np.float32)
            if hist.sum() > 0: hist /= hist.sum()
            blocks.append(_block(f"{method.id}.{ch}.histogram", f"{label} · {ch.upper()}", hist, source_prefix, ch, "histogram", f"Whole-domain {ch.upper()} histogram.", bin_edges=edges.astype(float).tolist()))
        elif method.kind == "statistics":
            measures = method.measures or ["mean", "std", "min", "max"]
            names, data = _stat_values(values, measures)
            blocks.append(_block(f"{method.id}.{ch}.statistics", f"{label} · {ch.upper()}", data, source_prefix, ch, "statistics", "Whole-domain channel statistics.", feature_names=names))
    return blocks


def _rays_blocks(method: SamplingMethodDefinition, frame: ImageFrame, source_prefix: str) -> tuple[list[DataBlock], dict[str, Any]]:
    h, w = frame.height, frame.width
    axis = str(method.parameters.get("axis", "x"))
    ray_count = max(1, int(method.parameters.get("ray_count", 5)))
    geometries: list[dict[str, Any]] = []
    paths: list[np.ndarray] = []
    if axis in {"x", "both"}:
        ys = np.linspace(0, h - 1, ray_count + 2)[1:-1] if ray_count > 1 else np.asarray([(h - 1) * 0.5])
        for idx, y in enumerate(ys):
            paths.append(np.asarray([[0.0, y], [w - 1.0, y]], dtype=np.float32)); geometries.append({"id": f"ray_x_{idx}", "kind": "line", "points": [[0.0, float(y)/(max(1,h-1))],[1.0,float(y)/(max(1,h-1))]]})
    if axis in {"y", "both"}:
        xs = np.linspace(0, w - 1, ray_count + 2)[1:-1] if ray_count > 1 else np.asarray([(w - 1) * 0.5])
        for idx, x in enumerate(xs):
            paths.append(np.asarray([[x, 0.0], [x, h - 1.0]], dtype=np.float32)); geometries.append({"id": f"ray_y_{idx}", "kind": "line", "points": [[float(x)/(max(1,w-1)),0.0],[float(x)/(max(1,w-1)),1.0]]})
    blocks: list[DataBlock] = []
    label = method.label or "Rays"
    for path, geom in zip(paths, geometries):
        length = float(np.linalg.norm(path[-1] - path[0]))
        count = _sample_count(method.sampling_mode, method.sample_count, method.sample_step, length)
        geom["sample_count"] = count
        for ch in method.channels or ["gray"]:
            samples = _sample_polyline(channel_array(frame, ch), path, count)
            blocks.extend(_blocks_for_samples(method, label, ch, geom["id"], samples))
    return blocks, {"kind": "rays", "elements": geometries}


def _cross_blocks(method: SamplingMethodDefinition, frame: ImageFrame, source_prefix: str) -> tuple[list[DataBlock], dict[str, Any]]:
    h, w = frame.height, frame.width
    length_ratio = float(method.parameters.get("length_ratio", 0.8))
    centers = _placement_centers(method, w, h)
    blocks: list[DataBlock] = []
    elements: list[dict[str, Any]] = []
    label = method.label or "Cross"
    for ci, (cx, cy) in enumerate(centers):
        half_x = max(1.0, w * length_ratio * 0.5); half_y = max(1.0, h * length_ratio * 0.5)
        paths = [
            (f"cross_{ci}_h", np.asarray([[max(0,cx-half_x),cy],[min(w-1,cx+half_x),cy]],dtype=np.float32)),
            (f"cross_{ci}_v", np.asarray([[cx,max(0,cy-half_y)],[cx,min(h-1,cy+half_y)]],dtype=np.float32)),
        ]
        elements.append({"id": f"cross_{ci}", "kind":"cross", "center":[cx/max(1,w-1),cy/max(1,h-1)], "length_ratio": length_ratio})
        for element_id, path in paths:
            length = float(np.linalg.norm(path[-1]-path[0])); count=_sample_count(method.sampling_mode,method.sample_count,method.sample_step,length)
            for ch in method.channels or ["gray"]:
                blocks.extend(_blocks_for_samples(method,label,ch,element_id,_sample_polyline(channel_array(frame,ch),path,count)))
    return blocks, {"kind":"crosses","elements":elements}


def _rings_blocks(method: SamplingMethodDefinition, frame: ImageFrame, source_prefix: str) -> tuple[list[DataBlock], dict[str, Any]]:
    h,w=frame.height,frame.width
    ring_count=max(1,int(method.parameters.get("ring_count",3)))
    max_ratio=float(method.parameters.get("max_radius_ratio",0.4))
    centers=_placement_centers(method,w,h)
    blocks: list[DataBlock]=[]; elements: list[dict[str,Any]]=[]; label=method.label or "Concentric Rings"
    for ci,(cx,cy) in enumerate(centers):
        local_max=max(2.0,min(w,h)*max_ratio)
        for ri,radius in enumerate(np.linspace(local_max/ring_count,local_max,ring_count)):
            circumference=2*pi*float(radius); count=_sample_count(method.sampling_mode,method.sample_count,method.sample_step,circumference)
            theta=np.linspace(0,2*pi,count,endpoint=False,dtype=np.float32)
            points=np.stack([cx+np.cos(theta)*radius,cy+np.sin(theta)*radius],axis=1)
            points[:,0]=np.clip(points[:,0],0,w-1);points[:,1]=np.clip(points[:,1],0,h-1)
            element_id=f"ring_{ci}_{ri}"
            elements.append({"id":element_id,"kind":"ring","center":[cx/max(1,w-1),cy/max(1,h-1)],"radius":float(radius)/max(1,min(w,h)),"sample_count":count})
            closed=np.vstack([points,points[:1]])
            for ch in method.channels or ["gray"]:
                blocks.extend(_blocks_for_samples(method,label,ch,element_id,_sample_polyline(channel_array(frame,ch),closed,count)))
    return blocks,{"kind":"rings","elements":elements}


def execute_method(method: SamplingMethodDefinition, frame: ImageFrame, source_prefix: str) -> tuple[list[DataBlock], dict[str, Any]]:
    if not method.enabled:
        return [], {"kind": method.kind, "disabled": True}
    if method.kind in {"histogram", "statistics"}:
        return _whole_domain_blocks(method,frame,source_prefix), {"kind":method.kind,"domain":"whole"}
    if method.kind == "rays": return _rays_blocks(method,frame,source_prefix)
    if method.kind == "cross": return _cross_blocks(method,frame,source_prefix)
    if method.kind == "rings": return _rings_blocks(method,frame,source_prefix)
    raise ValueError(f"Unsupported sampling method: {method.kind}")


def _compose_vector(blocks: list[DataBlock], *, label: str) -> ComposedData:
    arrays=[np.asarray(b.values,dtype=np.float32).reshape(-1) for b in blocks]
    values=np.concatenate(arrays) if arrays else np.zeros((0,),dtype=np.float32)
    return ComposedData(values=values,layout="vector",block_order=[b.block_id for b in blocks],block_shapes={b.block_id:list(np.asarray(b.values).shape) for b in blocks},metadata={"label":label,"feature_count":int(values.size)})


def _patch_frame(frame: ImageFrame, x0:int,y0:int,x1:int,y1:int,patch_id:str)->ImageFrame:
    return ImageFrame(data=np.asarray(frame.data)[y0:y1,x0:x1].copy(),color_space=frame.color_space,source_id=patch_id,coordinate_frame=frame.coordinate_frame,metadata={**frame.metadata,"patch_bounds":[x0,y0,x1,y1]})


@dataclass
class SamplingProgramRun:
    global_blocks: DataBlockSet
    global_data: ComposedData
    local_patch_blocks: list[DataBlockSet]
    local_patch_bounds: list[list[int]]
    local_data: ComposedData
    combined_data: ComposedData
    method_summaries: dict[str, Any]
    timings_ms: dict[str, float]

    def manifest(self) -> dict[str, Any]:
        return {
            "global_feature_count": int(np.asarray(self.global_data.values).size),
            "local_shape": list(np.asarray(self.local_data.values).shape),
            "combined_feature_count": int(np.asarray(self.combined_data.values).size),
            "patch_count": len(self.local_patch_blocks),
            "method_summaries": self.method_summaries,
            "timings_ms": self.timings_ms,
        }


class SamplingProgramRuntime:
    def __init__(self, definition: SamplingProgramDefinition) -> None:
        self.definition = definition

    def run(self, frame: ImageFrame) -> SamplingProgramRun:
        timings: dict[str,float]={}; summaries: dict[str,Any]={}
        start=perf_counter(); global_blocks: list[DataBlock]=[]
        for method in self.definition.global_domain.methods:
            t0=perf_counter(); blocks,geometry=execute_method(method,frame,"global");global_blocks.extend(blocks)
            timings[f"global:{method.id}"]=(perf_counter()-t0)*1000.0
            summaries[f"global:{method.id}"]={"kind":method.kind,"block_count":len(blocks),"dimension":int(sum(np.asarray(b.values).size for b in blocks)),"geometry":geometry}
        global_set=DataBlockSet(global_blocks,metadata={"domain":"global"});global_data=_compose_vector(global_blocks,label="global")
        timings["global_total"]=(perf_counter()-start)*1000.0

        local_start=perf_counter();grid=self.definition.local_domain.grid;rows,cols=int(grid.rows),int(grid.cols)
        xs=np.linspace(0,frame.width,cols+1,dtype=int);ys=np.linspace(0,frame.height,rows+1,dtype=int)
        patch_sets: list[DataBlockSet]=[];bounds: list[list[int]]=[];patch_vectors: list[np.ndarray]=[]
        for r in range(rows):
            for c in range(cols):
                x0,x1=int(xs[c]),int(xs[c+1]);y0,y1=int(ys[r]),int(ys[r+1]);patch_id=f"patch_{r}_{c}";patch=_patch_frame(frame,x0,y0,x1,y1,patch_id);blocks: list[DataBlock]=[]
                for method in self.definition.local_domain.methods:
                    t0=perf_counter();method_blocks,geometry=execute_method(method,patch,patch_id);blocks.extend(method_blocks)
                    key=f"local:{method.id}";entry=summaries.setdefault(key,{"kind":method.kind,"block_count_per_patch":len(method_blocks),"dimension_per_patch":int(sum(np.asarray(b.values).size for b in method_blocks)),"geometry":geometry})
                    timings[key]=timings.get(key,0.0)+(perf_counter()-t0)*1000.0
                patch_sets.append(DataBlockSet(blocks,metadata={"domain":"local","patch_id":patch_id,"row":r,"col":c,"bounds":[x0,y0,x1,y1]}));bounds.append([x0,y0,x1,y1]);patch_vectors.append(_compose_vector(blocks,label=patch_id).values.reshape(-1))
        max_dim=max([int(v.size) for v in patch_vectors],default=0);matrix=np.zeros((rows*cols,max_dim),dtype=np.float32);ragged=False
        for i,v in enumerate(patch_vectors):
            if v.size!=max_dim:ragged=True
            matrix[i,:v.size]=v
        layout=self.definition.output_shape.local_layout
        order=self.definition.output_shape.local_order
        if layout=="flatten":
            local_values=matrix.reshape(-1) if order=="patch_major" else matrix.T.reshape(-1)
        elif layout=="patch_matrix":
            local_values=matrix if order=="patch_major" else matrix.T
        else:
            local_values=(
                matrix.reshape(rows,cols,max_dim)
                if order=="patch_major"
                else matrix.T.reshape(max_dim,rows,cols)
            )
        local_data=ComposedData(values=local_values,layout=layout,block_order=[f"patch_{r}_{c}" for r in range(rows) for c in range(cols)],block_shapes={f"patch_{r}_{c}":[int(patch_vectors[r*cols+c].size)] for r in range(rows) for c in range(cols)},metadata={"rows":rows,"cols":cols,"feature_depth":max_dim,"ragged_zero_padding":ragged,"order":order})
        timings["local_total"]=(perf_counter()-local_start)*1000.0
        combined=np.concatenate([np.asarray(global_data.values).reshape(-1),np.asarray(local_values).reshape(-1)]).astype(np.float32)
        combined_data=ComposedData(values=combined,layout="vector",block_order=["global","local"],block_shapes={"global":[int(np.asarray(global_data.values).size)],"local":[int(matrix.size)]},metadata={"global_features":int(np.asarray(global_data.values).size),"local_features":int(np.asarray(local_values).size)})
        return SamplingProgramRun(global_set,global_data,patch_sets,bounds,local_data,combined_data,summaries,timings)
