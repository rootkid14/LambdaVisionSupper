"""
Train Engineer Master Fusion V1
===============================

This script trains ONLY the Knowledge Master. The two existing Engineers are
loaded from their best checkpoints, switched to eval mode, and frozen.

Five Master streams
-------------------
Flow 1 - MLP telemetry concat [B,1728]
    The current e1108D MLP does not contain one native 1728D layer. To preserve
    the 1728D design while using the current production MLP, this script builds
    an explicit multi-checkpoint telemetry vector:

        specialized  [576]
      + holistic     [576]
      + refined      [512]
      + valid_embed   [64]
      ---------------------
        telemetry   [1728]

    This is deliberate: Flow 1 is a wide observation of several important MLP
    checkpoints rather than a new trainable MLP representation.

Flow 2 - MLP latent             [B,256]
Flow 3 - CNN bottleneck         [B,256,8,8]
Flow 4 - CNN D0 / decoder64     [B,32,64,64]
Flow 5 - disagreement           built from MLP/CNN logits + Valid

Final Master decision
---------------------
    Z_master = W_mlp * Z_mlp + W_cnn * Z_cnn + DeltaZ

where W_mlp + W_cnn = 1 and DeltaZ is bounded.

No command-line arguments are used. Edit CONFIG below.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import csv
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
    TOTAL_FEATURE_DIM,
    extract_feature_vector,
)

from e1108D_neural_network import (
    EngineerMLP,
    EngineerMLPConfig,
)

from engineer_cnn_u3 import (
    EngineerCNNU3,
    EngineerCNNU3Config,
)

from engineer_master_v1 import (
    EngineerMasterV1,
    EngineerMasterV1Config,
    count_parameters,
    engineer_master_v1_loss,
)


# =============================================================================
# CONFIG - EDIT HERE
# =============================================================================

# -----------------------------------------------------------------------------
# Dataset
# -----------------------------------------------------------------------------

DATASET_ROOT = Path(
    "/home/hieu/Desktop/Nidec Vision/stations_divided"
)

IMAGE_DIR = DATASET_ROOT / "images"
GT_MASK_DIR = DATASET_ROOT / "masks"
VALID_MASK_DIR = DATASET_ROOT / "valid"
META_DIR = DATASET_ROOT / "meta"

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
}

# -----------------------------------------------------------------------------
# Frozen Engineer checkpoints
# -----------------------------------------------------------------------------

RUN_ROOT = Path(
    "/home/hieu/Desktop/Nidec Vision/run"
)

MLP_CHECKPOINT_PATH = (
    RUN_ROOT
    / "engineer_mlp_1108_v1"
    / "checkpoints"
    / "best.pt"
)

CNN_CHECKPOINT_PATH = (
    RUN_ROOT
    / "engineer_cnn_u3_v1"
    / "checkpoints"
    / "best.pt"
)

# -----------------------------------------------------------------------------
# Master output
# -----------------------------------------------------------------------------

RUN_NAME = "engineer_master_v1"
RUN_DIR = RUN_ROOT / RUN_NAME
CHECKPOINT_DIR = RUN_DIR / "checkpoints"
HISTORY_PATH = RUN_DIR / "history.csv"

# Deterministic e1108D extraction is expensive. Cache RAW 1108D vectors once.
FEATURE_CACHE_DIR = RUN_DIR / "feature_cache_1108"
REBUILD_FEATURE_CACHE = False

# -----------------------------------------------------------------------------
# Split
# -----------------------------------------------------------------------------

# Reuse the same station split as the production MLP/CNN whenever possible.
REFERENCE_SPLIT_MANIFEST = (
    RUN_ROOT
    / "engineer_mlp_1108_v1"
    / "split_manifest.csv"
)

USE_REFERENCE_SPLIT_IF_AVAILABLE = True
STRICT_REFERENCE_SPLIT = True

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10
RANDOM_SEED = 20260820
STRICT_GROUP_SPLIT = False

# -----------------------------------------------------------------------------
# Training
# -----------------------------------------------------------------------------

EPOCHS = 150
BATCH_SIZE = 64
NUM_WORKERS = 0
PIN_MEMORY = True

LEARNING_RATE = 3e-4
WEIGHT_DECAY = 1e-4
GRAD_CLIP_NORM = 1.0

PREDICTION_THRESHOLD = 0.50

LR_REDUCE_FACTOR = 0.5
LR_PATIENCE = 6
MIN_LR = 1e-6

EARLY_STOPPING_PATIENCE = 40
MIN_DICE_IMPROVEMENT = 1e-4

USE_AMP = True

# Loss
DICE_WEIGHT = 1.0
RESIDUAL_PENALTY_WEIGHT = 0.01
GATE_SUPERVISION_WEIGHT = 0.05
GATE_TARGET_TEMPERATURE = 0.15

# If CUDA OOM occurs, reduce BATCH_SIZE to 32 before changing architecture.

# -----------------------------------------------------------------------------
# Master architecture
# -----------------------------------------------------------------------------

MASTER_CFG = EngineerMasterV1Config(
    mlp_concat_dim=1728,
    mlp_latent_dim=256,
    residual_logit_max=2.0,
    logit_diff_scale=4.0,
    dropout=0.0,

    dice_weight=DICE_WEIGHT,
    residual_penalty_weight=RESIDUAL_PENALTY_WEIGHT,
    gate_supervision_weight=GATE_SUPERVISION_WEIGHT,
    gate_target_temperature=GATE_TARGET_TEMPERATURE,
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


def choose_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")


def make_grad_scaler(enabled: bool):
    try:
        return torch.amp.GradScaler(
            "cuda",
            enabled=enabled,
        )
    except (AttributeError, TypeError):
        return torch.cuda.amp.GradScaler(
            enabled=enabled,
        )


def safe_torch_load(
    path: Path,
    device: torch.device,
):
    try:
        return torch.load(
            path,
            map_location=device,
            weights_only=False,
        )
    except TypeError:
        return torch.load(
            path,
            map_location=device,
        )


# =============================================================================
# RECORD DISCOVERY
# =============================================================================

@dataclass
class StationRecord:
    key: str
    image_path: Path
    gt_path: Path
    valid_path: Path
    meta_path: Optional[Path]
    source_group: str


def _find_same_relative(
    root: Path,
    relative_path: Path,
) -> Optional[Path]:
    exact = root / relative_path

    if exact.exists():
        return exact

    parent = root / relative_path.parent

    if not parent.exists():
        return None

    for ext in IMAGE_EXTENSIONS:
        candidate = parent / f"{relative_path.stem}{ext}"
        if candidate.exists():
            return candidate

    return None


def _load_json(path: Optional[Path]) -> Dict:
    if path is None or not path.exists():
        return {}

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception:
        return {}


def _strip_station_suffix(stem: str) -> str:
    patterns = [
        r"(?i)(?:[_-]station[_-]?\d+)$",
        r"(?i)(?:[_-]st[_-]?\d+)$",
        r"(?i)(?:[_-]s[_-]?\d+)$",
    ]

    for pattern in patterns:
        stripped = re.sub(pattern, "", stem)
        if stripped != stem:
            return stripped

    return stem


def _infer_source_group(
    relative_image: Path,
    metadata: Dict,
) -> Tuple[str, bool]:
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

    stripped = _strip_station_suffix(
        relative_image.stem
    )

    if stripped != relative_image.stem:
        return (
            (relative_image.parent / stripped).as_posix(),
            True,
        )

    if relative_image.parent != Path("."):
        return relative_image.parent.as_posix(), True

    return relative_image.with_suffix("").as_posix(), False


def discover_records() -> List[StationRecord]:
    for name, path in (
        ("IMAGE_DIR", IMAGE_DIR),
        ("GT_MASK_DIR", GT_MASK_DIR),
        ("VALID_MASK_DIR", VALID_MASK_DIR),
    ):
        if not path.exists():
            raise FileNotFoundError(
                f"{name} does not exist: {path.resolve()}"
            )

    image_paths = sorted(
        p
        for p in IMAGE_DIR.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_paths:
        raise RuntimeError(
            f"No station images found under {IMAGE_DIR.resolve()}"
        )

    records: List[StationRecord] = []
    skipped = 0
    unreliable = 0

    for image_path in image_paths:
        rel = image_path.relative_to(IMAGE_DIR)

        gt_path = _find_same_relative(
            GT_MASK_DIR,
            rel,
        )
        valid_path = _find_same_relative(
            VALID_MASK_DIR,
            rel,
        )

        if gt_path is None or valid_path is None:
            print(
                f"[SKIP] {rel}: "
                f"GT={'OK' if gt_path else 'MISSING'} "
                f"VALID={'OK' if valid_path else 'MISSING'}"
            )
            skipped += 1
            continue

        meta_candidate = META_DIR / rel.with_suffix(".json")
        meta_path = (
            meta_candidate
            if meta_candidate.exists()
            else None
        )

        metadata = _load_json(meta_path)
        source_group, reliable = _infer_source_group(
            rel,
            metadata,
        )

        if not reliable:
            unreliable += 1
            if STRICT_GROUP_SPLIT:
                raise RuntimeError(
                    "Cannot infer reliable source group for "
                    f"{rel}."
                )

        records.append(
            StationRecord(
                key=rel.with_suffix("").as_posix(),
                image_path=image_path,
                gt_path=gt_path,
                valid_path=valid_path,
                meta_path=meta_path,
                source_group=source_group,
            )
        )

    if not records:
        raise RuntimeError(
            "No complete image/GT/valid station triplets found."
        )

    print(f"[DATA] discovered stations : {len(records)}")
    print(f"[DATA] skipped incomplete  : {skipped}")
    print(f"[DATA] unreliable grouping : {unreliable}")

    return records


# =============================================================================
# SPLIT
# =============================================================================

def split_records_by_group(
    records: Sequence[StationRecord],
) -> Tuple[
    List[StationRecord],
    List[StationRecord],
    List[StationRecord],
]:
    total_ratio = TRAIN_RATIO + VAL_RATIO + TEST_RATIO
    if abs(total_ratio - 1.0) > 1e-8:
        raise ValueError(
            "TRAIN_RATIO + VAL_RATIO + TEST_RATIO must equal 1.0"
        )

    groups: Dict[str, List[StationRecord]] = {}
    for r in records:
        groups.setdefault(r.source_group, []).append(r)

    group_names = sorted(groups.keys())
    if len(group_names) < 3:
        raise RuntimeError(
            f"Need >= 3 source groups, found {len(group_names)}"
        )

    rng = random.Random(RANDOM_SEED)
    rng.shuffle(group_names)

    n_groups = len(group_names)
    n_train = max(1, int(round(n_groups * TRAIN_RATIO)))
    n_val = max(1, int(round(n_groups * VAL_RATIO)))

    if n_train + n_val >= n_groups:
        overflow = n_train + n_val - (n_groups - 1)
        if n_train >= n_val and n_train - overflow >= 1:
            n_train -= overflow
        else:
            n_val = max(1, n_val - overflow)

    train_groups = set(group_names[:n_train])
    val_groups = set(group_names[n_train:n_train + n_val])
    test_groups = set(group_names[n_train + n_val:])

    assert train_groups.isdisjoint(val_groups)
    assert train_groups.isdisjoint(test_groups)
    assert val_groups.isdisjoint(test_groups)

    train = [r for r in records if r.source_group in train_groups]
    val = [r for r in records if r.source_group in val_groups]
    test = [r for r in records if r.source_group in test_groups]

    if not train or not val or not test:
        raise RuntimeError("Group split produced an empty split.")

    return train, val, test


def split_records_from_reference_manifest(
    records: Sequence[StationRecord],
    manifest_path: Path,
) -> Tuple[
    List[StationRecord],
    List[StationRecord],
    List[StationRecord],
]:
    mapping: Dict[str, str] = {}

    with manifest_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        required = {"split", "station_key"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError(
                f"Reference manifest {manifest_path} lacks split/station_key."
            )

        for row in reader:
            key = row["station_key"]
            split = row["split"].strip().lower()

            if split not in {"train", "val", "test"}:
                raise RuntimeError(
                    f"Invalid split {split!r} for {key!r}"
                )

            if key in mapping:
                raise RuntimeError(
                    f"Duplicate station_key in reference: {key}"
                )

            mapping[key] = split

    current_keys = {r.key for r in records}
    reference_keys = set(mapping.keys())

    missing = current_keys - reference_keys
    stale = reference_keys - current_keys

    if missing or stale:
        message = (
            "Reference split does not exactly match dataset. "
            f"missing={len(missing)} stale={len(stale)}"
        )

        if STRICT_REFERENCE_SPLIT:
            raise RuntimeError(message)

        print(f"[WARN] {message}")
        return split_records_by_group(records)

    train = [r for r in records if mapping[r.key] == "train"]
    val = [r for r in records if mapping[r.key] == "val"]
    test = [r for r in records if mapping[r.key] == "test"]

    train_groups = {r.source_group for r in train}
    val_groups = {r.source_group for r in val}
    test_groups = {r.source_group for r in test}

    if (
        not train_groups.isdisjoint(val_groups)
        or not train_groups.isdisjoint(test_groups)
        or not val_groups.isdisjoint(test_groups)
    ):
        raise RuntimeError(
            "Reference manifest causes source-group leakage."
        )

    return train, val, test


def choose_split(
    records: Sequence[StationRecord],
) -> Tuple[
    List[StationRecord],
    List[StationRecord],
    List[StationRecord],
    str,
]:
    if (
        USE_REFERENCE_SPLIT_IF_AVAILABLE
        and REFERENCE_SPLIT_MANIFEST.exists()
    ):
        print(
            f"[SPLIT] Reusing: {REFERENCE_SPLIT_MANIFEST.resolve()}"
        )
        train, val, test = split_records_from_reference_manifest(
            records,
            REFERENCE_SPLIT_MANIFEST,
        )
        source = str(REFERENCE_SPLIT_MANIFEST.resolve())
    else:
        if USE_REFERENCE_SPLIT_IF_AVAILABLE:
            print(
                "[SPLIT] Reference manifest not found; "
                "using group-aware deterministic split."
            )
        train, val, test = split_records_by_group(records)
        source = "deterministic_group_split"

    print("[SPLIT]")
    print(
        f"  train : {len(train):6d} stations / "
        f"{len({r.source_group for r in train}):4d} groups"
    )
    print(
        f"  val   : {len(val):6d} stations / "
        f"{len({r.source_group for r in val}):4d} groups"
    )
    print(
        f"  test  : {len(test):6d} stations / "
        f"{len({r.source_group for r in test}):4d} groups"
    )

    return train, val, test, source


def save_split_manifest(
    train: Sequence[StationRecord],
    val: Sequence[StationRecord],
    test: Sequence[StationRecord],
) -> None:
    rows = []

    for split_name, split_records in (
        ("train", train),
        ("val", val),
        ("test", test),
    ):
        for r in split_records:
            rows.append({
                "split": split_name,
                "station_key": r.key,
                "source_group": r.source_group,
                "image_path": str(r.image_path),
                "gt_path": str(r.gt_path),
                "valid_path": str(r.valid_path),
            })

    rows.sort(
        key=lambda x: (
            x["split"],
            x["source_group"],
            x["station_key"],
        )
    )

    path = RUN_DIR / "split_manifest.csv"
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


# =============================================================================
# FROZEN ENGINEER LOADING
# =============================================================================

def _config_from_checkpoint(
    raw_cfg: Optional[Dict],
    config_cls,
):
    if not raw_cfg:
        return config_cls()

    allowed = {f.name for f in fields(config_cls)}
    filtered = {
        k: v
        for k, v in raw_cfg.items()
        if k in allowed
    }
    return config_cls(**filtered)


def load_frozen_mlp(
    device: torch.device,
) -> Tuple[
    EngineerMLP,
    np.ndarray,
    np.ndarray,
    Dict,
]:
    if not MLP_CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"MLP checkpoint not found: {MLP_CHECKPOINT_PATH.resolve()}"
        )

    checkpoint = safe_torch_load(
        MLP_CHECKPOINT_PATH,
        device,
    )

    cfg = _config_from_checkpoint(
        checkpoint.get("model_config"),
        EngineerMLPConfig,
    )

    model = EngineerMLP(cfg)
    model.load_state_dict(
        checkpoint["model_state_dict"]
    )
    model.to(device)
    model.eval()

    for p in model.parameters():
        p.requires_grad_(False)

    mean = np.asarray(
        checkpoint["standardizer_mean"],
        dtype=np.float32,
    ).reshape(-1)

    std = np.asarray(
        checkpoint["standardizer_std"],
        dtype=np.float32,
    ).reshape(-1)

    if mean.shape != (TOTAL_FEATURE_DIM,):
        raise RuntimeError(
            f"MLP standardizer mean shape={mean.shape}"
        )

    if std.shape != (TOTAL_FEATURE_DIM,):
        raise RuntimeError(
            f"MLP standardizer std shape={std.shape}"
        )

    std = std.copy()
    std[np.abs(std) < 1e-12] = 1.0

    return model, mean, std, checkpoint


def load_frozen_cnn(
    device: torch.device,
) -> Tuple[
    EngineerCNNU3,
    np.ndarray,
    np.ndarray,
    Dict,
]:
    if not CNN_CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"CNN checkpoint not found: {CNN_CHECKPOINT_PATH.resolve()}"
        )

    checkpoint = safe_torch_load(
        CNN_CHECKPOINT_PATH,
        device,
    )

    cfg = _config_from_checkpoint(
        checkpoint.get("model_config"),
        EngineerCNNU3Config,
    )

    model = EngineerCNNU3(cfg)
    model.load_state_dict(
        checkpoint["model_state_dict"]
    )
    model.to(device)
    model.eval()

    for p in model.parameters():
        p.requires_grad_(False)

    rgb_mean = np.asarray(
        checkpoint["rgb_mean"],
        dtype=np.float32,
    ).reshape(-1)

    rgb_std = np.asarray(
        checkpoint["rgb_std"],
        dtype=np.float32,
    ).reshape(-1)

    if rgb_mean.shape != (3,) or rgb_std.shape != (3,):
        raise RuntimeError(
            "CNN checkpoint RGB mean/std must both be shape (3,)"
        )

    rgb_std = rgb_std.copy()
    rgb_std[np.abs(rgb_std) < 1e-12] = 1.0

    return model, rgb_mean, rgb_std, checkpoint


# =============================================================================
# IMAGE / FEATURE PREPROCESSING
# =============================================================================

def read_station_arrays(
    record: StationRecord,
) -> Tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Returns:
        image_bgr_u8 : [64,64,3]
        valid_bin    : [64,64] uint8 {0,1}
        gt_bin       : [64,64] uint8 {0,1}, clipped to valid
    """
    image = cv2.imread(
        str(record.image_path),
        cv2.IMREAD_COLOR,
    )
    gt = cv2.imread(
        str(record.gt_path),
        cv2.IMREAD_GRAYSCALE,
    )
    valid = cv2.imread(
        str(record.valid_path),
        cv2.IMREAD_GRAYSCALE,
    )

    if image is None:
        raise RuntimeError(
            f"Cannot read image: {record.image_path}"
        )
    if gt is None:
        raise RuntimeError(
            f"Cannot read GT: {record.gt_path}"
        )
    if valid is None:
        raise RuntimeError(
            f"Cannot read valid: {record.valid_path}"
        )

    if image.shape[:2] != (64, 64):
        image = cv2.resize(
            image,
            (64, 64),
            interpolation=cv2.INTER_AREA,
        )

    if gt.shape[:2] != (64, 64):
        gt = cv2.resize(
            gt,
            (64, 64),
            interpolation=cv2.INTER_NEAREST,
        )

    if valid.shape[:2] != (64, 64):
        valid = cv2.resize(
            valid,
            (64, 64),
            interpolation=cv2.INTER_NEAREST,
        )

    valid_bin = (valid > 0).astype(np.uint8)
    if not valid_bin.any():
        raise RuntimeError(
            f"Station has zero valid pixels: {record.image_path}"
        )

    gt_bin = (
        (gt > 0)
        & (valid_bin > 0)
    ).astype(np.uint8)

    return image, valid_bin, gt_bin


