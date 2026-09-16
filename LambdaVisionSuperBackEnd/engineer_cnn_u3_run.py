"""
Run / visualize Engineer CNN U3 predictions on station images.
==============================================================

Input
-----
A folder of station images plus the corresponding VALID masks.

Output
------
One highlighted image per station:
    original image
    + semi-transparent predicted mask
    + predicted contour

Important
---------
- GT masks are NOT required for inference.
- RGB preprocessing is reconstructed from best.pt:
    * RGB -> [0,1]
    * invalid pixels -> median RGB of valid pixels
    * RGB standardization using TRAIN-only mean/std saved in checkpoint
    * append Valid as channel #4
- Final probability is multiplied by Valid.
- Model prediction remains 64x64; only saved visualizations are enlarged.

No command-line arguments are used. Edit CONFIG below.
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

# If a valid mask is missing:
#   False -> skip image (recommended)
#   True  -> assume all 64x64 pixels are valid
ALLOW_FULL_VALID_IF_MISSING = False


# -----------------------------------------------------------------------------
# Model checkpoint
# -----------------------------------------------------------------------------

CHECKPOINT_PATH = Path(
    "/home/hieu/Desktop/Nidec Vision/run/"
    "engineer_cnn_u3_v1/checkpoints/best.pt"
)


# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------

OUTPUT_DIR = Path(
    "/home/hieu/Desktop/Nidec Vision/run/"
    "engineer_cnn_u3_v1/test_run"
)

HIGHLIGHT_SUBDIR = "highlighted"

SAVE_BINARY_MASK = False
SAVE_PROBABILITY_MAP = False
SAVE_SIDE_BY_SIDE = False

MASK_SUBDIR = "masks"
PROB_SUBDIR = "probability"
SIDE_BY_SIDE_SUBDIR = "side_by_side"


# -----------------------------------------------------------------------------
# Prediction
# -----------------------------------------------------------------------------

# None -> use threshold stored in checkpoint.
# Set e.g. 0.45 to override.
PREDICTION_THRESHOLD_OVERRIDE: Optional[float] = None

INFERENCE_BATCH_SIZE = 128

# "auto", "cuda", "cpu", "mps"
DEVICE = "auto"

USE_AMP = True


# -----------------------------------------------------------------------------
# Visualization
# -----------------------------------------------------------------------------

# OpenCV BGR colors.
MASK_COLOR_BGR = (0, 0, 255)       # red
CONTOUR_COLOR_BGR = (0, 255, 255)  # yellow

OVERLAY_ALPHA = 0.42

DRAW_CONTOUR = True
CONTOUR_THICKNESS = 1

DIM_INVALID_AREA = False
INVALID_DIM_FACTOR = 0.45

# Better leave False for 64x64 stations so text does not cover the object.
DRAW_INFO_TEXT = False

# Enlarge ONLY the saved visualization.
# 64x64 * 8 = 512x512
OUTPUT_SCALE = 8
OUTPUT_RESIZE_INTERPOLATION = cv2.INTER_NEAREST


# -----------------------------------------------------------------------------
# File types
# -----------------------------------------------------------------------------

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
}


# =============================================================================
# DEVICE / CHECKPOINT
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
    checkpoint_path: Path,
    device: torch.device,
):
    try:
        return torch.load(
            checkpoint_path,
            map_location=device,
            weights_only=False,
        )
    except TypeError:
        return torch.load(
            checkpoint_path,
            map_location=device,
        )


def config_from_checkpoint(
    checkpoint: Dict,
) -> EngineerCNNU3Config:
    raw_cfg = checkpoint.get("model_config")

    if not raw_cfg:
        print(
            "[WARN] checkpoint has no model_config; "
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


def load_model_and_preprocessing(
    checkpoint_path: Path,
    device: torch.device,
) -> Tuple[
    EngineerCNNU3,
    np.ndarray,
    np.ndarray,
    float,
    Dict,
]:
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: "
            f"{checkpoint_path.resolve()}"
        )

    checkpoint = safe_torch_load(
        checkpoint_path,
        device,
    )

    if "model_state_dict" not in checkpoint:
        raise KeyError(
            "Checkpoint does not contain model_state_dict."
        )

    cfg = config_from_checkpoint(
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
            "Checkpoint does not contain rgb_mean."
        )

    if "rgb_std" not in checkpoint:
        raise KeyError(
            "Checkpoint does not contain rgb_std."
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
            f"rgb_mean shape={rgb_mean.shape}, expected (3,)"
        )

    if rgb_std.shape != (3,):
        raise ValueError(
            f"rgb_std shape={rgb_std.shape}, expected (3,)"
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
        if PREDICTION_THRESHOLD_OVERRIDE is None
        else float(PREDICTION_THRESHOLD_OVERRIDE)
    )

    if not (
        0.0 <= threshold <= 1.0
    ):
        raise ValueError(
            f"threshold must be in [0,1], got {threshold}"
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


# =============================================================================
# PREPROCESSING
# =============================================================================

def read_station_and_valid(
    image_path: Path,
) -> Optional[
    Tuple[np.ndarray, np.ndarray, Path]
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
            f"[WARN] Missing valid mask for {relative}; "
            "using full-valid mask."
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


def prepare_64(
    image_bgr: np.ndarray,
    valid_mask: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:

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

    valid_bin = (
        valid_mask > 0
    ).astype(np.uint8)

    if not valid_bin.any():
        raise RuntimeError(
            "Station has zero valid pixels."
        )

    return (
        image_bgr,
        valid_bin,
    )


def make_cnn_input(
    image_bgr: np.ndarray,
    valid_mask: np.ndarray,
    rgb_mean: np.ndarray,
    rgb_std: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns:
        cnn_input   : [4,64,64], float32
        original64  : [64,64,3], uint8 BGR
        valid64     : [64,64], uint8 {0,1}
    """
    original64, valid64 = prepare_64(
        image_bgr,
        valid_mask,
    )

    image_rgb = cv2.cvtColor(
        original64,
        cv2.COLOR_BGR2RGB,
    ).astype(
        np.float32
    ) / 255.0

    valid_bool = valid64.astype(
        bool
    )

    # Same preprocessing as training:
    # invalid RGB <- per-channel median over valid pixels.
    fill = np.median(
        image_rgb[valid_bool],
        axis=0,
    ).astype(np.float32)

    image_rgb = image_rgb.copy()
    image_rgb[~valid_bool] = fill

    # Train-only RGB standardization.
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
            f"Bad CNN input shape: {cnn_input.shape}"
        )

    if not np.isfinite(
        cnn_input
    ).all():
        raise RuntimeError(
            "Non-finite value found in CNN input."
        )

    return (
        cnn_input,
        original64,
        valid64,
    )


