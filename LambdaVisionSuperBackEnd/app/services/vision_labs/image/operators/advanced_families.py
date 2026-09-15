from __future__ import annotations

import math

import cv2
import numpy as np

from app.services.vision_labs.core import (
    BinaryMaskPort,
    BoolParam,
    EnumParam,
    ExecutionContext,
    FloatParam,
    ImagePort,
    IntParam,
)
from app.services.vision_labs.image.operator import ImageOperator
from app.services.vision_labs.image.registry import image_operator
from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame


# ===========================================================================
# Shared helpers
# ===========================================================================

def _as_u8(data: np.ndarray) -> np.ndarray:
    if data.dtype == np.uint8:
        return data
    finite = np.nan_to_num(data, nan=0.0, posinf=255.0, neginf=0.0)
    normalized = cv2.normalize(finite, None, 0, 255, cv2.NORM_MINMAX)
    return np.clip(normalized, 0, 255).astype(np.uint8)


def _to_gray(src: ImageFrame) -> np.ndarray:
    data = _as_u8(src.data)
    if data.ndim == 2 or src.color_space == ColorSpace.GRAY:
        return data.copy()
    if src.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2GRAY)
    if src.color_space == ColorSpace.HSV:
        bgr = cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)


def _to_bgr(src: ImageFrame) -> np.ndarray:
    data = _as_u8(src.data)
    if data.ndim == 2 or src.color_space == ColorSpace.GRAY:
        return cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
    if src.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
    if src.color_space == ColorSpace.HSV:
        return cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
    return data.copy()


def _restore_from_bgr(src: ImageFrame, bgr: np.ndarray) -> ImageFrame:
    if src.color_space == ColorSpace.RGB:
        return src.with_data(
            cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB),
            color_space=ColorSpace.RGB,
        )
    if src.color_space == ColorSpace.HSV:
        return src.with_data(
            cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV),
            color_space=ColorSpace.HSV,
        )
    return src.with_data(bgr, color_space=ColorSpace.BGR)


def _apply_to_luminance(src: ImageFrame, function) -> ImageFrame:
    if src.channels == 1:
        gray = function(_to_gray(src))
        return src.with_data(_as_u8(gray), color_space=ColorSpace.GRAY)

    bgr = _to_bgr(src)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = _as_u8(function(lab[:, :, 0]))
    corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return _restore_from_bgr(src, corrected)


def _normalize_response(data: np.ndarray) -> np.ndarray:
    finite = np.nan_to_num(data.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    lo = float(np.min(finite))
    hi = float(np.max(finite))
    if hi <= lo + 1e-12:
        return np.zeros(finite.shape, dtype=np.uint8)
    return np.clip((finite - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)


def _gaussian_ksize(sigma: float) -> int:
    sigma = max(0.1, float(sigma))
    k = max(3, int(math.ceil(sigma * 6.0)) | 1)
    return min(k, 1001)


def _gaussian_blur_float(data: np.ndarray, sigma: float) -> np.ndarray:
    k = _gaussian_ksize(sigma)
    return cv2.GaussianBlur(
        data.astype(np.float32),
        (k, k),
        float(sigma),
        borderType=cv2.BORDER_REFLECT101,
    )


def _box_mean(data: np.ndarray, radius: int) -> np.ndarray:
    k = int(radius) * 2 + 1
    return cv2.boxFilter(
        data.astype(np.float32),
        ddepth=cv2.CV_32F,
        ksize=(k, k),
        normalize=True,
        borderType=cv2.BORDER_REFLECT101,
    )


def _frequency_mask(shape: tuple[int, int], mode: str, low: float, high: float) -> np.ndarray:
    h, w = shape
    yy = np.arange(h, dtype=np.float32) - h / 2.0
    xx = np.arange(w, dtype=np.float32) - w / 2.0
    y, x = np.meshgrid(yy, xx, indexing="ij")
    max_radius = max(1.0, 0.5 * math.sqrt(h * h + w * w))
    radius = np.sqrt(x * x + y * y) / max_radius

    low = max(0.0, min(1.0, float(low)))
    high = max(low, min(1.0, float(high)))

    if mode == "low_pass":
        return (radius <= high).astype(np.float32)
    if mode == "high_pass":
        return (radius >= low).astype(np.float32)
    if mode == "band_pass":
        return ((radius >= low) & (radius <= high)).astype(np.float32)
    if mode == "band_stop":
        return ((radius < low) | (radius > high)).astype(np.float32)
    raise ValueError(f"Unsupported frequency mode: {mode}")


def _fft_filter_plane(plane: np.ndarray, mask: np.ndarray) -> np.ndarray:
    spectrum = np.fft.fftshift(np.fft.fft2(plane.astype(np.float32)))
    filtered = spectrum * mask
    restored = np.fft.ifft2(np.fft.ifftshift(filtered))
    return np.real(restored).astype(np.float32)


def _frequency_filter_image(src: ImageFrame, mode: str, low: float, high: float) -> ImageFrame:
    data = _as_u8(src.data)
    mask = _frequency_mask((src.height, src.width), mode, low, high)

    if data.ndim == 2:
        restored = _fft_filter_plane(data, mask)
        return src.with_data(_normalize_response(restored), color_space=ColorSpace.GRAY)

    channels = [
        _fft_filter_plane(data[:, :, index], mask)
        for index in range(data.shape[2])
    ]
    merged = np.stack(channels, axis=2)
    merged = np.clip(merged, 0, 255).astype(np.uint8)
    return src.with_data(merged)


def _reconstruct_by_dilation(marker: np.ndarray, mask: np.ndarray, max_iterations: int = 2048) -> np.ndarray:
    marker = marker.astype(np.uint8, copy=True)
    mask = mask.astype(np.uint8, copy=False)
    kernel = np.ones((3, 3), dtype=np.uint8)

    for _ in range(int(max_iterations)):
        previous = marker
        dilated = cv2.dilate(previous, kernel)
        marker = np.minimum(dilated, mask)
        if np.array_equal(marker, previous):
            break

    return marker


def _opening_by_reconstruction_plane(data: np.ndarray, kernel_size: int, iterations: int) -> np.ndarray:
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (int(kernel_size), int(kernel_size)),
    )
    marker = cv2.erode(data, kernel, iterations=int(iterations))
    return _reconstruct_by_dilation(marker, data)


def _skeletonize_morphology(binary: np.ndarray) -> np.ndarray:
    image = np.where(binary > 0, 255, 0).astype(np.uint8)
    skeleton = np.zeros_like(image)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while cv2.countNonZero(image) > 0:
        eroded = cv2.erode(image, kernel)
        opened = cv2.dilate(eroded, kernel)
        residue = cv2.subtract(image, opened)
        skeleton = cv2.bitwise_or(skeleton, residue)
        image = eroded

    return skeleton


def _zhang_suen(binary: np.ndarray, max_iterations: int = 512) -> np.ndarray:
    image = (binary > 0).astype(np.uint8)

    if image.shape[0] < 3 or image.shape[1] < 3:
        return (image * 255).astype(np.uint8)

    for _ in range(int(max_iterations)):
        changed = False

        for step in (0, 1):
            p2 = image[:-2, 1:-1]
            p3 = image[:-2, 2:]
            p4 = image[1:-1, 2:]
            p5 = image[2:, 2:]
            p6 = image[2:, 1:-1]
            p7 = image[2:, :-2]
            p8 = image[1:-1, :-2]
            p9 = image[:-2, :-2]
            center = image[1:-1, 1:-1]

            neighbor_sum = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = (
                ((p2 == 0) & (p3 == 1)).astype(np.uint8)
                + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
                + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
                + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
                + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
                + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
                + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
                + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
            )

            base = (
                (center == 1)
                & (neighbor_sum >= 2)
                & (neighbor_sum <= 6)
                & (transitions == 1)
            )

            if step == 0:
                condition = base & ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0)
            else:
                condition = base & ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0)

            if np.any(condition):
                inner = image[1:-1, 1:-1].copy()
                inner[condition] = 0
                image[1:-1, 1:-1] = inner
                changed = True

        if not changed:
            break

    return (image * 255).astype(np.uint8)