def neutral_fill_rgb(
    image_rgb_01: np.ndarray,
    valid_bin: np.ndarray,
) -> np.ndarray:
    valid_bool = valid_bin.astype(bool)

    fill = np.median(
        image_rgb_01[valid_bool],
        axis=0,
    ).astype(np.float32)

    out = image_rgb_01.copy()
    out[~valid_bool] = fill
    return out


def feature_cache_path(record: StationRecord) -> Path:
    return (
        FEATURE_CACHE_DIR
        / Path(record.key).with_suffix(".npy")
    )


def build_feature_cache(
    records: Sequence[StationRecord],
) -> None:
    FEATURE_CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    built = 0
    reused = 0
    t0 = time.time()

    for i, record in enumerate(records, start=1):
        path = feature_cache_path(record)

        if path.exists() and not REBUILD_FEATURE_CACHE:
            reused += 1
            continue

        image, valid, _ = read_station_arrays(record)

        feature = extract_feature_vector(
            image,
            valid,
            color_order="BGR",
        ).astype(np.float32)

        if feature.shape != (TOTAL_FEATURE_DIM,):
            raise RuntimeError(
                f"Extractor returned {feature.shape} for {record.key}"
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        np.save(path, feature)
        built += 1

        if i % 100 == 0 or i == len(records):
            print(
                f"[FEATURE CACHE] {i}/{len(records)} "
                f"built={built} reused={reused} "
                f"time={time.time()-t0:.1f}s"
            )

    print(
        f"[FEATURE CACHE] complete built={built} reused={reused}"
    )


# =============================================================================
# DATASET
# =============================================================================

class MasterStationDataset(Dataset):
    def __init__(
        self,
        records: Sequence[StationRecord],
        mlp_mean: np.ndarray,
        mlp_std: np.ndarray,
        cnn_rgb_mean: np.ndarray,
        cnn_rgb_std: np.ndarray,
    ):
        self.records = list(records)
        self.mlp_mean = mlp_mean.astype(np.float32)
        self.mlp_std = mlp_std.astype(np.float32)
        self.cnn_rgb_mean = cnn_rgb_mean.astype(np.float32)
        self.cnn_rgb_std = cnn_rgb_std.astype(np.float32)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        record = self.records[index]
        image_bgr, valid, gt = read_station_arrays(record)

        # MLP branch ----------------------------------------------------------
        cp = feature_cache_path(record)
        if cp.exists():
            raw_feature = np.load(cp).astype(np.float32)
        else:
            raw_feature = extract_feature_vector(
                image_bgr,
                valid,
                color_order="BGR",
            ).astype(np.float32)

        mlp_feature = (
            raw_feature - self.mlp_mean
        ) / self.mlp_std

        if not np.isfinite(mlp_feature).all():
            raise RuntimeError(
                f"Non-finite MLP feature: {record.key}"
            )

        # CNN branch ----------------------------------------------------------
        image_rgb = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2RGB,
        ).astype(np.float32) / 255.0

        image_rgb = neutral_fill_rgb(
            image_rgb,
            valid,
        )

        image_rgb = (
            image_rgb
            - self.cnn_rgb_mean[None, None, :]
        ) / self.cnn_rgb_std[None, None, :]

        rgb_chw = np.transpose(
            image_rgb,
            (2, 0, 1),
        ).astype(np.float32)

        valid_chw = valid.astype(np.float32)[None, ...]
        cnn_input = np.concatenate(
            [rgb_chw, valid_chw],
            axis=0,
        ).astype(np.float32)

        gt_chw = gt.astype(np.float32)[None, ...]

        return {
            "mlp_input": torch.from_numpy(mlp_feature),
            "cnn_input": torch.from_numpy(cnn_input),
            "gt": torch.from_numpy(gt_chw),
            "valid": torch.from_numpy(valid_chw),
            "key": record.key,
        }


