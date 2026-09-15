from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_u8(data: np.ndarray) -> np.ndarray:
    if data.dtype == np.uint8:
        return data
    normalized = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX)
    return np.clip(normalized, 0, 255).astype(np.uint8)


def _to_bgr(src: ImageFrame) -> np.ndarray:
    data = _as_u8(src.data)
    if src.channels == 1 or src.color_space == ColorSpace.GRAY:
        return cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
    if src.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
    if src.color_space == ColorSpace.HSV:
        return cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
    return data.copy()


def _to_gray(src: ImageFrame) -> np.ndarray:
    data = _as_u8(src.data)
    if src.channels == 1 or src.color_space == ColorSpace.GRAY:
        return data.copy()
    if src.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2GRAY)
    if src.color_space == ColorSpace.HSV:
        bgr = cv2.cvtColor(data, cv2.COLOR_HSV2BGR)
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)


def _to_hsv(src: ImageFrame) -> np.ndarray:
    data = _as_u8(src.data)
    if src.color_space == ColorSpace.HSV and src.channels == 3:
        return data.copy()
    if src.channels == 1 or src.color_space == ColorSpace.GRAY:
        data = cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
        return cv2.cvtColor(data, cv2.COLOR_BGR2HSV)
    if src.color_space == ColorSpace.RGB:
        return cv2.cvtColor(data, cv2.COLOR_RGB2HSV)
    return cv2.cvtColor(data, cv2.COLOR_BGR2HSV)


def _restore_bgr(src: ImageFrame, bgr: np.ndarray) -> ImageFrame:
    if src.color_space == ColorSpace.RGB:
        return src.with_data(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), color_space=ColorSpace.RGB)
    if src.color_space == ColorSpace.HSV:
        return src.with_data(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV), color_space=ColorSpace.HSV)
    return src.with_data(bgr, color_space=ColorSpace.BGR)


def _morph_kernel(size: int, shape: str) -> np.ndarray:
    mapping = {
        "rect": cv2.MORPH_RECT,
        "ellipse": cv2.MORPH_ELLIPSE,
        "cross": cv2.MORPH_CROSS,
    }
    return cv2.getStructuringElement(mapping.get(shape, cv2.MORPH_RECT), (size, size))


# ---------------------------------------------------------------------------
# Color & channels
# ---------------------------------------------------------------------------

