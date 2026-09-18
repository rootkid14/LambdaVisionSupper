from __future__ import annotations

import cv2
import numpy as np

from app.services.vision_app.models import LocatedRoi, MasterRoi, NormalizedRect, RoiLocatorConfig, RoiSearchConfig


def _odd_kernel(value: int) -> int:
    value = max(1, int(value))
    return value if value % 2 == 1 else value + 1


def _rect_px(rect: NormalizedRect, shape) -> tuple[int, int, int, int]:
    h, w = int(shape[0]), int(shape[1])
    x = max(0, min(w - 1, int(round(rect.x * w))))
    y = max(0, min(h - 1, int(round(rect.y * h))))
    rw = max(1, min(w - x, int(round(rect.w * w))))
    rh = max(1, min(h - y, int(round(rect.h * h))))
    return x, y, rw, rh


def _norm_rect(x: int, y: int, w: int, h: int, shape) -> NormalizedRect:
    ih, iw = int(shape[0]), int(shape[1])
    return NormalizedRect(
        x=max(0.0, min(1.0, x / max(1, iw))),
        y=max(0.0, min(1.0, y / max(1, ih))),
        w=max(1.0 / max(1, iw), min(1.0, w / max(1, iw))),
        h=max(1.0 / max(1, ih), min(1.0, h / max(1, ih))),
    )


def _gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _match_template(search: np.ndarray, template: np.ndarray) -> tuple[float, tuple[int, int]]:
    """Return a normalized high-is-good score and the best top-left location.

    Low-texture templates make TM_CCOEFF_NORMED numerically ambiguous, so use
    normalized squared difference in that case and invert the score.
    """
    if float(np.std(template)) < 1e-6:
        response = cv2.matchTemplate(search, template, cv2.TM_SQDIFF_NORMED)
        min_value, _, min_location, _ = cv2.minMaxLoc(response)
        return 1.0 - float(min_value), (int(min_location[0]), int(min_location[1]))

    response = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
    _, max_value, _, max_location = cv2.minMaxLoc(response)
    return float(max_value), (int(max_location[0]), int(max_location[1]))


def blur_preview(image: np.ndarray, kernel: int) -> np.ndarray:
    gray = _gray(image)
    blurred = cv2.GaussianBlur(gray, (_odd_kernel(kernel), _odd_kernel(kernel)), 0)
    return cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)


def _search_window(rect_px, shape, margin: int):
    x, y, w, h = rect_px
    ih, iw = shape[:2]
    x0 = max(0, x - margin)
    y0 = max(0, y - margin)
    x1 = min(iw, x + w + margin)
    y1 = min(ih, y + h + margin)
    return x0, y0, x1, y1


def _legacy_config(roi: MasterRoi) -> RoiLocatorConfig:
    legacy = roi.search or RoiSearchConfig()
    payload = legacy.model_dump() if hasattr(legacy, "model_dump") else legacy.dict()
    return RoiLocatorConfig(**payload)


def locate_manual(roi: MasterRoi, test_image: np.ndarray, config: RoiLocatorConfig | None = None) -> LocatedRoi:
    return LocatedRoi(
        roi_id=roi.roi_id,
        name=roi.name,
        rect=roi.rect,
        score=1.0,
        method="manual",
        found=True,
        message="Manual ROI uses identical normalized coordinates on the test image.",
    )