# =============================================================================
# FIVE-STREAM EXTRACTION FROM FROZEN ENGINEERS
# =============================================================================

@torch.no_grad()
def extract_frozen_engineer_states(
    mlp_model: EngineerMLP,
    cnn_model: EngineerCNNU3,
    mlp_input: torch.Tensor,
    cnn_input: torch.Tensor,
) -> Dict[str, torch.Tensor]:
    """
    Build the exact five-stream inputs used by EngineerMasterV1.

    Flow 1 is a 1728D telemetry concat from CURRENT e1108D MLP checkpoints:
        specialized 576 + holistic 576 + refined 512 + valid_embed 64 = 1728.
    """
    mlp_out = mlp_model(
        mlp_input,
        return_intermediates=True,
    )

    cnn_out = cnn_model(
        cnn_input,
        return_intermediates=True,
    )

    # Explicit valid-family embedding from the frozen MLP.
    split = mlp_model.split_features(mlp_input)
    valid_embed = mlp_model.valid_encoder(
        split["valid"]
    )

    mlp_concat_1728 = torch.cat(
        [
            mlp_out["specialized"],  # 576
            mlp_out["holistic"],     # 576
            mlp_out["refined"],      # 512
            valid_embed,              #  64
        ],
        dim=1,
    )

    if mlp_concat_1728.shape[1] != MASTER_CFG.mlp_concat_dim:
        raise RuntimeError(
            "MLP telemetry concat mismatch: "
            f"got {mlp_concat_1728.shape[1]}, "
            f"expected {MASTER_CFG.mlp_concat_dim}."
        )

    return {
        "mlp_concat": mlp_concat_1728.detach(),
        "mlp_latent": mlp_out["latent"].detach(),
        "cnn_bottleneck": cnn_out["bottleneck"].detach(),
        "cnn_d0": cnn_out["decoder64"].detach(),
        "mlp_logits": mlp_out["logits"].detach(),
        "cnn_logits": cnn_out["logits"].detach(),
    }


