"""
Train Engineer CNN U3
=====================

Trains engineer_cnn_u3.py on the 64x64 station dataset.

Dataset layout
--------------
STATION_ROOT/
    images/
    masks/      <- GT paste/relevance segmentation mask
    valid/      <- valid ROI mask
    meta/       <- optional JSON metadata from station builder

Core rules
----------
1. CNN input is [RGB_normalized + Valid] -> [4,64,64].
2. Invalid RGB pixels are filled with the median RGB of VALID pixels.
3. RGB mean/std are fitted from TRAIN split only, using VALID pixels only.
4. GT is never used as an input.
5. Loss and metrics ignore invalid pixels.
6. Splitting is group-aware by source ROI/source image.
7. If the e1108D split_manifest.csv exists, this script can reuse it so the
   CNN and MLP are evaluated on exactly the same train/val/test partition.
8. No augmentation is applied in this baseline. This keeps the first CNN-vs-MLP
   comparison clean.

No command-line arguments are used. Edit the CONFIG section below.
"""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
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

from engineer_cnn_u3 import (
    EngineerCNNU3,
    EngineerCNNU3Config,
    count_parameters,
    engineer_cnn_u3_loss,
)


# =============================================================================
# CONFIG - EDIT HERE
# =============================================================================

# -----------------------------------------------------------------------------
# Dataset
# -----------------------------------------------------------------------------

STATION_ROOT = Path("/home/hieu/Desktop/Nidec Vision/stations_divided")

IMAGE_DIR = STATION_ROOT / "images"
GT_MASK_DIR = STATION_ROOT / "masks"
VALID_MASK_DIR = STATION_ROOT / "valid"
META_DIR = STATION_ROOT / "meta"

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
}

# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------

RUN_ROOT = Path("/home/hieu/Desktop/Nidec Vision/run")
RUN_NAME = "engineer_cnn_u3_v1"

RUN_DIR = RUN_ROOT / RUN_NAME
CHECKPOINT_DIR = RUN_DIR / "checkpoints"

# -----------------------------------------------------------------------------
# Split
# -----------------------------------------------------------------------------

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10

# Keep identical to e1108D when possible.
RANDOM_SEED = 20260820

# Stations from one source ROI overlap strongly, so they must remain together.
STRICT_GROUP_SPLIT = False

# Recommended for a fair CNN-vs-e1108D comparison:
# if this MLP manifest exists, use EXACTLY the same station partition.
USE_REFERENCE_SPLIT_IF_AVAILABLE = True

REFERENCE_SPLIT_MANIFEST = (
    RUN_ROOT
    / "engineer_mlp_1108_v1"
    / "split_manifest.csv"
)

# If a reference manifest exists but does not match the current dataset,
# True -> stop instead of silently creating a different split.
STRICT_REFERENCE_SPLIT = True

# -----------------------------------------------------------------------------
# Training
# -----------------------------------------------------------------------------

EPOCHS = 200
BATCH_SIZE = 64

NUM_WORKERS = 0
PIN_MEMORY = True

LEARNING_RATE = 3e-4
WEIGHT_DECAY = 1e-4

GRAD_CLIP_NORM = 1.0

DICE_WEIGHT = 1.0
COARSE_WEIGHT = 0.20

PREDICTION_THRESHOLD = 0.50

# ReduceLROnPlateau monitors validation Dice.
LR_REDUCE_FACTOR = 0.5
LR_PATIENCE = 6
MIN_LR = 1e-6

# Early stopping monitors validation Dice.
EARLY_STOPPING_PATIENCE = 50
MIN_DICE_IMPROVEMENT = 1e-4

USE_AMP = True

SAVE_LAST_EVERY = 1

# -----------------------------------------------------------------------------
# RGB preprocessing
# -----------------------------------------------------------------------------

# RGB is converted to [0,1], then standardized:
#     x = (x - train_mean) / train_std
#
# Statistics are fitted using VALID TRAIN pixels only.
RGB_STANDARDIZER_EPS = 1e-6

# Invalid pixels are missing data, not black pixels.
# Baseline policy:
#     invalid RGB = median RGB of valid pixels in the SAME station.
INVALID_FILL_MODE = "median_valid_rgb"

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------

