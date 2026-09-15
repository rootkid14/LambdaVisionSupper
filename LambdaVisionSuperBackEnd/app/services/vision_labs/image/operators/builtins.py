from __future__ import annotations

import cv2
import numpy as np

from app.services.vision_labs.core import (
    BinaryMaskPort,
    BoolParam,
    ExecutionContext,
    FloatParam,
    ImagePort,
    IntParam,
)
from app.services.vision_labs.image.operator import ImageOperator
from app.services.vision_labs.image.registry import image_operator
from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame


@image_operator(
    id="image.color.grayscale",
    label="Grayscale",
    category="Color",
    description="Convert BGR/RGB image to single-channel grayscale.",
)
class Grayscale(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        if src.channels == 1:
            gray = src.data.copy()
        elif src.color_space == ColorSpace.RGB:
            gray = cv2.cvtColor(src.data, cv2.COLOR_RGB2GRAY)
        else:
            gray = cv2.cvtColor(src.data, cv2.COLOR_BGR2GRAY)
        return {"image": src.with_data(gray, color_space=ColorSpace.GRAY)}


@image_operator(
    id="image.filter.gaussian",
    label="Gaussian Blur",
    category="Smooth / Blur",
    description="Smooth an image using a Gaussian kernel.",
)
class GaussianBlur(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=5, min=1, max=51, odd=True, ui_hint="slider"),
        "sigma": FloatParam(default=0.0, min=0.0, max=20.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        k = int(params["kernel_size"])
        dst = cv2.GaussianBlur(src.data, (k, k), float(params["sigma"]))
        return {"image": src.with_data(dst)}


@image_operator(
    id="image.threshold.binary",
    label="Binary Threshold",
    category="Binarize",
    description="Apply a fixed threshold to a single-channel image.",
)
class BinaryThreshold(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "threshold": IntParam(default=127, min=0, max=255, ui_hint="slider"),
        "invert": BoolParam(default=False),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        if src.channels != 1:
            raise ValueError(
                "Binary Threshold expects a single-channel image. "
                "Add Grayscale before Threshold."
            )
        flag = cv2.THRESH_BINARY_INV if params["invert"] else cv2.THRESH_BINARY
        _, data = cv2.threshold(src.data, int(params["threshold"]), 255, flag)
        return {"mask": BinaryMask.from_image(data, src)}


@image_operator(
    id="image.morphology.close",
    label="Morphology Close",
    category="Morphology",
    description="Close small holes/gaps in a binary mask.",
)
class MorphologyClose(ImageOperator):
    INPUTS = {"mask": BinaryMaskPort()}
    OUTPUTS = {"mask": BinaryMaskPort()}
    PARAMETERS = {
        "kernel_size": IntParam(default=3, min=1, max=31, odd=True, ui_hint="slider"),
        "iterations": IntParam(default=1, min=1, max=20),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: BinaryMask = inputs["mask"]
        k = int(params["kernel_size"])
        kernel = np.ones((k, k), dtype=np.uint8)
        dst = cv2.morphologyEx(
            src.data,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=int(params["iterations"]),
        )
        return {"mask": src.with_data(dst)}


@image_operator(
    id="image.transform.resize",
    label="Resize",
    category="Transform",
    description="Resize an image by a scalar factor and record transform history.",
)
class Resize(ImageOperator):
    INPUTS = {"image": ImagePort()}
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {
        "scale": FloatParam(default=1.0, min=0.05, max=8.0, ui_hint="slider"),
    }

    def process(self, inputs, params, context: ExecutionContext):
        src: ImageFrame = inputs["image"]
        scale = float(params["scale"])
        width = max(1, int(round(src.width * scale)))
        height = max(1, int(round(src.height * scale)))
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        dst = cv2.resize(src.data, (width, height), interpolation=interpolation)
        history = list(src.metadata.get("transform_history", []))
        history.append(
            {
                "type": "resize",
                "from": [src.width, src.height],
                "to": [width, height],
                "scale_x": width / src.width,
                "scale_y": height / src.height,
            }
        )
        return {
            "image": src.with_data(
                dst,
                metadata_update={"transform_history": history},
            )
        }


@image_operator(
    id="image.arithmetic.absdiff",
    label="Absolute Difference",
    category="Arithmetic",
    description="Compute absolute difference between two same-sized images.",
)
class AbsDifference(ImageOperator):
    INPUTS = {
        "image_a": ImagePort(),
        "image_b": ImagePort(),
    }
    OUTPUTS = {"image": ImagePort()}
    PARAMETERS = {}

    def process(self, inputs, params, context: ExecutionContext):
        a: ImageFrame = inputs["image_a"]
        b: ImageFrame = inputs["image_b"]
        if a.data.shape != b.data.shape:
            raise ValueError(
                f"Absolute Difference requires equal shapes, got {a.data.shape} and {b.data.shape}"
            )
        dst = cv2.absdiff(a.data, b.data)
        return {"image": a.with_data(dst)}