# =============================================================================
# METRICS
# =============================================================================

class SegmentationAccumulator:
    def __init__(self, threshold: float = 0.5):
        self.threshold = float(threshold)
        self.tp = 0.0
        self.fp = 0.0
        self.fn = 0.0
        self.tn = 0.0

    @torch.no_grad()
    def update(
        self,
        logits: torch.Tensor,
        target: torch.Tensor,
        valid: torch.Tensor,
    ) -> None:
        prob = torch.sigmoid(logits)
        pred = prob >= self.threshold
        target_b = target >= 0.5
        valid_b = valid >= 0.5

        self.tp += float(
            (pred & target_b & valid_b).sum().item()
        )
        self.fp += float(
            (pred & ~target_b & valid_b).sum().item()
        )
        self.fn += float(
            (~pred & target_b & valid_b).sum().item()
        )
        self.tn += float(
            (~pred & ~target_b & valid_b).sum().item()
        )

    def compute(self) -> Dict[str, float]:
        eps = 1e-12
        tp, fp, fn, tn = self.tp, self.fp, self.fn, self.tn

        dice = (2 * tp) / (2 * tp + fp + fn + eps)
        iou = tp / (tp + fp + fn + eps)
        precision = tp / (tp + fp + eps)
        recall = tp / (tp + fn + eps)
        accuracy = (tp + tn) / (tp + fp + fn + tn + eps)

        return {
            "dice": dice,
            "iou": iou,
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
        }