MODEL_CFG = EngineerCNNU3Config(
    input_channels=4,
    input_size=64,
    c0=32,
    c1=64,
    c2=128,
    c3=256,
    group_norm_groups=8,
    dropout=0.0,
    dice_weight=DICE_WEIGHT,
    coarse_weight=COARSE_WEIGHT,
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

    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def choose_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")


def _autocast_context(
    device: torch.device,
    enabled: bool,
):
    if enabled and device.type == "cuda":
        return torch.autocast(
            device_type="cuda",
            dtype=torch.float16,
        )

    return nullcontext()


def _make_grad_scaler(enabled: bool):
    """Compatibility with newer and older PyTorch versions."""
    try:
        return torch.amp.GradScaler(
            "cuda",
            enabled=enabled,
        )
    except Exception:
        return torch.cuda.amp.GradScaler(
            enabled=enabled,
        )


def _safe_torch_load(
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
# DATA RECORDS
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


def _load_json(
    path: Optional[Path],
) -> Dict:
    if path is None or not path.exists():
        return {}

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception:
        return {}


def _strip_station_suffix(stem: str) -> str:
    """
    Fallback grouping examples:
        roi_001_station_000
        roi_001-station-12
        roi_001_st003
    """
    patterns = [
        r"(?i)(?:[_-]station[_-]?\d+)$",
        r"(?i)(?:[_-]st[_-]?\d+)$",
        r"(?i)(?:[_-]s[_-]?\d+)$",
    ]

    for pattern in patterns:
        stripped = re.sub(
            pattern,
            "",
            stem,
        )

        if stripped != stem:
            return stripped

    return stem


def _infer_source_group(
    relative_image: Path,
    metadata: Dict,
) -> Tuple[str, bool]:
    """
    Returns:
        source_group, is_reliable

    Metadata is preferred because overlapping stations from one original ROI
    must never be distributed across train/val/test.
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

    stripped = _strip_station_suffix(
        relative_image.stem
    )

    if stripped != relative_image.stem:
        group = (
            relative_image.parent / stripped
        ).as_posix()

        return group, True

    if relative_image.parent != Path("."):
        return (
            relative_image.parent.as_posix(),
            True,
        )

    # Potentially unsafe fallback.
    return (
        relative_image.with_suffix("").as_posix(),
        False,
    )


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
            f"No station images found under: "
            f"{IMAGE_DIR.resolve()}"
        )

    records: List[StationRecord] = []

    skipped_missing = 0
    unreliable_groups = 0

    for image_path in image_paths:
        rel = image_path.relative_to(
            IMAGE_DIR
        )

        gt_path = _find_same_relative(
            GT_MASK_DIR,
            rel,
        )

        valid_path = _find_same_relative(
            VALID_MASK_DIR,
            rel,
        )

        if (
            gt_path is None
            or valid_path is None
        ):
            print(
                f"[SKIP] {rel}: "
                f"gt={'OK' if gt_path else 'MISSING'}, "
                f"valid={'OK' if valid_path else 'MISSING'}"
            )

            skipped_missing += 1
            continue

        meta_candidate = (
            META_DIR
            / rel.with_suffix(".json")
        )

        meta_path = (
            meta_candidate
            if meta_candidate.exists()
            else None
        )

        metadata = _load_json(
            meta_path
        )

        source_group, reliable = _infer_source_group(
            rel,
            metadata,
        )

        if not reliable:
            unreliable_groups += 1

            if STRICT_GROUP_SPLIT:
                raise RuntimeError(
                    "Unable to infer reliable source group for "
                    f"{rel}. Add source_roi/source_image metadata "
                    "or use filenames with a station suffix."
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
    print(f"[DATA] skipped incomplete  : {skipped_missing}")
    print(f"[DATA] unreliable grouping : {unreliable_groups}")

    return records


# =============================================================================
# IMAGE / MASK READING
# =============================================================================

def read_station_arrays(
    record: StationRecord,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns:
        image_rgb_u8 : [64,64,3], uint8, RGB
        valid_bin    : [64,64], uint8 {0,1}
        gt_bin       : [64,64], uint8 {0,1}, clipped to valid
    """
    image_bgr = cv2.imread(
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

    if image_bgr is None:
        raise RuntimeError(
            f"Could not read image: {record.image_path}"
        )

    if gt is None:
        raise RuntimeError(
            f"Could not read GT: {record.gt_path}"
        )

    if valid is None:
        raise RuntimeError(
            f"Could not read valid mask: {record.valid_path}"
        )

    size = MODEL_CFG.input_size

    if image_bgr.shape[:2] != (size, size):
        image_bgr = cv2.resize(
            image_bgr,
            (size, size),
            interpolation=cv2.INTER_AREA,
        )

    if gt.shape[:2] != (size, size):
        gt = cv2.resize(
            gt,
            (size, size),
            interpolation=cv2.INTER_NEAREST,
        )

    if valid.shape[:2] != (size, size):
        valid = cv2.resize(
            valid,
            (size, size),
            interpolation=cv2.INTER_NEAREST,
        )

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB,
    )

    valid_bin = (
        valid > 0
    ).astype(np.uint8)

    if not valid_bin.any():
        raise RuntimeError(
            f"Station has zero valid pixels: {record.image_path}"
        )

    gt_bin = (
        (gt > 0)
        & (valid_bin > 0)
    ).astype(np.uint8)

    return (
        image_rgb,
        valid_bin,
        gt_bin,
    )


def neutral_fill_rgb(
    image_rgb_01: np.ndarray,
    valid_bin: np.ndarray,
) -> np.ndarray:
    """
    Fill invalid pixels without creating a fake black polygon boundary.

    Baseline:
        invalid RGB <- per-channel median over valid pixels in that station.
    """
    if INVALID_FILL_MODE != "median_valid_rgb":
        raise ValueError(
            f"Unsupported INVALID_FILL_MODE={INVALID_FILL_MODE!r}"
        )

    valid_bool = valid_bin.astype(bool)

    if not valid_bool.any():
        raise RuntimeError(
            "Cannot neutral-fill an image with zero valid pixels."
        )

    fill = np.median(
        image_rgb_01[valid_bool],
        axis=0,
    ).astype(np.float32)

    out = image_rgb_01.copy()
    out[~valid_bool] = fill

    return out


# =============================================================================
# GROUP-AWARE SPLITTING
# =============================================================================

def split_records_by_group(
    records: Sequence[StationRecord],
) -> Tuple[
    List[StationRecord],
    List[StationRecord],
    List[StationRecord],
]:
    total_ratio = (
        TRAIN_RATIO
        + VAL_RATIO
        + TEST_RATIO
    )

    if abs(total_ratio - 1.0) > 1e-8:
        raise ValueError(
            "TRAIN_RATIO + VAL_RATIO + TEST_RATIO "
            f"must equal 1.0, got {total_ratio}"
        )

    groups: Dict[
        str,
        List[StationRecord],
    ] = {}

    for record in records:
        groups.setdefault(
            record.source_group,
            [],
        ).append(record)

    group_names = sorted(
        groups.keys()
    )

    if len(group_names) < 3:
        raise RuntimeError(
            "Need at least 3 source groups for "
            f"train/val/test, got {len(group_names)}."
        )

    rng = random.Random(
        RANDOM_SEED
    )

    rng.shuffle(
        group_names
    )

    n_groups = len(
        group_names
    )

    n_train = max(
        1,
        int(round(
            n_groups * TRAIN_RATIO
        )),
    )

    n_val = max(
        1,
        int(round(
            n_groups * VAL_RATIO
        )),
    )

    if n_train + n_val >= n_groups:
        overflow = (
            n_train
            + n_val
            - (n_groups - 1)
        )

        if (
            n_train >= n_val
            and n_train - overflow >= 1
        ):
            n_train -= overflow
        else:
            n_val = max(
                1,
                n_val - overflow,
            )

    n_test = (
        n_groups
        - n_train
        - n_val
    )

    if n_test < 1:
        raise RuntimeError(
            "Could not allocate at least one source "
            "group to every split."
        )

    train_groups = set(
        group_names[:n_train]
    )

    val_groups = set(
        group_names[
            n_train:
            n_train + n_val
        ]
    )

    test_groups = set(
        group_names[
            n_train + n_val:
        ]
    )

    assert train_groups.isdisjoint(
        val_groups
    )
    assert train_groups.isdisjoint(
        test_groups
    )
    assert val_groups.isdisjoint(
        test_groups
    )

    train = [
        r
        for r in records
        if r.source_group in train_groups
    ]

    val = [
        r
        for r in records
        if r.source_group in val_groups
    ]

    test = [
        r
        for r in records
        if r.source_group in test_groups
    ]

    return train, val, test


def split_records_from_reference_manifest(
    records: Sequence[StationRecord],
    manifest_path: Path,
) -> Tuple[
    List[StationRecord],
    List[StationRecord],
    List[StationRecord],
]:
    """
    Reuse the MLP station-level split manifest.

    This is preferred when comparing e1108D MLP against CNN U3, because every
    station is then evaluated in the exact same partition.
    """
    mapping: Dict[str, str] = {}

    with manifest_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        required = {
            "split",
            "station_key",
        }

        if not required.issubset(
            set(reader.fieldnames or [])
        ):
            raise RuntimeError(
                f"Reference manifest {manifest_path} "
                "does not contain split/station_key columns."
            )

        for row in reader:
            key = row["station_key"]
            split = row["split"].strip().lower()

            if split not in {
                "train",
                "val",
                "test",
            }:
                raise RuntimeError(
                    f"Bad split {split!r} for station {key!r}"
                )

            if key in mapping:
                raise RuntimeError(
                    f"Duplicate station_key in reference manifest: {key}"
                )

            mapping[key] = split

    current_keys = {
        r.key
        for r in records
    }

    reference_keys = set(
        mapping.keys()
    )

    missing_in_reference = (
        current_keys
        - reference_keys
    )

    stale_reference = (
        reference_keys
        - current_keys
    )

    if (
        missing_in_reference
        or stale_reference
    ):
        message = (
            "Reference split does not exactly match current dataset.\n"
            f"  missing in reference: {len(missing_in_reference)}\n"
            f"  stale in reference  : {len(stale_reference)}"
        )

        if STRICT_REFERENCE_SPLIT:
            raise RuntimeError(
                message
            )

        print(
            "[WARN] "
            + message.replace("\n", " | ")
        )

        return split_records_by_group(
            records
        )

    train = [
        r
        for r in records
        if mapping[r.key] == "train"
    ]

    val = [
        r
        for r in records
        if mapping[r.key] == "val"
    ]

    test = [
        r
        for r in records
        if mapping[r.key] == "test"
    ]

    if not train or not val or not test:
        raise RuntimeError(
            "Reference manifest produced an empty split."
        )

    # Additional source-group leakage assertion.
    train_groups = {
        r.source_group
        for r in train
    }

    val_groups = {
        r.source_group
        for r in val
    }

    test_groups = {
        r.source_group
        for r in test
    }

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
            f"[SPLIT] Reusing reference manifest: "
            f"{REFERENCE_SPLIT_MANIFEST.resolve()}"
        )

        train, val, test = (
            split_records_from_reference_manifest(
                records,
                REFERENCE_SPLIT_MANIFEST,
            )
        )

        split_source = str(
            REFERENCE_SPLIT_MANIFEST.resolve()
        )

    else:
        if USE_REFERENCE_SPLIT_IF_AVAILABLE:
            print(
                "[SPLIT] Reference manifest not found; "
                "using deterministic group-aware split."
            )

        train, val, test = (
            split_records_by_group(
                records
            )
        )

        split_source = (
            "deterministic_group_split"
        )

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

    return (
        train,
        val,
        test,
        split_source,
    )


def save_split_manifest(
    train: Sequence[StationRecord],
    val: Sequence[StationRecord],
    test: Sequence[StationRecord],
) -> None:
    RUN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    for split_name, split_records in (
        ("train", train),
        ("val", val),
        ("test", test),
    ):
        for record in split_records:
            rows.append(
                {
                    "split": split_name,
                    "station_key": record.key,
                    "source_group": record.source_group,
                    "image_path": str(record.image_path),
                    "gt_path": str(record.gt_path),
                    "valid_path": str(record.valid_path),
                }
            )

    rows.sort(
        key=lambda x: (
            x["split"],
            x["source_group"],
            x["station_key"],
        )
    )

    path = (
        RUN_DIR
        / "split_manifest.csv"
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(rows)


# =============================================================================
# TRAIN-ONLY RGB NORMALIZATION
# =============================================================================

@dataclass
class RGBStandardizer:
    mean: np.ndarray  # [3]
    std: np.ndarray   # [3]

    def transform(
        self,
        image_rgb_01: np.ndarray,
    ) -> np.ndarray:
        return (
            (
                image_rgb_01.astype(np.float32)
                - self.mean[None, None, :]
            )
            / self.std[None, None, :]
        ).astype(np.float32)


def fit_rgb_standardizer(
    train_records: Sequence[StationRecord],
) -> RGBStandardizer:
    """
    Pixel-weighted RGB statistics using TRAIN VALID pixels only.

    Each valid RGB pixel contributes equally.
    Invalid pixels never influence mean/std.
    """
    count = 0

    sum_rgb = np.zeros(
        3,
        dtype=np.float64,
    )

    sum_rgb2 = np.zeros(
        3,
        dtype=np.float64,
    )

    t0 = time.time()

    for i, record in enumerate(
        train_records,
        start=1,
    ):
        image_rgb_u8, valid, _ = (
            read_station_arrays(
                record
            )
        )

        image = (
            image_rgb_u8.astype(
                np.float32
            )
            / 255.0
        )

        pixels = image[
            valid.astype(bool)
        ].astype(np.float64)

        if pixels.size == 0:
            raise RuntimeError(
                f"No valid RGB pixels: {record.image_path}"
            )

        sum_rgb += pixels.sum(
            axis=0
        )

        sum_rgb2 += (
            pixels * pixels
        ).sum(
            axis=0
        )

        count += pixels.shape[0]

        if (
            i % 500 == 0
            or i == len(train_records)
        ):
            print(
                f"[RGB NORM] {i}/{len(train_records)} stations "
                f"| valid pixels={count:,} "
                f"| {time.time() - t0:.1f}s"
            )

    if count == 0:
        raise RuntimeError(
            "No valid TRAIN pixels available "
            "for RGB normalization."
        )

    mean = sum_rgb / count

    variance = np.maximum(
        sum_rgb2 / count
        - mean * mean,
        0.0,
    )

    std = np.sqrt(
        variance
    )

    near_constant = (
        std < RGB_STANDARDIZER_EPS
    )

    std[
        near_constant
    ] = 1.0

    standardizer = RGBStandardizer(
        mean=mean.astype(
            np.float32
        ),
        std=std.astype(
            np.float32
        ),
    )

    np.savez_compressed(
        RUN_DIR / "rgb_standardizer.npz",
        mean=standardizer.mean,
        std=standardizer.std,
        near_constant=near_constant.astype(
            np.uint8
        ),
    )

    print()
    print(
        "[RGB NORM] TRAIN valid-pixel mean: "
        f"{standardizer.mean.tolist()}"
    )
    print(
        "[RGB NORM] TRAIN valid-pixel std : "
        f"{standardizer.std.tolist()}"
    )

    return standardizer


# =============================================================================
# DATASET
# =============================================================================

class EngineerCNNU3Dataset(Dataset):
    def __init__(
        self,
        records: Sequence[StationRecord],
        rgb_standardizer: RGBStandardizer,
    ):
        self.records = list(
            records
        )

        self.rgb_standardizer = (
            rgb_standardizer
        )

    def __len__(self) -> int:
        return len(
            self.records
        )

    def __getitem__(
        self,
        index: int,
    ):
        record = self.records[
            index
        ]

        image_rgb_u8, valid, gt = (
            read_station_arrays(
                record
            )
        )

        image = (
            image_rgb_u8.astype(
                np.float32
            )
            / 255.0
        )

        # Prevent artificial black boundary at invalid ROI pixels.
        image = neutral_fill_rgb(
            image,
            valid,
        )

        # Normalize RGB only.
        image = (
            self.rgb_standardizer.transform(
                image
            )
        )

        # HWC -> CHW
        rgb_chw = np.transpose(
            image,
            (2, 0, 1),
        ).astype(np.float32)

        valid_chw = (
            valid.astype(
                np.float32
            )[None, ...]
        )

        gt_chw = (
            gt.astype(
                np.float32
            )[None, ...]
        )

        # Final network input:
        # [3,64,64] RGB + [1,64,64] Valid
        cnn_input = np.concatenate(
            [
                rgb_chw,
                valid_chw,
            ],
            axis=0,
        ).astype(np.float32)

        if cnn_input.shape != (
            4,
            MODEL_CFG.input_size,
            MODEL_CFG.input_size,
        ):
            raise RuntimeError(
                f"Bad CNN input shape: {cnn_input.shape}"
            )

        return {
            "input": torch.from_numpy(
                cnn_input
            ),
            "gt": torch.from_numpy(
                gt_chw
            ),
            "valid": torch.from_numpy(
                valid_chw
            ),
            "key": record.key,
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
        pin_memory=(
            PIN_MEMORY
            and device.type == "cuda"
        ),
        drop_last=False,
        persistent_workers=(
            NUM_WORKERS > 0
        ),
    )


# =============================================================================
# SEGMENTATION METRICS
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
        pred = (
            torch.sigmoid(logits)
            >= self.threshold
        )

        target_b = (
            target >= 0.5
        )

        valid_b = (
            valid >= 0.5
        )

        pred = (
            pred
            & valid_b
        )

        target_b = (
            target_b
            & valid_b
        )

        self.tp += float(
            (
                pred
                & target_b
            ).sum().item()
        )

        self.fp += float(
            (
                pred
                & (~target_b)
                & valid_b
            ).sum().item()
        )

        self.fn += float(
            (
                (~pred)
                & target_b
                & valid_b
            ).sum().item()
        )

        self.tn += float(
            (
                (~pred)
                & (~target_b)
                & valid_b
            ).sum().item()
        )

    def compute(
        self,
    ) -> Dict[str, float]:
        eps = 1e-9

        dice = (
            2.0 * self.tp
        ) / (
            2.0 * self.tp
            + self.fp
            + self.fn
            + eps
        )

        iou = self.tp / (
            self.tp
            + self.fp
            + self.fn
            + eps
        )

        precision = self.tp / (
            self.tp
            + self.fp
            + eps
        )

        recall = self.tp / (
            self.tp
            + self.fn
            + eps
        )

        accuracy = (
            self.tp
            + self.tn
        ) / (
            self.tp
            + self.fp
            + self.fn
            + self.tn
            + eps
        )

        return {
            "dice": dice,
            "iou": iou,
            "precision": precision,
            "recall": recall,
            "accuracy": accuracy,
        }


# =============================================================================
# TRAIN / EVALUATE
# =============================================================================

def train_one_epoch(
    model: EngineerCNNU3,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scaler,
    device: torch.device,
    amp_enabled: bool,
) -> Dict[str, float]:
    model.train()

    metrics = SegmentationAccumulator(
        threshold=PREDICTION_THRESHOLD
    )

    total_loss = 0.0
    total_fine_bce = 0.0
    total_fine_dice = 0.0
    total_coarse_bce = 0.0
    total_coarse_dice = 0.0

    sample_count = 0

    for batch in loader:
        x = batch["input"].to(
            device,
            non_blocking=True,
        )

        gt = batch["gt"].to(
            device,
            non_blocking=True,
        )

        valid = batch["valid"].to(
            device,
            non_blocking=True,
        )

        bs = x.shape[0]

        optimizer.zero_grad(
            set_to_none=True
        )

        with _autocast_context(
            device,
            amp_enabled,
        ):
            outputs = model(
                x,
                return_intermediates=True,
            )

            loss, parts = engineer_cnn_u3_loss(
                outputs,
                gt_mask_64=gt,
                valid_mask_64=valid,
                dice_weight=DICE_WEIGHT,
                coarse_weight=COARSE_WEIGHT,
            )

        scaler.scale(
            loss
        ).backward()

        if (
            GRAD_CLIP_NORM is not None
            and GRAD_CLIP_NORM > 0
        ):
            scaler.unscale_(
                optimizer
            )

            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                GRAD_CLIP_NORM,
            )

        scaler.step(
            optimizer
        )

        scaler.update()

        metrics.update(
            outputs["logits"].detach(),
            gt,
            valid,
        )

        total_loss += (
            float(loss.detach().item())
            * bs
        )

        total_fine_bce += (
            float(parts["fine_bce"].item())
            * bs
        )

        total_fine_dice += (
            float(parts["fine_dice"].item())
            * bs
        )

        total_coarse_bce += (
            float(parts["coarse_bce"].item())
            * bs
        )

        total_coarse_dice += (
            float(parts["coarse_dice"].item())
            * bs
        )

        sample_count += bs

    result = metrics.compute()

    denom = max(
        sample_count,
        1,
    )

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
    model: EngineerCNNU3,
    loader: DataLoader,
    device: torch.device,
    amp_enabled: bool,
) -> Dict[str, float]:
    model.eval()

    metrics = SegmentationAccumulator(
        threshold=PREDICTION_THRESHOLD
    )

    total_loss = 0.0
    total_fine_bce = 0.0
    total_fine_dice = 0.0
    total_coarse_bce = 0.0
    total_coarse_dice = 0.0

    sample_count = 0

    for batch in loader:
        x = batch["input"].to(
            device,
            non_blocking=True,
        )

        gt = batch["gt"].to(
            device,
            non_blocking=True,
        )

        valid = batch["valid"].to(
            device,
            non_blocking=True,
        )

        bs = x.shape[0]

        with _autocast_context(
            device,
            amp_enabled,
        ):
            outputs = model(
                x,
                return_intermediates=True,
            )

            loss, parts = engineer_cnn_u3_loss(
                outputs,
                gt_mask_64=gt,
                valid_mask_64=valid,
                dice_weight=DICE_WEIGHT,
                coarse_weight=COARSE_WEIGHT,
            )

        metrics.update(
            outputs["logits"],
            gt,
            valid,
        )

        total_loss += (
            float(loss.item())
            * bs
        )

        total_fine_bce += (
            float(parts["fine_bce"].item())
            * bs
        )

        total_fine_dice += (
            float(parts["fine_dice"].item())
            * bs
        )

        total_coarse_bce += (
            float(parts["coarse_bce"].item())
            * bs
        )

        total_coarse_dice += (
            float(parts["coarse_dice"].item())
            * bs
        )

        sample_count += bs

    result = metrics.compute()

    denom = max(
        sample_count,
        1,
    )

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
    model: EngineerCNNU3,
    optimizer: torch.optim.Optimizer,
    scheduler,
    epoch: int,
    best_val_dice: float,
    rgb_standardizer: RGBStandardizer,
    metrics: Dict[str, float],
    split_source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    torch.save(
        {
            "epoch": epoch,

            "model_state_dict": (
                model.state_dict()
            ),

            "optimizer_state_dict": (
                optimizer.state_dict()
            ),

            "scheduler_state_dict": (
                scheduler.state_dict()
                if scheduler is not None
                else None
            ),

            "best_val_dice": (
                best_val_dice
            ),

            "metrics": metrics,

            "model_config": (
                asdict(MODEL_CFG)
            ),

            "rgb_mean": (
                rgb_standardizer.mean
            ),

            "rgb_std": (
                rgb_standardizer.std
            ),

            "input_color_order": "RGB",

            "invalid_fill_mode": (
                INVALID_FILL_MODE
            ),

            "valid_is_input_channel": True,

            "prediction_threshold": (
                PREDICTION_THRESHOLD
            ),

            "split_source": (
                split_source
            ),
        },
        path,
    )


