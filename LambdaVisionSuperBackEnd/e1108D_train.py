"""
Train Engineer MLP V1 from 64x64 station images.
================================================

This training file connects the two modules already built:

    entropy1_feature_extractor_1108.py
        image + valid mask -> raw handcrafted vector [1108]

    engineer_mlp_v1.py
        standardized 1108D -> segmentation logits [1,64,64]

Pipeline
--------
1. Discover station image / valid mask / GT mask pairs.
2. Extract deterministic 1108D vectors and cache them once.
3. Split by SOURCE ROI / source image group (never random station split).
4. Fit per-feature mean/std using TRAIN split only.
5. Standardize 1108D vectors.
6. Train EngineerMLP with masked BCE + Dice and auxiliary coarse loss.
7. Save best checkpoint, last checkpoint, split manifest, standardizer,
   feature statistics, and training history.

IMPORTANT
---------
- GT mask is NEVER used to create the 1108D feature vector.
- VALID mask is used by the extractor and by the loss.
- Standardization statistics are fitted ONLY from the training split.
- No command-line parameters are used. Edit the CONFIG section below.
- Image augmentation is intentionally not performed here. Any geometric /
  appearance augmentation must transform image + valid + GT consistently and
  then re-run the 1108D extractor. The future Teacher pipeline can do that.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from contextlib import nullcontext
import csv
import hashlib
import json
import math
import random
import re
import time

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from e1108D_metrics_extractor import (
    CFG as FEATURE_CFG,
    FEATURE_NAMES,
    TOTAL_FEATURE_DIM,
    extract_feature_vector,
)
from e1108D_neural_network import (
    EngineerMLP,
    EngineerMLPConfig,
    count_parameters,
    engineer_loss,
)


# =============================================================================
# CONFIG - EDIT EVERYTHING HERE, NOT ON THE COMMAND LINE
# =============================================================================

# -----------------------------------------------------------------------------
# Input station dataset
# -----------------------------------------------------------------------------
# Expected default layout:
#
# _entropy1_stations/
#     images/
#     masks/      <- GT paste/relevance segmentation mask
#     valid/      <- valid ROI mask
#     meta/       <- optional JSON metadata from station builder
#
STATION_ROOT = Path("/home/hieu/Desktop/Nidec Vision/stations_divided")
IMAGE_DIR = STATION_ROOT / "images"
GT_MASK_DIR = STATION_ROOT / "masks"
VALID_MASK_DIR = STATION_ROOT / "valid"
META_DIR = STATION_ROOT / "meta"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

# -----------------------------------------------------------------------------
# Deterministic 1108D feature cache
# -----------------------------------------------------------------------------
# Extraction is deterministic and more expensive than loading a 1108-float
# vector, so the training script caches each station once.
FEATURE_CACHE_DIR = Path("/home/hieu/Desktop/Nidec Vision/e1108_cacheche_1108_v1")
REBUILD_FEATURE_CACHE = False

# -----------------------------------------------------------------------------
# Training outputs
# -----------------------------------------------------------------------------
RUN_ROOT = Path("/home/hieu/Desktop/Nidec Vision/run")
RUN_NAME = "engineer_mlp_1108_v1"
RUN_DIR = RUN_ROOT / RUN_NAME
CHECKPOINT_DIR = RUN_DIR / "checkpoints"

# -----------------------------------------------------------------------------
# Group-aware split
# -----------------------------------------------------------------------------
# Split is performed on SOURCE GROUPS, not individual stations.
TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10
RANDOM_SEED = 20260820

# If True, refuse to continue when a station cannot be assigned to a reliable
# source group from metadata or filename structure.
STRICT_GROUP_SPLIT = False

# -----------------------------------------------------------------------------
# Optimization
# -----------------------------------------------------------------------------
EPOCHS = 200
BATCH_SIZE = 64
NUM_WORKERS = 0               # 0 is safest on both Windows and Linux
PIN_MEMORY = True

LEARNING_RATE = 3e-4
WEIGHT_DECAY = 1e-4
GRAD_CLIP_NORM = 1.0

# Loss = fine + COARSE_WEIGHT * coarse
DICE_WEIGHT = 1.0
COARSE_WEIGHT = 0.20

# Segmentation threshold used only for validation metrics / inference.
PREDICTION_THRESHOLD = 0.50

# Learning-rate scheduler
LR_REDUCE_FACTOR = 0.5
LR_PATIENCE = 6
MIN_LR = 1e-6

# Early stopping based on validation Dice
EARLY_STOPPING_PATIENCE = 50
MIN_DICE_IMPROVEMENT = 1e-4

# Mixed precision is automatically disabled on CPU.
USE_AMP = True

# Save last checkpoint every N epochs.
SAVE_LAST_EVERY = 1

# -----------------------------------------------------------------------------
# Standardization
# -----------------------------------------------------------------------------
STANDARDIZER_EPS = 1e-6
CLIP_STANDARDIZED_FEATURES = None
# Example: 8.0 would clip z-scores to [-8, 8].
# Keep None initially so the network sees the real training distribution.

# -----------------------------------------------------------------------------
# Model configuration
# -----------------------------------------------------------------------------
MODEL_CFG = EngineerMLPConfig(
    dropout=0.08,
    num_residual_blocks=2,
)


# =============================================================================
# REPRODUCIBILITY / DEVICE
# =============================================================================

def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # MLP training is not convolution-heavy, so deterministic mode is a
    # reasonable default for reproducible experiments.
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def choose_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# =============================================================================
# DATA RECORDS / DISCOVERY
# =============================================================================

@dataclass
class StationRecord:
    key: str
    image_path: Path
    gt_path: Path
    valid_path: Path
    meta_path: Optional[Path]
    source_group: str
    cache_path: Path


def _find_same_relative(root: Path, relative_path: Path) -> Optional[Path]:
    exact = root / relative_path
    if exact.exists():
        return exact

    parent = root / relative_path.parent
    if not parent.exists():
        return None

    for ext in IMAGE_EXTENSIONS:
        p = parent / f"{relative_path.stem}{ext}"
        if p.exists():
            return p
    return None


def _load_json(path: Optional[Path]) -> Dict:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _strip_station_suffix(stem: str) -> str:
    """
    Fallback grouping for filenames such as:
        roi_001_station_000
        roi_001-station-12
        roi_001_st003

    The metadata source_roi field is preferred whenever available.
    """
    patterns = [
        r"(?i)(?:[_-]station[_-]?\d+)$",
        r"(?i)(?:[_-]st[_-]?\d+)$",
        r"(?i)(?:[_-]s[_-]?\d+)$",
    ]
    out = stem
    for p in patterns:
        out2 = re.sub(p, "", out)
        if out2 != out:
            return out2
    return out


def _infer_source_group(relative_image: Path, metadata: Dict) -> Tuple[str, bool]:
    """
    Returns (group_name, is_reliable).

    Preferred metadata keys are tried first because stations from the same ROI
    overlap strongly and MUST remain in the same dataset split.
    """
    for key in (
        "source_roi",
        "source_image",
        "source_path",
        "source",
        "roi_name",
        "roi_id",
    ):
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value), True

    stripped = _strip_station_suffix(relative_image.stem)
    if stripped != relative_image.stem:
        group = (relative_image.parent / stripped).as_posix()
        return group, True

    # If station builder stores every ROI in its own folder, the parent folder
    # is still a useful grouping key.
    if relative_image.parent != Path("."):
        return relative_image.parent.as_posix(), True

    # Last-resort fallback. This is potentially unsafe because each station may
    # become its own group. We report it so the user can fix metadata.
    return relative_image.with_suffix("").as_posix(), False


def _cache_path_for(relative_image: Path) -> Path:
    return FEATURE_CACHE_DIR / relative_image.with_suffix(".npz")


def discover_records() -> List[StationRecord]:
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"IMAGE_DIR does not exist: {IMAGE_DIR.resolve()}")
    if not VALID_MASK_DIR.exists():
        raise FileNotFoundError(f"VALID_MASK_DIR does not exist: {VALID_MASK_DIR.resolve()}")
    if not GT_MASK_DIR.exists():
        raise FileNotFoundError(f"GT_MASK_DIR does not exist: {GT_MASK_DIR.resolve()}")

    image_paths = sorted(
        p for p in IMAGE_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_paths:
        raise RuntimeError(f"No station images found under {IMAGE_DIR.resolve()}")

    records: List[StationRecord] = []
    unreliable_groups = 0
    skipped_missing = 0

    for image_path in image_paths:
        rel = image_path.relative_to(IMAGE_DIR)

        valid_path = _find_same_relative(VALID_MASK_DIR, rel)
        gt_path = _find_same_relative(GT_MASK_DIR, rel)

        if valid_path is None or gt_path is None:
            print(
                f"[SKIP] Missing pair for {rel}: "
                f"valid={'OK' if valid_path else 'MISSING'}, "
                f"gt={'OK' if gt_path else 'MISSING'}"
            )
            skipped_missing += 1
            continue

        meta_candidate = META_DIR / rel.with_suffix(".json")
        meta_path = meta_candidate if meta_candidate.exists() else None
        metadata = _load_json(meta_path)
        source_group, reliable = _infer_source_group(rel, metadata)

        if not reliable:
            unreliable_groups += 1
            if STRICT_GROUP_SPLIT:
                raise RuntimeError(
                    "Unable to infer a reliable source group for "
                    f"{rel}. Add source_roi/source_image metadata or use a "
                    "station filename containing a station index."
                )

        records.append(
            StationRecord(
                key=rel.with_suffix("").as_posix(),
                image_path=image_path,
                gt_path=gt_path,
                valid_path=valid_path,
                meta_path=meta_path,
                source_group=source_group,
                cache_path=_cache_path_for(rel),
            )
        )

    if not records:
        raise RuntimeError("No complete image/GT/valid station triplets were found.")

    print(f"[DATA] discovered stations : {len(records)}")
    print(f"[DATA] skipped incomplete  : {skipped_missing}")
    print(f"[DATA] unreliable grouping : {unreliable_groups}")

    return records


# =============================================================================
# FEATURE CACHE
# =============================================================================

def _read_station_arrays(record: StationRecord) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    image = cv2.imread(str(record.image_path), cv2.IMREAD_COLOR)
    valid = cv2.imread(str(record.valid_path), cv2.IMREAD_GRAYSCALE)
    gt = cv2.imread(str(record.gt_path), cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise RuntimeError(f"Could not read image: {record.image_path}")
    if valid is None:
        raise RuntimeError(f"Could not read valid mask: {record.valid_path}")
    if gt is None:
        raise RuntimeError(f"Could not read GT mask: {record.gt_path}")

    size = FEATURE_CFG.station_size
    if image.shape[:2] != (size, size):
        image = cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    if valid.shape[:2] != (size, size):
        valid = cv2.resize(valid, (size, size), interpolation=cv2.INTER_NEAREST)
    if gt.shape[:2] != (size, size):
        gt = cv2.resize(gt, (size, size), interpolation=cv2.INTER_NEAREST)

    valid_bin = (valid > 0).astype(np.uint8)
    gt_bin = ((gt > 0) & (valid_bin > 0)).astype(np.uint8)

    return image, valid_bin, gt_bin


def build_or_validate_feature_cache(records: Sequence[StationRecord]) -> None:
    FEATURE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    built = 0
    reused = 0
    t0 = time.time()

    for i, record in enumerate(records, start=1):
        cp = record.cache_path

        if cp.exists() and not REBUILD_FEATURE_CACHE:
            # Validate the minimum cache contract before reusing it.
            try:
                with np.load(cp, allow_pickle=False) as z:
                    ok = (
                        "features" in z
                        and "gt_mask" in z
                        and "valid_mask" in z
                        and z["features"].shape == (TOTAL_FEATURE_DIM,)
                        and z["gt_mask"].shape == (64, 64)
                        and z["valid_mask"].shape == (64, 64)
                    )
                if ok:
                    reused += 1
                    continue
            except Exception:
                pass

        image, valid, gt = _read_station_arrays(record)

        # CRITICAL: GT is intentionally NOT passed to the feature extractor.
        features = extract_feature_vector(
            image,
            valid,
            color_order="BGR",
        )

        cp.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cp,
            features=features.astype(np.float32),
            gt_mask=gt.astype(np.uint8),
            valid_mask=valid.astype(np.uint8),
        )
        built += 1

        if i % 100 == 0 or i == len(records):
            elapsed = time.time() - t0
            print(
                f"[CACHE] {i}/{len(records)} | built={built} reused={reused} "
                f"| {elapsed:.1f}s"
            )

    print(f"[CACHE] complete: built={built}, reused={reused}")


# =============================================================================
# GROUP-AWARE SPLIT
# =============================================================================

def split_records_by_group(
    records: Sequence[StationRecord],
) -> Tuple[List[StationRecord], List[StationRecord], List[StationRecord]]:
    total_ratio = TRAIN_RATIO + VAL_RATIO + TEST_RATIO
    if abs(total_ratio - 1.0) > 1e-8:
        raise ValueError(
            f"TRAIN_RATIO + VAL_RATIO + TEST_RATIO must equal 1.0, got {total_ratio}"
        )

    groups: Dict[str, List[StationRecord]] = {}
    for r in records:
        groups.setdefault(r.source_group, []).append(r)

    group_names = sorted(groups.keys())
    if len(group_names) < 3:
        raise RuntimeError(
            f"Need at least 3 source groups for train/val/test, found {len(group_names)}."
        )

    rng = random.Random(RANDOM_SEED)
    rng.shuffle(group_names)

    n_groups = len(group_names)
    n_train = max(1, int(round(n_groups * TRAIN_RATIO)))
    n_val = max(1, int(round(n_groups * VAL_RATIO)))

    # Guarantee at least one test group.
    if n_train + n_val >= n_groups:
        overflow = n_train + n_val - (n_groups - 1)
        if n_train >= n_val and n_train - overflow >= 1:
            n_train -= overflow
        else:
            n_val = max(1, n_val - overflow)

    n_test = n_groups - n_train - n_val
    if n_test < 1:
        raise RuntimeError("Could not allocate at least one group to each split.")

    train_groups = set(group_names[:n_train])
    val_groups = set(group_names[n_train:n_train + n_val])
    test_groups = set(group_names[n_train + n_val:])

    # Hard leakage assertions.
    assert train_groups.isdisjoint(val_groups)
    assert train_groups.isdisjoint(test_groups)
    assert val_groups.isdisjoint(test_groups)

    train = [r for r in records if r.source_group in train_groups]
    val = [r for r in records if r.source_group in val_groups]
    test = [r for r in records if r.source_group in test_groups]

    print("[SPLIT]")
    print(f"  source groups : {n_groups}")
    print(f"  train         : {len(train):6d} stations / {len(train_groups):4d} groups")
    print(f"  val           : {len(val):6d} stations / {len(val_groups):4d} groups")
    print(f"  test          : {len(test):6d} stations / {len(test_groups):4d} groups")

    return train, val, test


def save_split_manifest(
    train: Sequence[StationRecord],
    val: Sequence[StationRecord],
    test: Sequence[StationRecord],
) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    split_of_key = {}
    for split_name, records in (("train", train), ("val", val), ("test", test)):
        for r in records:
            split_of_key[r.key] = split_name

    rows = []
    for records in (train, val, test):
        for r in records:
            rows.append(
                {
                    "split": split_of_key[r.key],
                    "station_key": r.key,
                    "source_group": r.source_group,
                    "image_path": str(r.image_path),
                    "gt_path": str(r.gt_path),
                    "valid_path": str(r.valid_path),
                    "cache_path": str(r.cache_path),
                }
            )

    rows.sort(key=lambda x: (x["split"], x["source_group"], x["station_key"]))

    path = RUN_DIR / "split_manifest.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# =============================================================================
# TRAIN-ONLY STANDARDIZER
# =============================================================================

@dataclass
class FeatureStandardizer:
    mean: np.ndarray
    std: np.ndarray

    def transform(self, x: np.ndarray) -> np.ndarray:
        y = (x.astype(np.float32) - self.mean) / self.std
        if CLIP_STANDARDIZED_FEATURES is not None:
            c = float(CLIP_STANDARDIZED_FEATURES)
            y = np.clip(y, -c, c)
        return y.astype(np.float32)


def fit_standardizer(train_records: Sequence[StationRecord]) -> FeatureStandardizer:
    """
    Streaming mean/std over TRAIN vectors only.

    Uses sums in float64 so it does not need to load all station vectors into
    RAM at once.
    """
    count = 0
    sum_x = np.zeros(TOTAL_FEATURE_DIM, dtype=np.float64)
    sum_x2 = np.zeros(TOTAL_FEATURE_DIM, dtype=np.float64)

    for record in train_records:
        with np.load(record.cache_path, allow_pickle=False) as z:
            x = z["features"].astype(np.float64)

        if x.shape != (TOTAL_FEATURE_DIM,):
            raise RuntimeError(f"Bad feature shape in {record.cache_path}: {x.shape}")
        if not np.isfinite(x).all():
            raise RuntimeError(f"NaN/Inf in {record.cache_path}")

        sum_x += x
        sum_x2 += x * x
        count += 1

    if count == 0:
        raise RuntimeError("No training samples available for standardizer.")

    mean = sum_x / count
    variance = np.maximum(sum_x2 / count - mean * mean, 0.0)
    std = np.sqrt(variance)

    # Constant / almost-constant feature dimensions should remain numerically
    # harmless instead of being amplified by division by a tiny std.
    constant = std < STANDARDIZER_EPS
    std[constant] = 1.0

    standardizer = FeatureStandardizer(
        mean=mean.astype(np.float32),
        std=std.astype(np.float32),
    )

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        RUN_DIR / "standardizer.npz",
        mean=standardizer.mean,
        std=standardizer.std,
        constant_feature_mask=constant.astype(np.uint8),
    )

    # Human-readable diagnostics keyed by the explicit feature names.
    stats_path = RUN_DIR / "feature_statistics.csv"
    with stats_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "feature_name", "train_mean", "train_std", "constant"])
        for i, name in enumerate(FEATURE_NAMES):
            writer.writerow(
                [
                    i,
                    name,
                    float(standardizer.mean[i]),
                    float(standardizer.std[i]),
                    int(constant[i]),
                ]
            )

    print(f"[NORM] fitted on {count} TRAIN stations")
    print(f"[NORM] near-constant dimensions: {int(constant.sum())}/{TOTAL_FEATURE_DIM}")

    return standardizer


# =============================================================================
# PYTORCH DATASET
# =============================================================================

class EngineerStationDataset(Dataset):
    def __init__(
        self,
        records: Sequence[StationRecord],
        standardizer: FeatureStandardizer,
    ):
        self.records = list(records)
        self.standardizer = standardizer

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        r = self.records[index]
        with np.load(r.cache_path, allow_pickle=False) as z:
            x = z["features"].astype(np.float32)
            gt = z["gt_mask"].astype(np.float32)
            valid = z["valid_mask"].astype(np.float32)

        x = self.standardizer.transform(x)

        # Convert masks from {0,1} to [1,H,W].
        gt = (gt > 0).astype(np.float32)[None, ...]
        valid = (valid > 0).astype(np.float32)[None, ...]

        # Safety: target cannot be positive outside the valid region.
        gt *= valid

        return {
            "features": torch.from_numpy(x),
            "gt": torch.from_numpy(gt),
            "valid": torch.from_numpy(valid),
            "key": r.key,
        }


def make_loader(
    dataset: Dataset,
    *,
    shuffle: bool,
    device: torch.device,
) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=shuffle,
        num_workers=NUM_WORKERS,
        pin_memory=(PIN_MEMORY and device.type == "cuda"),
        drop_last=False,
        persistent_workers=(NUM_WORKERS > 0),
    )


# =============================================================================
# METRICS
# =============================================================================

@dataclass
class SegmentationAccumulator:
    threshold: float = 0.5
    tp: float = 0.0
    fp: float = 0.0
    fn: float = 0.0
    tn: float = 0.0

    @torch.no_grad()
    def update(
        self,
        logits: torch.Tensor,
        target: torch.Tensor,
        valid: torch.Tensor,
    ) -> None:
        pred = torch.sigmoid(logits) >= self.threshold
        target_b = target >= 0.5
        valid_b = valid >= 0.5

        pred = pred & valid_b
        target_b = target_b & valid_b

        self.tp += float((pred & target_b).sum().item())
        self.fp += float((pred & (~target_b) & valid_b).sum().item())
        self.fn += float(((~pred) & target_b & valid_b).sum().item())
        self.tn += float(((~pred) & (~target_b) & valid_b).sum().item())

    def compute(self) -> Dict[str, float]:
        eps = 1e-9
        dice = (2.0 * self.tp) / (2.0 * self.tp + self.fp + self.fn + eps)
        iou = self.tp / (self.tp + self.fp + self.fn + eps)
        precision = self.tp / (self.tp + self.fp + eps)
        recall = self.tp / (self.tp + self.fn + eps)
        accuracy = (self.tp + self.tn) / (self.tp + self.fp + self.fn + self.tn + eps)

        return {
            "dice": dice,
            "iou": iou,
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
        }


# =============================================================================
# TRAIN / EVALUATE ONE EPOCH
# =============================================================================

def _autocast_context(device: torch.device, enabled: bool):
    if enabled and device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    return nullcontext()


def _make_grad_scaler(enabled: bool):
    """Compatible with both newer and older PyTorch APIs."""
    try:
        return torch.amp.GradScaler("cuda", enabled=enabled)
    except Exception:
        return torch.cuda.amp.GradScaler(enabled=enabled)


def train_one_epoch(
    model: EngineerMLP,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scaler,
    device: torch.device,
    amp_enabled: bool,
) -> Dict[str, float]:
    model.train()

    metrics = SegmentationAccumulator(threshold=PREDICTION_THRESHOLD)
    total_loss = 0.0
    total_fine_bce = 0.0
    total_fine_dice = 0.0
    total_coarse_bce = 0.0
    total_coarse_dice = 0.0
    sample_count = 0

    for batch in loader:
        features = batch["features"].to(device, non_blocking=True)
        gt = batch["gt"].to(device, non_blocking=True)
        valid = batch["valid"].to(device, non_blocking=True)
        bs = features.shape[0]

        optimizer.zero_grad(set_to_none=True)

        with _autocast_context(device, amp_enabled):
            outputs = model(features, return_intermediates=True)
            loss, parts = engineer_loss(
                outputs,
                gt_mask_64=gt,
                valid_mask_64=valid,
                dice_weight=DICE_WEIGHT,
                coarse_weight=COARSE_WEIGHT,
            )

        scaler.scale(loss).backward()

        if GRAD_CLIP_NORM is not None and GRAD_CLIP_NORM > 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP_NORM)

        scaler.step(optimizer)
        scaler.update()

        metrics.update(outputs["logits"].detach(), gt, valid)

        total_loss += float(loss.detach().item()) * bs
        total_fine_bce += float(parts["fine_bce"].item()) * bs
        total_fine_dice += float(parts["fine_dice"].item()) * bs
        total_coarse_bce += float(parts["coarse_bce"].item()) * bs
        total_coarse_dice += float(parts["coarse_dice"].item()) * bs
        sample_count += bs

    result = metrics.compute()
    denom = max(sample_count, 1)
    result.update(
        {
            "loss": total_loss / denom,
            "fine_bce": total_fine_bce / denom,
            "fine_dice_loss": total_fine_dice / denom,
            "coarse_bce": total_coarse_bce / denom,
            "coarse_dice_loss": total_coarse_dice / denom,
        }
    )
    return result


@torch.no_grad()
def evaluate(
    model: EngineerMLP,
    loader: DataLoader,
    device: torch.device,
    amp_enabled: bool,
) -> Dict[str, float]:
    model.eval()

    metrics = SegmentationAccumulator(threshold=PREDICTION_THRESHOLD)
    total_loss = 0.0
    total_fine_bce = 0.0
    total_fine_dice = 0.0
    total_coarse_bce = 0.0
    total_coarse_dice = 0.0
    sample_count = 0

    for batch in loader:
        features = batch["features"].to(device, non_blocking=True)
        gt = batch["gt"].to(device, non_blocking=True)
        valid = batch["valid"].to(device, non_blocking=True)
        bs = features.shape[0]

        with _autocast_context(device, amp_enabled):
            outputs = model(features, return_intermediates=True)
            loss, parts = engineer_loss(
                outputs,
                gt_mask_64=gt,
                valid_mask_64=valid,
                dice_weight=DICE_WEIGHT,
                coarse_weight=COARSE_WEIGHT,
            )

        metrics.update(outputs["logits"], gt, valid)

        total_loss += float(loss.item()) * bs
        total_fine_bce += float(parts["fine_bce"].item()) * bs
        total_fine_dice += float(parts["fine_dice"].item()) * bs
        total_coarse_bce += float(parts["coarse_bce"].item()) * bs
        total_coarse_dice += float(parts["coarse_dice"].item()) * bs
        sample_count += bs

    result = metrics.compute()
    denom = max(sample_count, 1)
    result.update(
        {
            "loss": total_loss / denom,
            "fine_bce": total_fine_bce / denom,
            "fine_dice_loss": total_fine_dice / denom,
            "coarse_bce": total_coarse_bce / denom,
            "coarse_dice_loss": total_coarse_dice / denom,
        }
    )
    return result


# =============================================================================
# CHECKPOINT / HISTORY
# =============================================================================

def save_checkpoint(
    path: Path,
    *,
    model: EngineerMLP,
    optimizer: torch.optim.Optimizer,
    scheduler,
    epoch: int,
    best_val_dice: float,
    standardizer: FeatureStandardizer,
    metrics: Dict[str, float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict() if scheduler is not None else None,
            "best_val_dice": best_val_dice,
            "metrics": metrics,
            "model_config": asdict(MODEL_CFG),
            "feature_dim": TOTAL_FEATURE_DIM,
            "feature_names": FEATURE_NAMES,
            "standardizer_mean": standardizer.mean,
            "standardizer_std": standardizer.std,
            "prediction_threshold": PREDICTION_THRESHOLD,
        },
        path,
    )


def append_history_row(path: Path, row: Dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


# =============================================================================
# MAIN TRAINING PROGRAM
# =============================================================================

def main() -> None:
    seed_everything(RANDOM_SEED)
    device = choose_device()
    amp_enabled = bool(USE_AMP and device.type == "cuda")

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("Engineer MLP 1108D training")
    print("=" * 78)
    print(f"Device          : {device}")
    print(f"AMP             : {amp_enabled}")
    print(f"Station root    : {STATION_ROOT.resolve()}")
    print(f"Run directory   : {RUN_DIR.resolve()}")
    print()

    # Save the full experiment configuration for reproducibility.
    config_dump = {
        "station_root": str(STATION_ROOT),
        "image_dir": str(IMAGE_DIR),
        "gt_mask_dir": str(GT_MASK_DIR),
        "valid_mask_dir": str(VALID_MASK_DIR),
        "meta_dir": str(META_DIR),
        "feature_cache_dir": str(FEATURE_CACHE_DIR),
        "train_ratio": TRAIN_RATIO,
        "val_ratio": VAL_RATIO,
        "test_ratio": TEST_RATIO,
        "seed": RANDOM_SEED,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "dice_weight": DICE_WEIGHT,
        "coarse_weight": COARSE_WEIGHT,
        "prediction_threshold": PREDICTION_THRESHOLD,
        "model_config": asdict(MODEL_CFG),
    }
    (RUN_DIR / "run_config.json").write_text(
        json.dumps(config_dump, indent=2),
        encoding="utf-8",
    )

    # 1) Discover and cache deterministic features.
    records = discover_records()
    build_or_validate_feature_cache(records)

    # 2) Group-aware split BEFORE fitting normalization.
    train_records, val_records, test_records = split_records_by_group(records)
    save_split_manifest(train_records, val_records, test_records)

    # 3) Fit standardizer using TRAIN ONLY.
    standardizer = fit_standardizer(train_records)

    # 4) PyTorch datasets/loaders.
    train_ds = EngineerStationDataset(train_records, standardizer)
    val_ds = EngineerStationDataset(val_records, standardizer)
    test_ds = EngineerStationDataset(test_records, standardizer)

    train_loader = make_loader(train_ds, shuffle=True, device=device)
    val_loader = make_loader(val_ds, shuffle=False, device=device)
    test_loader = make_loader(test_ds, shuffle=False, device=device)

    # 5) Model / optimizer / scheduler.
    model = EngineerMLP(MODEL_CFG).to(device)
    params = count_parameters(model)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=LR_REDUCE_FACTOR,
        patience=LR_PATIENCE,
        min_lr=MIN_LR,
    )

    scaler = _make_grad_scaler(amp_enabled)

    print()
    print(f"Model parameters : {params['total']:,}")
    print(f"Trainable        : {params['trainable']:,}")
    print(f"Train stations   : {len(train_ds)}")
    print(f"Val stations     : {len(val_ds)}")
    print(f"Test stations    : {len(test_ds)}")
    print()

    history_path = RUN_DIR / "history.csv"
    if history_path.exists():
        history_path.unlink()

    best_val_dice = -math.inf
    epochs_without_improvement = 0
    best_path = CHECKPOINT_DIR / "best.pt"
    last_path = CHECKPOINT_DIR / "last.pt"

    # 6) Training loop.
    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()

        train_metrics = train_one_epoch(
            model,
            train_loader,
            optimizer,
            scaler,
            device,
            amp_enabled,
        )

        val_metrics = evaluate(
            model,
            val_loader,
            device,
            amp_enabled,
        )

        scheduler.step(val_metrics["dice"])
        lr = float(optimizer.param_groups[0]["lr"])
        elapsed = time.time() - t0

        row = {
            "epoch": epoch,
            "lr": lr,
            "seconds": elapsed,
            **{f"train_{k}": v for k, v in train_metrics.items()},
            **{f"val_{k}": v for k, v in val_metrics.items()},
        }
        append_history_row(history_path, row)

        print(
            f"Epoch {epoch:03d}/{EPOCHS} | "
            f"lr={lr:.2e} | "
            f"train loss={train_metrics['loss']:.4f} dice={train_metrics['dice']:.4f} | "
            f"val loss={val_metrics['loss']:.4f} dice={val_metrics['dice']:.4f} "
            f"IoU={val_metrics['iou']:.4f} P={val_metrics['precision']:.4f} "
            f"R={val_metrics['recall']:.4f} | {elapsed:.1f}s"
        )

        improved = val_metrics["dice"] > best_val_dice + MIN_DICE_IMPROVEMENT

        if improved:
            best_val_dice = val_metrics["dice"]
            epochs_without_improvement = 0

            save_checkpoint(
                best_path,
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                epoch=epoch,
                best_val_dice=best_val_dice,
                standardizer=standardizer,
                metrics=val_metrics,
            )
            print(f"  [BEST] val Dice -> {best_val_dice:.6f}")
        else:
            epochs_without_improvement += 1

        if SAVE_LAST_EVERY > 0 and epoch % SAVE_LAST_EVERY == 0:
            save_checkpoint(
                last_path,
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                epoch=epoch,
                best_val_dice=best_val_dice,
                standardizer=standardizer,
                metrics=val_metrics,
            )

        if epochs_without_improvement >= EARLY_STOPPING_PATIENCE:
            print(
                f"[EARLY STOP] no validation Dice improvement for "
                f"{EARLY_STOPPING_PATIENCE} epochs."
            )
            break

    # 7) Final TEST evaluation using the BEST validation checkpoint.
    if not best_path.exists():
        raise RuntimeError("Training ended without producing best.pt")

    checkpoint = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_metrics = evaluate(model, test_loader, device, amp_enabled)

    print()
    print("=" * 78)
    print("BEST MODEL - TEST SET")
    print("=" * 78)
    print(f"Best epoch : {checkpoint['epoch']}")
    print(f"Val Dice   : {checkpoint['best_val_dice']:.6f}")
    print(f"Test loss  : {test_metrics['loss']:.6f}")
    print(f"Test Dice  : {test_metrics['dice']:.6f}")
    print(f"Test IoU   : {test_metrics['iou']:.6f}")
    print(f"Precision  : {test_metrics['precision']:.6f}")
    print(f"Recall     : {test_metrics['recall']:.6f}")
    print(f"Accuracy   : {test_metrics['accuracy']:.6f}")

    (RUN_DIR / "test_metrics.json").write_text(
        json.dumps(test_metrics, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Best checkpoint : {best_path.resolve()}")
    print(f"Standardizer    : {(RUN_DIR / 'standardizer.npz').resolve()}")
    print(f"History         : {history_path.resolve()}")
    print(f"Split manifest  : {(RUN_DIR / 'split_manifest.csv').resolve()}")


if __name__ == "__main__":
    main()