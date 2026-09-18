from __future__ import annotations

import math

import numpy as np

from app.services.vision_labs.core import BoolParam, EnumParam, ExecutionContext, IntParam
from app.services.vision_labs.image.types import ImageFrame
from app.services.vision_labs.sampling_geometry.operator import SamplingGeometryOperator
from app.services.vision_labs.sampling_geometry.registry import sampling_operator
from app.services.vision_labs.sampling_geometry.specs import SamplingPort
from app.services.vision_labs.sampling_geometry.types import (
    FeatureVector,
    Histogram1D,
    Spectrum2D,
)
from app.services.vision_labs.sampling_geometry.operators.common import (
    image_channel,
    normalized_entropy,
)


_CHANNELS = ["gray", "r", "g", "b", "h", "s", "v"]


def _window_2d(height: int, width: int, mode: str) -> np.ndarray:
    if mode == "hann":
        return np.outer(np.hanning(height), np.hanning(width)).astype(np.float32)
    return np.ones((height, width), dtype=np.float32)


@sampling_operator
class FFT2D(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spectral.fft2d"
    LABEL = "2D Fourier Spectrum"
    CATEGORY = "Spectral / Fourier"
    WORKSPACE = "spectral"
    DESCRIPTION = "Convert a raster channel into a centered 2D Fourier magnitude map."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"spectrum": SamplingPort("spectrum_2d")}
    PARAMETERS = {
        "channel": EnumParam(_CHANNELS, default="gray", label="Channel"),
        "window": EnumParam(["none", "hann"], default="hann", label="Window"),
        "remove_mean": BoolParam(default=True, label="Remove mean / DC"),
    }
    GUIDE = {
        "overview": "Re-expresses the image as spatial-frequency energy instead of pixel position.",
        "how_it_works": "The selected channel is optionally mean-centered and Hann-windowed, transformed with a 2D FFT, shifted so zero frequency is at the center, then converted to magnitude.",
        "tips": [
            "Keep Hann window enabled for cropped images unless border discontinuity is itself meaningful.",
            "Remove mean when you care about texture/periodicity more than absolute brightness.",
        ],
        "notes": [
            "The spectrum map is visualizable, but downstream models should usually consume structured frequency descriptors rather than a flattened full spectrum.",
        ],
        "visualization": "fft2d",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        image = image_channel(frame, params["channel"]).astype(np.float32)
        h, w = image.shape[:2]
        if bool(params["remove_mean"]):
            image = image - float(image.mean())
        image = image * _window_2d(h, w, params["window"])
        spectrum = np.fft.fftshift(np.fft.fft2(image))
        magnitude = np.abs(spectrum).astype(np.float32)
        return {
            "spectrum": Spectrum2D(
                magnitude=magnitude,
                source_shape=(h, w),
                window=params["window"],
                channel=params["channel"],
                metadata={"remove_mean": bool(params["remove_mean"])},
            )
        }


@sampling_operator
class RadialFrequencyBands(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spectral.radial_bands"
    LABEL = "Radial Frequency Bands"
    CATEGORY = "Spectral / Descriptor"
    WORKSPACE = "spectral"
    DESCRIPTION = "Pool Fourier energy into concentric radial frequency bands."
    INPUTS = {"spectrum": SamplingPort("spectrum_2d")}
    OUTPUTS = {"features": SamplingPort("feature_vector")}
    PARAMETERS = {
        "bands": IntParam(default=8, min=2, max=64, label="Radial bands"),
        "normalize": BoolParam(default=True, label="Normalize energy"),
    }
    GUIDE = {
        "overview": "Compresses a 2D Fourier map into a compact low-to-high-frequency descriptor.",
        "how_it_works": "Distance from the spectrum center corresponds to spatial frequency magnitude. Pixels are grouped into equal normalized radial bands and their squared magnitude is summed.",
        "tips": [
            "Use 4-12 bands first; too many bands often create unstable high-dimensional descriptors.",
            "Normalized energy is useful when overall image contrast varies but frequency distribution matters.",
        ],
        "notes": [
            "This descriptor discards orientation. Use Angular Frequency Bands when directional texture matters.",
        ],
        "visualization": "radial_bands",
    }

    def process(self, inputs, params, context: ExecutionContext):
        spectrum: Spectrum2D = inputs["spectrum"]
        mag = np.asarray(spectrum.magnitude, dtype=np.float64)
        h, w = mag.shape[:2]
        yy, xx = np.indices((h, w), dtype=np.float64)
        cx = (w - 1) / 2.0
        cy = (h - 1) / 2.0
        radius = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        radius /= max(1e-9, float(radius.max()))
        energy = mag * mag
        bands = int(params["bands"])
        edges = np.linspace(0.0, 1.0, bands + 1)
        values = []
        for i in range(bands):
            if i == bands - 1:
                mask = (radius >= edges[i]) & (radius <= edges[i + 1])
            else:
                mask = (radius >= edges[i]) & (radius < edges[i + 1])
            values.append(float(energy[mask].sum()))
        values_array = np.asarray(values, dtype=np.float64)
        if bool(params["normalize"]):
            total = float(values_array.sum())
            if total > 0:
                values_array /= total
        names = [f"radial_band_{i:02d}" for i in range(bands)]
        return {
            "features": FeatureVector(
                values=values_array.astype(np.float32),
                names=names,
                groups=["radial_frequency"] * bands,
                metadata={"normalized": bool(params["normalize"])},
            )
        }


@sampling_operator
class AngularFrequencyBands(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.spectral.angular_bands"
    LABEL = "Angular Frequency Bands"
    CATEGORY = "Spectral / Descriptor"
    WORKSPACE = "spectral"
    DESCRIPTION = "Pool Fourier energy by orientation sector."
    INPUTS = {"spectrum": SamplingPort("spectrum_2d")}
    OUTPUTS = {"features": SamplingPort("feature_vector")}
    PARAMETERS = {
        "sectors": IntParam(default=12, min=4, max=72, label="Angular sectors"),
        "normalize": BoolParam(default=True, label="Normalize energy"),
    }
    GUIDE = {
        "overview": "Measures how strongly the image contains texture/structure at different orientations.",
        "how_it_works": "Spectrum pixels are converted to angle around the Fourier center and energy is pooled into orientation sectors. Opposite directions are folded together over 0..180 degrees.",
        "tips": [
            "Use 8-18 sectors for a first descriptor.",
            "Directional repetitive texture usually produces strong peaks in a small number of sectors.",
        ],
        "notes": [
            "A strong image-space line produces Fourier energy in the perpendicular frequency direction.",
        ],
        "visualization": "angular_bands",
    }

    def process(self, inputs, params, context: ExecutionContext):
        spectrum: Spectrum2D = inputs["spectrum"]
        mag = np.asarray(spectrum.magnitude, dtype=np.float64)
        h, w = mag.shape[:2]
        yy, xx = np.indices((h, w), dtype=np.float64)
        cx = (w - 1) / 2.0
        cy = (h - 1) / 2.0
        angle = np.mod(np.arctan2(yy - cy, xx - cx), math.pi)
        energy = mag * mag
        sectors = int(params["sectors"])
        edges = np.linspace(0.0, math.pi, sectors + 1)
        values = []
        for i in range(sectors):
            if i == sectors - 1:
                mask = (angle >= edges[i]) & (angle <= edges[i + 1])
            else:
                mask = (angle >= edges[i]) & (angle < edges[i + 1])
            values.append(float(energy[mask].sum()))
        arr = np.asarray(values, dtype=np.float64)
        if bool(params["normalize"]):
            total = float(arr.sum())
            if total > 0:
                arr /= total
        names = [f"angle_{(180.0 * i / sectors):.1f}_deg" for i in range(sectors)]
        return {
            "features": FeatureVector(
                values=arr.astype(np.float32),
                names=names,
                groups=["angular_frequency"] * sectors,
                metadata={"normalized": bool(params["normalize"])},
            )
        }


@sampling_operator
class Histogram(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.statistics.histogram"
    LABEL = "Intensity Histogram"
    CATEGORY = "Statistics / Distribution"
    WORKSPACE = "spectral"
    DESCRIPTION = "Build a one-dimensional intensity histogram for a selected image channel."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"histogram": SamplingPort("histogram_1d")}
    PARAMETERS = {
        "channel": EnumParam(_CHANNELS, default="gray", label="Channel"),
        "bins": IntParam(default=32, min=4, max=256, label="Bins"),
        "normalize": BoolParam(default=True, label="Normalize"),
    }
    GUIDE = {
        "overview": "Summarizes how pixel intensities are distributed without preserving pixel location.",
        "how_it_works": "The selected channel is partitioned into equally spaced intensity bins and the number/proportion of pixels in each bin is counted.",
        "tips": [
            "16-64 bins are often enough for compact MLP descriptors.",
            "Use normalized histograms when image/ROI size can change.",
        ],
        "notes": [
            "Histograms discard spatial arrangement, so combine them with patch/grid sampling when location matters.",
        ],
        "visualization": "histogram",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        image = image_channel(frame, params["channel"])
        bins = int(params["bins"])
        hist, edges = np.histogram(image.reshape(-1), bins=bins, range=(0.0, 256.0))
        values = hist.astype(np.float64)
        if bool(params["normalize"]):
            total = float(values.sum())
            if total > 0:
                values /= total
        centers = (edges[:-1] + edges[1:]) * 0.5
        return {
            "histogram": Histogram1D(
                bins=centers.astype(np.float32),
                values=values.astype(np.float32),
                channel=params["channel"],
                normalized=bool(params["normalize"]),
            )
        }


@sampling_operator
class BasicStatistics(SamplingGeometryOperator):
    OPERATOR_ID = "sampling.statistics.basic"
    LABEL = "Basic Statistics"
    CATEGORY = "Statistics / Descriptor"
    WORKSPACE = "spectral"
    DESCRIPTION = "Extract compact global intensity statistics as a named FeatureVector."
    INPUTS = {"image": SamplingPort("image")}
    OUTPUTS = {"features": SamplingPort("feature_vector")}
    PARAMETERS = {
        "channel": EnumParam(_CHANNELS, default="gray", label="Channel"),
    }
    GUIDE = {
        "overview": "Creates a compact global descriptor from simple distribution statistics.",
        "how_it_works": "Mean, standard deviation, minimum, maximum, 5/50/95 percentiles and normalized entropy are computed from the selected channel.",
        "tips": [
            "Use this as a baseline descriptor before adding more complex Fourier or patch features.",
        ],
        "notes": [
            "Global statistics are cheap but cannot encode where a defect occurs.",
        ],
        "visualization": "statistics",
    }

    def process(self, inputs, params, context: ExecutionContext):
        frame: ImageFrame = inputs["image"]
        image = image_channel(frame, params["channel"]).reshape(-1)
        values = np.array(
            [
                float(np.mean(image)),
                float(np.std(image)),
                float(np.min(image)),
                float(np.max(image)),
                float(np.percentile(image, 5)),
                float(np.percentile(image, 50)),
                float(np.percentile(image, 95)),
                float(normalized_entropy(image)),
            ],
            dtype=np.float32,
        )
        names = [
            "mean",
            "std",
            "min",
            "max",
            "p05",
            "p50",
            "p95",
            "entropy_norm",
        ]
        return {
            "features": FeatureVector(
                values=values,
                names=names,
                groups=["statistics"] * len(names),
                metadata={"channel": params["channel"]},
            )
        }