def append_history_row(
    path: Path,
    row: Dict[str, float],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    exists = path.exists()

    with path.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                row.keys()
            ),
        )

        if not exists:
            writer.writeheader()

        writer.writerow(
            row
        )


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    seed_everything(
        RANDOM_SEED
    )

    device = choose_device()

    amp_enabled = bool(
        USE_AMP
        and device.type == "cuda"
    )

    RUN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 78)
    print("Engineer CNN U3 training")
    print("=" * 78)

    print(f"Device        : {device}")
    print(f"AMP           : {amp_enabled}")
    print(f"Station root  : {STATION_ROOT.resolve()}")
    print(f"Run directory : {RUN_DIR.resolve()}")
    print()

    # -------------------------------------------------------------------------
    # 1. Discover data
    # -------------------------------------------------------------------------

    records = discover_records()

    # -------------------------------------------------------------------------
    # 2. Split
    # -------------------------------------------------------------------------

    (
        train_records,
        val_records,
        test_records,
        split_source,
    ) = choose_split(
        records
    )

    save_split_manifest(
        train_records,
        val_records,
        test_records,
    )

    # -------------------------------------------------------------------------
    # 3. Fit TRAIN-only RGB normalization
    # -------------------------------------------------------------------------

    rgb_standardizer = (
        fit_rgb_standardizer(
            train_records
        )
    )

    # -------------------------------------------------------------------------
    # Save experiment config after split choice is known
    # -------------------------------------------------------------------------

    config_dump = {
        "station_root": str(
            STATION_ROOT
        ),
        "image_dir": str(
            IMAGE_DIR
        ),
        "gt_mask_dir": str(
            GT_MASK_DIR
        ),
        "valid_mask_dir": str(
            VALID_MASK_DIR
        ),
        "meta_dir": str(
            META_DIR
        ),

        "split_source": (
            split_source
        ),

        "reference_split_manifest": str(
            REFERENCE_SPLIT_MANIFEST
        ),

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

        "prediction_threshold": (
            PREDICTION_THRESHOLD
        ),

        "invalid_fill_mode": (
            INVALID_FILL_MODE
        ),

        "rgb_mean": (
            rgb_standardizer.mean.tolist()
        ),

        "rgb_std": (
            rgb_standardizer.std.tolist()
        ),

        "augmentation": "none",

        "model_config": (
            asdict(MODEL_CFG)
        ),
    }

    (
        RUN_DIR
        / "run_config.json"
    ).write_text(
        json.dumps(
            config_dump,
            indent=2,
        ),
        encoding="utf-8",
    )

    # -------------------------------------------------------------------------
    # 4. Dataset / DataLoader
    # -------------------------------------------------------------------------

    train_ds = EngineerCNNU3Dataset(
        train_records,
        rgb_standardizer,
    )

    val_ds = EngineerCNNU3Dataset(
        val_records,
        rgb_standardizer,
    )

    test_ds = EngineerCNNU3Dataset(
        test_records,
        rgb_standardizer,
    )

    train_loader = make_loader(
        train_ds,
        shuffle=True,
        device=device,
    )

    val_loader = make_loader(
        val_ds,
        shuffle=False,
        device=device,
    )

    test_loader = make_loader(
        test_ds,
        shuffle=False,
        device=device,
    )

    # -------------------------------------------------------------------------
    # 5. Model / optimizer / scheduler
    # -------------------------------------------------------------------------

    model = EngineerCNNU3(
        MODEL_CFG
    ).to(
        device
    )

    params = count_parameters(
        model
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    scheduler = (
        torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="max",
            factor=LR_REDUCE_FACTOR,
            patience=LR_PATIENCE,
            min_lr=MIN_LR,
        )
    )

    scaler = _make_grad_scaler(
        amp_enabled
    )

    print()
    print(
        f"Model parameters : "
        f"{params['total']:,}"
    )
    print(
        f"Trainable        : "
        f"{params['trainable']:,}"
    )

    print(
        f"Train stations   : "
        f"{len(train_ds)}"
    )
    print(
        f"Val stations     : "
        f"{len(val_ds)}"
    )
    print(
        f"Test stations    : "
        f"{len(test_ds)}"
    )
    print()

    # -------------------------------------------------------------------------
    # 6. Training loop
    # -------------------------------------------------------------------------

    history_path = (
        RUN_DIR
        / "history.csv"
    )

    if history_path.exists():
        history_path.unlink()

    best_val_dice = -math.inf
    epochs_without_improvement = 0

    best_path = (
        CHECKPOINT_DIR
        / "best.pt"
    )

    last_path = (
        CHECKPOINT_DIR
        / "last.pt"
    )

    for epoch in range(
        1,
        EPOCHS + 1,
    ):
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

        scheduler.step(
            val_metrics["dice"]
        )

        lr = float(
            optimizer.param_groups[0]["lr"]
        )

        elapsed = (
            time.time()
            - t0
        )

        row = {
            "epoch": epoch,
            "lr": lr,
            "seconds": elapsed,

            **{
                f"train_{k}": v
                for k, v
                in train_metrics.items()
            },

            **{
                f"val_{k}": v
                for k, v
                in val_metrics.items()
            },
        }

        append_history_row(
            history_path,
            row,
        )

        print(
            f"Epoch {epoch:03d}/{EPOCHS} | "
            f"lr={lr:.2e} | "
            f"train loss={train_metrics['loss']:.4f} "
            f"dice={train_metrics['dice']:.4f} | "
            f"val loss={val_metrics['loss']:.4f} "
            f"dice={val_metrics['dice']:.4f} "
            f"IoU={val_metrics['iou']:.4f} "
            f"P={val_metrics['precision']:.4f} "
            f"R={val_metrics['recall']:.4f} | "
            f"{elapsed:.1f}s"
        )

        improved = (
            val_metrics["dice"]
            > best_val_dice
            + MIN_DICE_IMPROVEMENT
        )

        if improved:
            best_val_dice = (
                val_metrics["dice"]
            )

            epochs_without_improvement = 0

            save_checkpoint(
                best_path,
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                epoch=epoch,
                best_val_dice=best_val_dice,
                rgb_standardizer=rgb_standardizer,
                metrics=val_metrics,
                split_source=split_source,
            )

            print(
                f"  [BEST] val Dice -> "
                f"{best_val_dice:.6f}"
            )

        else:
            epochs_without_improvement += 1

        if (
            SAVE_LAST_EVERY > 0
            and epoch % SAVE_LAST_EVERY == 0
        ):
            save_checkpoint(
                last_path,
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                epoch=epoch,
                best_val_dice=best_val_dice,
                rgb_standardizer=rgb_standardizer,
                metrics=val_metrics,
                split_source=split_source,
            )

        if (
            epochs_without_improvement
            >= EARLY_STOPPING_PATIENCE
        ):
            print(
                "[EARLY STOP] no validation Dice "
                f"improvement for "
                f"{EARLY_STOPPING_PATIENCE} epochs."
            )
            break

    # -------------------------------------------------------------------------
    # 7. Test best validation checkpoint
    # -------------------------------------------------------------------------

    if not best_path.exists():
        raise RuntimeError(
            "Training ended without producing best.pt"
        )

    checkpoint = _safe_torch_load(
        best_path,
        device,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    test_metrics = evaluate(
        model,
        test_loader,
        device,
        amp_enabled,
    )

    print()
    print("=" * 78)
    print("BEST CNN U3 - TEST SET")
    print("=" * 78)

    print(
        f"Best epoch : "
        f"{checkpoint['epoch']}"
    )

    print(
        f"Val Dice   : "
        f"{checkpoint['best_val_dice']:.6f}"
    )

    print(
        f"Test loss  : "
        f"{test_metrics['loss']:.6f}"
    )

    print(
        f"Test Dice  : "
        f"{test_metrics['dice']:.6f}"
    )

    print(
        f"Test IoU   : "
        f"{test_metrics['iou']:.6f}"
    )

    print(
        f"Precision  : "
        f"{test_metrics['precision']:.6f}"
    )

    print(
        f"Recall     : "
        f"{test_metrics['recall']:.6f}"
    )

    print(
        f"Accuracy   : "
        f"{test_metrics['accuracy']:.6f}"
    )

    (
        RUN_DIR
        / "test_metrics.json"
    ).write_text(
        json.dumps(
            test_metrics,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        f"Best checkpoint : "
        f"{best_path.resolve()}"
    )
    print(
        f"RGB standardizer: "
        f"{(RUN_DIR / 'rgb_standardizer.npz').resolve()}"
    )
    print(
        f"History         : "
        f"{history_path.resolve()}"
    )
    print(
        f"Split manifest  : "
        f"{(RUN_DIR / 'split_manifest.csv').resolve()}"
    )


if __name__ == "__main__":
    main()