def _hessian_eigenvalues(gray: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    smoothed = _gaussian_blur_float(gray, sigma)
    scale = float(sigma) ** 2

    dxx = cv2.Sobel(smoothed, cv2.CV_32F, 2, 0, ksize=3) * scale
    dyy = cv2.Sobel(smoothed, cv2.CV_32F, 0, 2, ksize=3) * scale
    dxy = cv2.Sobel(smoothed, cv2.CV_32F, 1, 1, ksize=3) * scale

    trace = dxx + dyy
    delta = np.sqrt(np.maximum((dxx - dyy) ** 2 + 4.0 * dxy * dxy, 0.0))

    lambda1 = 0.5 * (trace - delta)
    lambda2 = 0.5 * (trace + delta)

    swap = np.abs(lambda1) > np.abs(lambda2)
    small = np.where(swap, lambda2, lambda1)
    large = np.where(swap, lambda1, lambda2)
    return small, large


def _frangi_response(
    gray: np.ndarray,
    sigma_min: float,
    sigma_max: float,
    scales: int,
    beta: float,
    c_value: float,
    polarity: str,
) -> np.ndarray:
    sigmas = np.linspace(float(sigma_min), float(sigma_max), int(scales), dtype=np.float32)
    result = np.zeros(gray.shape, dtype=np.float32)
    beta2 = max(1e-9, 2.0 * float(beta) ** 2)
    c2 = max(1e-9, 2.0 * float(c_value) ** 2)

    for sigma in sigmas:
        l1, l2 = _hessian_eigenvalues(gray, float(sigma))
        rb = np.abs(l1) / (np.abs(l2) + 1e-9)
        s2 = l1 * l1 + l2 * l2

        vesselness = np.exp(-(rb * rb) / beta2) * (1.0 - np.exp(-s2 / c2))

        if polarity == "bright":
            vesselness[l2 > 0] = 0.0
        elif polarity == "dark":
            vesselness[l2 < 0] = 0.0

        result = np.maximum(result, vesselness.astype(np.float32))

    return result


def _local_entropy(gray: np.ndarray, radius: int, bins: int) -> np.ndarray:
    quantized = np.floor(gray.astype(np.float32) * (float(bins) / 256.0)).astype(np.int32)
    quantized = np.clip(quantized, 0, int(bins) - 1)
    entropy = np.zeros(gray.shape, dtype=np.float32)

    for index in range(int(bins)):
        indicator = (quantized == index).astype(np.float32)
        probability = _box_mean(indicator, int(radius))
        entropy -= np.where(
            probability > 1e-12,
            probability * np.log2(probability + 1e-12),
            0.0,
        )

    return entropy


def _gaussian_psf(size: int, sigma: float) -> np.ndarray:
    size = int(size)
    axis = np.arange(size, dtype=np.float32) - (size - 1) / 2.0
    y, x = np.meshgrid(axis, axis)
    psf = np.exp(-(x * x + y * y) / (2.0 * float(sigma) ** 2))
    psf /= max(float(psf.sum()), 1e-12)
    return psf.astype(np.float32)


def _wiener_plane(data: np.ndarray, psf_size: int, psf_sigma: float, noise: float) -> np.ndarray:
    h, w = data.shape
    psf = _gaussian_psf(psf_size, psf_sigma)
    padded = np.zeros((h, w), dtype=np.float32)
    ph, pw = psf.shape
    y0 = max(0, (h - ph) // 2)
    x0 = max(0, (w - pw) // 2)
    y1 = min(h, y0 + ph)
    x1 = min(w, x0 + pw)
    padded[y0:y1, x0:x1] = psf[: y1 - y0, : x1 - x0]
    padded = np.fft.ifftshift(padded)

    h_fft = np.fft.fft2(padded)
    g_fft = np.fft.fft2(data.astype(np.float32))
    denominator = np.abs(h_fft) ** 2 + max(float(noise), 1e-9)
    restored = np.fft.ifft2(np.conj(h_fft) * g_fft / denominator)
    return np.real(restored).astype(np.float32)


# ===========================================================================
# Illumination correction
# ===========================================================================

@image_operator(
    id="image.illumination.shading_correction",
    label="Shading Correction",
    category="Illumination Correction",
    description="Estimate slow background illumination and divide it out.",
)
class ShadingCorrection(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "background_sigma": FloatParam(
            default=35.0, min=1.0, max=200.0, ui_hint="slider",
            description="Spatial scale of slow illumination variation.",
        ),
        "strength": FloatParam(default=1.0, min=0.0, max=1.5, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        sigma = float(params["background_sigma"])
        strength = float(params["strength"])

        def correct(channel: np.ndarray) -> np.ndarray:
            source = channel.astype(np.float32) + 1.0
            background = _gaussian_blur_float(source, sigma) + 1.0
            normalized = source / background
            normalized *= float(np.mean(background))
            blended = (1.0 - strength) * source + strength * normalized
            return np.clip(blended, 0, 255).astype(np.uint8)

        return {"image": _apply_to_luminance(src, correct)}


@image_operator(
    id="image.illumination.homomorphic",
    label="Homomorphic Filter",
    category="Illumination Correction",
    description="Suppress low-frequency illumination while preserving reflectance/detail.",
)
class HomomorphicFilter(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "cutoff": FloatParam(default=0.12, min=0.01, max=0.5, ui_hint="slider"),
        "gamma_low": FloatParam(default=0.6, min=0.05, max=1.0, ui_hint="slider"),
        "gamma_high": FloatParam(default=1.6, min=1.0, max=4.0, ui_hint="slider"),
        "sharpness": FloatParam(default=2.0, min=0.1, max=10.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        cutoff = float(params["cutoff"])
        gamma_low = float(params["gamma_low"])
        gamma_high = float(params["gamma_high"])
        sharpness = float(params["sharpness"])

        def filter_plane(channel: np.ndarray) -> np.ndarray:
            data = np.log1p(channel.astype(np.float32))
            h, w = data.shape
            yy = np.arange(h, dtype=np.float32) - h / 2.0
            xx = np.arange(w, dtype=np.float32) - w / 2.0
            y, x = np.meshgrid(yy, xx, indexing="ij")
            d2 = (x * x + y * y) / max(float(h * h + w * w), 1.0)
            transfer = (
                gamma_low
                + (gamma_high - gamma_low)
                * (1.0 - np.exp(-sharpness * d2 / max(cutoff * cutoff, 1e-9)))
            )
            spectrum = np.fft.fftshift(np.fft.fft2(data))
            restored = np.real(
                np.fft.ifft2(np.fft.ifftshift(spectrum * transfer))
            )
            return _normalize_response(np.expm1(restored))

        return {"image": _apply_to_luminance(src, filter_plane)}


@image_operator(
    id="image.illumination.single_scale_retinex",
    label="Single-scale Retinex",
    category="Illumination Correction",
    description="Log-domain illumination normalization using a Gaussian surround.",
)
class SingleScaleRetinex(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "sigma": FloatParam(default=30.0, min=1.0, max=200.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        sigma = float(params["sigma"])

        def retinex(channel: np.ndarray) -> np.ndarray:
            data = channel.astype(np.float32) + 1.0
            surround = _gaussian_blur_float(data, sigma) + 1.0
            response = np.log(data) - np.log(surround)
            return _normalize_response(response)

        return {"image": _apply_to_luminance(src, retinex)}


# ===========================================================================
# Edge-preserving / nonlinear denoise
# ===========================================================================

@image_operator(
    id="image.filter.guided",
    label="Guided Filter",
    category="Edge-preserving Filter",
    description="Edge-preserving smoothing with the image luminance as guidance.",
)
class GuidedFilter(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "radius": IntParam(default=8, min=1, max=64, ui_hint="slider"),
        "epsilon": FloatParam(default=64.0, min=0.01, max=5000.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        radius = int(params["radius"])
        epsilon = float(params["epsilon"])

        guidance = _to_gray(src).astype(np.float32) / 255.0
        mean_i = _box_mean(guidance, radius)
        corr_i = _box_mean(guidance * guidance, radius)
        var_i = corr_i - mean_i * mean_i

        data = _as_u8(src.data)

        def guided_plane(plane: np.ndarray) -> np.ndarray:
            p = plane.astype(np.float32) / 255.0
            mean_p = _box_mean(p, radius)
            corr_ip = _box_mean(guidance * p, radius)
            cov_ip = corr_ip - mean_i * mean_p
            a = cov_ip / (var_i + epsilon / (255.0 * 255.0))
            b = mean_p - a * mean_i
            mean_a = _box_mean(a, radius)
            mean_b = _box_mean(b, radius)
            q = mean_a * guidance + mean_b
            return np.clip(q * 255.0, 0, 255).astype(np.uint8)

        if data.ndim == 2:
            return {"image": src.with_data(guided_plane(data), color_space=ColorSpace.GRAY)}

        result = np.stack(
            [guided_plane(data[:, :, i]) for i in range(data.shape[2])],
            axis=2,
        )
        return {"image": src.with_data(result)}


@image_operator(
    id="image.filter.anisotropic_diffusion",
    label="Anisotropic Diffusion",
    category="Edge-preserving Filter",
    description="Perona-Malik diffusion: smooth homogeneous regions while retaining strong edges.",
)
class AnisotropicDiffusion(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "iterations": IntParam(default=8, min=1, max=40, ui_hint="slider"),
        "kappa": FloatParam(default=30.0, min=1.0, max=150.0, ui_hint="slider"),
        "gamma": FloatParam(default=0.18, min=0.01, max=0.24, ui_hint="slider"),
        "conduction": EnumParam(("exponential", "reciprocal"), default="exponential"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        iterations = int(params["iterations"])
        kappa = float(params["kappa"])
        gamma = float(params["gamma"])
        conduction = str(params["conduction"])
        data = _as_u8(src.data).astype(np.float32)

        if data.ndim == 2:
            work = data[:, :, None]
        else:
            work = data.copy()

        for _ in range(iterations):
            north = np.zeros_like(work)
            south = np.zeros_like(work)
            east = np.zeros_like(work)
            west = np.zeros_like(work)

            north[1:] = work[:-1] - work[1:]
            south[:-1] = work[1:] - work[:-1]
            west[:, 1:] = work[:, :-1] - work[:, 1:]
            east[:, :-1] = work[:, 1:] - work[:, :-1]

            if conduction == "exponential":
                c_n = np.exp(-((north / kappa) ** 2))
                c_s = np.exp(-((south / kappa) ** 2))
                c_e = np.exp(-((east / kappa) ** 2))
                c_w = np.exp(-((west / kappa) ** 2))
            else:
                c_n = 1.0 / (1.0 + (north / kappa) ** 2)
                c_s = 1.0 / (1.0 + (south / kappa) ** 2)
                c_e = 1.0 / (1.0 + (east / kappa) ** 2)
                c_w = 1.0 / (1.0 + (west / kappa) ** 2)

            work += gamma * (
                c_n * north
                + c_s * south
                + c_e * east
                + c_w * west
            )

        result = np.clip(work, 0, 255).astype(np.uint8)
        if data.ndim == 2:
            result = result[:, :, 0]
        return {"image": src.with_data(result)}


# ===========================================================================
# Ridge / elongated structure enhancement
# ===========================================================================

@image_operator(
    id="image.structure.hessian_ridge",
    label="Hessian Ridge Response",
    category="Ridge / Structure",
    description="Enhance elongated ridge/valley structures from Hessian eigenvalues.",
)
class HessianRidgeResponse(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "sigma": FloatParam(default=2.0, min=0.5, max=20.0, ui_hint="slider"),
        "polarity": EnumParam(("bright", "dark", "both"), default="bright"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src)
        _, large = _hessian_eigenvalues(gray, float(params["sigma"]))
        polarity = str(params["polarity"])

        if polarity == "bright":
            response = np.maximum(-large, 0.0)
        elif polarity == "dark":
            response = np.maximum(large, 0.0)
        else:
            response = np.abs(large)

        return {
            "image": src.with_data(
                _normalize_response(response),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.structure.frangi_ridge",
    label="Frangi Multi-scale Ridge",
    category="Ridge / Structure",
    description="Multi-scale vesselness/ridge enhancement for long curved line-like structures.",
)
class FrangiRidge(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "sigma_min": FloatParam(default=1.0, min=0.5, max=20.0, ui_hint="slider"),
        "sigma_max": FloatParam(default=5.0, min=0.5, max=40.0, ui_hint="slider"),
        "scales": IntParam(default=5, min=1, max=12, ui_hint="slider"),
        "beta": FloatParam(default=0.5, min=0.05, max=2.0, ui_hint="slider"),
        "c": FloatParam(default=15.0, min=0.1, max=200.0, ui_hint="slider"),
        "polarity": EnumParam(("bright", "dark", "both"), default="bright"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        sigma_min = float(params["sigma_min"])
        sigma_max = float(params["sigma_max"])
        if sigma_max < sigma_min:
            raise ValueError("sigma_max must be >= sigma_min")

        response = _frangi_response(
            _to_gray(src),
            sigma_min,
            sigma_max,
            int(params["scales"]),
            float(params["beta"]),
            float(params["c"]),
            str(params["polarity"]),
        )
        return {
            "image": src.with_data(
                _normalize_response(response),
                color_space=ColorSpace.GRAY,
            )
        }


# ===========================================================================
# Distance / skeleton raster
# ===========================================================================

@image_operator(
    id="image.distance.transform",
    label="Distance Transform",
    category="Distance / Skeleton",
    description="Distance from each foreground pixel to the nearest background boundary.",
)
class DistanceTransform(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "metric": EnumParam(("l2", "l1", "chebyshev"), default="l2"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        binary = np.where(src.data > 0, 255, 0).astype(np.uint8)
        metric_map = {
            "l2": cv2.DIST_L2,
            "l1": cv2.DIST_L1,
            "chebyshev": cv2.DIST_C,
        }
        metric = str(params["metric"])
        distance = cv2.distanceTransform(
            binary,
            metric_map[metric],
            5 if metric == "l2" else 3,
        )
        max_distance = float(distance.max()) if distance.size else 0.0
        data = _normalize_response(distance)

        frame = ImageFrame(
            data=data,
            color_space=ColorSpace.GRAY,
            coordinate_frame=src.coordinate_frame,
            metadata={
                **dict(src.metadata),
                "distance_transform_max": max_distance,
                "distance_metric": metric,
            },
        )
        return {"image": frame}


@image_operator(
    id="image.distance.signed_distance",
    label="Signed Distance Field",
    category="Distance / Skeleton",
    description="Signed distance raster: inside above mid-gray, outside below mid-gray.",
)
class SignedDistanceField(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        foreground = np.where(src.data > 0, 255, 0).astype(np.uint8)
        background = cv2.bitwise_not(foreground)
        inside = cv2.distanceTransform(foreground, cv2.DIST_L2, 5)
        outside = cv2.distanceTransform(background, cv2.DIST_L2, 5)
        signed = inside - outside

        max_abs = max(float(np.max(np.abs(signed))), 1e-6)
        data = np.clip(127.5 + signed * (127.5 / max_abs), 0, 255).astype(np.uint8)

        frame = ImageFrame(
            data=data,
            color_space=ColorSpace.GRAY,
            coordinate_frame=src.coordinate_frame,
            metadata={
                **dict(src.metadata),
                "signed_distance_abs_max": max_abs,
                "signed_distance_zero_level": 127.5,
            },
        )
        return {"image": frame}


@image_operator(
    id="image.skeleton.morphological",
    label="Morphological Skeleton",
    category="Distance / Skeleton",
    description="Binary morphological skeleton. Output remains a raster mask.",
)
class MorphologicalSkeleton(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        return {"mask": src.with_data(_skeletonize_morphology(src.data))}


@image_operator(
    id="image.skeleton.zhang_suen",
    label="Zhang-Suen Thinning",
    category="Distance / Skeleton",
    description="Iterative one-pixel thinning of a binary mask.",
)
class ZhangSuenThinning(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "max_iterations": IntParam(default=128, min=1, max=512),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        data = _zhang_suen(src.data, int(params["max_iterations"]))
        return {"mask": src.with_data(data)}


# ===========================================================================
# Morphological reconstruction
# ===========================================================================

@image_operator(
    id="image.reconstruction.open",
    label="Opening by Reconstruction",
    category="Morphological Reconstruction",
    description="Remove bright structures smaller than the structuring element while preserving surviving contours.",
)
class OpeningByReconstruction(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=5, min=3, max=51, odd=True, ui_hint="slider"),
        "erosion_iterations": IntParam(default=1, min=1, max=10),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data)
        kernel_size = int(params["kernel_size"])
        iterations = int(params["erosion_iterations"])

        if data.ndim == 2:
            result = _opening_by_reconstruction_plane(data, kernel_size, iterations)
        else:
            result = np.stack(
                [
                    _opening_by_reconstruction_plane(data[:, :, i], kernel_size, iterations)
                    for i in range(data.shape[2])
                ],
                axis=2,
            )

        return {"image": src.with_data(result)}


@image_operator(
    id="image.reconstruction.close",
    label="Closing by Reconstruction",
    category="Morphological Reconstruction",
    description="Fill small dark structures while preserving outer object contours better than normal closing.",
)
class ClosingByReconstruction(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=5, min=3, max=51, odd=True, ui_hint="slider"),
        "dilation_iterations": IntParam(default=1, min=1, max=10),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data)
        kernel_size = int(params["kernel_size"])
        iterations = int(params["dilation_iterations"])

        def close_plane(plane: np.ndarray) -> np.ndarray:
            inverted = cv2.bitwise_not(plane)
            opened = _opening_by_reconstruction_plane(inverted, kernel_size, iterations)
            return cv2.bitwise_not(opened)

        if data.ndim == 2:
            result = close_plane(data)
        else:
            result = np.stack(
                [close_plane(data[:, :, i]) for i in range(data.shape[2])],
                axis=2,
            )

        return {"image": src.with_data(result)}


@image_operator(
    id="image.morphology.clear_border",
    label="Clear Border Components",
    category="Morphological Reconstruction",
    description="Remove foreground components touching any image border.",
)
class ClearBorderComponents(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "connectivity": EnumParam((4, 8), default=8),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        binary = np.where(src.data > 0, 255, 0).astype(np.uint8)
        count, labels, _, _ = cv2.connectedComponentsWithStats(
            binary,
            connectivity=int(params["connectivity"]),
        )
        border_labels = np.unique(
            np.concatenate(
                [
                    labels[0, :],
                    labels[-1, :],
                    labels[:, 0],
                    labels[:, -1],
                ]
            )
        )
        keep = np.ones(count, dtype=bool)
        keep[border_labels] = False
        keep[0] = False
        result = np.where(keep[labels], 255, 0).astype(np.uint8)
        return {"mask": src.with_data(result)}


# ===========================================================================
# Advanced adaptive binarization
# ===========================================================================

@image_operator(
    id="image.threshold.sauvola",
    label="Sauvola Threshold",
    category="Advanced Binarization",
    description="Adaptive threshold using local mean and local standard deviation.",
)
class SauvolaThreshold(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "window_size": IntParam(default=25, min=3, max=151, odd=True, ui_hint="slider"),
        "k": FloatParam(default=0.2, min=-1.0, max=1.0, ui_hint="slider"),
        "r": FloatParam(default=128.0, min=1.0, max=255.0),
        "invert": BoolParam(default=False),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src).astype(np.float32)
        radius = (int(params["window_size"]) - 1) // 2
        mean = _box_mean(gray, radius)
        mean_sq = _box_mean(gray * gray, radius)
        std = np.sqrt(np.maximum(mean_sq - mean * mean, 0.0))
        threshold = mean * (
            1.0
            + float(params["k"])
            * (std / float(params["r"]) - 1.0)
        )
        mask = gray > threshold
        if bool(params["invert"]):
            mask = ~mask
        return {"mask": BinaryMask.from_image((mask.astype(np.uint8) * 255), src)}


@image_operator(
    id="image.threshold.niblack",
    label="Niblack Threshold",
    category="Advanced Binarization",
    description="Adaptive threshold T = local mean + k × local standard deviation.",
)
class NiblackThreshold(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "window_size": IntParam(default=25, min=3, max=151, odd=True, ui_hint="slider"),
        "k": FloatParam(default=-0.2, min=-2.0, max=2.0, ui_hint="slider"),
        "invert": BoolParam(default=False),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src).astype(np.float32)
        radius = (int(params["window_size"]) - 1) // 2
        mean = _box_mean(gray, radius)
        mean_sq = _box_mean(gray * gray, radius)
        std = np.sqrt(np.maximum(mean_sq - mean * mean, 0.0))
        threshold = mean + float(params["k"]) * std
        mask = gray > threshold
        if bool(params["invert"]):
            mask = ~mask
        return {"mask": BinaryMask.from_image((mask.astype(np.uint8) * 255), src)}


@image_operator(
    id="image.threshold.bradley",
    label="Bradley Local Threshold",
    category="Advanced Binarization",
    description="Fast local-mean threshold suitable for uneven illumination.",
)
class BradleyThreshold(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "window_size": IntParam(default=31, min=3, max=201, odd=True, ui_hint="slider"),
        "sensitivity": FloatParam(default=0.15, min=0.0, max=0.5, ui_hint="slider"),
        "invert": BoolParam(default=False),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src).astype(np.float32)
        radius = (int(params["window_size"]) - 1) // 2
        mean = _box_mean(gray, radius)
        mask = gray >= mean * (1.0 - float(params["sensitivity"]))
        if bool(params["invert"]):
            mask = ~mask
        return {"mask": BinaryMask.from_image((mask.astype(np.uint8) * 255), src)}


# ===========================================================================
# Frequency domain
# ===========================================================================

@image_operator(
    id="image.frequency.spectrum",
    label="FFT Magnitude Spectrum",
    category="Frequency Domain",
    description="Visualize log magnitude of the centered Fourier spectrum.",
)
class FFTMagnitudeSpectrum(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src).astype(np.float32)
        spectrum = np.fft.fftshift(np.fft.fft2(gray))
        magnitude = np.log1p(np.abs(spectrum))
        return {
            "image": src.with_data(
                _normalize_response(magnitude),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.frequency.filter",
    label="FFT Frequency Filter",
    category="Frequency Domain",
    description="Ideal low/high/band-pass or band-stop filtering in the Fourier domain.",
)
class FFTFrequencyFilter(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "mode": EnumParam(
            ("low_pass", "high_pass", "band_pass", "band_stop"),
            default="low_pass",
        ),
        "low_cutoff": FloatParam(default=0.05, min=0.0, max=1.0, ui_hint="slider"),
        "high_cutoff": FloatParam(default=0.18, min=0.0, max=1.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        low = float(params["low_cutoff"])
        high = float(params["high_cutoff"])
        if high < low:
            raise ValueError("high_cutoff must be >= low_cutoff")
        return {
            "image": _frequency_filter_image(
                src,
                str(params["mode"]),
                low,
                high,
            )
        }


@image_operator(
    id="image.frequency.notch_reject",
    label="Symmetric Notch Reject",
    category="Frequency Domain",
    description="Remove one symmetric pair of periodic-frequency peaks from the Fourier spectrum.",
)
class SymmetricNotchReject(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "u_offset": FloatParam(default=0.12, min=-0.5, max=0.5, ui_hint="slider"),
        "v_offset": FloatParam(default=0.0, min=-0.5, max=0.5, ui_hint="slider"),
        "radius": FloatParam(default=0.025, min=0.002, max=0.2, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        h, w = src.height, src.width
        cy, cx = h / 2.0, w / 2.0
        u = float(params["u_offset"]) * w
        v = float(params["v_offset"]) * h
        radius_px = float(params["radius"]) * min(h, w)

        yy, xx = np.ogrid[:h, :w]
        mask = np.ones((h, w), dtype=np.float32)

        for sign in (-1.0, 1.0):
            px = cx + sign * u
            py = cy + sign * v
            reject = (xx - px) ** 2 + (yy - py) ** 2 <= radius_px ** 2
            mask[reject] = 0.0

        data = _as_u8(src.data)
        if data.ndim == 2:
            result = _fft_filter_plane(data, mask)
            return {
                "image": src.with_data(
                    np.clip(result, 0, 255).astype(np.uint8),
                    color_space=ColorSpace.GRAY,
                )
            }

        channels = [
            _fft_filter_plane(data[:, :, i], mask)
            for i in range(data.shape[2])
        ]
        result = np.stack(channels, axis=2)
        return {"image": src.with_data(np.clip(result, 0, 255).astype(np.uint8))}


# ===========================================================================
# Texture / local statistics
# ===========================================================================

@image_operator(
    id="image.texture.gabor",
    label="Gabor Response",
    category="Texture / Local Statistics",
    description="Orientation- and frequency-selective texture response.",
)
class GaborResponse(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=31, min=7, max=101, odd=True, ui_hint="slider"),
        "sigma": FloatParam(default=5.0, min=0.5, max=30.0, ui_hint="slider"),
        "theta_deg": FloatParam(default=0.0, min=0.0, max=180.0, ui_hint="slider"),
        "wavelength": FloatParam(default=10.0, min=2.0, max=50.0, ui_hint="slider"),
        "gamma": FloatParam(default=0.5, min=0.1, max=2.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        kernel = cv2.getGaborKernel(
            (int(params["kernel_size"]), int(params["kernel_size"])),
            float(params["sigma"]),
            math.radians(float(params["theta_deg"])),
            float(params["wavelength"]),
            float(params["gamma"]),
            0.0,
            ktype=cv2.CV_32F,
        )
        response = cv2.filter2D(
            _to_gray(src).astype(np.float32),
            cv2.CV_32F,
            kernel,
        )
        return {
            "image": src.with_data(
                _normalize_response(np.abs(response)),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.texture.gabor_bank_max",
    label="Gabor Bank Maximum",
    category="Texture / Local Statistics",
    description="Maximum response over an evenly spaced bank of Gabor orientations.",
)
class GaborBankMaximum(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "orientations": IntParam(default=6, min=2, max=18),
        "kernel_size": IntParam(default=31, min=7, max=101, odd=True, ui_hint="slider"),
        "sigma": FloatParam(default=5.0, min=0.5, max=30.0, ui_hint="slider"),
        "wavelength": FloatParam(default=10.0, min=2.0, max=50.0, ui_hint="slider"),
        "gamma": FloatParam(default=0.5, min=0.1, max=2.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src).astype(np.float32)
        response = np.zeros(gray.shape, dtype=np.float32)
        orientations = int(params["orientations"])

        for index in range(orientations):
            theta = math.pi * index / orientations
            kernel = cv2.getGaborKernel(
                (int(params["kernel_size"]), int(params["kernel_size"])),
                float(params["sigma"]),
                theta,
                float(params["wavelength"]),
                float(params["gamma"]),
                0.0,
                ktype=cv2.CV_32F,
            )
            current = np.abs(cv2.filter2D(gray, cv2.CV_32F, kernel))
            response = np.maximum(response, current)

        return {
            "image": src.with_data(
                _normalize_response(response),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.texture.local_stddev",
    label="Local Standard Deviation",
    category="Texture / Local Statistics",
    description="Local contrast/roughness map based on neighborhood standard deviation.",
)
class LocalStandardDeviation(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "window_size": IntParam(default=15, min=3, max=101, odd=True, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src).astype(np.float32)
        radius = (int(params["window_size"]) - 1) // 2
        mean = _box_mean(gray, radius)
        mean_sq = _box_mean(gray * gray, radius)
        std = np.sqrt(np.maximum(mean_sq - mean * mean, 0.0))
        return {
            "image": src.with_data(
                _normalize_response(std),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.texture.local_entropy",
    label="Local Entropy",
    category="Texture / Local Statistics",
    description="Local texture complexity map from a quantized neighborhood histogram.",
)
class LocalEntropy(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "window_size": IntParam(default=15, min=3, max=61, odd=True, ui_hint="slider"),
        "bins": EnumParam((8, 16, 32), default=16),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        radius = (int(params["window_size"]) - 1) // 2
        entropy = _local_entropy(_to_gray(src), radius, int(params["bins"]))
        return {
            "image": src.with_data(
                _normalize_response(entropy),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.texture.local_range",
    label="Local Intensity Range",
    category="Texture / Local Statistics",
    description="Local max-min intensity range, useful for simple texture/contrast inspection.",
)
class LocalIntensityRange(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "window_size": IntParam(default=9, min=3, max=61, odd=True, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src)
        kernel = np.ones(
            (int(params["window_size"]), int(params["window_size"])),
            dtype=np.uint8,
        )
        maximum = cv2.dilate(gray, kernel)
        minimum = cv2.erode(gray, kernel)
        result = cv2.subtract(maximum, minimum)
        return {"image": src.with_data(result, color_space=ColorSpace.GRAY)}


# ===========================================================================
# Multiscale / scale-space
# ===========================================================================

@image_operator(
    id="image.multiscale.dog",
    label="Difference of Gaussians",
    category="Multiscale / Scale-space",
    description="Band-pass-like blob/detail response from two Gaussian scales.",
)
class DifferenceOfGaussians(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "sigma_small": FloatParam(default=1.0, min=0.2, max=30.0, ui_hint="slider"),
        "sigma_large": FloatParam(default=2.0, min=0.2, max=60.0, ui_hint="slider"),
        "absolute": BoolParam(default=True),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        sigma_small = float(params["sigma_small"])
        sigma_large = float(params["sigma_large"])
        if sigma_large <= sigma_small:
            raise ValueError("sigma_large must be > sigma_small")

        gray = _to_gray(src).astype(np.float32)
        first = _gaussian_blur_float(gray, sigma_small)
        second = _gaussian_blur_float(gray, sigma_large)
        response = first - second
        if bool(params["absolute"]):
            response = np.abs(response)

        return {
            "image": src.with_data(
                _normalize_response(response),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.multiscale.log",
    label="Laplacian of Gaussian",
    category="Multiscale / Scale-space",
    description="Blob/detail response from Laplacian applied at a Gaussian scale.",
)
class LaplacianOfGaussian(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "sigma": FloatParam(default=1.5, min=0.2, max=30.0, ui_hint="slider"),
        "absolute": BoolParam(default=True),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        sigma = float(params["sigma"])
        smoothed = _gaussian_blur_float(_to_gray(src), sigma)
        response = cv2.Laplacian(smoothed, cv2.CV_32F, ksize=3) * (sigma ** 2)
        if bool(params["absolute"]):
            response = np.abs(response)

        return {
            "image": src.with_data(
                _normalize_response(response),
                color_space=ColorSpace.GRAY,
            )
        }


@image_operator(
    id="image.multiscale.pyr_down",
    label="Pyramid Down",
    category="Multiscale / Scale-space",
    description="Gaussian pyramid downsample by approximately 2×.",
)
class PyramidDown(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        result = cv2.pyrDown(src.data)
        history = list(src.metadata.get("transform_history", []))
        history.append(
            {
                "type": "pyr_down",
                "from": [src.width, src.height],
                "to": [int(result.shape[1]), int(result.shape[0])],
            }
        )
        return {
            "image": src.with_data(
                result,
                metadata_update={"transform_history": history},
            )
        }


@image_operator(
    id="image.multiscale.pyr_up",
    label="Pyramid Up",
    category="Multiscale / Scale-space",
    description="Gaussian pyramid upsample by approximately 2×.",
)
class PyramidUp(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        result = cv2.pyrUp(src.data)
        history = list(src.metadata.get("transform_history", []))
        history.append(
            {
                "type": "pyr_up",
                "from": [src.width, src.height],
                "to": [int(result.shape[1]), int(result.shape[0])],
            }
        )
        return {
            "image": src.with_data(
                result,
                metadata_update={"transform_history": history},
            )
        }


# ===========================================================================
# Classical segmentation (single-image only)
# ===========================================================================

@image_operator(
    id="image.segment.region_grow",
    label="Seeded Region Grow",
    category="Classical Segmentation",
    description="Flood-fill a connected region from a normalized seed using intensity tolerances.",
)
class SeededRegionGrow(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "seed_x": FloatParam(default=0.5, min=0.0, max=1.0, ui_hint="slider"),
        "seed_y": FloatParam(default=0.5, min=0.0, max=1.0, ui_hint="slider"),
        "lower_diff": IntParam(default=15, min=0, max=255, ui_hint="slider"),
        "upper_diff": IntParam(default=15, min=0, max=255, ui_hint="slider"),
        "connectivity": EnumParam((4, 8), default=8),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src)
        seed_x = min(src.width - 1, max(0, int(round(float(params["seed_x"]) * (src.width - 1)))))
        seed_y = min(src.height - 1, max(0, int(round(float(params["seed_y"]) * (src.height - 1)))))

        flood_mask = np.zeros((src.height + 2, src.width + 2), dtype=np.uint8)
        work = gray.copy()
        flags = int(params["connectivity"]) | cv2.FLOODFILL_MASK_ONLY | (255 << 8)

        cv2.floodFill(
            work,
            flood_mask,
            (seed_x, seed_y),
            0,
            int(params["lower_diff"]),
            int(params["upper_diff"]),
            flags,
        )
        result = flood_mask[1:-1, 1:-1]
        return {"mask": BinaryMask.from_image(result, src)}


@image_operator(
    id="image.segment.grabcut_rect",
    label="GrabCut from Rectangle",
    category="Classical Segmentation",
    description="Foreground segmentation initialized from a normalized rectangle.",
)
class GrabCutRectangle(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "x": FloatParam(default=0.05, min=0.0, max=0.95, ui_hint="slider"),
        "y": FloatParam(default=0.05, min=0.0, max=0.95, ui_hint="slider"),
        "width": FloatParam(default=0.90, min=0.01, max=1.0, ui_hint="slider"),
        "height": FloatParam(default=0.90, min=0.01, max=1.0, ui_hint="slider"),
        "iterations": IntParam(default=3, min=1, max=10),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        x = float(params["x"])
        y = float(params["y"])
        width = float(params["width"])
        height = float(params["height"])

        if x + width > 1.0 or y + height > 1.0:
            raise ValueError("GrabCut rectangle must remain inside the image")

        x0 = int(round(x * src.width))
        y0 = int(round(y * src.height))
        w = max(1, int(round(width * src.width)))
        h = max(1, int(round(height * src.height)))
        x0 = min(max(0, x0), src.width - 1)
        y0 = min(max(0, y0), src.height - 1)
        w = min(w, src.width - x0)
        h = min(h, src.height - y0)

        mask = np.zeros((src.height, src.width), dtype=np.uint8)
        bgd_model = np.zeros((1, 65), dtype=np.float64)
        fgd_model = np.zeros((1, 65), dtype=np.float64)
        cv2.grabCut(
            _to_bgr(src),
            mask,
            (x0, y0, w, h),
            bgd_model,
            fgd_model,
            int(params["iterations"]),
            cv2.GC_INIT_WITH_RECT,
        )
        foreground = np.where(
            (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
            255,
            0,
        ).astype(np.uint8)
        return {"mask": BinaryMask.from_image(foreground, src)}


@image_operator(
    id="image.segment.kmeans_color",
    label="K-Means Color Quantization",
    category="Classical Segmentation",
    description="Quantize image colors into K clusters as a segmentation-oriented raster transform.",
)
class KMeansColorQuantization(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "clusters": IntParam(default=4, min=2, max=16, ui_hint="slider"),
        "attempts": IntParam(default=3, min=1, max=10),
        "max_iterations": IntParam(default=20, min=2, max=100),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data)

        if data.ndim == 2:
            samples = data.reshape((-1, 1)).astype(np.float32)
        else:
            samples = data.reshape((-1, data.shape[2])).astype(np.float32)

        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            int(params["max_iterations"]),
            0.5,
        )
        _, labels, centers = cv2.kmeans(
            samples,
            int(params["clusters"]),
            None,
            criteria,
            int(params["attempts"]),
            cv2.KMEANS_PP_CENTERS,
        )
        centers = np.clip(centers, 0, 255).astype(np.uint8)
        quantized = centers[labels.flatten()]
        result = quantized.reshape(data.shape)
        return {"image": src.with_data(result)}


# ===========================================================================
# Restoration
# ===========================================================================

@image_operator(
    id="image.restore.wiener",
    label="Wiener Deconvolution",
    category="Restoration",
    description="FFT-domain Wiener restoration using an approximate Gaussian point-spread function.",
)
class WienerDeconvolution(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "psf_size": IntParam(default=9, min=3, max=51, odd=True, ui_hint="slider"),
        "psf_sigma": FloatParam(default=2.0, min=0.2, max=15.0, ui_hint="slider"),
        "noise_power": FloatParam(default=0.01, min=0.000001, max=1.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data)

        if data.ndim == 2:
            restored = _wiener_plane(
                data,
                int(params["psf_size"]),
                float(params["psf_sigma"]),
                float(params["noise_power"]),
            )
            result = np.clip(restored, 0, 255).astype(np.uint8)
        else:
            result = np.stack(
                [
                    np.clip(
                        _wiener_plane(
                            data[:, :, i],
                            int(params["psf_size"]),
                            float(params["psf_sigma"]),
                            float(params["noise_power"]),
                        ),
                        0,
                        255,
                    ).astype(np.uint8)
                    for i in range(data.shape[2])
                ],
                axis=2,
            )

        return {"image": src.with_data(result)}
