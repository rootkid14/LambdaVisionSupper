from __future__ import annotations

from time import perf_counter
from typing import Any

import cv2
import numpy as np

from app.services.vision_app.models import (
    DecisionRule,
    LocatedRoi,
    ServiceExecutionResult,
    StationRunResult,
    VisionProgramDefinition,
    VisionProgramRunResult,
    WorkingServiceBinding,
)
from app.services.vision_app.roi_search import locate_all
from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.service.repository import LabServiceRepository
from app.services.vision_labs.service.runtime import LabServiceRuntime


def _frame_from_bgr(image: np.ndarray, source_id: str) -> ImageFrame:
    if image.ndim == 2:
        color_space = ColorSpace.GRAY
    else:
        color_space = ColorSpace.BGR
    return ImageFrame(data=np.ascontiguousarray(image), color_space=color_space, source_id=source_id)


def _crop_normalized(image: np.ndarray, rect) -> np.ndarray:
    h, w = image.shape[:2]
    x0 = max(0, min(w - 1, int(round(rect.x * w))))
    y0 = max(0, min(h - 1, int(round(rect.y * h))))
    x1 = max(x0 + 1, min(w, int(round((rect.x + rect.w) * w))))
    y1 = max(y0 + 1, min(h, int(round((rect.y + rect.h) * h))))
    return np.ascontiguousarray(image[y0:y1, x0:x1])


def _value_by_path(value: Any, path: str) -> Any:
    current = value
    for token in [part for part in path.split(".") if part]:
        if isinstance(current, dict):
            current = current[token]
        elif isinstance(current, (list, tuple)):
            current = current[int(token)]
        else:
            current = getattr(current, token)
    return current


def _as_scalar(value: Any, path: str = "") -> float:
    if path:
        value = _value_by_path(value, path)
    if isinstance(value, (int, float, np.number)):
        return float(value)
    if hasattr(value, "values"):
        array = np.asarray(value.values)
        if array.size == 1:
            return float(array.reshape(-1)[0])
        return float(np.mean(array))
    array = np.asarray(value)
    if array.size == 0:
        raise ValueError("Cannot extract scalar from empty output")
    if array.size == 1:
        return float(array.reshape(-1)[0])
    return float(np.mean(array.astype(np.float64)))


def _evaluate(rule: DecisionRule, outputs: dict[str, Any]) -> tuple[bool, float | None, str]:
    if rule.mode == "service_success":
        return True, None, "Service executed successfully"
    if not outputs:
        return False, None, "Service produced no outputs"
    output_name = rule.output_name or next(iter(outputs))
    if output_name not in outputs:
        return False, None, f"Output {output_name!r} was not produced"
    scalar = _as_scalar(outputs[output_name], rule.value_path)
    threshold = float(rule.threshold)
    checks = {
        "scalar_gt": scalar > threshold,
        "scalar_gte": scalar >= threshold,
        "scalar_lt": scalar < threshold,
        "scalar_lte": scalar <= threshold,
        "scalar_eq": bool(np.isclose(scalar, threshold)),
    }
    return bool(checks[rule.mode]), scalar, f"{rule.mode}: {scalar:.6g} vs {threshold:.6g}"


class VisionProgramRuntime:
    def __init__(
        self,
        service_repository: LabServiceRepository | None = None,
        service_runtime: LabServiceRuntime | None = None,
    ) -> None:
        self.services = service_repository or LabServiceRepository()
        self.runtime = service_runtime or LabServiceRuntime()

    def _run_binding(self, binding: WorkingServiceBinding, frame: ImageFrame) -> ServiceExecutionResult:
        try:
            service = self.services.get(binding.service_id, version=binding.version)
            run = self.runtime.run(service, {"image": frame})
            ok, scalar, message = _evaluate(binding.decision, run.outputs)
            output_name = binding.decision.output_name or (next(iter(run.outputs)) if run.outputs else "")
            shape = None
            if output_name and output_name in run.outputs:
                value = run.outputs[output_name]
                if hasattr(value, "shape"):
                    shape = list(value.shape)
                elif hasattr(value, "values"):
                    shape = list(np.asarray(value.values).shape)
            return ServiceExecutionResult(
                binding_id=binding.binding_id,
                service_id=binding.service_id,
                ok=ok,
                output_name=output_name,
                scalar_value=scalar,
                message=message,
                shape=shape,
            )
        except Exception as exc:
            return ServiceExecutionResult(
                binding_id=binding.binding_id,
                service_id=binding.service_id,
                ok=False,
                message=str(exc),
            )

    def run_test(
        self,
        program: VisionProgramDefinition,
        master_image: np.ndarray,
        test_image: np.ndarray,
    ) -> VisionProgramRunResult:
        start = perf_counter()
        located = locate_all(program.master.rois, master_image, test_image)
        located_by_id: dict[str, LocatedRoi] = {item.roi_id: item for item in located}
        full_frame = _frame_from_bgr(test_image, "vision_app:test")

        global_results = [
            self._run_binding(binding, full_frame)
            for binding in program.working.global_services
            if binding.enabled and binding.service_id
        ]
        global_ok = all(item.ok for item in global_results) if global_results else True

        station_results: list[StationRunResult] = []
        roi_defs = {roi.roi_id: roi for roi in program.master.rois if roi.enabled}
        for roi_id, roi in roi_defs.items():
            found = located_by_id.get(roi_id)
            if found is None:
                continue
            bindings = [
                binding
                for binding in program.working.station_services.get(roi_id, [])
                if binding.enabled and binding.service_id
            ]
            service_results: list[ServiceExecutionResult] = []
            if found.found:
                crop = _crop_normalized(test_image, found.rect)
                station_frame = _frame_from_bgr(crop, f"vision_app:{roi_id}")
                service_results = [self._run_binding(binding, station_frame) for binding in bindings]
            station_ok = found.found and (all(item.ok for item in service_results) if service_results else True)
            station_results.append(
                StationRunResult(
                    station_id=roi_id,
                    station_name=roi.name,
                    rect=found.rect,
                    located=found.found,
                    search_score=found.score,
                    ok=station_ok,
                    services=service_results,
                )
            )

        overall_ok = global_ok and all(item.ok for item in station_results)
        return VisionProgramRunResult(
            program_id=program.program_id,
            global_ok=global_ok,
            overall_ok=overall_ok,
            located_rois=located,
            global_services=global_results,
            stations=station_results,
            total_ms=(perf_counter() - start) * 1000.0,
        )
