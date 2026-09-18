from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import re
from time import perf_counter
from typing import Any

import cv2
import numpy as np

from app.services.vision_app.debug_store import VISION_DEBUG_STORE, VisionDebugStore
from app.services.vision_app.decision_runtime import run_decision_script
from app.services.vision_app.models import (
    BenchmarkStep,
    DecisionExecutionResult,
    LocatedRoi,
    ScopePipelineConfig,
    ScopeRunResult,
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


def _frame_from_array(image: np.ndarray, source_id: str) -> ImageFrame:
    array = np.asarray(image)
    if array.dtype == bool:
        array = array.astype(np.uint8) * 255
    if array.ndim == 2:
        color_space = ColorSpace.GRAY
    else:
        color_space = ColorSpace.BGR
    return ImageFrame(data=np.ascontiguousarray(array), color_space=color_space, source_id=source_id)


def _artifact_array(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return np.asarray(value)
    data = getattr(value, "data", None)
    if isinstance(data, np.ndarray):
        return np.asarray(data)
    values = getattr(value, "values", None)
    if isinstance(values, np.ndarray) and values.ndim in {2, 3}:
        return np.asarray(values)
    raise TypeError(f"Artifact {type(value).__name__} is not image-like")


def _crop_array(image: np.ndarray, rect) -> np.ndarray:
    h, w = image.shape[:2]
    x0 = max(0, min(w - 1, int(round(rect.x * w))))
    y0 = max(0, min(h - 1, int(round(rect.y * h))))
    x1 = max(x0 + 1, min(w, int(round((rect.x + rect.w) * w))))
    y1 = max(y0 + 1, min(h, int(round((rect.y + rect.h) * h))))
    return np.ascontiguousarray(image[y0:y1, x0:x1])


def _alias(binding: WorkingServiceBinding, index: int) -> str:
    raw = binding.alias or binding.label or f"logic_{index + 1}"
    value = re.sub(r"[^A-Za-z0-9_]+", "_", raw.strip()).strip("_")
    return value or f"logic_{index + 1}"


def _numeric_summary(array: np.ndarray) -> dict[str, Any]:
    arr = np.asarray(array)
    payload: dict[str, Any] = {"shape": list(arr.shape), "size": int(arr.size)}
    if arr.size and np.issubdtype(arr.dtype, np.number):
        finite = np.nan_to_num(arr.astype(np.float64))
        payload.update(
            mean=float(np.mean(finite)),
            std=float(np.std(finite)),
            min=float(np.min(finite)),
            max=float(np.max(finite)),
        )
        if arr.size <= 1024:
            payload["values"] = finite.reshape(-1).tolist()
    return payload


def _output_summary(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, np.number):
        return float(value)
    if isinstance(value, np.ndarray):
        return _numeric_summary(value)
    data = getattr(value, "data", None)
    if isinstance(data, np.ndarray):
        result = _numeric_summary(data)
        result["artifact_type"] = type(value).__name__
        return result
    values = getattr(value, "values", None)
    if isinstance(values, (np.ndarray, list, tuple)):
        try:
            arr = np.asarray(values)
            result = _numeric_summary(arr)
            result["artifact_type"] = type(value).__name__
            return result
        except Exception:
            pass
    contours = getattr(value, "contours", None)
    if contours is not None:
        try:
            return {"artifact_type": type(value).__name__, "count": len(contours)}
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _output_summary(v) for k, v in list(value.items())[:128]}
    if isinstance(value, (list, tuple)):
        return [_output_summary(v) for v in value[:128]]
    shape = getattr(value, "shape", None)
    return {"artifact_type": type(value).__name__, "shape": list(shape) if shape is not None else []}


class VisionProgramRuntime:
    def __init__(
        self,
        service_repository: LabServiceRepository | None = None,
        service_runtime: LabServiceRuntime | None = None,
        debug_store: VisionDebugStore | None = None,
    ) -> None:
        self.services = service_repository or LabServiceRepository()
        self.runtime = service_runtime or LabServiceRuntime()
        self.debug = debug_store or VISION_DEBUG_STORE

    def _run_service(self, binding: WorkingServiceBinding, artifact: Any, *, alias: str) -> tuple[ServiceExecutionResult, dict[str, Any]]:
        started = perf_counter()
        try:
            service = self.services.get(binding.service_id, version=binding.version)
            input_name = next(iter(service.inputs), "image")
            run = self.runtime.run(service, {input_name: artifact})
            summaries = {name: _output_summary(value) for name, value in run.outputs.items()}
            return (
                ServiceExecutionResult(
                    binding_id=binding.binding_id,
                    service_id=binding.service_id,
                    alias=alias,
                    ok=True,
                    outputs=summaries,
                    message="Service executed successfully",
                    elapsed_ms=(perf_counter() - started) * 1000.0,
                ),
                run.outputs,
            )
        except Exception as exc:
            return (
                ServiceExecutionResult(
                    binding_id=binding.binding_id,
                    service_id=binding.service_id,
                    alias=alias,
                    ok=False,
                    message=str(exc),
                    elapsed_ms=(perf_counter() - started) * 1000.0,
                ),
                {},
            )

    @staticmethod
    def _next_image(outputs: dict[str, Any]) -> Any:
        for value in outputs.values():
            try:
                _artifact_array(value)
                return value
            except Exception:
                continue
        raise RuntimeError("Filter service did not expose an image-like output")

    def _filter_stack(
        self,
        bindings: list[WorkingServiceBinding],
        artifact: Any,
        *,
        scope_name: str,
        run_id: str | None,
        benchmarks: list[BenchmarkStep] | None,
        emit_debug: bool = True,
    ) -> tuple[Any, list[ServiceExecutionResult], bool]:
        current = artifact
        results: list[ServiceExecutionResult] = []
        for index, binding in enumerate(bindings):
            if not binding.enabled or not binding.service_id:
                continue
            alias = _alias(binding, index)
            result, outputs = self._run_service(binding, current, alias=alias)
            results.append(result)
            if benchmarks is not None:
                benchmarks.append(BenchmarkStep(scope=scope_name, phase="filter", name=alias, elapsed_ms=result.elapsed_ms, detail=binding.service_id))
            if not result.ok:
                return current, results, False
            try:
                current = self._next_image(outputs)
            except Exception as exc:
                result.ok = False
                result.message = str(exc)
                return current, results, False
            if emit_debug and run_id:
                try:
                    self.debug.put(run_id, f"{scope_name}_filter_{index}", _artifact_array(current), label=f"{scope_name} · Filter {index + 1} · {alias}", scope=scope_name, phase="filter")
                except Exception:
                    pass
        return current, results, True

    def _logic_stack(
        self,
        bindings: list[WorkingServiceBinding],
        artifact: Any,
        *,
        scope_name: str,
        benchmarks: list[BenchmarkStep],
    ) -> tuple[list[ServiceExecutionResult], dict[str, Any], bool]:
        results: list[ServiceExecutionResult] = []
        context: dict[str, Any] = {}
        ok = True
        for index, binding in enumerate(bindings):
            if not binding.enabled or not binding.service_id:
                continue
            alias = _alias(binding, index)
            result, outputs = self._run_service(binding, artifact, alias=alias)
            results.append(result)
            benchmarks.append(BenchmarkStep(scope=scope_name, phase="logic", name=alias, elapsed_ms=result.elapsed_ms, detail=binding.service_id))
            ok = ok and result.ok
            context[alias] = {name: _output_summary(value) for name, value in outputs.items()} if result.ok else {"error": result.message}
        return results, context, ok

    def _run_scope(
        self,
        scope: ScopePipelineConfig,
        artifact: Any,
        *,
        scope_id: str,
        scope_name: str,
        run_id: str,
        benchmarks: list[BenchmarkStep],
    ) -> tuple[ScopeRunResult, Any]:
        started = perf_counter()
        filter_results: list[ServiceExecutionResult] = []
        filter_ok = True
        current = artifact
        if scope.enable_filter:
            current, filter_results, filter_ok = self._filter_stack(
                scope.filter_services,
                current,
                scope_name=scope_id,
                run_id=run_id,
                benchmarks=benchmarks,
            )

        logic_results: list[ServiceExecutionResult] = []
        logic_context: dict[str, Any] = {}
        logic_ok = True
        if filter_ok and scope.enable_logic:
            logic_results, logic_context, logic_ok = self._logic_stack(
                scope.logic_services,
                current,
                scope_name=scope_id,
                benchmarks=benchmarks,
            )

        decision = DecisionExecutionResult(enabled=scope.enable_decision, ok=filter_ok and logic_ok, result="OK" if filter_ok and logic_ok else "NG")
        if filter_ok and scope.enable_decision:
            d0 = perf_counter()
            try:
                decision_ok, result_text = run_decision_script(
                    scope.decision.script,
                    {
                        "logic": logic_context,
                        "logic_ok": bool(logic_ok),
                        "filter_ok": bool(filter_ok),
                    },
                )
                decision = DecisionExecutionResult(enabled=True, ok=decision_ok, result=result_text, message="Decision script evaluated", elapsed_ms=(perf_counter() - d0) * 1000.0)
            except Exception as exc:
                decision = DecisionExecutionResult(enabled=True, ok=False, result="NG", message=str(exc), elapsed_ms=(perf_counter() - d0) * 1000.0)
            benchmarks.append(BenchmarkStep(scope=scope_id, phase="decision", name="Decision script", elapsed_ms=decision.elapsed_ms, detail=decision.message))

        scope_ok = filter_ok and (decision.ok if scope.enable_decision else logic_ok)
        return (
            ScopeRunResult(
                scope_id=scope_id,
                scope_name=scope_name,
                ok=scope_ok,
                filter_services=filter_results,
                logic_services=logic_results,
                decision=decision,
                elapsed_ms=(perf_counter() - started) * 1000.0,
            ),
            current,
        )

    def _filtered_master(self, program: VisionProgramDefinition, master_image: np.ndarray) -> np.ndarray:
        scope = program.working.global_scope
        if not scope.enable_filter or not scope.filter_services:
            return master_image
        artifact, _, ok = self._filter_stack(
            scope.filter_services,
            _frame_from_array(master_image, "vision_app:master"),
            scope_name="master_global",
            run_id=None,
            benchmarks=None,
            emit_debug=False,
        )
        return _artifact_array(artifact) if ok else master_image

    def _station_run(
        self,
        program: VisionProgramDefinition,
        found: LocatedRoi,
        filtered_test: np.ndarray,
        run_id: str,
    ) -> tuple[StationRunResult, list[BenchmarkStep]]:
        local_benchmarks: list[BenchmarkStep] = []
        if not found.found:
            return StationRunResult(station_id=found.roi_id, station_name=found.name, rect=found.rect, located=False, search_score=found.score, ok=False), local_benchmarks
        crop = _crop_array(filtered_test, found.rect)
        self.debug.put(run_id, f"station_{found.roi_id}_input", crop, label=f"{found.name} · Input", scope=found.roi_id, phase="input")
        scope = program.working.station_scopes.get(found.roi_id, ScopePipelineConfig())
        scope_result, _ = self._run_scope(
            scope,
            _frame_from_array(crop, f"vision_app:{found.roi_id}"),
            scope_id=found.roi_id,
            scope_name=found.name,
            run_id=run_id,
            benchmarks=local_benchmarks,
        )
        return StationRunResult(station_id=found.roi_id, station_name=found.name, rect=found.rect, located=True, search_score=found.score, ok=scope_result.ok, scope=scope_result), local_benchmarks

    def run_test(self, program: VisionProgramDefinition, master_image: np.ndarray, test_image: np.ndarray) -> VisionProgramRunResult:
        started = perf_counter()
        run_id = self.debug.new_run()
        benchmarks: list[BenchmarkStep] = []
        self.debug.put(run_id, "test_input", test_image, label="Test Input", scope="global", phase="input")

        global_scope, filtered_artifact = self._run_scope(
            program.working.global_scope,
            _frame_from_array(test_image, "vision_app:test"),
            scope_id="global",
            scope_name="Global Scope",
            run_id=run_id,
            benchmarks=benchmarks,
        )
        try:
            filtered_test = _artifact_array(filtered_artifact)
        except Exception:
            filtered_test = test_image
        self.debug.put(run_id, "global_filtered_final", filtered_test, label="Global · Filtered image", scope="global", phase="filter_final")

        filtered_master = self._filtered_master(program, master_image)
        locate_started = perf_counter()
        located = locate_all(program.master.rois, filtered_master, filtered_test, program.master.locator)
        benchmarks.append(BenchmarkStep(scope="global", phase="locate", name=f"ROI locator · {program.master.locator.method}", elapsed_ms=(perf_counter() - locate_started) * 1000.0, detail=f"{len(located)} ROI(s)"))

        if program.working.station_execution == "parallel" and len(located) > 1:
            workers = min(8, len(located))
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="vision-station") as pool:
                futures = [pool.submit(self._station_run, program, item, filtered_test, run_id) for item in located]
                station_pairs = [future.result() for future in futures]
        else:
            station_pairs = [self._station_run(program, item, filtered_test, run_id) for item in located]

        stations = [pair[0] for pair in station_pairs]
        for _, items in station_pairs:
            benchmarks.extend(items)

        global_ok = global_scope.ok
        overall_ok = global_ok and all(item.ok for item in stations)
        total_ms = (perf_counter() - started) * 1000.0
        benchmarks.append(BenchmarkStep(scope="program", phase="total", name="Total inspection", elapsed_ms=total_ms, detail=program.working.station_execution))
        return VisionProgramRunResult(
            program_id=program.program_id,
            run_id=run_id,
            global_ok=global_ok,
            overall_ok=overall_ok,
            located_rois=located,
            global_scope=global_scope,
            stations=stations,
            debug_images=self.debug.refs(run_id),
            benchmarks=benchmarks,
            total_ms=total_ms,
        )

    def preview_scope_filters(
        self,
        program: VisionProgramDefinition,
        master_image: np.ndarray,
        test_image: np.ndarray,
        *,
        scope_id: str,
    ) -> tuple[str, list[Any]]:
        run_id = self.debug.new_run()
        self.debug.put(run_id, "preview_input", test_image, label="Preview Input", scope=scope_id, phase="input")
        if scope_id == "global":
            scope = program.working.global_scope
            artifact = _frame_from_array(test_image, "vision_app:preview:global")
        else:
            global_scope = program.working.global_scope
            global_artifact = _frame_from_array(test_image, "vision_app:preview:test")
            if global_scope.enable_filter:
                global_artifact, _, _ = self._filter_stack(global_scope.filter_services, global_artifact, scope_name="preview_global", run_id=None, benchmarks=None, emit_debug=False)
            filtered_test = _artifact_array(global_artifact)
            filtered_master = self._filtered_master(program, master_image)
            located = {item.roi_id: item for item in locate_all(program.master.rois, filtered_master, filtered_test, program.master.locator)}
            found = located.get(scope_id)
            if found is None or not found.found:
                raise RuntimeError(f"Station {scope_id} could not be located for filter preview")
            artifact = _frame_from_array(_crop_array(filtered_test, found.rect), f"vision_app:preview:{scope_id}")
            scope = program.working.station_scopes.get(scope_id, ScopePipelineConfig())
        if scope.enable_filter:
            self._filter_stack(scope.filter_services, artifact, scope_name=scope_id, run_id=run_id, benchmarks=[], emit_debug=True)
        return run_id, self.debug.refs(run_id)
