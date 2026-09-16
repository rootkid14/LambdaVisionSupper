
"""
Test / visualize Engineer MLP predictions on station images.
===========================================================

Input
-----
A folder of station images, plus the corresponding VALID masks used by the
5204D extractor.

Output
------
One highlighted image per station:
    original image + semi-transparent predicted mask + predicted contour

This script uses:
    e5204_metrics_extractor.py
    e5204_neural_network.py
    best.pt checkpoint produced by e5204_train.py

No command-line arguments are used. Edit the CONFIG section below.

Important
---------
- The model was trained on 5204D features created from IMAGE + VALID MASK.
  Therefore using the real valid mask at inference is strongly recommended.
- GT masks are NOT required for inference.
- All 5204 features are standardized with mean/std stored inside the checkpoint.
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

from e5204_metrics_extractor import (
    TOTAL_FEATURE_DIM,
    extract_feature_vector,
)
from e5204_neural_network import (
    EngineerMLP,
    EngineerMLPConfig,
)


# =============================================================================
# CONFIG - EDIT HERE
# =============================================================================

# -----------------------------------------------------------------------------
# Input
# -----------------------------------------------------------------------------

# Folder containing the 64x64 station images to test.
INPUT_IMAGE_DIR = Path("/home/hieu/Desktop/Nidec Vision/stations_divided/images")

# Corresponding valid masks. The script searches the same relative path/name.
VALID_MASK_DIR = Path("/home/hieu/Desktop/Nidec Vision/stations_divided/valid")

# If a valid mask is missing:
#   False -> skip that image (recommended)
#   True  -> assume all 64x64 pixels are valid
#
# WARNING:
# Using full-valid changes the 100D valid-geometry block and may create
# distribution shift if the model was trained with non-rectangular valid masks.
ALLOW_FULL_VALID_IF_MISSING = False


# -----------------------------------------------------------------------------
# Model checkpoint
# -----------------------------------------------------------------------------

CHECKPOINT_PATH = Path(
    "/home/hieu/Desktop/Nidec Vision/run/engineer_mlp_5204_v2/checkpoints/best.pt"
)


# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------

OUTPUT_DIR = Path("/home/hieu/Desktop/Nidec Vision/run/engineer_mlp_5204_v2/test_run")

# Main requested output:
# original image with predicted region highlighted.
HIGHLIGHT_SUBDIR = "highlighted"

# Optional diagnostic outputs.
SAVE_BINARY_MASK = False
SAVE_PROBABILITY_MAP = False
SAVE_SIDE_BY_SIDE = False

MASK_SUBDIR = "masks"
PROB_SUBDIR = "probability"
SIDE_BY_SIDE_SUBDIR = "side_by_side"


# -----------------------------------------------------------------------------
# Prediction
# -----------------------------------------------------------------------------

# None -> use prediction_threshold saved in best.pt.
# Set e.g. 0.45 if you want to test a manually chosen threshold.
PREDICTION_THRESHOLD_OVERRIDE: Optional[float] = None

# Feature extraction is CPU work. Model inference will run in batches.
INFERENCE_BATCH_SIZE = 128

# Device:
#   "auto", "cuda", "cpu", or "mps"
DEVICE = "auto"

# Use autocast during CUDA inference.
USE_AMP = True


# -----------------------------------------------------------------------------
# Highlight appearance
# -----------------------------------------------------------------------------

# OpenCV uses BGR order.
MASK_COLOR_BGR = (0, 0, 255)       # red
CONTOUR_COLOR_BGR = (0, 255, 255)  # yellow

# 0 -> original only, 1 -> solid mask color.
OVERLAY_ALPHA = 0.42

DRAW_CONTOUR = True
CONTOUR_THICKNESS = 1

# Dim pixels outside valid ROI slightly so the valid measurement domain is clear.
DIM_INVALID_AREA = False
INVALID_DIM_FACTOR = 0.45

# Optional text overlay.
DRAW_INFO_TEXT = True


# -----------------------------------------------------------------------------
# File types
# -----------------------------------------------------------------------------

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"
}


# -----------------------------------------------------------------------------
# Output display resize
# -----------------------------------------------------------------------------
# Station is only 64x64, so enlarge the FINAL visualization before saving.
# 8x -> 512x512.
OUTPUT_SCALE = 8

# For inspecting segmentation pixels/boundaries, INTER_NEAREST is preferable.
# Change to cv2.INTER_CUBIC if you want a smoother-looking preview.
OUTPUT_RESIZE_INTERPOLATION = cv2.INTER_NEAREST


# ----------------------------------------------------------------------------


# =============================================================================
# DEVICE / MODEL
# =============================================================================

def choose_device() -> torch.device:
    requested = DEVICE.lower()

    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("DEVICE='cuda' but CUDA is not available.")
        return torch.device("cuda")

    if requested == "mps":
        if not (
            hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
        ):
            raise RuntimeError("DEVICE='mps' but MPS is not available.")
        return torch.device("mps")

    if requested == "cpu":
        return torch.device("cpu")

    if requested != "auto":
        raise ValueError(
            "DEVICE must be one of: 'auto', 'cuda', 'cpu', 'mps'"
        )

    if torch.cuda.is_available():
        return torch.device("cuda")

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")


def _config_from_checkpoint(checkpoint: Dict) -> EngineerMLPConfig:
    """
    Reconstruct EngineerMLPConfig from the checkpoint.

    The filter makes the loader tolerant if a future checkpoint contains
    extra config keys not present in this version of EngineerMLPConfig.
    """
    raw_cfg = checkpoint.get("model_config")

    if not raw_cfg:
        print(
            "[WARN] checkpoint has no model_config; "
            "using EngineerMLPConfig() defaults."
        )
        return EngineerMLPConfig()

    allowed = {f.name for f in fields(EngineerMLPConfig)}
    filtered = {
        k: v
        for k, v in raw_cfg.items()
        if k in allowed
    }

    return EngineerMLPConfig(**filtered)


def load_model_and_standardizer(
    checkpoint_path: Path,
    device: torch.device,
) -> Tuple[EngineerMLP, np.ndarray, np.ndarray, float, Dict]:
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_path.resolve()}"
        )

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )

    if "model_state_dict" not in checkpoint:
        raise KeyError(
            "Checkpoint does not contain 'model_state_dict'."
        )

    model_cfg = _config_from_checkpoint(checkpoint)
    model = EngineerMLP(model_cfg)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    if "standardizer_mean" not in checkpoint:
        raise KeyError(
            "Checkpoint does not contain 'standardizer_mean'."
        )
    if "standardizer_std" not in checkpoint:
        raise KeyError(
            "Checkpoint does not contain 'standardizer_std'."
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
            f"standardizer mean shape={mean.shape}, "
            f"expected ({TOTAL_FEATURE_DIM},)"
        )

    if std.shape != (TOTAL_FEATURE_DIM,):
        raise ValueError(
            f"standardizer std shape={std.shape}, "
            f"expected ({TOTAL_FEATURE_DIM},)"
        )

    # Defensive protection against an abnormal/legacy checkpoint.
    std = std.copy()
    std[np.abs(std) < 1e-12] = 1.0

    saved_threshold = float(
        checkpoint.get("prediction_threshold", 0.5)
    )

    threshold = (
        saved_threshold
        if PREDICTION_THRESHOLD_OVERRIDE is None
        else float(PREDICTION_THRESHOLD_OVERRIDE)
    )

    if not (0.0 <= threshold <= 1.0):
        raise ValueError(
            f"Prediction threshold must be in [0,1], got {threshold}"
        )

    return model, mean, std, threshold, checkpoint


# =============================================================================
# FILE DISCOVERY
# =============================================================================

def find_corresponding_mask(
    mask_root: Path,
    relative_image: Path,
) -> Optional[Path]:
    """
    First try exact relative path. Then try the same stem with any supported
    image extension.
    """
    exact = mask_root / relative_image
    if exact.exists():
        return exact

    parent = mask_root / relative_image.parent
    if not parent.exists():
        return None

    for ext in IMAGE_EXTENSIONS:
        candidate = parent / f"{relative_image.stem}{ext}"
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
            f"No images found under: {INPUT_IMAGE_DIR.resolve()}"
        )

    return images


# =============================================================================
# PREPROCESSING
# =============================================================================

def read_station_and_valid(
    image_path: Path,
) -> Optional[Tuple[np.ndarray, np.ndarray, Path]]:
    relative = image_path.relative_to(INPUT_IMAGE_DIR)

    image = cv2.imread(
        str(image_path),
        cv2.IMREAD_COLOR,
    )
    if image is None:
        print(f"[SKIP] Could not read image: {image_path}")
        return None

    valid_path = find_corresponding_mask(
        VALID_MASK_DIR,
        relative,
    )

    if valid_path is None:
        if not ALLOW_FULL_VALID_IF_MISSING:
            print(
                f"[SKIP] Missing valid mask for: {relative}"
            )
            return None

        print(
            f"[WARN] Missing valid mask for {relative}; "
            f"using full-valid mask."
        )
        valid = np.ones(
            image.shape[:2],
            dtype=np.uint8,
        ) * 255
    else:
        valid = cv2.imread(
            str(valid_path),
            cv2.IMREAD_GRAYSCALE,
        )
        if valid is None:
            print(
                f"[SKIP] Could not read valid mask: {valid_path}"
            )
            return None

    return image, valid, relative


def make_standardized_feature(
    image: np.ndarray,
    valid: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
) -> np.ndarray:
    raw = extract_feature_vector(
        image,
        valid,
        color_order="BGR",
    )

    if raw.shape != (TOTAL_FEATURE_DIM,):
        raise RuntimeError(
            f"Extractor returned {raw.shape}, "
            f"expected ({TOTAL_FEATURE_DIM},)"
        )

    standardized = (
        raw.astype(np.float32) - mean
    ) / std

    if not np.isfinite(standardized).all():
        bad = np.flatnonzero(
            ~np.isfinite(standardized)
        )
        raise RuntimeError(
            f"Non-finite standardized features at indices "
            f"{bad[:20].tolist()}"
        )

    return standardized.astype(np.float32)


# =============================================================================
# VISUALIZATION
# =============================================================================

def prepare_original_64(image: np.ndarray) -> np.ndarray:
    if image.shape[:2] == (64, 64):
        return image.copy()

    return cv2.resize(
        image,
        (64, 64),
        interpolation=cv2.INTER_AREA,
    )


def highlight_prediction(
    image_bgr: np.ndarray,
    binary_mask: np.ndarray,
    valid_mask: np.ndarray,
    probability: np.ndarray,
    threshold: float,
) -> np.ndarray:
    """
    Highlight predicted foreground on the original image.

    binary_mask, valid_mask, probability are all 64x64.
    """
    base = prepare_original_64(image_bgr)

    valid_bool = valid_mask.astype(bool)
    pred_bool = binary_mask.astype(bool) & valid_bool

    if DIM_INVALID_AREA:
        invalid = ~valid_bool
        temp = base.astype(np.float32)
        temp[invalid] *= float(INVALID_DIM_FACTOR)
        base = np.clip(temp, 0, 255).astype(np.uint8)

    result = base.copy()

    # Semi-transparent fill only on predicted pixels.
    if pred_bool.any():
        color_layer = np.zeros_like(base)
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

        result[pred_bool] = blended[pred_bool]

    # Draw the boundary of the predicted mask.
    if DRAW_CONTOUR and pred_bool.any():
        mask_u8 = (
            pred_bool.astype(np.uint8) * 255
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
        predicted_pixels = int(pred_bool.sum())
        valid_pixels = max(int(valid_bool.sum()), 1)
        predicted_ratio = predicted_pixels / valid_pixels

        if pred_bool.any():
            mean_prob_inside = float(
                probability[pred_bool].mean()
            )
        else:
            mean_prob_inside = 0.0

        text1 = (
            f"thr={threshold:.3f} "
            f"area={predicted_ratio*100:.1f}%"
        )
        text2 = f"meanP={mean_prob_inside:.3f}"

        cv2.rectangle(
            result,
            (0, 0),
            (63, 19),
            (0, 0, 0),
            thickness=-1,
        )

        cv2.putText(
            result,
            text1,
            (2, 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.22,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            result,
            text2,
            (2, 17),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.22,
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
    p[valid_mask == 0] = 0.0
    return np.clip(
        p * 255.0,
        0,
        255,
    ).astype(np.uint8)


def resize_for_output(image: np.ndarray) -> np.ndarray:
    """Enlarge a visualization image only for easier viewing/saving."""
    if OUTPUT_SCALE <= 1:
        return image

    h, w = image.shape[:2]
    return cv2.resize(
        image,
        (w * OUTPUT_SCALE, h * OUTPUT_SCALE),
        interpolation=OUTPUT_RESIZE_INTERPOLATION,
    )


def save_outputs(
    relative: Path,
    image: np.ndarray,
    valid64: np.ndarray,
    probability: np.ndarray,
    binary_mask: np.ndarray,
    threshold: float,
) -> None:
    highlighted = highlight_prediction(
        image,
        binary_mask,
        valid64,
        probability,
        threshold,
    )

    highlight_path = (
        OUTPUT_DIR
        / HIGHLIGHT_SUBDIR
        / relative.with_suffix(".png")
    )
    highlight_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    # Resize only the final visualization.
    # The model still predicts at the native 64x64 resolution.
    highlighted_to_save = resize_for_output(highlighted)

    cv2.imwrite(
        str(highlight_path),
        highlighted_to_save,
    )

    if SAVE_BINARY_MASK:
        mask_path = (
            OUTPUT_DIR
            / MASK_SUBDIR
            / relative.with_suffix(".png")
        )
        mask_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        mask_to_save = resize_for_output(
            binary_mask.astype(np.uint8) * 255
        )
        cv2.imwrite(
            str(mask_path),
            mask_to_save,
        )

    if SAVE_PROBABILITY_MAP:
        prob_path = (
            OUTPUT_DIR
            / PROB_SUBDIR
            / relative.with_suffix(".png")
        )
        prob_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        probability_vis = make_probability_visualization(
            probability,
            valid64,
        )
        probability_vis = resize_for_output(probability_vis)
        cv2.imwrite(
            str(prob_path),
            probability_vis,
        )

    if SAVE_SIDE_BY_SIDE:
        original64 = prepare_original_64(image)

        valid_contours, _ = cv2.findContours(
            (valid64 * 255).astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        original_panel = original64.copy()
        cv2.drawContours(
            original_panel,
            valid_contours,
            -1,
            (255, 255, 0),
            1,
            lineType=cv2.LINE_AA,
        )

        comparison = np.concatenate(
            [original_panel, highlighted],
            axis=1,
        )

        side_path = (
            OUTPUT_DIR
            / SIDE_BY_SIDE_SUBDIR
            / relative.with_suffix(".png")
        )
        side_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        comparison_to_save = resize_for_output(comparison)
        cv2.imwrite(
            str(side_path),
            comparison_to_save,
        )


# =============================================================================
# BATCH INFERENCE
# =============================================================================

def run_batch(
    model: EngineerMLP,
    device: torch.device,
    amp_enabled: bool,
    feature_batch: List[np.ndarray],
    valid_batch: List[np.ndarray],
) -> np.ndarray:
    """
    Returns probabilities with shape [B,64,64].
    """
    x_np = np.stack(
        feature_batch,
        axis=0,
    ).astype(np.float32)

    x = torch.from_numpy(x_np).to(device)

    valid_np = np.stack(
        valid_batch,
        axis=0,
    ).astype(np.float32)

    valid_tensor = torch.from_numpy(
        valid_np[:, None, :, :]
    ).to(device)

    with torch.no_grad():
        if amp_enabled:
            with torch.autocast(
                device_type="cuda",
                dtype=torch.float16,
            ):
                logits = model(x)
        else:
            logits = model(x)

        probability = torch.sigmoid(logits)

        # Enforce the known valid measurement domain.
        probability = probability * valid_tensor

    return (
        probability[:, 0]
        .detach()
        .float()
        .cpu()
        .numpy()
    )


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    t0 = time.time()

    device = choose_device()
    amp_enabled = bool(
        USE_AMP and device.type == "cuda"
    )

    print("========================================")
    print("Engineer MLP station inference")
    print("========================================")
    print(f"Device     : {device}")
    print(f"Checkpoint : {CHECKPOINT_PATH.resolve()}")
    print(f"Input      : {INPUT_IMAGE_DIR.resolve()}")
    print(f"Valid      : {VALID_MASK_DIR.resolve()}")
    print(f"Output     : {OUTPUT_DIR.resolve()}")

    (
        model,
        mean,
        std,
        threshold,
        checkpoint,
    ) = load_model_and_standardizer(
        CHECKPOINT_PATH,
        device,
    )

    print(
        f"Checkpoint epoch : "
        f"{checkpoint.get('epoch', 'unknown')}"
    )
    print(
        f"Best val Dice    : "
        f"{checkpoint.get('best_val_dice', 'unknown')}"
    )
    print(f"Threshold        : {threshold:.4f}")
    print(f"AMP              : {amp_enabled}")
    print()

    image_paths = discover_images()
    print(f"Found {len(image_paths)} station images.")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings = {
        "checkpoint": str(CHECKPOINT_PATH),
        "checkpoint_epoch": checkpoint.get(
            "epoch",
            None,
        ),
        "best_val_dice": checkpoint.get(
            "best_val_dice",
            None,
        ),
        "threshold": threshold,
        "input_image_dir": str(INPUT_IMAGE_DIR),
        "valid_mask_dir": str(VALID_MASK_DIR),
        "total_feature_dim": TOTAL_FEATURE_DIM,
        "device": str(device),
    }

    try:
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
    except Exception as exc:
        print(
            f"[WARN] Could not save settings JSON: {exc}"
        )

    processed = 0
    skipped = 0

    features: List[np.ndarray] = []
    valids: List[np.ndarray] = []
    batch_images: List[np.ndarray] = []
    batch_relatives: List[Path] = []

    def flush_batch() -> None:
        nonlocal processed

        if not features:
            return

        probabilities = run_batch(
            model,
            device,
            amp_enabled,
            features,
            valids,
        )

        for (
            image,
            relative,
            valid64,
            probability,
        ) in zip(
            batch_images,
            batch_relatives,
            valids,
            probabilities,
        ):
            binary = (
                probability >= threshold
            ).astype(np.uint8)

            binary = (
                binary
                * valid64.astype(np.uint8)
            )

            save_outputs(
                relative,
                image,
                valid64,
                probability,
                binary,
                threshold,
            )
            processed += 1

        features.clear()
        valids.clear()
        batch_images.clear()
        batch_relatives.clear()

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

        image, valid, relative = loaded

        try:
            feature = make_standardized_feature(
                image,
                valid,
                mean,
                std,
            )
        except Exception as exc:
            print(
                f"[SKIP] Feature extraction failed "
                f"for {relative}: {exc}"
            )
            skipped += 1
            continue

        valid64 = cv2.resize(
            valid,
            (64, 64),
            interpolation=cv2.INTER_NEAREST,
        )
        valid64 = (
            valid64 > 0
        ).astype(np.uint8)

        features.append(feature)
        valids.append(valid64)
        batch_images.append(image)
        batch_relatives.append(relative)

        if len(features) >= INFERENCE_BATCH_SIZE:
            flush_batch()

        if index % 100 == 0:
            print(
                f"[INFO] scanned={index}/{len(image_paths)} "
                f"processed={processed} skipped={skipped}"
            )

    flush_batch()

    elapsed = time.time() - t0

    print()
    print("========================================")
    print("Inference complete")
    print("========================================")
    print(f"Processed : {processed}")
    print(f"Skipped   : {skipped}")
    print(f"Time      : {elapsed:.2f} s")
    print(
        f"Highlighted images: "
        f"{(OUTPUT_DIR / HIGHLIGHT_SUBDIR).resolve()}"
    )


if __name__ == "__main__":
    main()