class TelemetryAccumulator:
    def __init__(self):
        self.valid_pixels = 0.0
        self.mlp_weight_sum = 0.0
        self.cnn_weight_sum = 0.0
        self.residual_sq_sum = 0.0
        self.disagreement_sum = 0.0

    @torch.no_grad()
    def update(
        self,
        outputs: Dict[str, torch.Tensor],
        valid: torch.Tensor,
    ) -> None:
        v = valid.float()
        n = float(v.sum().item())
        if n <= 0:
            return

        self.valid_pixels += n
        self.mlp_weight_sum += float(
            (outputs["mlp_weight"] * v).sum().item()
        )
        self.cnn_weight_sum += float(
            (outputs["cnn_weight"] * v).sum().item()
        )
        self.residual_sq_sum += float(
            (
                outputs["residual_logits"]
                * outputs["residual_logits"]
                * v
            ).sum().item()
        )
        self.disagreement_sum += float(
            (
                outputs["probability_disagreement"]
                * v
            ).sum().item()
        )

    def compute(self) -> Dict[str, float]:
        n = max(self.valid_pixels, 1e-12)
        return {
            "mlp_reliance": self.mlp_weight_sum / n,
            "cnn_reliance": self.cnn_weight_sum / n,
            "residual_rms": math.sqrt(self.residual_sq_sum / n),
            "mean_disagreement": self.disagreement_sum / n,
        }


# =============================================================================
# TRAIN / EVAL
# =============================================================================

def move_batch(
    batch: Dict,
    device: torch.device,
) -> Dict[str, torch.Tensor]:
    return {
        "mlp_input": batch["mlp_input"].to(
            device,
            non_blocking=True,
        ),
        "cnn_input": batch["cnn_input"].to(
            device,
            non_blocking=True,
        ),
        "gt": batch["gt"].to(
            device,
            non_blocking=True,
        ),
        "valid": batch["valid"].to(
            device,
            non_blocking=True,
        ),
    }


def forward_master(
    master: EngineerMasterV1,
    mlp_model: EngineerMLP,
    cnn_model: EngineerCNNU3,
    batch: Dict[str, torch.Tensor],
) -> Dict[str, torch.Tensor]:
    states = extract_frozen_engineer_states(
        mlp_model,
        cnn_model,
        batch["mlp_input"],
        batch["cnn_input"],
    )

    return master(
        mlp_concat=states["mlp_concat"],
        mlp_latent=states["mlp_latent"],
        cnn_bottleneck=states["cnn_bottleneck"],
        cnn_d0=states["cnn_d0"],
        mlp_logits=states["mlp_logits"],
        cnn_logits=states["cnn_logits"],
        valid=batch["valid"],
        return_intermediates=True,
    )


def train_one_epoch(
    *,
    master: EngineerMasterV1,
    mlp_model: EngineerMLP,
    cnn_model: EngineerCNNU3,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scaler,
    device: torch.device,
    amp_enabled: bool,
) -> Dict[str, float]:
    master.train()
    mlp_model.eval()
    cnn_model.eval()

    metrics = SegmentationAccumulator(
        PREDICTION_THRESHOLD
    )
    telemetry = TelemetryAccumulator()

    loss_sum = 0.0
    bce_sum = 0.0
    dice_loss_sum = 0.0
    residual_loss_sum = 0.0
    gate_loss_sum = 0.0
    batches = 0

    for batch in loader:
        b = move_batch(batch, device)

        optimizer.zero_grad(set_to_none=True)

        with torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
            enabled=amp_enabled,
        ):
            outputs = forward_master(
                master,
                mlp_model,
                cnn_model,
                b,
            )

            loss, parts = engineer_master_v1_loss(
                outputs,
                b["gt"],
                b["valid"],
                dice_weight=DICE_WEIGHT,
                residual_penalty_weight=RESIDUAL_PENALTY_WEIGHT,
                gate_supervision_weight=GATE_SUPERVISION_WEIGHT,
                gate_target_temperature=GATE_TARGET_TEMPERATURE,
            )

        scaler.scale(loss).backward()

        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(
            master.parameters(),
            GRAD_CLIP_NORM,
        )

        scaler.step(optimizer)
        scaler.update()

        metrics.update(
            outputs["logits"].detach(),
            b["gt"],
            b["valid"],
        )
        telemetry.update(outputs, b["valid"])

        loss_sum += float(loss.detach().item())
        bce_sum += float(parts["bce"].item())
        dice_loss_sum += float(parts["dice_loss"].item())
        residual_loss_sum += float(parts["residual_penalty"].item())
        gate_loss_sum += float(parts["gate_loss"].item())
        batches += 1

    result = metrics.compute()
    result.update(telemetry.compute())

    d = max(batches, 1)
    result.update({
        "loss": loss_sum / d,
        "bce": bce_sum / d,
        "dice_loss": dice_loss_sum / d,
        "residual_penalty": residual_loss_sum / d,
        "gate_loss": gate_loss_sum / d,
    })

    return result


