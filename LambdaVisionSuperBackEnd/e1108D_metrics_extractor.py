"""
Entropy #1 - 1108D Handcrafted Station Feature Extractor

Input
-----
- station image: 64x64x3 (BGR by default)
- valid mask:    64x64

Output
------
1108D float32 feature vector in this exact order:
    Global      48D   [0:48]
    Grid       128D   [48:176]
    Profiles   384D   [176:560]
    Radial     384D   [560:944]
    Edge        64D   [944:1008]
    Valid      100D   [1008:1108]

IMPORTANT
---------
- GT paste mask is NEVER used to compute features.
- Invalid pixels are missing data, not intensity zero.
- The returned vector is RAW engineered data. Dataset standardization must be
  fitted later using TRAIN split only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import csv
import json
import math

import cv2
import numpy as np


@dataclass(frozen=True)
class FeatureConfig:
    station_size: int = 64

    # A. Global
    hist_L_bins: int = 16
    hist_a_bins: int = 8
    hist_b_bins: int = 8
    percentiles: Tuple[int, int, int] = (10, 50, 90)

    # B. Grid
    grid_rows: int = 4
    grid_cols: int = 4

    # C. Profiles
    profiles_each_axis: int = 32

    # D. Radial
    radial_directions: int = 32
    radial_radii: Tuple[int, int, int] = (8, 16, 24)
    radial_center_patch: int = 5
    radial_sample_patch: int = 3

    # E. Edge
    orientation_bins: int = 16
    edge_grid_rows: int = 4
    edge_grid_cols: int = 4
    edge_erode_iterations: int = 2
    sobel_axis_scale: float = 4.0
    sobel_mag_scale: float = 4.0 * math.sqrt(2.0)
    edge_threshold: float = 0.08
    laplacian_scale: float = 4.0


CFG = FeatureConfig()
TOTAL_FEATURE_DIM = 1108

FEATURE_SLICES: Dict[str, slice] = {
    "global": slice(0, 48),
    "grid": slice(48, 176),
    "profiles": slice(176, 560),
    "radial": slice(560, 944),
    "edge": slice(944, 1008),
    "valid": slice(1008, 1108),
}

# Optional offline-precompute layout
STATION_ROOT = Path("_entropy1_stations")
IMAGE_DIR = STATION_ROOT / "images"
VALID_DIR = STATION_ROOT / "valid"
GT_DIR = STATION_ROOT / "masks"     # optional training target only
META_DIR = STATION_ROOT / "meta"
OUTPUT_ROOT = Path("_entropy1_features_1108")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def build_feature_names(cfg: FeatureConfig = CFG) -> List[str]:
    n: List[str] = []

    # A. Global 48
    n += [f"global.hist_L.{i:02d}" for i in range(cfg.hist_L_bins)]
    n += [f"global.hist_a.{i:02d}" for i in range(cfg.hist_a_bins)]
    n += [f"global.hist_b.{i:02d}" for i in range(cfg.hist_b_bins)]
    n += [f"global.mean_{c}" for c in "Lab"]
    n += [f"global.std_{c}" for c in "Lab"]
    for c in "Lab":
        n += [f"global.p{p}_{c}" for p in cfg.percentiles]
    n.append("global.valid_ratio")
    assert len(n) == 48

    # B. Grid 128
    fields = ("mean_L", "mean_a", "mean_b", "std_L", "std_a", "std_b", "mean_grad", "coverage")
    for gy in range(4):
        for gx in range(4):
            n += [f"grid.r{gy}.c{gx}.{f}" for f in fields]
    assert len(n) == 176

    # C. Profiles 384
    fields = ("mean_L", "mean_a", "mean_b", "std_L", "mean_grad", "coverage")
    for axis in ("vertical", "horizontal"):
        for i in range(32):
            n += [f"profile.{axis}.{i:02d}.{f}" for f in fields]
    assert len(n) == 560

    # D. Radial 384
    fields = ("delta_L", "delta_a", "delta_b", "valid_fraction")
    for k in range(32):
        angle = k * 360.0 / 32
        for r in cfg.radial_radii:
            n += [f"radial.a{angle:06.2f}.r{r:02d}.{f}" for f in fields]
    assert len(n) == 944

    # E1 8
    n += [
        "edge.global.mean_abs_gx", "edge.global.std_abs_gx",
        "edge.global.mean_abs_gy", "edge.global.std_abs_gy",
        "edge.global.mean_g", "edge.global.std_g",
        "edge.global.p90_g", "edge.global.edge_density",
    ]
    # E2 16
    n += [f"edge.orientation.{i:02d}" for i in range(16)]
    # E3 32
    for gy in range(4):
        for gx in range(4):
            n += [f"edge.grid.r{gy}.c{gx}.mean_g", f"edge.grid.r{gy}.c{gx}.edge_density"]
    # E4 8
    n += [
        "edge.lap.mean_abs", "edge.lap.std_abs", "edge.lap.p50_abs",
        "edge.lap.p75_abs", "edge.lap.p90_abs", "edge.lap.positive_ratio",
        "edge.lap.negative_ratio", "edge.lap.zero_cross_density",
    ]
    assert len(n) == 1008

    # F. valid 100
    for y in range(10):
        for x in range(10):
            n.append(f"valid.map10.r{y}.c{x}")

    assert len(n) == 1108
    return n


FEATURE_NAMES = build_feature_names()


def _prepare(image: np.ndarray, valid_mask: np.ndarray, cfg: FeatureConfig):
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"image must be HxWx3, got {image.shape}")
    if valid_mask.ndim == 3:
        valid_mask = valid_mask[..., 0]
    if image.shape[:2] != valid_mask.shape[:2]:
        raise ValueError("image and valid_mask sizes differ")

    s = cfg.station_size
    if image.shape[:2] != (s, s):
        image = cv2.resize(image, (s, s), interpolation=cv2.INTER_AREA)
        valid_mask = cv2.resize(valid_mask, (s, s), interpolation=cv2.INTER_NEAREST)
    valid = (valid_mask > 0).astype(np.uint8)
    return image, valid


def _to_lab(image: np.ndarray, color_order: str):
    x = image.astype(np.float32)
    if image.dtype == np.uint8 or x.max(initial=0.0) > 1.5:
        x /= 255.0
    x = np.clip(x, 0.0, 1.0)
    if color_order.upper() == "BGR":
        lab = cv2.cvtColor(x, cv2.COLOR_BGR2LAB)
    elif color_order.upper() == "RGB":
        lab = cv2.cvtColor(x, cv2.COLOR_RGB2LAB)
    else:
        raise ValueError("color_order must be BGR or RGB")
    L = np.clip(lab[..., 0] / 100.0, 0.0, 1.0).astype(np.float32)
    a = np.clip(lab[..., 1] / 128.0, -1.0, 1.0).astype(np.float32)
    b = np.clip(lab[..., 2] / 128.0, -1.0, 1.0).astype(np.float32)
    return L, a, b


def _mean_std(x: np.ndarray, mask: np.ndarray):
    v = x[mask.astype(bool)]
    return (0.0, 0.0) if v.size == 0 else (float(v.mean()), float(v.std()))


def _percentiles(x: np.ndarray, mask: np.ndarray, ps: Sequence[int]):
    v = x[mask.astype(bool)]
    return [0.0] * len(ps) if v.size == 0 else [float(z) for z in np.percentile(v, ps)]


def _hist(x, mask, bins, value_range):
    v = x[mask.astype(bool)]
    if v.size == 0:
        return np.zeros(bins, np.float32)
    h, _ = np.histogram(v, bins=bins, range=value_range)
    h = h.astype(np.float32)
    h /= max(float(h.sum()), 1.0)
    return h


def _bounds(length: int, count: int):
    e = np.rint(np.linspace(0, length, count + 1)).astype(int)
    return [(int(e[i]), int(e[i + 1])) for i in range(count)]


class EdgeMaps:
    def __init__(self, safe, abs_gx, abs_gy, mag, theta, strong, lap, abs_lap):
        self.safe = safe
        self.abs_gx = abs_gx
        self.abs_gy = abs_gy
        self.mag = mag
        self.theta = theta
        self.strong = strong
        self.lap = lap
        self.abs_lap = abs_lap


def _edge_maps(L: np.ndarray, valid: np.ndarray, cfg: FeatureConfig):
    vb = valid.astype(bool)
    fill = float(np.median(L[vb])) if vb.any() else 0.0
    x = L.copy()
    x[~vb] = fill

    gx_raw = cv2.Sobel(x, cv2.CV_32F, 1, 0, ksize=3, borderType=cv2.BORDER_REFLECT101)
    gy_raw = cv2.Sobel(x, cv2.CV_32F, 0, 1, ksize=3, borderType=cv2.BORDER_REFLECT101)
    abs_gx = np.abs(gx_raw / cfg.sobel_axis_scale).astype(np.float32)
    abs_gy = np.abs(gy_raw / cfg.sobel_axis_scale).astype(np.float32)
    mag = (np.sqrt(gx_raw**2 + gy_raw**2) / cfg.sobel_mag_scale).astype(np.float32)
    theta = np.mod(np.degrees(np.arctan2(gy_raw, gx_raw)), 180.0).astype(np.float32)

    safe = cv2.erode(valid, np.ones((3, 3), np.uint8), iterations=cfg.edge_erode_iterations)
    strong = ((mag >= cfg.edge_threshold) & safe.astype(bool)).astype(np.uint8)

    kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]], np.float32)
    lap = (cv2.filter2D(x, cv2.CV_32F, kernel, borderType=cv2.BORDER_REFLECT101) / cfg.laplacian_scale).astype(np.float32)
    return EdgeMaps(safe, abs_gx, abs_gy, mag, theta, strong, lap, np.abs(lap).astype(np.float32))


def _global(L, a, b, valid, cfg):
    f: List[float] = []
    f.extend(_hist(L, valid, 16, (0,1)))
    f.extend(_hist(a, valid, 8, (-1,1)))
    f.extend(_hist(b, valid, 8, (-1,1)))
    for c in (L,a,b): f.append(_mean_std(c, valid)[0])
    for c in (L,a,b): f.append(_mean_std(c, valid)[1])
    for c in (L,a,b): f.extend(_percentiles(c, valid, cfg.percentiles))
    f.append(float(valid.mean()))
    out = np.asarray(f, np.float32); assert out.shape == (48,); return out


def _grid(L, a, b, valid, edge, cfg):
    f: List[float] = []
    for y0,y1 in _bounds(64,4):
        for x0,x1 in _bounds(64,4):
            vm = valid[y0:y1,x0:x1]
            for c in (L,a,b): f.append(_mean_std(c[y0:y1,x0:x1], vm)[0])
            for c in (L,a,b): f.append(_mean_std(c[y0:y1,x0:x1], vm)[1])
            sm = edge.safe[y0:y1,x0:x1]
            f.append(_mean_std(edge.mag[y0:y1,x0:x1], sm)[0])
            f.append(float(vm.mean()))
    out = np.asarray(f,np.float32); assert out.shape==(128,); return out


def _profile_desc(L,a,b,valid,mag,safe):
    mL,sL = _mean_std(L,valid)
    return [mL, _mean_std(a,valid)[0], _mean_std(b,valid)[0], sL, _mean_std(mag,safe)[0], float(valid.mean())]


def _profiles(L,a,b,valid,edge,cfg):
    f: List[float] = []
    for x0,x1 in _bounds(64,32):
        f.extend(_profile_desc(L[:,x0:x1],a[:,x0:x1],b[:,x0:x1],valid[:,x0:x1],edge.mag[:,x0:x1],edge.safe[:,x0:x1]))
    for y0,y1 in _bounds(64,32):
        f.extend(_profile_desc(L[y0:y1,:],a[y0:y1,:],b[y0:y1,:],valid[y0:y1,:],edge.mag[y0:y1,:],edge.safe[y0:y1,:]))
    out=np.asarray(f,np.float32); assert out.shape==(384,); return out


def _patch_mean(L,a,b,valid,cx,cy,size):
    half=size//2; ix=int(round(cx)); iy=int(round(cy)); h,w=valid.shape
    x0=max(0,ix-half); x1=min(w,ix+half+1); y0=max(0,iy-half); y1=min(h,iy+half+1)
    vm=valid[y0:y1,x0:x1].astype(bool); area=max((x1-x0)*(y1-y0),1); frac=float(vm.sum()/area)
    if not vm.any(): return np.zeros(3,np.float32),0.0
    lab=np.stack([L[y0:y1,x0:x1],a[y0:y1,x0:x1],b[y0:y1,x0:x1]],axis=-1)
    return lab[vm].mean(axis=0).astype(np.float32),frac


def _radial(L,a,b,valid,cfg):
    cx=cy=31.5
    ref,frac=_patch_mean(L,a,b,valid,cx,cy,cfg.radial_center_patch)
    if frac==0:
        ref,frac=_patch_mean(L,a,b,valid,cx,cy,9)
    if frac==0 and valid.astype(bool).any():
        vb=valid.astype(bool); ref=np.array([L[vb].mean(),a[vb].mean(),b[vb].mean()],np.float32)
    f: List[float]=[]
    for k in range(32):
        th=2*math.pi*k/32
        for r in cfg.radial_radii:
            sample,vf=_patch_mean(L,a,b,valid,cx+r*math.cos(th),cy+r*math.sin(th),cfg.radial_sample_patch)
            if vf>0:
                d=sample-ref; f.extend([float(d[0]),float(d[1]),float(d[2]),vf])
            else:
                f.extend([0.0,0.0,0.0,0.0])
    out=np.asarray(f,np.float32); assert out.shape==(384,); return out


def _zero_cross(lap,safe):
    s=safe.astype(bool); crossings=pairs=0
    pm=s[:,:-1]&s[:,1:]
    if pm.any():
        a,b=lap[:,:-1],lap[:,1:]; c=((a>0)&(b<0))|((a<0)&(b>0)); crossings+=int((c&pm).sum()); pairs+=int(pm.sum())
    pm=s[:-1,:]&s[1:,:]
    if pm.any():
        a,b=lap[:-1,:],lap[1:,:]; c=((a>0)&(b<0))|((a<0)&(b>0)); crossings+=int((c&pm).sum()); pairs+=int(pm.sum())
    return 0.0 if pairs==0 else float(crossings/pairs)


def _edge(edge,cfg):
    f: List[float]=[]; s=edge.safe.astype(bool)
    if s.any():
        gx=edge.abs_gx[s]; gy=edge.abs_gy[s]; g=edge.mag[s]
        f += [float(gx.mean()),float(gx.std()),float(gy.mean()),float(gy.std()),float(g.mean()),float(g.std()),float(np.percentile(g,90)),float(edge.strong[s].mean())]
        h,_=np.histogram(edge.theta[s],bins=16,range=(0,180),weights=edge.mag[s]); h=h.astype(np.float32); h/=max(float(h.sum()),1e-12)
    else:
        f += [0.0]*8; h=np.zeros(16,np.float32)
    f.extend(h.tolist())

    for y0,y1 in _bounds(64,4):
        for x0,x1 in _bounds(64,4):
            sm=edge.safe[y0:y1,x0:x1].astype(bool)
            if sm.any():
                g=edge.mag[y0:y1,x0:x1]; st=edge.strong[y0:y1,x0:x1]; f += [float(g[sm].mean()),float(st[sm].mean())]
            else: f += [0.0,0.0]

    if s.any():
        lap=edge.lap[s]; al=edge.abs_lap[s]
        f += [float(al.mean()),float(al.std()),float(np.percentile(al,50)),float(np.percentile(al,75)),float(np.percentile(al,90)),float((lap>0).mean()),float((lap<0).mean()),_zero_cross(edge.lap,edge.safe)]
    else: f += [0.0]*8
    out=np.asarray(f,np.float32); assert out.shape==(64,); return out


def _valid_geometry(valid):
    m=cv2.resize(valid.astype(np.float32),(10,10),interpolation=cv2.INTER_AREA)
    return np.clip(m,0,1).reshape(-1).astype(np.float32)


def extract_feature_blocks(image: np.ndarray, valid_mask: np.ndarray, *, color_order: str="BGR", cfg: FeatureConfig=CFG):
    image,valid=_prepare(image,valid_mask,cfg)
    L,a,b=_to_lab(image,color_order)
    em=_edge_maps(L,valid,cfg)
    blocks={
        "global": _global(L,a,b,valid,cfg),
        "grid": _grid(L,a,b,valid,em,cfg),
        "profiles": _profiles(L,a,b,valid,em,cfg),
        "radial": _radial(L,a,b,valid,cfg),
        "edge": _edge(em,cfg),
        "valid": _valid_geometry(valid),
    }
    expected={"global":48,"grid":128,"profiles":384,"radial":384,"edge":64,"valid":100}
    for k,d in expected.items(): assert blocks[k].shape==(d,), (k,blocks[k].shape)
    return blocks


def extract_feature_vector(image: np.ndarray, valid_mask: np.ndarray, *, color_order: str="BGR", cfg: FeatureConfig=CFG) -> np.ndarray:
    """Public API for the future training pipeline. Returns float32 (1108,)."""
    b=extract_feature_blocks(image,valid_mask,color_order=color_order,cfg=cfg)
    v=np.concatenate([b["global"],b["grid"],b["profiles"],b["radial"],b["edge"],b["valid"]]).astype(np.float32)
    if v.shape!=(1108,): raise RuntimeError(f"Expected 1108D, got {v.shape}")
    if not np.isfinite(v).all(): raise RuntimeError("Feature vector contains NaN/Inf")
    return v


def _same_relative(root: Path, rel: Path) -> Optional[Path]:
    p=root/rel
    if p.exists(): return p
    for ext in IMAGE_EXTENSIONS:
        q=root/rel.parent/(rel.stem+ext)
        if q.exists(): return q
    return None


def build_feature_dataset(image_dir: Path=IMAGE_DIR, valid_dir: Path=VALID_DIR, gt_dir: Optional[Path]=GT_DIR, output_root: Path=OUTPUT_ROOT):
    """Precompute deterministic feature NPZs. GT is stored only as target."""
    feature_dir=output_root/"features"; feature_dir.mkdir(parents=True,exist_ok=True)
    (output_root/"feature_names.json").write_text(json.dumps({"dim":1108,"slices":{k:[s.start,s.stop] for k,s in FEATURE_SLICES.items()},"names":FEATURE_NAMES},indent=2),encoding="utf-8")

    images=sorted(p for p in image_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    if not images: raise FileNotFoundError(f"No station images under {image_dir.resolve()}")
    rows=[]
    for idx,ip in enumerate(images,1):
        rel=ip.relative_to(image_dir); vp=_same_relative(valid_dir,rel)
        if vp is None:
            print(f"[SKIP] missing valid: {rel}"); continue
        image=cv2.imread(str(ip),cv2.IMREAD_COLOR); valid=cv2.imread(str(vp),cv2.IMREAD_GRAYSCALE)
        if image is None or valid is None:
            print(f"[SKIP] unreadable: {rel}"); continue

        feat=extract_feature_vector(image,valid,color_order="BGR")
        _,valid64=_prepare(image,valid,CFG)
        arrays={"features":feat,"valid_mask":valid64.astype(np.uint8)}

        gp=_same_relative(gt_dir,rel) if gt_dir is not None else None
        if gp is not None:
            gt=cv2.imread(str(gp),cv2.IMREAD_GRAYSCALE)
            if gt is not None:
                gt=cv2.resize(gt,(64,64),interpolation=cv2.INTER_NEAREST)
                arrays["gt_mask"]=((gt>0)&(valid64>0)).astype(np.uint8)

        op=feature_dir/rel.with_suffix(".npz"); op.parent.mkdir(parents=True,exist_ok=True); np.savez_compressed(op,**arrays)

        meta_path=META_DIR/rel.with_suffix(".json"); meta={}
        if meta_path.exists():
            try: meta=json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception: pass
        rows.append({
            "station_key":rel.with_suffix("").as_posix(),
            "feature_path":op.relative_to(output_root).as_posix(),
            "image_path":ip.as_posix(),
            "valid_path":vp.as_posix(),
            "gt_path":gp.as_posix() if gp else "",
            "valid_ratio":f"{float(valid64.mean()):.8f}",
            "source_roi":str(meta.get("source_roi",meta.get("source",""))),
            "station_index":str(meta.get("station_index",meta.get("index",""))),
            "s_norm":str(meta.get("s_norm","")),
        })
        if idx%100==0: print(f"[INFO] {idx}/{len(images)}")

    with (output_root/"manifest.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["station_key","feature_path","image_path","valid_path","gt_path","valid_ratio","source_roi","station_index","s_norm"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"[DONE] {len(rows)} stations -> {output_root.resolve()}")


def sanity_check():
    image=np.zeros((64,64,3),np.uint8); image[:]=(60,85,110)
    cv2.line(image,(10,50),(52,14),(150,165,170),11)
    cv2.line(image,(20,41),(42,22),(225,225,225),3)
    valid=np.zeros((64,64),np.uint8)
    pts=np.array([[5,54],[11,35],[25,16],[45,5],[60,12],[52,29],[34,48],[16,61]],np.int32)
    cv2.fillPoly(valid,[pts],255)
    b=extract_feature_blocks(image,valid)
    v=extract_feature_vector(image,valid)
    for k,x in b.items(): print(f"{k:10s}: {x.shape}")
    print("TOTAL     :",v.shape)
    print("finite    :",bool(np.isfinite(v).all()))
    print("names     :",len(FEATURE_NAMES))
    for k,s in FEATURE_SLICES.items(): print(f"{k:10s}: [{s.start}:{s.stop}] = {s.stop-s.start}D")
    assert v.shape==(1108,) and len(FEATURE_NAMES)==1108 and np.isfinite(v).all()
    print("[OK] sanity check passed")


if __name__ == "__main__":
    # Safe default. Change to build_feature_dataset() when ready to precompute real data.
    sanity_check()