def locate_blur_template(
    roi: MasterRoi,
    master_image: np.ndarray,
    test_image: np.ndarray,
    config: RoiLocatorConfig | None = None,
) -> LocatedRoi:
    config = config or _legacy_config(roi)
    master_gray = _gray(master_image)
    test_gray = _gray(test_image)
    mx, my, mw, mh = _rect_px(roi.rect, master_gray.shape)
    base_template = master_gray[my : my + mh, mx : mx + mw]
    if base_template.size == 0:
        raise ValueError(f"ROI {roi.roi_id} has an empty master template")

    kernel = _odd_kernel(config.blur_kernel)

    # A nearly uniform ROI (for example a filled white rectangle) has very little
    # spatial information inside the ROI itself. Blurring makes that ambiguity
    # even worse and can move the correlation peak by a few pixels. In that case
    # include a small halo around the ROI so the template contains the object
    # boundary/background transition. The returned location is translated back
    # to the original ROI top-left.
    low_texture = float(np.std(base_template)) < 1e-3
    context_pad = max(4, kernel * 2) if low_texture else 0
    cmx0 = max(0, mx - context_pad)
    cmy0 = max(0, my - context_pad)
    cmx1 = min(master_gray.shape[1], mx + mw + context_pad)
    cmy1 = min(master_gray.shape[0], my + mh + context_pad)
    template_context = master_gray[cmy0:cmy1, cmx0:cmx1]
    roi_offset_x = mx - cmx0
    roi_offset_y = my - cmy0

    blurred_template = cv2.GaussianBlur(template_context, (kernel, kernel), 0)
    test_blur = cv2.GaussianBlur(test_gray, (kernel, kernel), 0)

    margin = config.geometry.search_margin_px if config.geometry.enabled else max(test_gray.shape)
    tx, ty, tw, th = _rect_px(roi.rect, test_gray.shape)

    expected_context_x = tx - roi_offset_x
    expected_context_y = ty - roi_offset_y
    context_w = int(template_context.shape[1])
    context_h = int(template_context.shape[0])
    x0, y0, x1, y1 = _search_window(
        (expected_context_x, expected_context_y, context_w, context_h),
        test_gray.shape,
        margin,
    )
    search_blur = test_blur[y0:y1, x0:x1]
    if search_blur.shape[0] < context_h or search_blur.shape[1] < context_w:
        return LocatedRoi(
            roi_id=roi.roi_id,
            name=roi.name,
            rect=roi.rect,
            score=0.0,
            method="blur_template",
            found=False,
            message="Search window is smaller than the master template",
        )

    coarse_score, coarse_location = _match_template(search_blur, blurred_template)
    coarse_cx = x0 + coarse_location[0]
    coarse_cy = y0 + coarse_location[1]

    # Refine on the original grayscale data in only a small neighborhood around
    # the coarse blurred result. This retains the noise-suppression benefit of
    # blur for discovery while restoring pixel-level edge alignment.
    refine_radius = max(2, kernel)
    rx0 = max(0, coarse_cx - refine_radius)
    ry0 = max(0, coarse_cy - refine_radius)
    rx1 = min(test_gray.shape[1], coarse_cx + context_w + refine_radius)
    ry1 = min(test_gray.shape[0], coarse_cy + context_h + refine_radius)
    refine_search = test_gray[ry0:ry1, rx0:rx1]

    refined_cx, refined_cy = coarse_cx, coarse_cy
    if refine_search.shape[0] >= context_h and refine_search.shape[1] >= context_w:
        _, refine_location = _match_template(refine_search, template_context)
        refined_cx = rx0 + refine_location[0]
        refined_cy = ry0 + refine_location[1]

    nx = refined_cx + roi_offset_x
    ny = refined_cy + roi_offset_y
    nx = max(0, min(test_gray.shape[1] - tw, nx))
    ny = max(0, min(test_gray.shape[0] - th, ny))

    if config.geometry.enabled:
        shift = float(np.hypot(nx - tx, ny - ty))
        if shift > config.geometry.max_shift_px:
            return LocatedRoi(
                roi_id=roi.roi_id,
                name=roi.name,
                rect=_norm_rect(nx, ny, tw, th, test_gray.shape),
                score=float(coarse_score),
                method="blur_template",
                found=False,
                message=f"Template shift {shift:.1f}px exceeds geometry constraint",
            )

    found = float(coarse_score) >= config.template_threshold
    return LocatedRoi(
        roi_id=roi.roi_id,
        name=roi.name,
        rect=_norm_rect(nx, ny, tw, th, test_gray.shape),
        score=float(coarse_score),
        method="blur_template",
        found=found,
        message=(
            "Template score accepted; coarse blur match refined on grayscale"
            if found
            else "Template score below threshold"
        ),
    )


def locate_fourier(
    roi: MasterRoi,
    master_image: np.ndarray,
    test_image: np.ndarray,
    config: RoiLocatorConfig | None = None,
) -> LocatedRoi:
    config = config or _legacy_config(roi)
    master_gray = _gray(master_image).astype(np.float32)
    test_gray = _gray(test_image).astype(np.float32)
    mx, my, mw, mh = _rect_px(roi.rect, master_gray.shape)
    tx, ty, tw, th = _rect_px(roi.rect, test_gray.shape)

    margin = config.geometry.search_margin_px if config.geometry.enabled else 0
    mx0, my0, mx1, my1 = _search_window((mx, my, mw, mh), master_gray.shape, margin)
    tx0, ty0, tx1, ty1 = _search_window((tx, ty, tw, th), test_gray.shape, margin)

    master_context = master_gray[my0:my1, mx0:mx1]
    test_context = test_gray[ty0:ty1, tx0:tx1]
    common_h = min(master_context.shape[0], test_context.shape[0])
    common_w = min(master_context.shape[1], test_context.shape[1])
    if common_h < 4 or common_w < 4:
        return LocatedRoi(roi_id=roi.roi_id, name=roi.name, rect=roi.rect, score=0.0, method="fourier", found=False, message="Fourier context is too small")

    master_context = master_context[:common_h, :common_w]
    test_context = test_context[:common_h, :common_w]
    window = cv2.createHanningWindow((common_w, common_h), cv2.CV_32F)
    (dx, dy), response = cv2.phaseCorrelate(master_context, test_context, window)

    nx = int(round(tx + dx))
    ny = int(round(ty + dy))
    nx = max(0, min(test_gray.shape[1] - tw, nx))
    ny = max(0, min(test_gray.shape[0] - th, ny))
    shift = float(np.hypot(dx, dy))
    found = bool(np.isfinite(response))
    if config.geometry.enabled and shift > config.geometry.max_shift_px:
        found = False

    return LocatedRoi(
        roi_id=roi.roi_id,
        name=roi.name,
        rect=_norm_rect(nx, ny, tw, th, test_gray.shape),
        score=float(response if np.isfinite(response) else 0.0),
        method="fourier",
        found=found,
        message=(
            f"Phase correlation shift=({dx:.1f},{dy:.1f})px"
            if found
            else f"Phase correlation rejected by geometry constraint; shift={shift:.1f}px"
        ),
    )


def locate_roi(
    roi: MasterRoi,
    master_image: np.ndarray,
    test_image: np.ndarray,
    config: RoiLocatorConfig | None = None,
) -> LocatedRoi:
    config = config or _legacy_config(roi)
    if config.method == "manual":
        return locate_manual(roi, test_image, config)
    if config.method == "blur_template":
        return locate_blur_template(roi, master_image, test_image, config)
    if config.method == "fourier":
        return locate_fourier(roi, master_image, test_image, config)
    raise ValueError(f"Unknown ROI search method: {config.method}")


def locate_all(
    rois: list[MasterRoi],
    master_image: np.ndarray,
    test_image: np.ndarray,
    config: RoiLocatorConfig | None = None,
) -> list[LocatedRoi]:
    return [locate_roi(roi, master_image, test_image, config) for roi in rois if roi.enabled]