@torch.no_grad()
def evaluate(
    *,
    master: EngineerMasterV1,
    mlp_model: EngineerMLP,
    cnn_model: EngineerCNNU3,
    loader: DataLoader,
    device: torch.device,
    amp_enabled: bool,
) -> Dict[str, float]:
    master.eval()
    mlp_model.eval()
    cnn_model.eval()

    master_metrics = SegmentationAccumulator(PREDICTION_THRESHOLD)
    mlp_metrics = SegmentationAccumulator(PREDICTION_THRESHOLD)
    cnn_metrics = SegmentationAccumulator(PREDICTION_THRESHOLD)
    avg_metrics = SegmentationAccumulator(PREDICTION_THRESHOLD)
    telemetry = TelemetryAccumulator()

    loss_sum = 0.0
    bce_sum = 0.0
    dice_loss_sum = 0.0
    residual_loss_sum = 0.0
    gate_loss_sum = 0.0
    batches = 0

    for batch in loader:
        b = move_batch(batch, device)

        with torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
            enabled=amp_enabled,
        ):
            states = extract_frozen_engineer_states(
                mlp_model,
                cnn_model,
                b["mlp_input"],
                b["cnn_input"],
            )

            outputs = master(
                mlp_concat=states["mlp_concat"],
                mlp_latent=states["mlp_latent"],
                cnn_bottleneck=states["cnn_bottleneck"],
                cnn_d0=states["cnn_d0"],
                mlp_logits=states["mlp_logits"],
                cnn_logits=states["cnn_logits"],
                valid=b["valid"],
                return_intermediates=True,
            )

            loss, parts = engineer_master_v1_loss(
                outputs,
                b["gt"],
                b["valid"],
                dice_weight=DICE_WEIGHT,
                residual_penalty_weight=RESIDUAL_PENALTY_WEIGHT,
                gate_supervision_weight=GATE_SUPERVISION_WEIGHT,
                gate_target_temperature=GATE_TARGET_TEMPERATURE,
            )

        master_metrics.update(
            outputs["logits"],
            b["gt"],
            b["valid"],
        )
        mlp_metrics.update(
            states["mlp_logits"],
            b["gt"],
            b["valid"],
        )
        cnn_metrics.update(
            states["cnn_logits"],
            b["gt"],
            b["valid"],
        )

        avg_logits = 0.5 * (
            states["mlp_logits"]
            + states["cnn_logits"]
        )
        avg_metrics.update(
            avg_logits,
            b["gt"],
            b["valid"],
        )

        telemetry.update(outputs, b["valid"])

        loss_sum += float(loss.item())
        bce_sum += float(parts["bce"].item())
        dice_loss_sum += float(parts["dice_loss"].item())
        residual_loss_sum += float(parts["residual_penalty"].item())
        gate_loss_sum += float(parts["gate_loss"].item())
        batches += 1

    out: Dict[str, float] = {}

    for prefix, acc in (
        ("master", master_metrics),
        ("mlp", mlp_metrics),
        ("cnn", cnn_metrics),
        ("avg", avg_metrics),
    ):
        for key, value in acc.compute().items():
            out[f"{prefix}_{key}"] = value

    out.update(telemetry.compute())

    d = max(batches, 1)
    out.update({
        "loss": loss_sum / d,
        "bce": bce_sum / d,
        "dice_loss": dice_loss_sum / d,
        "residual_penalty": residual_loss_sum / d,
        "gate_loss": gate_loss_sum / d,
    })

    return out


# =============================================================================
# CHECKPOINT / HISTORY
# =============================================================================

def save_checkpoint(
    path: Path,
    *,
    master: EngineerMasterV1,
    optimizer: torch.optim.Optimizer,
    scheduler,
    epoch: int,
    best_val_dice: float,
    metrics: Dict[str, float],
    mlp_checkpoint: Dict,
    cnn_checkpoint: Dict,
    split_source: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    torch.save({
        "epoch": epoch,
        "model_state_dict": master.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": (
            scheduler.state_dict()
            if scheduler is not None
            else None
        ),
        "best_val_dice": best_val_dice,
        "metrics": metrics,
        "model_config": asdict(MASTER_CFG),
        "prediction_threshold": PREDICTION_THRESHOLD,

        "mlp_checkpoint_path": str(MLP_CHECKPOINT_PATH),
        "cnn_checkpoint_path": str(CNN_CHECKPOINT_PATH),
        "mlp_checkpoint_epoch": mlp_checkpoint.get("epoch"),
        "cnn_checkpoint_epoch": cnn_checkpoint.get("epoch"),
        "mlp_checkpoint_best_val_dice": mlp_checkpoint.get("best_val_dice"),
        "cnn_checkpoint_best_val_dice": cnn_checkpoint.get("best_val_dice"),

        "flow1_definition": {
            "specialized": 576,
            "holistic": 576,
            "refined": 512,
            "valid_embedding": 64,
            "total": 1728,
        },
        "flow2_definition": "mlp latent 256D",
        "flow3_definition": "cnn bottleneck [256,8,8]",
        "flow4_definition": "cnn decoder64/D0 [32,64,64]",
        "flow5_definition": "[|Pc-Pm|, tanh(|Zc-Zm|/scale), Valid]",

        "split_source": split_source,
    }, path)


def append_history_row(
    path: Path,
    row: Dict[str, float],
) -> None:
    exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(row.keys()),
        )

        if not exists:
            writer.writeheader()

        writer.writerow(row)


# =============================================================================
# INTEGRATION SANITY CHECK
# =============================================================================

