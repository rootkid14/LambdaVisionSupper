from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.vision_app.camera_runtime import CameraController
from app.services.vision_app.debug_store import VISION_DEBUG_STORE
from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.models import VisionProgramDefinition, model_to_dict
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.roi_search import blur_preview, locate_all
from app.services.vision_app.runner import VisionTriggerRunnerManager
from app.services.vision_app.runtime import VisionProgramRuntime

router = APIRouter()
repository = VisionProgramRepository()
runtime = VisionProgramRuntime()
io_controller = ModbusIOController()
camera_controller = CameraController()
runner_manager = VisionTriggerRunnerManager(repository, runtime, camera_controller, io_controller)


def _error(exc: Exception, status: int = 400) -> HTTPException:
    return HTTPException(status_code=status, detail=str(exc))


def _decode(raw: bytes) -> np.ndarray:
    if not raw:
        raise ValueError("Image body is empty")
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image body could not be decoded")
    return image


def _decode_or_master(raw: bytes, master_image: np.ndarray) -> tuple[np.ndarray, str]:
    """Use the explicit test/camera image when supplied, otherwise fall back to Master Sample."""
    if raw:
        return _decode(raw), "test"
    return np.ascontiguousarray(master_image.copy()), "master"


def _encode_jpeg(image: np.ndarray, quality: int = 92) -> bytes:
    arr = np.asarray(image)
    if arr.dtype == bool:
        arr = arr.astype(np.uint8) * 255
    if arr.ndim == 2:
        arr = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    ok, encoded = cv2.imencode(".jpg", arr, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("Image preview encoding failed")
    return encoded.tobytes()


class CreateProgramRequest(BaseModel):
    name: str = "Vision Program"


class PulseRequest(BaseModel):
    result: str
    seconds: float | None = None


class FocusRequest(BaseModel):
    x: float = 0.5
    y: float = 0.5
    w: float = 1.0
    h: float = 1.0
    focal_length: float | None = None


@router.get("/programs", summary="List Computer Vision programs")
def list_programs():
    return {"success": True, "programs": [{**model_to_dict(program), "master_exists": repository.has_master(program.program_id)} for program in repository.list()]}


@router.post("/programs/new", summary="Create a Computer Vision program")
def create_program(request: CreateProgramRequest):
    try:
        program_id = repository.allocate_id(request.name)
        program = VisionProgramDefinition(program_id=program_id, name=request.name)
        repository.save(program)
        return {"success": True, "program": model_to_dict(program), "master_exists": False}
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}", summary="Load one Computer Vision program")
def get_program(program_id: str):
    try:
        program = repository.get(program_id)
        return {"success": True, "program": model_to_dict(program), "master_exists": repository.has_master(program_id)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.put("/programs/{program_id}", summary="Save Computer Vision program definition")
def save_program(program_id: str, program: VisionProgramDefinition):
    try:
        if program.program_id != program_id:
            raise ValueError("URL program_id does not match program payload")
        saved = repository.save(program)
        return {"success": True, "program": model_to_dict(saved)}
    except Exception as exc:
        raise _error(exc)


@router.delete("/programs/{program_id}", summary="Delete Computer Vision program")
def delete_program(program_id: str):
    try:
        runner_manager.stop(program_id)
        if not repository.delete(program_id):
            raise FileNotFoundError(f"Vision Program not found: {program_id}")
        return {"success": True}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/master", summary="Upload/replace master sample image")
async def upload_master(program_id: str, request: Request):
    try:
        program = repository.get(program_id)
        shape = repository.save_master_bytes(program_id, await request.body())
        program.master.master_shape = shape
        repository.save(program)
        return {"success": True, "shape": shape}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/master", summary="Preview master sample image")
def master_preview(program_id: str, quality: int = 92):
    try:
        return Response(content=_encode_jpeg(repository.load_master(program_id), quality), media_type="image/jpeg")
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/master/blur-preview", summary="Visualize Master Sample blur used by locator")
def master_blur_preview(program_id: str, kernel: int = 9, quality: int = 92):
    try:
        image = blur_preview(repository.load_master(program_id), kernel)
        return Response(content=_encode_jpeg(image, quality), media_type="image/jpeg")
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/locate-rois", summary="Locate all Master Sample ROIs on a test image")
async def locate_rois(program_id: str, request: Request):
    try:
        program = repository.get(program_id)
        master = repository.load_master(program_id)
        test = _decode(await request.body())
        located = locate_all(program.master.rois, master, test, program.master.locator)
        return {"success": True, "rois": [model_to_dict(item) for item in located]}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/test-run", summary="Run Global -> ROI -> Local inspection program")
async def test_run(program_id: str, request: Request):
    try:
        program = repository.get(program_id)
        result = runtime.run_test(program, repository.load_master(program_id), _decode(await request.body()))
        return {"success": True, "run": model_to_dict(result)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/scope-preview/{scope_id}", summary="Preview the configured filter stack for Global or one station")
async def scope_preview(program_id: str, scope_id: str, request: Request):
    try:
        program = repository.get(program_id)
        raw = await request.body()
        if raw:
            preview_image = _decode(raw)
            preview_source = "test"
            # Global Filter preview does not semantically require a Master Sample.
            # ROI preview still does because ROI location is defined from the Master.
            master = preview_image if scope_id == "global" else repository.load_master(program_id)
        else:
            master = repository.load_master(program_id)
            preview_image, preview_source = _decode_or_master(raw, master)
        run_id, refs, benchmarks = runtime.preview_scope_filters(
            program,
            master,
            preview_image,
            scope_id=scope_id,
        )
        return {
            "success": True,
            "run_id": run_id,
            "preview_source": preview_source,
            "debug_images": [model_to_dict(item) for item in refs],
            "benchmarks": [model_to_dict(item) for item in benchmarks],
        }
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.get("/debug/{run_id}/{key}", summary="Read one Working/debug image")
def debug_image(run_id: str, key: str):
    try:
        return Response(content=VISION_DEBUG_STORE.get(run_id, key), media_type="image/jpeg")
    except FileNotFoundError as exc:
        raise _error(exc, 404)


@router.get("/cameras/basler/scan", summary="Scan Basler devices by GigE IP or serial")
def basler_scan():
    try:
        return {"success": True, "devices": camera_controller.basler_scan()}
    except Exception as exc:
        return {"success": False, "devices": [], "error": str(exc)}


@router.post("/programs/{program_id}/camera/capture", summary="Capture current Camera input")
def camera_capture(program_id: str, quality: int = 94):
    try:
        program = repository.get(program_id)
        image = camera_controller.capture(program.camera)
        return Response(content=_encode_jpeg(image, quality), media_type="image/jpeg", headers={"X-Camera-Driver": program.camera.driver})
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/camera/focus", summary="Send configured URL-camera focus request")
def camera_focus(program_id: str, request: FocusRequest):
    try:
        program = repository.get(program_id)
        return {"success": True, **camera_controller.focus(program.camera, **model_to_dict(request))}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/iot/trigger", summary="Read configured Modbus trigger input once")
def read_trigger(program_id: str):
    try:
        program = repository.get(program_id)
        return {"success": True, "triggered": io_controller.read_trigger(program.io)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/iot/pulse", summary="Pulse configured OK or NG Modbus output")
def pulse_output(program_id: str, request: PulseRequest):
    try:
        program = repository.get(program_id)
        result = request.result.strip().lower()
        if result not in {"ok", "ng"}:
            raise ValueError("result must be 'ok' or 'ng'")
        io_controller.pulse_result(program.io, ok=result == "ok", seconds=request.seconds)
        return {"success": True, "result": result}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/runner/start", summary="Arm Modbus -> Camera -> Inspection -> OK/NG automatic cycle")
def runner_start(program_id: str):
    try:
        repository.get(program_id)
        return {"success": True, "status": model_to_dict(runner_manager.start(program_id))}
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/runner/stop", summary="Disarm automatic trigger cycle")
def runner_stop(program_id: str):
    return {"success": True, "status": model_to_dict(runner_manager.stop(program_id))}


@router.get("/programs/{program_id}/runner/status", summary="Automatic trigger runner status")
def runner_status(program_id: str):
    return {"success": True, "status": model_to_dict(runner_manager.status(program_id))}