# =============================================================================
# VISUALIZATION
# =============================================================================

def highlight_prediction(
    original_bgr: np.ndarray,
    binary_mask: np.ndarray,
    valid_mask: np.ndarray,
    probability: np.ndarray,
    threshold: float,
) -> np.ndarray:

    base = original_bgr.copy()

    valid_bool = valid_mask.astype(bool)

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

        color_layer[:] = np.array(
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

    if DRAW_INFO_TEXT:
        predicted_pixels = int(
            pred_bool.sum()
        )

        valid_pixels = max(
            int(valid_bool.sum()),
            1,
        )

        predicted_ratio = (
            predicted_pixels
            / valid_pixels
        )

        mean_prob = (
            float(
                probability[
                    pred_bool
                ].mean()
            )
            if pred_bool.any()
            else 0.0
        )

        text = (
            f"T={threshold:.2f} "
            f"Area={predicted_ratio:.2f} "
            f"P={mean_prob:.2f}"
        )

        cv2.rectangle(
            result,
            (0, 0),
            (63, 18),
            (0, 0, 0),
            thickness=-1,
        )

        cv2.putText(
            result,
            text,
            (2, 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.27,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    return result


def make_probability_visualization(
    probability: np.ndarray,
    valid_mask: np.ndarray,
) -> np.ndarray:

    p = probability.copy()

    p *= valid_mask.astype(
        np.float32
    )

    gray = np.clip(
        p * 255.0,
        0,
        255,
    ).astype(np.uint8)

    return cv2.applyColorMap(
        gray,
        cv2.COLORMAP_JET,
    )


def resize_for_output(
    image: np.ndarray,
) -> np.ndarray:

    if OUTPUT_SCALE <= 1:
        return image

    h, w = image.shape[:2]

    return cv2.resize(
        image,
        (
            w * OUTPUT_SCALE,
            h * OUTPUT_SCALE,
        ),
        interpolation=(
            OUTPUT_RESIZE_INTERPOLATION
        ),
    )


def save_outputs(
    relative: Path,
    original64: np.ndarray,
    valid64: np.ndarray,
    probability: np.ndarray,
    binary_mask: np.ndarray,
    threshold: float,
) -> None:

    highlighted = highlight_prediction(
        original64,
        binary_mask,
        valid64,
        probability,
        threshold,
    )

    highlight_path = (
        OUTPUT_DIR
        / HIGHLIGHT_SUBDIR
        / relative
    )

    highlight_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cv2.imwrite(
        str(highlight_path),
        resize_for_output(
            highlighted
        ),
    )

    if SAVE_BINARY_MASK:
        mask_path = (
            OUTPUT_DIR
            / MASK_SUBDIR
            / relative
        )

        mask_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        mask_vis = (
            binary_mask.astype(
                np.uint8
            )
            * 255
        )

        cv2.imwrite(
            str(mask_path),
            resize_for_output(
                mask_vis
            ),
        )

    if SAVE_PROBABILITY_MAP:
        prob_path = (
            OUTPUT_DIR
            / PROB_SUBDIR
            / relative
        )

        prob_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        prob_vis = (
            make_probability_visualization(
                probability,
                valid64,
            )
        )

        cv2.imwrite(
            str(prob_path),
            resize_for_output(
                prob_vis
            ),
        )

    if SAVE_SIDE_BY_SIDE:
        comparison = np.concatenate(
            [
                original64,
                highlighted,
            ],
            axis=1,
        )

        side_path = (
            OUTPUT_DIR
            / SIDE_BY_SIDE_SUBDIR
            / relative
        )

        side_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(side_path),
            resize_for_output(
                comparison
            ),
        )


# =============================================================================
# INFERENCE
# =============================================================================

def main() -> None:
    device = choose_device()

    amp_enabled = bool(
        USE_AMP
        and device.type == "cuda"
    )

    print("=" * 78)
    print("Engineer CNN U3 - station inference")
    print("=" * 78)

    print(f"Device      : {device}")
    print(f"AMP         : {amp_enabled}")
    print(
        f"Checkpoint  : "
        f"{CHECKPOINT_PATH.resolve()}"
    )

    (
        model,
        rgb_mean,
        rgb_std,
        threshold,
        checkpoint,
    ) = load_model_and_preprocessing(
        CHECKPOINT_PATH,
        device,
    )

    print(
        f"Checkpoint epoch : "
        f"{checkpoint.get('epoch', 'unknown')}"
    )

    print(
        f"Threshold        : "
        f"{threshold:.4f}"
    )

    print(
        f"RGB mean         : "
        f"{rgb_mean.tolist()}"
    )

    print(
        f"RGB std          : "
        f"{rgb_std.tolist()}"
    )

    print()

    images = discover_images()

    print(
        f"Images found     : "
        f"{len(images)}"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings = {
        "checkpoint": str(
            CHECKPOINT_PATH
        ),
        "checkpoint_epoch": (
            checkpoint.get(
                "epoch"
            )
        ),
        "threshold": threshold,
        "rgb_mean": (
            rgb_mean.tolist()
        ),
        "rgb_std": (
            rgb_std.tolist()
        ),
        "input_image_dir": str(
            INPUT_IMAGE_DIR
        ),
        "valid_mask_dir": str(
            VALID_MASK_DIR
        ),
        "output_scale": (
            OUTPUT_SCALE
        ),
        "overlay_alpha": (
            OVERLAY_ALPHA
        ),
    }

    (
        OUTPUT_DIR
        / "inference_settings.json"
    ).write_text(
        json.dumps(
            settings,
            indent=2,
        ),
        encoding="utf-8",
    )

    t0 = time.time()

    processed = 0
    skipped = 0

    batch_inputs: List[np.ndarray] = []
    batch_originals: List[np.ndarray] = []
    batch_valids: List[np.ndarray] = []
    batch_relatives: List[Path] = []

    def flush_batch() -> None:
        nonlocal processed

        if not batch_inputs:
            return

        x_np = np.stack(
            batch_inputs,
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

            probs = torch.sigmoid(
                logits
            ).float().cpu().numpy()

        for i in range(
            probs.shape[0]
        ):
            probability = probs[
                i,
                0,
            ].astype(np.float32)

            valid64 = batch_valids[
                i
            ]

            # Explicit inference masking.
            probability *= (
                valid64.astype(
                    np.float32
                )
            )

            binary_mask = (
                probability
                >= threshold
            ).astype(np.uint8)

            save_outputs(
                batch_relatives[i],
                batch_originals[i],
                valid64,
                probability,
                binary_mask,
                threshold,
            )

            processed += 1

        batch_inputs.clear()
        batch_originals.clear()
        batch_valids.clear()
        batch_relatives.clear()

    for image_path in images:
        item = read_station_and_valid(
            image_path
        )

        if item is None:
            skipped += 1
            continue

        (
            image_bgr,
            valid,
            relative,
        ) = item

        try:
            (
                cnn_input,
                original64,
                valid64,
            ) = make_cnn_input(
                image_bgr,
                valid,
                rgb_mean,
                rgb_std,
            )

        except Exception as exc:
            print(
                f"[SKIP] {relative}: "
                f"{exc}"
            )
            skipped += 1
            continue

        batch_inputs.append(
            cnn_input
        )

        batch_originals.append(
            original64
        )

        batch_valids.append(
            valid64
        )

        batch_relatives.append(
            relative
        )

        if (
            len(batch_inputs)
            >= INFERENCE_BATCH_SIZE
        ):
            flush_batch()

    flush_batch()

    elapsed = (
        time.time()
        - t0
    )

    print()
    print("=" * 78)
    print("DONE")
    print("=" * 78)

    print(
        f"Processed : {processed}"
    )

    print(
        f"Skipped   : {skipped}"
    )

    print(
        f"Elapsed   : {elapsed:.2f}s"
    )

    if processed > 0:
        print(
            f"Average   : "
            f"{1000.0 * elapsed / processed:.2f} ms/image "
            "(includes image I/O + preprocessing + saving)"
        )

    print(
        f"Output    : "
        f"{OUTPUT_DIR.resolve()}"
    )


if __name__ == "__main__":
    main()