@torch.no_grad()
def integration_sanity_check(
    master: EngineerMasterV1,
    mlp_model: EngineerMLP,
    cnn_model: EngineerCNNU3,
    loader: DataLoader,
    device: torch.device,
) -> None:
    batch = next(iter(loader))
    b = move_batch(batch, device)

    states = extract_frozen_engineer_states(
        mlp_model,
        cnn_model,
        b["mlp_input"],
        b["cnn_input"],
    )

    outputs = master(
        mlp_concat=states["mlp_concat"],
        mlp_latent=states["mlp_latent"],
        cnn_bottleneck=states["cnn_bottleneck"],
        cnn_d0=states["cnn_d0"],
        mlp_logits=states["mlp_logits"],
        cnn_logits=states["cnn_logits"],
        valid=b["valid"],
        return_intermediates=True,
    )

    print("[SANITY] five-stream shapes")
    print(f"  Flow1 MLP concat : {tuple(states['mlp_concat'].shape)}")
    print(f"  Flow2 MLP latent : {tuple(states['mlp_latent'].shape)}")
    print(f"  Flow3 bottleneck : {tuple(states['cnn_bottleneck'].shape)}")
    print(f"  Flow4 CNN D0     : {tuple(states['cnn_d0'].shape)}")
    print(f"  MLP logits       : {tuple(states['mlp_logits'].shape)}")
    print(f"  CNN logits       : {tuple(states['cnn_logits'].shape)}")
    print(f"  Master logits    : {tuple(outputs['logits'].shape)}")
    print(
        "  Gate sum error  : "
        f"{float(torch.max(torch.abs(outputs['mlp_weight'] + outputs['cnn_weight'] - 1.0))):.3e}"
    )


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    seed_everything(RANDOM_SEED)

    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass

    device = choose_device()
    amp_enabled = bool(
        USE_AMP and device.type == "cuda"
    )

    print("=" * 88)
    print("Engineer Master Fusion V1 - training")
    print("=" * 88)
    print(f"Device              : {device}")
    print(f"AMP                 : {amp_enabled}")
    print(f"Dataset             : {DATASET_ROOT.resolve()}")
    print(f"MLP checkpoint      : {MLP_CHECKPOINT_PATH.resolve()}")
    print(f"CNN checkpoint      : {CNN_CHECKPOINT_PATH.resolve()}")
    print(f"Run directory       : {RUN_DIR.resolve()}")
    print()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Load frozen Engineers
    # -------------------------------------------------------------------------
    (
        mlp_model,
        mlp_mean,
        mlp_std,
        mlp_checkpoint,
    ) = load_frozen_mlp(device)

    (
        cnn_model,
        cnn_rgb_mean,
        cnn_rgb_std,
        cnn_checkpoint,
    ) = load_frozen_cnn(device)

    print(
        f"Frozen MLP epoch    : {mlp_checkpoint.get('epoch', 'unknown')} "
        f"| best Dice={mlp_checkpoint.get('best_val_dice', 'unknown')}"
    )
    print(
        f"Frozen CNN epoch    : {cnn_checkpoint.get('epoch', 'unknown')} "
        f"| best Dice={cnn_checkpoint.get('best_val_dice', 'unknown')}"
    )
    print()

    # -------------------------------------------------------------------------
    # Data + split + raw feature cache
    # -------------------------------------------------------------------------
    records = discover_records()
    train_records, val_records, test_records, split_source = choose_split(
        records
    )
    save_split_manifest(
        train_records,
        val_records,
        test_records,
    )

    # Feature extraction is deterministic and frozen; cache all records once.
    build_feature_cache(records)

    train_ds = MasterStationDataset(
        train_records,
        mlp_mean,
        mlp_std,
        cnn_rgb_mean,
        cnn_rgb_std,
    )
    val_ds = MasterStationDataset(
        val_records,
        mlp_mean,
        mlp_std,
        cnn_rgb_mean,
        cnn_rgb_std,
    )
    test_ds = MasterStationDataset(
        test_records,
        mlp_mean,
        mlp_std,
        cnn_rgb_mean,
        cnn_rgb_std,
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=(PIN_MEMORY and device.type == "cuda"),
        drop_last=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=(PIN_MEMORY and device.type == "cuda"),
        drop_last=False,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=(PIN_MEMORY and device.type == "cuda"),
        drop_last=False,
    )

    # -------------------------------------------------------------------------
    # Master
    # -------------------------------------------------------------------------
    master = EngineerMasterV1(MASTER_CFG).to(device)
    params = count_parameters(master)

    print(f"Master parameters   : {params['total']:,}")
    print(f"Trainable parameters: {params['trainable']:,}")
    print()

    optimizer = torch.optim.AdamW(
        master.parameters(),
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

    scaler = make_grad_scaler(amp_enabled)

    # Save run configuration before training.
    run_config = {
        "master_config": asdict(MASTER_CFG),
        "dataset_root": str(DATASET_ROOT),
        "mlp_checkpoint": str(MLP_CHECKPOINT_PATH),
        "cnn_checkpoint": str(CNN_CHECKPOINT_PATH),
        "split_source": split_source,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "prediction_threshold": PREDICTION_THRESHOLD,
        "dice_weight": DICE_WEIGHT,
        "residual_penalty_weight": RESIDUAL_PENALTY_WEIGHT,
        "gate_supervision_weight": GATE_SUPERVISION_WEIGHT,
        "gate_target_temperature": GATE_TARGET_TEMPERATURE,
        "flow1_1728_composition": {
            "specialized": 576,
            "holistic": 576,
            "refined": 512,
            "valid_embedding": 64,
        },
    }

    (RUN_DIR / "run_config.json").write_text(
        json.dumps(run_config, indent=2),
        encoding="utf-8",
    )

    # Integration check with REAL dataset tensors before optimization.
    integration_sanity_check(
        master,
        mlp_model,
        cnn_model,
        val_loader,
        device,
    )
    print()

    best_path = CHECKPOINT_DIR / "best.pt"
    last_path = CHECKPOINT_DIR / "last.pt"

    best_val_dice = -float("inf")
    best_epoch = 0
    epochs_without_improvement = 0

    if HISTORY_PATH.exists():
        HISTORY_PATH.unlink()

    # -------------------------------------------------------------------------
    # Train
    # -------------------------------------------------------------------------
    for epoch in range(1, EPOCHS + 1):
        epoch_t0 = time.time()

        train_metrics = train_one_epoch(
            master=master,
            mlp_model=mlp_model,
            cnn_model=cnn_model,
            loader=train_loader,
            optimizer=optimizer,
            scaler=scaler,
            device=device,
            amp_enabled=amp_enabled,
        )

        val_metrics = evaluate(
            master=master,
            mlp_model=mlp_model,
            cnn_model=cnn_model,
            loader=val_loader,
            device=device,
            amp_enabled=amp_enabled,
        )

        val_dice = val_metrics["master_dice"]
        scheduler.step(val_dice)

        lr = optimizer.param_groups[0]["lr"]
        elapsed = time.time() - epoch_t0

        row = {
            "epoch": epoch,
            "lr": lr,

            "train_dice": train_metrics["dice"],
            "train_iou": train_metrics["iou"],
            "train_precision": train_metrics["precision"],
            "train_recall": train_metrics["recall"],
            "train_accuracy": train_metrics["accuracy"],
            "train_loss": train_metrics["loss"],
            "train_bce": train_metrics["bce"],
            "train_dice_loss": train_metrics["dice_loss"],
            "train_residual_penalty": train_metrics["residual_penalty"],
            "train_gate_loss": train_metrics["gate_loss"],
            "train_mlp_reliance": train_metrics["mlp_reliance"],
            "train_cnn_reliance": train_metrics["cnn_reliance"],
            "train_residual_rms": train_metrics["residual_rms"],
            "train_mean_disagreement": train_metrics["mean_disagreement"],

            "val_master_dice": val_metrics["master_dice"],
            "val_master_iou": val_metrics["master_iou"],
            "val_master_precision": val_metrics["master_precision"],
            "val_master_recall": val_metrics["master_recall"],
            "val_master_accuracy": val_metrics["master_accuracy"],

            "val_mlp_dice": val_metrics["mlp_dice"],
            "val_cnn_dice": val_metrics["cnn_dice"],
            "val_avg_dice": val_metrics["avg_dice"],

            "val_loss": val_metrics["loss"],
            "val_bce": val_metrics["bce"],
            "val_dice_loss": val_metrics["dice_loss"],
            "val_residual_penalty": val_metrics["residual_penalty"],
            "val_gate_loss": val_metrics["gate_loss"],

            "val_mlp_reliance": val_metrics["mlp_reliance"],
            "val_cnn_reliance": val_metrics["cnn_reliance"],
            "val_residual_rms": val_metrics["residual_rms"],
            "val_mean_disagreement": val_metrics["mean_disagreement"],

            "seconds": elapsed,
        }

        append_history_row(HISTORY_PATH, row)

        improved = (
            val_dice
            > best_val_dice + MIN_DICE_IMPROVEMENT
        )

        if improved:
            best_val_dice = val_dice
            best_epoch = epoch
            epochs_without_improvement = 0

            save_checkpoint(
                best_path,
                master=master,
                optimizer=optimizer,
                scheduler=scheduler,
                epoch=epoch,
                best_val_dice=best_val_dice,
                metrics=val_metrics,
                mlp_checkpoint=mlp_checkpoint,
                cnn_checkpoint=cnn_checkpoint,
                split_source=split_source,
            )
        else:
            epochs_without_improvement += 1

        save_checkpoint(
            last_path,
            master=master,
            optimizer=optimizer,
            scheduler=scheduler,
            epoch=epoch,
            best_val_dice=best_val_dice,
            metrics=val_metrics,
            mlp_checkpoint=mlp_checkpoint,
            cnn_checkpoint=cnn_checkpoint,
            split_source=split_source,
        )

        marker = " *BEST*" if improved else ""

        print(
            f"Epoch {epoch:03d} | "
            f"lr={lr:.2e} | "
            f"train D={train_metrics['dice']:.5f} | "
            f"val Master={val_metrics['master_dice']:.5f} "
            f"MLP={val_metrics['mlp_dice']:.5f} "
            f"CNN={val_metrics['cnn_dice']:.5f} "
            f"AVG={val_metrics['avg_dice']:.5f} | "
            f"R_mlp={val_metrics['mlp_reliance']:.3f} "
            f"R_cnn={val_metrics['cnn_reliance']:.3f} "
            f"dZrms={val_metrics['residual_rms']:.3f} | "
            f"{elapsed:.1f}s{marker}"
        )

        if epochs_without_improvement >= EARLY_STOPPING_PATIENCE:
            print(
                "[EARLY STOP] No validation Dice improvement for "
                f"{EARLY_STOPPING_PATIENCE} epochs."
            )
            break

    # -------------------------------------------------------------------------
    # Test best checkpoint
    # -------------------------------------------------------------------------
    if not best_path.exists():
        raise RuntimeError("best.pt was not created.")

    best_checkpoint = safe_torch_load(
        best_path,
        device,
    )

    master.load_state_dict(
        best_checkpoint["model_state_dict"]
    )

    test_metrics = evaluate(
        master=master,
        mlp_model=mlp_model,
        cnn_model=cnn_model,
        loader=test_loader,
        device=device,
        amp_enabled=amp_enabled,
    )

    report = {
        "best_epoch": best_epoch,
        "best_val_dice": best_val_dice,
        "test": test_metrics,
    }

    (RUN_DIR / "test_metrics.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 88)
    print("TRAINING COMPLETE")
    print("=" * 88)
    print(f"Best epoch       : {best_epoch}")
    print(f"Best val Dice    : {best_val_dice:.6f}")
    print()
    print("TEST")
    print(f"  Master Dice    : {test_metrics['master_dice']:.6f}")
    print(f"  MLP Dice       : {test_metrics['mlp_dice']:.6f}")
    print(f"  CNN Dice       : {test_metrics['cnn_dice']:.6f}")
    print(f"  Average Dice   : {test_metrics['avg_dice']:.6f}")
    print(f"  Master IoU     : {test_metrics['master_iou']:.6f}")
    print(f"  Master Prec.   : {test_metrics['master_precision']:.6f}")
    print(f"  Master Recall  : {test_metrics['master_recall']:.6f}")
    print()
    print(f"best.pt          : {best_path.resolve()}")
    print(f"last.pt          : {last_path.resolve()}")
    print(f"history.csv      : {HISTORY_PATH.resolve()}")
    print(f"test_metrics.json: {(RUN_DIR / 'test_metrics.json').resolve()}")


if __name__ == "__main__":
    main()
