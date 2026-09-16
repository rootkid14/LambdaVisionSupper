"""
Run Engineer MLP e1108D and Engineer CNN U3 in parallel on the SAME stations.
============================================================================

For every station, this script produces one comparison image:

    ORIGINAL | MLP e1108D | CNN U3

Both models receive the same source image and the same Valid mask.

MLP preprocessing
-----------------
image + valid
    -> e1108D handcrafted feature extractor
    -> checkpoint mean/std standardization
    -> EngineerMLP
    -> sigmoid
    -> multiply Valid

CNN preprocessing
-----------------
image + valid
    -> resize 64x64
    -> BGR -> RGB -> [0,1]
    -> invalid RGB = median RGB over valid pixels
    -> checkpoint TRAIN-only RGB normalization
    -> append Valid as channel 4
    -> EngineerCNNU3
    -> sigmoid
    -> multiply Valid

GT masks are NOT required.

Expected local modules
----------------------
e1108D_metrics_extractor.py
e1108D_neural_network.py
engineer_cnn_u3.py

Edit CONFIG below, then run:

    python3 run_compare_mlp_cnn.py
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import time

import cv2
import numpy as np
import torch

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


# =============================================================================
# CONFIG - EDIT HERE
# =============================================================================

# -----------------------------------------------------------------------------
# Input
# -----------------------------------------------------------------------------

INPUT_IMAGE_DIR = Path(
    "/home/hieu/Desktop/Nidec Vision/stations_divided/images"
)

VALID_MASK_DIR = Path(
    "/home/hieu/Desktop/Nidec Vision/stations_divided/valid"
)

ALLOW_FULL_VALID_IF_MISSING = False


# -----------------------------------------------------------------------------
# Checkpoints
# -----------------------------------------------------------------------------

MLP_CHECKPOINT_PATH = Path(
    "/home/hieu/Desktop/Nidec Vision/run/"
    "engineer_mlp_1108_v1/checkpoints/best.pt"
)

CNN_CHECKPOINT_PATH = Path(
    "/home/hieu/Desktop/Nidec Vision/run/"
    "engineer_cnn_u3_v1/checkpoints/best.pt"
)


# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------

OUTPUT_DIR = Path(
    "/home/hieu/Desktop/Nidec Vision/run/"
    "compare_mlp_cnn/test_run"
)

COMPARISON_SUBDIR = "comparison"

# Optional individual outputs.
SAVE_ORIGINAL_PANEL = False
SAVE_MLP_PANEL = False
SAVE_CNN_PANEL = False
SAVE_MLP_MASK = False
SAVE_CNN_MASK = False
SAVE_DISAGREEMENT_MASK = False

ORIGINAL_SUBDIR = "original"
MLP_SUBDIR = "mlp"
CNN_SUBDIR = "cnn"
MLP_MASK_SUBDIR = "mlp_mask"
CNN_MASK_SUBDIR = "cnn_mask"
DISAGREEMENT_SUBDIR = "disagreement"


# -----------------------------------------------------------------------------
# Prediction thresholds
# -----------------------------------------------------------------------------

# None = use threshold stored inside each checkpoint.
MLP_THRESHOLD_OVERRIDE: Optional[float] = None
CNN_THRESHOLD_OVERRIDE: Optional[float] = None


# -----------------------------------------------------------------------------
# Runtime
# -----------------------------------------------------------------------------

INFERENCE_BATCH_SIZE = 128

# "auto", "cuda", "cpu", "mps"
DEVICE = "auto"

USE_AMP = True


# -----------------------------------------------------------------------------
# Visualization
# -----------------------------------------------------------------------------

# Predicted region highlight.
MASK_COLOR_BGR = (0, 0, 255)       # red
CONTOUR_COLOR_BGR = (0, 255, 255)  # yellow
OVERLAY_ALPHA = 0.42

DRAW_CONTOUR = True
CONTOUR_THICKNESS = 1

DIM_INVALID_AREA = False
INVALID_DIM_FACTOR = 0.45

# Native station 64x64 -> panel 512x512.
OUTPUT_SCALE = 8

# INTER_NEAREST makes segmentation boundaries easy to inspect.
OUTPUT_RESIZE_INTERPOLATION = cv2.INTER_NEAREST

# Add a title bar above the three panels AFTER enlarging.
DRAW_PANEL_LABELS = True
HEADER_HEIGHT = 38

LABEL_FONT = cv2.FONT_HERSHEY_SIMPLEX
LABEL_FONT_SCALE = 0.72
LABEL_THICKNESS = 2

# Optional model information under each title.
DRAW_THRESHOLD_IN_LABEL = True

# Draw valid ROI contour on ORIGINAL panel.
DRAW_VALID_CONTOUR_ON_ORIGINAL = True
VALID_CONTOUR_COLOR_BGR = (255, 255, 0)

# Optional visual display of where MLP and CNN binary masks disagree.
# This does not affect either model.
DISAGREEMENT_COLOR_BGR = (255, 0, 255)  # magenta


# -----------------------------------------------------------------------------
# File types
# -----------------------------------------------------------------------------

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
}


# =============================================================================
# DEVICE / LOAD HELPERS
# =============================================================================

def choose_device() -> torch.device:
    requested = DEVICE.lower()

    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "DEVICE='cuda' but CUDA is not available."
            )
        return torch.device("cuda")

    if requested == "mps":
        if not (
            hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
        ):
            raise RuntimeError(
                "DEVICE='mps' but MPS is not available."
            )
        return torch.device("mps")

    if requested == "cpu":
        return torch.device("cpu")

    if requested != "auto":
        raise ValueError(
            "DEVICE must be one of: auto, cuda, cpu, mps"
        )

    if torch.cuda.is_available():
        return torch.device("cuda")

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")


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


def validate_threshold(
    threshold: float,
    name: str,
) -> float:
    threshold = float(threshold)

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            f"{name} must be in [0,1], got {threshold}"
        )

    return threshold


# =============================================================================
# LOAD MLP
# =============================================================================

def mlp_config_from_checkpoint(
    checkpoint: Dict,
) -> EngineerMLPConfig:
    raw_cfg = checkpoint.get("model_config")

    if not raw_cfg:
        print(
            "[WARN] MLP checkpoint has no model_config; "
            "using EngineerMLPConfig() defaults."
        )
        return EngineerMLPConfig()

    allowed = {
        f.name
        for f in fields(EngineerMLPConfig)
    }

    filtered = {
        k: v
        for k, v in raw_cfg.items()
        if k in allowed
    }

    return EngineerMLPConfig(
        **filtered
    )


def load_mlp(
    device: torch.device,
) -> Tuple[
    EngineerMLP,
    np.ndarray,
    np.ndarray,
    float,
    Dict,
]:
    if not MLP_CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"MLP checkpoint not found: "
            f"{MLP_CHECKPOINT_PATH.resolve()}"
        )

    checkpoint = safe_torch_load(
        MLP_CHECKPOINT_PATH,
        device,
    )

    if "model_state_dict" not in checkpoint:
        raise KeyError(
            "MLP checkpoint has no model_state_dict."
        )

    cfg = mlp_config_from_checkpoint(
        checkpoint
    )

    model = EngineerMLP(
        cfg
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(
        device
    )

    model.eval()

    if "standardizer_mean" not in checkpoint:
        raise KeyError(
            "MLP checkpoint has no standardizer_mean."
        )

    if "standardizer_std" not in checkpoint:
        raise KeyError(
            "MLP checkpoint has no standardizer_std."
        )

    mean = np.asarray(
        checkpoint["standardizer_mean"],
        dtype=np.float32,
    ).reshape(-1)

    std = np.asarray(
        checkpoint["standardizer_std"],
        dtype=np.float32,
    ).reshape(-1)

    if mean.shape != (TOTAL_FEATURE_DIM,):
        raise ValueError(
            f"MLP mean shape={mean.shape}, "
            f"expected ({TOTAL_FEATURE_DIM},)"
        )

    if std.shape != (TOTAL_FEATURE_DIM,):
        raise ValueError(
            f"MLP std shape={std.shape}, "
            f"expected ({TOTAL_FEATURE_DIM},)"
        )

    std = std.copy()
    std[np.abs(std) < 1e-12] = 1.0

    saved_threshold = float(
        checkpoint.get(
            "prediction_threshold",
            0.5,
        )
    )

    threshold = (
        saved_threshold
        if MLP_THRESHOLD_OVERRIDE is None
        else MLP_THRESHOLD_OVERRIDE
    )

    threshold = validate_threshold(
        threshold,
        "MLP threshold",
    )

    return (
        model,
        mean,
        std,
        threshold,
        checkpoint,
    )


# =============================================================================
# LOAD CNN
# =============================================================================

def cnn_config_from_checkpoint(
    checkpoint: Dict,
) -> EngineerCNNU3Config:
    raw_cfg = checkpoint.get("model_config")

    if not raw_cfg:
        print(
            "[WARN] CNN checkpoint has no model_config; "
            "using EngineerCNNU3Config() defaults."
        )
        return EngineerCNNU3Config()

    allowed = {
        f.name
        for f in fields(EngineerCNNU3Config)
    }

    filtered = {
        k: v
        for k, v in raw_cfg.items()
        if k in allowed
    }

    return EngineerCNNU3Config(
        **filtered
    )


def load_cnn(
    device: torch.device,
) -> Tuple[
    EngineerCNNU3,
    np.ndarray,
    np.ndarray,
    float,
    Dict,
]:
    if not CNN_CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"CNN checkpoint not found: "
            f"{CNN_CHECKPOINT_PATH.resolve()}"
        )

    checkpoint = safe_torch_load(
        CNN_CHECKPOINT_PATH,
        device,
    )

    if "model_state_dict" not in checkpoint:
        raise KeyError(
            "CNN checkpoint has no model_state_dict."
        )

    cfg = cnn_config_from_checkpoint(
        checkpoint
    )

    model = EngineerCNNU3(
        cfg
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(
        device
    )

    model.eval()

    if "rgb_mean" not in checkpoint:
        raise KeyError(
            "CNN checkpoint has no rgb_mean."
        )

    if "rgb_std" not in checkpoint:
        raise KeyError(
            "CNN checkpoint has no rgb_std."
        )

    rgb_mean = np.asarray(
        checkpoint["rgb_mean"],
        dtype=np.float32,
    ).reshape(-1)

    rgb_std = np.asarray(
        checkpoint["rgb_std"],
        dtype=np.float32,
    ).reshape(-1)

    if rgb_mean.shape != (3,):
        raise ValueError(
            f"CNN rgb_mean shape={rgb_mean.shape}, expected (3,)"
        )

    if rgb_std.shape != (3,):
        raise ValueError(
            f"CNN rgb_std shape={rgb_std.shape}, expected (3,)"
        )

    rgb_std = rgb_std.copy()
    rgb_std[np.abs(rgb_std) < 1e-12] = 1.0

    saved_threshold = float(
        checkpoint.get(
            "prediction_threshold",
            0.5,
        )
    )

    threshold = (
        saved_threshold
        if CNN_THRESHOLD_OVERRIDE is None
        else CNN_THRESHOLD_OVERRIDE
    )

    threshold = validate_threshold(
        threshold,
        "CNN threshold",
    )

    return (
        model,
        rgb_mean,
        rgb_std,
        threshold,
        checkpoint,
    )


# =============================================================================
# FILE DISCOVERY
# =============================================================================

def find_corresponding_mask(
    mask_root: Path,
    relative_image: Path,
) -> Optional[Path]:
    exact = (
        mask_root
        / relative_image
    )

    if exact.exists():
        return exact

    parent = (
        mask_root
        / relative_image.parent
    )

    if not parent.exists():
        return None

    for ext in IMAGE_EXTENSIONS:
        candidate = (
            parent
            / f"{relative_image.stem}{ext}"
        )

        if candidate.exists():
            return candidate

    return None


def discover_images() -> List[Path]:
    if not INPUT_IMAGE_DIR.exists():
        raise FileNotFoundError(
            f"INPUT_IMAGE_DIR does not exist: "
            f"{INPUT_IMAGE_DIR.resolve()}"
        )

    images = sorted(
        p
        for p in INPUT_IMAGE_DIR.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not images:
        raise RuntimeError(
            f"No images found under: "
            f"{INPUT_IMAGE_DIR.resolve()}"
        )

    return images


def read_station_and_valid(
    image_path: Path,
) -> Optional[
    Tuple[
        np.ndarray,
        np.ndarray,
        Path,
    ]
]:
    relative = image_path.relative_to(
        INPUT_IMAGE_DIR
    )

    image_bgr = cv2.imread(
        str(image_path),
        cv2.IMREAD_COLOR,
    )

    if image_bgr is None:
        print(
            f"[SKIP] Could not read image: "
            f"{image_path}"
        )
        return None

    valid_path = find_corresponding_mask(
        VALID_MASK_DIR,
        relative,
    )

    if valid_path is None:
        if not ALLOW_FULL_VALID_IF_MISSING:
            print(
                f"[SKIP] Missing valid mask for: "
                f"{relative}"
            )
            return None

        print(
            f"[WARN] Missing valid for {relative}; "
            "using full-valid."
        )

        valid = np.ones(
            image_bgr.shape[:2],
            dtype=np.uint8,
        ) * 255

    else:
        valid = cv2.imread(
            str(valid_path),
            cv2.IMREAD_GRAYSCALE,
        )

        if valid is None:
            print(
                f"[SKIP] Could not read valid mask: "
                f"{valid_path}"
            )
            return None

    return (
        image_bgr,
        valid,
        relative,
    )


# =============================================================================
# COMMON 64x64 PREPARATION
# =============================================================================

def prepare_64(
    image_bgr: np.ndarray,
    valid_mask: np.ndarray,
) -> Tuple[
    np.ndarray,
    np.ndarray,
]:
    if image_bgr.shape[:2] != (64, 64):
        image_bgr = cv2.resize(
            image_bgr,
            (64, 64),
            interpolation=cv2.INTER_AREA,
        )

    if valid_mask.shape[:2] != (64, 64):
        valid_mask = cv2.resize(
            valid_mask,
            (64, 64),
            interpolation=cv2.INTER_NEAREST,
        )

    valid64 = (
        valid_mask > 0
    ).astype(np.uint8)

    if not valid64.any():
        raise RuntimeError(
            "Station has zero valid pixels."
        )

    return (
        image_bgr,
        valid64,
    )


# =============================================================================
# MLP PREPROCESSING
# =============================================================================

def make_mlp_feature(
    image_bgr: np.ndarray,
    valid_mask: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
) -> np.ndarray:
    raw = extract_feature_vector(
        image_bgr,
        valid_mask,
        color_order="BGR",
    )

    if raw.shape != (
        TOTAL_FEATURE_DIM,
    ):
        raise RuntimeError(
            f"MLP extractor returned {raw.shape}, "
            f"expected ({TOTAL_FEATURE_DIM},)"
        )

    feature = (
        raw.astype(np.float32)
        - mean
    ) / std

    if not np.isfinite(
        feature
    ).all():
        bad = np.flatnonzero(
            ~np.isfinite(feature)
        )

        raise RuntimeError(
            "Non-finite MLP features at indices "
            f"{bad[:20].tolist()}"
        )

    return feature.astype(
        np.float32
    )


# =============================================================================
# CNN PREPROCESSING
# =============================================================================

def make_cnn_input(
    original64_bgr: np.ndarray,
    valid64: np.ndarray,
    rgb_mean: np.ndarray,
    rgb_std: np.ndarray,
) -> np.ndarray:
    image_rgb = cv2.cvtColor(
        original64_bgr,
        cv2.COLOR_BGR2RGB,
    ).astype(
        np.float32
    ) / 255.0

    valid_bool = valid64.astype(
        bool
    )

    fill = np.median(
        image_rgb[valid_bool],
        axis=0,
    ).astype(np.float32)

    image_rgb = image_rgb.copy()

    image_rgb[
        ~valid_bool
    ] = fill

    image_rgb = (
        image_rgb
        - rgb_mean[None, None, :]
    ) / (
        rgb_std[None, None, :]
    )

    rgb_chw = np.transpose(
        image_rgb,
        (2, 0, 1),
    ).astype(np.float32)

    valid_chw = (
        valid64.astype(np.float32)
        [None, ...]
    )

    cnn_input = np.concatenate(
        [
            rgb_chw,
            valid_chw,
        ],
        axis=0,
    ).astype(np.float32)

    if cnn_input.shape != (
        4,
        64,
        64,
    ):
        raise RuntimeError(
            f"Bad CNN input shape: "
            f"{cnn_input.shape}"
        )

    if not np.isfinite(
        cnn_input
    ).all():
        raise RuntimeError(
            "Non-finite value in CNN input."
        )

    return cnn_input


# =============================================================================
# BATCH INFERENCE
# =============================================================================

def run_mlp_batch(
    model: EngineerMLP,
    feature_batch: List[np.ndarray],
    valid_batch: List[np.ndarray],
    device: torch.device,
    amp_enabled: bool,
) -> np.ndarray:
    x_np = np.stack(
        feature_batch,
        axis=0,
    ).astype(np.float32)

    valid_np = np.stack(
        valid_batch,
        axis=0,
    ).astype(np.float32)

    x = torch.from_numpy(
        x_np
    ).to(
        device,
        non_blocking=True,
    )

    valid_tensor = torch.from_numpy(
        valid_np[:, None, :, :]
    ).to(
        device,
        non_blocking=True,
    )

    with torch.no_grad():
        if amp_enabled:
            with torch.autocast(
                device_type="cuda",
                dtype=torch.float16,
            ):
                logits = model(
                    x
                )
        else:
            logits = model(
                x
            )

        prob = torch.sigmoid(
            logits
        )

        prob = (
            prob
            * valid_tensor
        )

    return (
        prob[:, 0]
        .detach()
        .float()
        .cpu()
        .numpy()
    )


def run_cnn_batch(
    model: EngineerCNNU3,
    cnn_batch: List[np.ndarray],
    valid_batch: List[np.ndarray],
    device: torch.device,
    amp_enabled: bool,
) -> np.ndarray:
    x_np = np.stack(
        cnn_batch,
        axis=0,
    ).astype(np.float32)

    valid_np = np.stack(
        valid_batch,
        axis=0,
    ).astype(np.float32)

    x = torch.from_numpy(
        x_np
    ).to(
        device,
        non_blocking=True,
    )

    with torch.no_grad():
        if amp_enabled:
            with torch.autocast(
                device_type="cuda",
                dtype=torch.float16,
            ):
                logits = model(
                    x
                )
        else:
            logits = model(
                x
            )

        prob = torch.sigmoid(
            logits
        )

    prob_np = (
        prob[:, 0]
        .detach()
        .float()
        .cpu()
        .numpy()
    )

    prob_np *= valid_np

    return prob_np


# =============================================================================
# VISUALIZATION
# =============================================================================

def highlight_prediction(
    original_bgr: np.ndarray,
    binary_mask: np.ndarray,
    valid64: np.ndarray,
) -> np.ndarray:
    base = original_bgr.copy()

    valid_bool = (
        valid64.astype(bool)
    )

    pred_bool = (
        binary_mask.astype(bool)
        & valid_bool
    )

    if DIM_INVALID_AREA:
        invalid = ~valid_bool

        temp = base.astype(
            np.float32
        )

        temp[invalid] *= float(
            INVALID_DIM_FACTOR
        )

        base = np.clip(
            temp,
            0,
            255,
        ).astype(np.uint8)

    result = base.copy()

    if pred_bool.any():
        color_layer = np.zeros_like(
            base
        )

        color_layer[:] = np.asarray(
            MASK_COLOR_BGR,
            dtype=np.uint8,
        )

        blended = cv2.addWeighted(
            base,
            1.0 - OVERLAY_ALPHA,
            color_layer,
            OVERLAY_ALPHA,
            0.0,
        )

        result[pred_bool] = (
            blended[pred_bool]
        )

    if (
        DRAW_CONTOUR
        and pred_bool.any()
    ):
        mask_u8 = (
            pred_bool.astype(
                np.uint8
            )
            * 255
        )

        contours, _ = cv2.findContours(
            mask_u8,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        cv2.drawContours(
            result,
            contours,
            -1,
            CONTOUR_COLOR_BGR,
            CONTOUR_THICKNESS,
            lineType=cv2.LINE_AA,
        )

    return result


def original_panel(
    original64: np.ndarray,
    valid64: np.ndarray,
) -> np.ndarray:
    panel = original64.copy()

    if DRAW_VALID_CONTOUR_ON_ORIGINAL:
        contours, _ = cv2.findContours(
            (
                valid64.astype(
                    np.uint8
                )
                * 255
            ),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        cv2.drawContours(
            panel,
            contours,
            -1,
            VALID_CONTOUR_COLOR_BGR,
            1,
            lineType=cv2.LINE_AA,
        )

    return panel


def resize_panel(
    panel64: np.ndarray,
) -> np.ndarray:
    if OUTPUT_SCALE <= 1:
        return panel64.copy()

    return cv2.resize(
        panel64,
        (
            panel64.shape[1]
            * OUTPUT_SCALE,
            panel64.shape[0]
            * OUTPUT_SCALE,
        ),
        interpolation=OUTPUT_RESIZE_INTERPOLATION,
    )


def add_header(
    panel: np.ndarray,
    title: str,
) -> np.ndarray:
    if not DRAW_PANEL_LABELS:
        return panel

    header = np.zeros(
        (
            HEADER_HEIGHT,
            panel.shape[1],
            3,
        ),
        dtype=np.uint8,
    )

    text_size, _ = cv2.getTextSize(
        title,
        LABEL_FONT,
        LABEL_FONT_SCALE,
        LABEL_THICKNESS,
    )

    x = max(
        8,
        (
            panel.shape[1]
            - text_size[0]
        ) // 2,
    )

    y = (
        HEADER_HEIGHT
        + text_size[1]
    ) // 2 - 2

    cv2.putText(
        header,
        title,
        (x, y),
        LABEL_FONT,
        LABEL_FONT_SCALE,
        (255, 255, 255),
        LABEL_THICKNESS,
        cv2.LINE_AA,
    )

    return np.concatenate(
        [
            header,
            panel,
        ],
        axis=0,
    )


def ensure_png_relative(
    relative: Path,
) -> Path:
    return relative.with_suffix(
        ".png"
    )


def save_comparison(
    relative: Path,
    original64: np.ndarray,
    valid64: np.ndarray,
    mlp_probability: np.ndarray,
    cnn_probability: np.ndarray,
    mlp_threshold: float,
    cnn_threshold: float,
) -> None:
    mlp_binary = (
        mlp_probability
        >= mlp_threshold
    ).astype(np.uint8)

    cnn_binary = (
        cnn_probability
        >= cnn_threshold
    ).astype(np.uint8)

    mlp_binary *= valid64
    cnn_binary *= valid64

    original64_panel = original_panel(
        original64,
        valid64,
    )

    mlp64_panel = highlight_prediction(
        original64,
        mlp_binary,
        valid64,
    )

    cnn64_panel = highlight_prediction(
        original64,
        cnn_binary,
        valid64,
    )

    original_big = resize_panel(
        original64_panel
    )

    mlp_big = resize_panel(
        mlp64_panel
    )

    cnn_big = resize_panel(
        cnn64_panel
    )

    original_title = "ORIGINAL"

    if DRAW_THRESHOLD_IN_LABEL:
        mlp_title = (
            f"MLP e1108D  |  T={mlp_threshold:.3f}"
        )

        cnn_title = (
            f"CNN U3  |  T={cnn_threshold:.3f}"
        )
    else:
        mlp_title = "MLP e1108D"
        cnn_title = "CNN U3"

    original_big = add_header(
        original_big,
        original_title,
    )

    mlp_big = add_header(
        mlp_big,
        mlp_title,
    )

    cnn_big = add_header(
        cnn_big,
        cnn_title,
    )

    comparison = np.concatenate(
        [
            original_big,
            mlp_big,
            cnn_big,
        ],
        axis=1,
    )

    relative_png = ensure_png_relative(
        relative
    )

    comparison_path = (
        OUTPUT_DIR
        / COMPARISON_SUBDIR
        / relative_png
    )

    comparison_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cv2.imwrite(
        str(comparison_path),
        comparison,
    )

    if SAVE_ORIGINAL_PANEL:
        path = (
            OUTPUT_DIR
            / ORIGINAL_SUBDIR
            / relative_png
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(path),
            original_big,
        )

    if SAVE_MLP_PANEL:
        path = (
            OUTPUT_DIR
            / MLP_SUBDIR
            / relative_png
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(path),
            mlp_big,
        )

    if SAVE_CNN_PANEL:
        path = (
            OUTPUT_DIR
            / CNN_SUBDIR
            / relative_png
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(path),
            cnn_big,
        )

    if SAVE_MLP_MASK:
        path = (
            OUTPUT_DIR
            / MLP_MASK_SUBDIR
            / relative_png
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(path),
            resize_panel(
                mlp_binary * 255
            ),
        )

    if SAVE_CNN_MASK:
        path = (
            OUTPUT_DIR
            / CNN_MASK_SUBDIR
            / relative_png
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(path),
            resize_panel(
                cnn_binary * 255
            ),
        )

    if SAVE_DISAGREEMENT_MASK:
        disagreement = (
            (mlp_binary != cnn_binary)
            & valid64.astype(bool)
        ).astype(np.uint8)

        disagreement_vis = np.zeros_like(
            original64
        )

        disagreement_vis[
            disagreement.astype(bool)
        ] = np.asarray(
            DISAGREEMENT_COLOR_BGR,
            dtype=np.uint8,
        )

        path = (
            OUTPUT_DIR
            / DISAGREEMENT_SUBDIR
            / relative_png
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(path),
            resize_panel(
                disagreement_vis
            ),
        )


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    t0 = time.time()

    device = choose_device()

    amp_enabled = bool(
        USE_AMP
        and device.type == "cuda"
    )

    print("=" * 84)
    print("MLP e1108D vs CNN U3 - parallel station inference")
    print("=" * 84)

    print(
        f"Device          : {device}"
    )

    print(
        f"AMP             : {amp_enabled}"
    )

    print(
        f"Input           : "
        f"{INPUT_IMAGE_DIR.resolve()}"
    )

    print(
        f"Valid           : "
        f"{VALID_MASK_DIR.resolve()}"
    )

    print(
        f"MLP checkpoint  : "
        f"{MLP_CHECKPOINT_PATH.resolve()}"
    )

    print(
        f"CNN checkpoint  : "
        f"{CNN_CHECKPOINT_PATH.resolve()}"
    )

    print(
        f"Output          : "
        f"{OUTPUT_DIR.resolve()}"
    )

    print()

    (
        mlp_model,
        mlp_mean,
        mlp_std,
        mlp_threshold,
        mlp_checkpoint,
    ) = load_mlp(
        device
    )

    (
        cnn_model,
        cnn_rgb_mean,
        cnn_rgb_std,
        cnn_threshold,
        cnn_checkpoint,
    ) = load_cnn(
        device
    )

    print(
        f"MLP epoch       : "
        f"{mlp_checkpoint.get('epoch', 'unknown')}"
    )

    print(
        f"MLP best Dice   : "
        f"{mlp_checkpoint.get('best_val_dice', 'unknown')}"
    )

    print(
        f"MLP threshold   : "
        f"{mlp_threshold:.4f}"
    )

    print()

    print(
        f"CNN epoch       : "
        f"{cnn_checkpoint.get('epoch', 'unknown')}"
    )

    print(
        f"CNN best Dice   : "
        f"{cnn_checkpoint.get('best_val_dice', 'unknown')}"
    )

    print(
        f"CNN threshold   : "
        f"{cnn_threshold:.4f}"
    )

    print()

    image_paths = discover_images()

    print(
        f"Found           : "
        f"{len(image_paths)} station images"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings = {
        "input_image_dir": str(
            INPUT_IMAGE_DIR
        ),
        "valid_mask_dir": str(
            VALID_MASK_DIR
        ),
        "mlp_checkpoint": str(
            MLP_CHECKPOINT_PATH
        ),
        "mlp_epoch": (
            mlp_checkpoint.get(
                "epoch"
            )
        ),
        "mlp_best_val_dice": (
            mlp_checkpoint.get(
                "best_val_dice"
            )
        ),
        "mlp_threshold": (
            mlp_threshold
        ),
        "cnn_checkpoint": str(
            CNN_CHECKPOINT_PATH
        ),
        "cnn_epoch": (
            cnn_checkpoint.get(
                "epoch"
            )
        ),
        "cnn_best_val_dice": (
            cnn_checkpoint.get(
                "best_val_dice"
            )
        ),
        "cnn_threshold": (
            cnn_threshold
        ),
        "device": str(
            device
        ),
        "amp": (
            amp_enabled
        ),
        "output_scale": (
            OUTPUT_SCALE
        ),
        "panel_order": [
            "original",
            "mlp_e1108D",
            "cnn_u3",
        ],
    }

    (
        OUTPUT_DIR
        / "inference_settings.json"
    ).write_text(
        json.dumps(
            settings,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    processed = 0
    skipped = 0

    mlp_features: List[
        np.ndarray
    ] = []

    cnn_inputs: List[
        np.ndarray
    ] = []

    valids: List[
        np.ndarray
    ] = []

    originals: List[
        np.ndarray
    ] = []

    relatives: List[
        Path
    ] = []

    def flush_batch() -> None:
        nonlocal processed

        if not mlp_features:
            return

        mlp_probs = run_mlp_batch(
            mlp_model,
            mlp_features,
            valids,
            device,
            amp_enabled,
        )

        cnn_probs = run_cnn_batch(
            cnn_model,
            cnn_inputs,
            valids,
            device,
            amp_enabled,
        )

        for (
            relative,
            original64,
            valid64,
            mlp_prob,
            cnn_prob,
        ) in zip(
            relatives,
            originals,
            valids,
            mlp_probs,
            cnn_probs,
        ):
            save_comparison(
                relative,
                original64,
                valid64,
                mlp_prob,
                cnn_prob,
                mlp_threshold,
                cnn_threshold,
            )

            processed += 1

        mlp_features.clear()
        cnn_inputs.clear()
        valids.clear()
        originals.clear()
        relatives.clear()

    for index, image_path in enumerate(
        image_paths,
        start=1,
    ):
        loaded = read_station_and_valid(
            image_path
        )

        if loaded is None:
            skipped += 1
            continue

        (
            image_bgr,
            valid,
            relative,
        ) = loaded

        try:
            original64, valid64 = prepare_64(
                image_bgr,
                valid,
            )

            # IMPORTANT:
            # Keep the original MLP run behavior:
            # feature extractor sees the source image + valid mask.
            mlp_feature = make_mlp_feature(
                image_bgr,
                valid,
                mlp_mean,
                mlp_std,
            )

            # CNN receives its own exact training preprocessing.
            cnn_input = make_cnn_input(
                original64,
                valid64,
                cnn_rgb_mean,
                cnn_rgb_std,
            )

        except Exception as exc:
            print(
                f"[SKIP] {relative}: "
                f"{exc}"
            )
            skipped += 1
            continue

        mlp_features.append(
            mlp_feature
        )

        cnn_inputs.append(
            cnn_input
        )

        valids.append(
            valid64
        )

        originals.append(
            original64
        )

        relatives.append(
            relative
        )

        if (
            len(mlp_features)
            >= INFERENCE_BATCH_SIZE
        ):
            flush_batch()

        if index % 100 == 0:
            print(
                f"[INFO] scanned={index}/{len(image_paths)} "
                f"processed={processed} skipped={skipped}"
            )

    flush_batch()

    elapsed = (
        time.time()
        - t0
    )

    print()
    print("=" * 84)
    print("DONE")
    print("=" * 84)

    print(
        f"Processed       : "
        f"{processed}"
    )

    print(
        f"Skipped         : "
        f"{skipped}"
    )

    print(
        f"Elapsed         : "
        f"{elapsed:.2f} s"
    )

    if processed > 0:
        print(
            f"Average         : "
            f"{1000.0 * elapsed / processed:.2f} ms/image "
            "(MLP feature extraction + both models + I/O + saving)"
        )

    print(
        f"Comparison dir  : "
        f"{(OUTPUT_DIR / COMPARISON_SUBDIR).resolve()}"
    )

    if OUTPUT_SCALE == 8:
        print(
            "Comparison size : "
            "1536 x 550 px "
            "(3 x 512 panels + header)"
        )


if __name__ == "__main__":
    main()