@image_operator(
    id="image.color.bgr_to_hsv",
    label="BGR / RGB → HSV",
    category="Color & Channels",
    description="Convert a color image into HSV representation.",
)
class ToHSV(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        return {"image": src.with_data(_to_hsv(src), color_space=ColorSpace.HSV)}


@image_operator(
    id="image.color.hsv_to_bgr",
    label="HSV → BGR",
    category="Color & Channels",
    description="Convert HSV representation back to BGR.",
)
class HSVToBGR(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        return {"image": src.with_data(_to_bgr(src), color_space=ColorSpace.BGR)}


@image_operator(
    id="image.color.extract_channel",
    label="Extract Channel",
    category="Color & Channels",
    description="Extract B/G/R or H/S/V as a grayscale image.",
)
class ExtractChannel(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "channel": EnumParam(("B", "G", "R", "H", "S", "V"), default="B"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        channel = str(params["channel"])
        if channel in ("H", "S", "V"):
            data = _to_hsv(src)[:, :, {"H": 0, "S": 1, "V": 2}[channel]]
        else:
            data = _to_bgr(src)[:, :, {"B": 0, "G": 1, "R": 2}[channel]]
        return {"image": src.with_data(data, color_space=ColorSpace.GRAY)}


@image_operator(
    id="image.color.invert",
    label="Invert Image",
    category="Color & Channels",
    description="Invert every image intensity value.",
)
class InvertImage(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        return {"image": src.with_data(cv2.bitwise_not(_as_u8(src.data)))}


# ---------------------------------------------------------------------------
# Intensity & contrast
# ---------------------------------------------------------------------------

@image_operator(
    id="image.enhance.brightness_contrast",
    label="Brightness / Contrast",
    category="Enhancement",
    description="Linear intensity transform: output = alpha * input + beta.",
)
class BrightnessContrast(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "alpha": FloatParam(default=1.0, min=0.0, max=4.0, ui_hint="slider"),
        "beta": IntParam(default=0, min=-255, max=255, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        base = _as_u8(src.data).astype(np.float32)
        dst = np.clip(base * float(params["alpha"]) + int(params["beta"]), 0, 255).astype(np.uint8)
        return {"image": src.with_data(dst)}


@image_operator(
    id="image.enhance.gamma",
    label="Gamma Correction",
    category="Enhancement",
    description="Apply nonlinear gamma intensity correction.",
)
class GammaCorrection(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "gamma": FloatParam(default=1.0, min=0.05, max=5.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gamma = max(0.01, float(params["gamma"]))
        table = np.array([((i / 255.0) ** gamma) * 255.0 for i in range(256)], dtype=np.uint8)
        return {"image": src.with_data(cv2.LUT(_as_u8(src.data), table))}


@image_operator(
    id="image.enhance.normalize_minmax",
    label="Normalize Min / Max",
    category="Enhancement",
    description="Normalize image values into the 0..255 range.",
)
class NormalizeMinMax(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        dst = cv2.normalize(src.data, None, 0, 255, cv2.NORM_MINMAX)
        return {"image": src.with_data(np.clip(dst, 0, 255).astype(np.uint8))}


@image_operator(
    id="image.enhance.equalize_hist",
    label="Histogram Equalization",
    category="Enhancement",
    description="Equalize grayscale or luminance histogram.",
)
class HistogramEqualization(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        if src.channels == 1:
            return {"image": src.with_data(cv2.equalizeHist(_to_gray(src)), color_space=ColorSpace.GRAY)}
        if src.color_space == ColorSpace.HSV:
            hsv = _to_hsv(src)
            hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
            return {"image": src.with_data(hsv, color_space=ColorSpace.HSV)}
        bgr = _to_bgr(src)
        ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        return {"image": _restore_bgr(src, cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR))}


@image_operator(
    id="image.enhance.clahe",
    label="CLAHE",
    category="Enhancement",
    description="Contrast-limited adaptive histogram equalization.",
)
class CLAHE(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "clip_limit": FloatParam(default=2.0, min=0.1, max=20.0, ui_hint="slider"),
        "tile_grid": IntParam(default=8, min=2, max=32, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        clahe = cv2.createCLAHE(
            clipLimit=float(params["clip_limit"]),
            tileGridSize=(int(params["tile_grid"]), int(params["tile_grid"])),
        )
        if src.channels == 1:
            return {"image": src.with_data(clahe.apply(_to_gray(src)), color_space=ColorSpace.GRAY)}
        if src.color_space == ColorSpace.HSV:
            hsv = _to_hsv(src)
            hsv[:, :, 2] = clahe.apply(hsv[:, :, 2])
            return {"image": src.with_data(hsv, color_space=ColorSpace.HSV)}
        bgr = _to_bgr(src)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return {"image": _restore_bgr(src, cv2.cvtColor(lab, cv2.COLOR_LAB2BGR))}


# ---------------------------------------------------------------------------
# Smooth / denoise
# ---------------------------------------------------------------------------

@image_operator(
    id="image.filter.box",
    label="Box Blur",
    category="Smooth / Denoise",
    description="Uniform mean blur.",
)
class BoxBlur(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=3, min=1, max=51, odd=True, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        k = int(params["kernel_size"])
        return {"image": src.with_data(cv2.blur(src.data, (k, k)))}


@image_operator(
    id="image.filter.median",
    label="Median Blur",
    category="Smooth / Denoise",
    description="Median filter, effective against impulse noise.",
)
class MedianBlur(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=3, min=1, max=31, odd=True, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        k = int(params["kernel_size"])
        if k == 1:
            return {"image": src.with_data(src.data.copy())}
        return {"image": src.with_data(cv2.medianBlur(_as_u8(src.data), k))}


@image_operator(
    id="image.filter.bilateral",
    label="Bilateral Filter",
    category="Smooth / Denoise",
    description="Edge-preserving bilateral smoothing.",
)
class BilateralFilter(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "diameter": IntParam(default=7, min=1, max=31, ui_hint="slider"),
        "sigma_color": FloatParam(default=50.0, min=1.0, max=200.0, ui_hint="slider"),
        "sigma_space": FloatParam(default=50.0, min=1.0, max=200.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        dst = cv2.bilateralFilter(
            _as_u8(src.data),
            int(params["diameter"]),
            float(params["sigma_color"]),
            float(params["sigma_space"]),
        )
        return {"image": src.with_data(dst)}


@image_operator(
    id="image.filter.nlmeans",
    label="Non-local Means Denoise",
    category="Smooth / Denoise",
    description="High-quality non-local means denoising.",
)
class NonLocalMeans(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "strength": FloatParam(default=7.0, min=1.0, max=30.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        h = float(params["strength"])
        if src.channels == 1:
            dst = cv2.fastNlMeansDenoising(_to_gray(src), None, h, 7, 21)
            return {"image": src.with_data(dst, color_space=ColorSpace.GRAY)}
        bgr = _to_bgr(src)
        dst = cv2.fastNlMeansDenoisingColored(bgr, None, h, h, 7, 21)
        return {"image": _restore_bgr(src, dst)}


# ---------------------------------------------------------------------------
# Sharpen / detail
# ---------------------------------------------------------------------------

@image_operator(
    id="image.sharpen.unsharp",
    label="Unsharp Mask",
    category="Sharpen / Detail",
    description="Sharpen by subtracting a Gaussian-smoothed version.",
)
class UnsharpMask(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=5, min=3, max=31, odd=True, ui_hint="slider"),
        "sigma": FloatParam(default=1.0, min=0.0, max=10.0, ui_hint="slider"),
        "amount": FloatParam(default=1.0, min=0.0, max=5.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data)
        k = int(params["kernel_size"])
        blur = cv2.GaussianBlur(data, (k, k), float(params["sigma"]))
        amount = float(params["amount"])
        dst = cv2.addWeighted(data, 1.0 + amount, blur, -amount, 0)
        return {"image": src.with_data(dst)}


@image_operator(
    id="image.sharpen.laplacian",
    label="Laplacian Sharpen",
    category="Sharpen / Detail",
    description="Sharpen using Laplacian high-frequency detail.",
)
class LaplacianSharpen(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "amount": FloatParam(default=0.7, min=0.0, max=3.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data).astype(np.float32)
        lap = cv2.Laplacian(data, cv2.CV_32F, ksize=3)
        dst = np.clip(data - float(params["amount"]) * lap, 0, 255).astype(np.uint8)
        return {"image": src.with_data(dst)}


# ---------------------------------------------------------------------------
# Threshold / segmentation primitives
# ---------------------------------------------------------------------------

@image_operator(
    id="image.threshold.otsu",
    label="Otsu Threshold",
    category="Threshold / Binarize",
    description="Automatic global threshold selected by Otsu's method.",
)
class OtsuThreshold(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {"invert": BoolParam(default=False)}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        flag = cv2.THRESH_BINARY_INV if params["invert"] else cv2.THRESH_BINARY
        _, data = cv2.threshold(_to_gray(src), 0, 255, flag | cv2.THRESH_OTSU)
        return {"mask": BinaryMask.from_image(data, src)}


@image_operator(
    id="image.threshold.adaptive_mean",
    label="Adaptive Mean Threshold",
    category="Threshold / Binarize",
    description="Local adaptive threshold using neighborhood mean.",
)
class AdaptiveMeanThreshold(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "block_size": IntParam(default=11, min=3, max=101, odd=True, ui_hint="slider"),
        "c": FloatParam(default=2.0, min=-30.0, max=30.0, ui_hint="slider"),
        "invert": BoolParam(default=False),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        kind = cv2.THRESH_BINARY_INV if params["invert"] else cv2.THRESH_BINARY
        data = cv2.adaptiveThreshold(
            _to_gray(src),
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            kind,
            int(params["block_size"]),
            float(params["c"]),
        )
        return {"mask": BinaryMask.from_image(data, src)}


@image_operator(
    id="image.threshold.adaptive_gaussian",
    label="Adaptive Gaussian Threshold",
    category="Threshold / Binarize",
    description="Local adaptive threshold with Gaussian neighborhood weighting.",
)
class AdaptiveGaussianThreshold(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "block_size": IntParam(default=11, min=3, max=101, odd=True, ui_hint="slider"),
        "c": FloatParam(default=2.0, min=-30.0, max=30.0, ui_hint="slider"),
        "invert": BoolParam(default=False),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        kind = cv2.THRESH_BINARY_INV if params["invert"] else cv2.THRESH_BINARY
        data = cv2.adaptiveThreshold(
            _to_gray(src),
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            kind,
            int(params["block_size"]),
            float(params["c"]),
        )
        return {"mask": BinaryMask.from_image(data, src)}


@image_operator(
    id="image.threshold.gray_range",
    label="Gray Range",
    category="Threshold / Binarize",
    description="Keep grayscale pixels between lower and upper bounds.",
)
class GrayRange(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "lower": IntParam(default=80, min=0, max=255, ui_hint="slider"),
        "upper": IntParam(default=255, min=0, max=255, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        lower, upper = sorted((int(params["lower"]), int(params["upper"])))
        return {"mask": BinaryMask.from_image(cv2.inRange(_to_gray(src), lower, upper), src)}


@image_operator(
    id="image.threshold.hsv_range",
    label="HSV Range",
    category="Threshold / Binarize",
    description="Create a mask from H/S/V lower and upper bounds.",
)
class HSVRange(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "h_low": IntParam(default=0, min=0, max=179, ui_hint="slider"),
        "h_high": IntParam(default=179, min=0, max=179, ui_hint="slider"),
        "s_low": IntParam(default=0, min=0, max=255, ui_hint="slider"),
        "s_high": IntParam(default=255, min=0, max=255, ui_hint="slider"),
        "v_low": IntParam(default=0, min=0, max=255, ui_hint="slider"),
        "v_high": IntParam(default=255, min=0, max=255, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        lower = np.array([params["h_low"], params["s_low"], params["v_low"]], dtype=np.uint8)
        upper = np.array([params["h_high"], params["s_high"], params["v_high"]], dtype=np.uint8)
        data = cv2.inRange(_to_hsv(src), lower, upper)
        return {"mask": BinaryMask.from_image(data, src)}


# ---------------------------------------------------------------------------
# Edge / gradient
# ---------------------------------------------------------------------------

@image_operator(
    id="image.edge.canny",
    label="Canny Edge",
    category="Edge / Gradient",
    description="Canny edge detector producing a binary edge mask.",
)
class CannyEdge(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "low": IntParam(default=50, min=0, max=255, ui_hint="slider"),
        "high": IntParam(default=150, min=0, max=255, ui_hint="slider"),
        "aperture": EnumParam((3, 5, 7), default=3),
        "l2_gradient": BoolParam(default=False),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        low, high = sorted((int(params["low"]), int(params["high"])))
        data = cv2.Canny(
            _to_gray(src),
            low,
            high,
            apertureSize=int(params["aperture"]),
            L2gradient=bool(params["l2_gradient"]),
        )
        return {"mask": BinaryMask.from_image(data, src)}


class _SobelBase(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": EnumParam((1, 3, 5, 7), default=3),
    }
    DX = 1
    DY = 0

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        grad = cv2.Sobel(_to_gray(src), cv2.CV_32F, self.DX, self.DY, ksize=int(params["kernel_size"]))
        data = cv2.convertScaleAbs(grad)
        return {"image": src.with_data(data, color_space=ColorSpace.GRAY)}


@image_operator(
    id="image.edge.sobel_x",
    label="Sobel X",
    category="Edge / Gradient",
    description="Horizontal derivative response.",
)
class SobelX(_SobelBase):
    DX, DY = 1, 0


@image_operator(
    id="image.edge.sobel_y",
    label="Sobel Y",
    category="Edge / Gradient",
    description="Vertical derivative response.",
)
class SobelY(_SobelBase):
    DX, DY = 0, 1


@image_operator(
    id="image.edge.gradient_magnitude",
    label="Gradient Magnitude",
    category="Edge / Gradient",
    description="Magnitude of Sobel X/Y gradient.",
)
class GradientMagnitude(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {"kernel_size": EnumParam((1, 3, 5, 7), default=3)}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        gray = _to_gray(src)
        k = int(params["kernel_size"])
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=k)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=k)
        magnitude = cv2.magnitude(gx, gy)
        data = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return {"image": src.with_data(data, color_space=ColorSpace.GRAY)}


@image_operator(
    id="image.edge.laplacian",
    label="Laplacian Edge",
    category="Edge / Gradient",
    description="Second derivative edge response.",
)
class LaplacianEdge(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {"kernel_size": EnumParam((1, 3, 5, 7), default=3)}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        lap = cv2.Laplacian(_to_gray(src), cv2.CV_32F, ksize=int(params["kernel_size"]))
        return {"image": src.with_data(cv2.convertScaleAbs(lap), color_space=ColorSpace.GRAY)}


# ---------------------------------------------------------------------------
# Binary-mask morphology / cleanup
# ---------------------------------------------------------------------------

class _MorphBase(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=3, min=1, max=51, odd=True, ui_hint="slider"),
        "shape": EnumParam(("rect", "ellipse", "cross"), default="rect"),
        "iterations": IntParam(default=1, min=1, max=20),
    }
    OP = cv2.MORPH_OPEN

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        kernel = _morph_kernel(int(params["kernel_size"]), str(params["shape"]))
        data = cv2.morphologyEx(
            src.data,
            self.OP,
            kernel,
            iterations=int(params["iterations"]),
        )
        return {"mask": src.with_data(data)}


@image_operator(
    id="image.morphology.erode",
    label="Erode",
    category="Morphology / Mask",
    description="Shrink white regions in a binary mask.",
)
class Erode(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = _MorphBase.PARAMETERS

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        kernel = _morph_kernel(int(params["kernel_size"]), str(params["shape"]))
        return {"mask": src.with_data(cv2.erode(src.data, kernel, iterations=int(params["iterations"])))}


@image_operator(
    id="image.morphology.dilate",
    label="Dilate",
    category="Morphology / Mask",
    description="Expand white regions in a binary mask.",
)
class Dilate(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = _MorphBase.PARAMETERS

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        kernel = _morph_kernel(int(params["kernel_size"]), str(params["shape"]))
        return {"mask": src.with_data(cv2.dilate(src.data, kernel, iterations=int(params["iterations"])))}


@image_operator(
    id="image.morphology.open",
    label="Morphology Open",
    category="Morphology / Mask",
    description="Remove small bright noise with erosion then dilation.",
)
class MorphologyOpen(_MorphBase):
    OP = cv2.MORPH_OPEN


@image_operator(
    id="image.morphology.gradient",
    label="Morphology Gradient",
    category="Morphology / Mask",
    description="Difference between dilation and erosion.",
)
class MorphologyGradient(_MorphBase):
    OP = cv2.MORPH_GRADIENT


@image_operator(
    id="image.morphology.tophat",
    label="Top Hat",
    category="Morphology / Mask",
    description="Extract small bright structures.",
)
class TopHat(_MorphBase):
    OP = cv2.MORPH_TOPHAT


@image_operator(
    id="image.morphology.blackhat",
    label="Black Hat",
    category="Morphology / Mask",
    description="Extract small dark holes/structures.",
)
class BlackHat(_MorphBase):
    OP = cv2.MORPH_BLACKHAT


@image_operator(
    id="image.morphology.fill_holes",
    label="Fill Holes",
    category="Morphology / Mask",
    description="Fill enclosed black holes inside white mask regions.",
)
class FillHoles(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        base = np.where(src.data > 0, 255, 0).astype(np.uint8)
        padded = cv2.copyMakeBorder(base, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
        flood = padded.copy()
        flood_mask = np.zeros((flood.shape[0] + 2, flood.shape[1] + 2), np.uint8)
        cv2.floodFill(flood, flood_mask, (0, 0), 255)
        holes = cv2.bitwise_not(flood)
        filled = cv2.bitwise_or(padded, holes)[1:-1, 1:-1]
        return {"mask": src.with_data(filled)}


@image_operator(
    id="image.morphology.remove_small",
    label="Remove Small Components",
    category="Morphology / Mask",
    description="Remove connected foreground components below a minimum area.",
)
class RemoveSmallComponents(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "min_area": IntParam(default=50, min=1, max=100000, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        binary = np.where(src.data > 0, 255, 0).astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        dst = np.zeros_like(binary)
        min_area = int(params["min_area"])
        for label in range(1, count):
            if int(stats[label, cv2.CC_STAT_AREA]) >= min_area:
                dst[labels == label] = 255
        return {"mask": src.with_data(dst)}


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

@image_operator(
    id="image.convert.mask_to_image",
    label="Mask → Image",
    category="Conversion",
    description="Convert a BinaryMask back into a grayscale ImageFrame.",
)
class MaskToImage(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        frame = ImageFrame(
            data=src.data.copy(),
            color_space=ColorSpace.GRAY,
            coordinate_frame=src.coordinate_frame,
            metadata=dict(src.metadata),
        )
        return {"image": frame}


# ---------------------------------------------------------------------------
# Geometry / transforms
# ---------------------------------------------------------------------------

@image_operator(
    id="image.transform.rotate",
    label="Rotate",
    category="Transform",
    description="Rotate around image center while preserving canvas size.",
)
class Rotate(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "angle": FloatParam(default=0.0, min=-180.0, max=180.0, ui_hint="slider"),
        "border_value": IntParam(default=0, min=0, max=255),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        center = ((src.width - 1) / 2.0, (src.height - 1) / 2.0)
        matrix = cv2.getRotationMatrix2D(center, float(params["angle"]), 1.0)
        dst = cv2.warpAffine(
            src.data,
            matrix,
            (src.width, src.height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=int(params["border_value"]),
        )
        history = list(src.metadata.get("transform_history", []))
        history.append({"type": "rotate", "angle": float(params["angle"]), "matrix": matrix.tolist()})
        return {"image": src.with_data(dst, metadata_update={"transform_history": history})}


@image_operator(
    id="image.transform.flip",
    label="Flip",
    category="Transform",
    description="Flip image horizontally, vertically or both.",
)
class Flip(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "mode": EnumParam(("horizontal", "vertical", "both"), default="horizontal"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        code = {"horizontal": 1, "vertical": 0, "both": -1}[str(params["mode"])]
        dst = cv2.flip(src.data, code)
        history = list(src.metadata.get("transform_history", []))
        history.append({"type": "flip", "mode": str(params["mode"])})
        return {"image": src.with_data(dst, metadata_update={"transform_history": history})}


@image_operator(
    id="image.transform.crop_normalized",
    label="Crop (Normalized)",
    category="Transform",
    description="Crop using normalized x/y/width/height values in the 0..1 range.",
)
class CropNormalized(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "x": FloatParam(default=0.0, min=0.0, max=1.0, ui_hint="slider"),
        "y": FloatParam(default=0.0, min=0.0, max=1.0, ui_hint="slider"),
        "width": FloatParam(default=1.0, min=0.01, max=1.0, ui_hint="slider"),
        "height": FloatParam(default=1.0, min=0.01, max=1.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        x = float(params["x"])
        y = float(params["y"])
        w = float(params["width"])
        h = float(params["height"])
        if x + w > 1.0 or y + h > 1.0:
            raise ValueError("Crop x+width and y+height must remain <= 1.0")
        x0 = int(round(x * src.width))
        y0 = int(round(y * src.height))
        x1 = max(x0 + 1, int(round((x + w) * src.width)))
        y1 = max(y0 + 1, int(round((y + h) * src.height)))
        dst = src.data[y0:y1, x0:x1].copy()
        history = list(src.metadata.get("transform_history", []))
        history.append({"type": "crop", "pixel_bounds": [x0, y0, x1, y1], "normalized": [x, y, w, h]})
        return {"image": src.with_data(dst, metadata_update={"transform_history": history})}


@image_operator(
    id="image.transform.translate",
    label="Translate",
    category="Transform",
    description="Translate image in X/Y while preserving canvas size.",
)
class Translate(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "x": IntParam(default=0, min=-2000, max=2000, ui_hint="slider"),
        "y": IntParam(default=0, min=-2000, max=2000, ui_hint="slider"),
        "border_value": IntParam(default=0, min=0, max=255),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        matrix = np.float32([[1, 0, int(params["x"])], [0, 1, int(params["y"])]])
        dst = cv2.warpAffine(
            src.data,
            matrix,
            (src.width, src.height),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=int(params["border_value"]),
        )
        history = list(src.metadata.get("transform_history", []))
        history.append({"type": "translate", "x": int(params["x"]), "y": int(params["y"])})
        return {"image": src.with_data(dst, metadata_update={"transform_history": history})}


# ---------------------------------------------------------------------------
# Arithmetic / point operations
# ---------------------------------------------------------------------------

@image_operator(
    id="image.arithmetic.add_scalar",
    label="Add Scalar",
    category="Arithmetic",
    description="Add a scalar value to every pixel with clipping.",
)
class AddScalar(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "value": IntParam(default=0, min=-255, max=255, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data).astype(np.int16) + int(params["value"])
        return {"image": src.with_data(np.clip(data, 0, 255).astype(np.uint8))}


@image_operator(
    id="image.arithmetic.multiply_scalar",
    label="Multiply Scalar",
    category="Arithmetic",
    description="Multiply every pixel by a scalar with clipping.",
)
class MultiplyScalar(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "value": FloatParam(default=1.0, min=0.0, max=5.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        data = _as_u8(src.data).astype(np.float32) * float(params["value"])
        return {"image": src.with_data(np.clip(data, 0, 255).astype(np.uint8))}


@image_operator(
    id="image.arithmetic.weighted_blend",
    label="Weighted Blend",
    category="Arithmetic / Advanced",
    description="Blend two same-sized images. Requires multi-input wiring.",
)
class WeightedBlend(ImageOperator):
    INPUTS = {"image_a": ImagePort(), "image_b": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "alpha": FloatParam(default=0.5, min=0.0, max=1.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        a: ImageFrame = inputs["image_a"]
        b: ImageFrame = inputs["image_b"]
        if a.data.shape != b.data.shape:
            raise ValueError(f"Weighted Blend requires equal shapes, got {a.data.shape} and {b.data.shape}")
        alpha = float(params["alpha"])
        return {"image": a.with_data(cv2.addWeighted(_as_u8(a.data), alpha, _as_u8(b.data), 1.0 - alpha, 0))}


@image_operator(
    id="image.arithmetic.bitwise_and",
    label="Bitwise AND",
    category="Arithmetic / Advanced",
    description="Bitwise AND of two same-sized images. Requires multi-input wiring.",
)
class BitwiseAnd(ImageOperator):
    INPUTS = {"image_a": ImagePort(), "image_b": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        a: ImageFrame = inputs["image_a"]
        b: ImageFrame = inputs["image_b"]
        if a.data.shape != b.data.shape:
            raise ValueError(f"Bitwise AND requires equal shapes, got {a.data.shape} and {b.data.shape}")
        return {"image": a.with_data(cv2.bitwise_and(_as_u8(a.data), _as_u8(b.data)))}
