from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.vision_app.camera_runtime import CameraController
from app.services.vision_app.automation_manager import AutomationManager
from app.services.vision_app.debug_store import VISION_DEBUG_STORE
from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.models import SoftTriggerConfig, VisionProgramDefinition, model_to_dict
from app.services.vision_app.endpoint_registry import safe_alias
from app.services.vision_app.frame_slot_store import VISION_FRAME_SLOTS
from app.services.vision_app.workspace_runtime import projected_program, workspace_by_alias
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.roi_search import blur_preview, locate_all
from app.services.vision_app.runner import VisionTriggerRunnerManager
from app.services.vision_app.runtime import VisionProgramRuntime

router = APIRouter()
repository = VisionProgramRepository()
runtime = VisionProgramRuntime()
io_controller = ModbusIOController()
camera_controller = CameraController()
automation_manager = AutomationManager(repository, runtime, camera_controller, io_controller)
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
        automation_manager.shutdown_program(program_id)
        if not repository.delete(program_id):
            raise FileNotFoundError(f"Vision Program not found: {program_id}")
        return {"success": True}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/master", summary="Upload/replace workspace master sample image")
async def upload_master(program_id: str, request: Request, workspace_id: str | None = None):
    try:
        program = repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_id)
        shape = repository.save_master_bytes(program_id, await request.body(), workspace.workspace_id)
        workspace.master.master_shape = shape
        if workspace.workspace_id == "workspace_1":
            program.master.master_shape = shape
        repository.save(program)
        return {"success": True, "shape": shape, "workspace_id": workspace.workspace_id}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/master", summary="Preview workspace master sample image")
def master_preview(program_id: str, quality: int = 92, workspace_id: str | None = None):
    try:
        program = repository.get(program_id); workspace = workspace_by_alias(program, workspace_id)
        return Response(content=_encode_jpeg(repository.load_master(program_id, workspace.workspace_id), quality), media_type="image/jpeg")
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/master/blur-preview", summary="Visualize workspace Master Sample blur used by locator")
def master_blur_preview(program_id: str, kernel: int = 9, quality: int = 92, workspace_id: str | None = None):
    try:
        program = repository.get(program_id); workspace = workspace_by_alias(program, workspace_id)
        image = blur_preview(repository.load_master(program_id, workspace.workspace_id), kernel)
        return Response(content=_encode_jpeg(image, quality), media_type="image/jpeg")
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/locate-rois", summary="Locate workspace Master ROIs on a test image")
async def locate_rois(program_id: str, request: Request, workspace_id: str | None = None):
    try:
        program = repository.get(program_id); workspace = workspace_by_alias(program, workspace_id)
        master = repository.load_master(program_id, workspace.workspace_id)
        test = _decode(await request.body())
        located = locate_all(workspace.master.rois, master, test, workspace.master.locator)
        return {"success": True, "rois": [model_to_dict(item) for item in located]}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/test-run", summary="Run one workspace inspection program")
async def test_run(program_id: str, request: Request, workspace_id: str | None = None):
    try:
        result = automation_manager.run_inspection(program_id, _decode(await request.body()), workspace_alias=workspace_id)
        return {"success": True, "run": model_to_dict(result), "system_state": model_to_dict(automation_manager.state(program_id))}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/workspaces/{workspace_alias}/activate", summary="Activate one workspace without running inspection")
def workspace_activate(program_id: str, workspace_alias: str):
    try:
        state = automation_manager.activate_workspace(program_id, workspace_alias)
        return {"success": True, "state": model_to_dict(state)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/workspaces/{workspace_alias}/run", summary="Run workspace using its configured input binding")
def workspace_run(program_id: str, workspace_alias: str):
    try:
        result = automation_manager.run_inspection(program_id, workspace_alias=workspace_alias)
        return {"success": True, "run": model_to_dict(result), "system_state": model_to_dict(automation_manager.state(program_id))}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/scope-preview/{scope_id}", summary="Preview the configured filter stack for Global or one station")
async def scope_preview(program_id: str, scope_id: str, request: Request, workspace_id: str | None = None):
    try:
        program = repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_id)
        projected = projected_program(program, workspace)
        raw = await request.body()
        if raw:
            preview_image = _decode(raw)
            preview_source = "test"
            # Global Filter preview does not semantically require a Master Sample.
            # ROI preview still does because ROI location is defined from the Master.
            master = preview_image if scope_id == "global" else repository.load_master(program_id, workspace.workspace_id)
        else:
            master = repository.load_master(program_id, workspace.workspace_id)
            preview_image, preview_source = _decode_or_master(raw, master)
        run_id, refs, benchmarks = runtime.preview_scope_filters(
            projected,
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
        image = automation_manager.capture(program_id)
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


class SimPointRequest(BaseModel):
    value: Any


@router.post("/programs/{program_id}/cameras/{camera_alias}/capture", summary="Capture one declared camera into its image slot")
def declared_camera_capture(program_id: str, camera_alias: str, quality: int = 94):
    try:
        image = automation_manager.capture(program_id, camera_alias)
        return Response(content=_encode_jpeg(image, quality), media_type="image/jpeg", headers={"X-Camera-Alias": camera_alias})
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/cameras/{camera_alias}/stream-frame", summary="Engineering stream preview frame")
def declared_camera_stream_frame(program_id: str, camera_alias: str, quality: int = 88):
    try:
        program = automation_manager._active_program(repository.get(program_id)); camera = automation_manager._camera(program, camera_alias)
        image = automation_manager.camera_resources.stream_frame(program_id, camera)
        return Response(content=_encode_jpeg(image, quality), media_type="image/jpeg", headers={"X-Stream-Preview": "poll"})
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/cameras/{camera_alias}/sim-frame", summary="Upload simulated camera frame")
async def simulated_camera_frame(program_id: str, camera_alias: str, request: Request):
    try:
        program = automation_manager._active_program(repository.get(program_id)); camera = automation_manager._camera(program, camera_alias)
        image = _decode(await request.body())
        if camera.driver != "simulated": raise ValueError("Camera driver must be simulated")
        VISION_FRAME_SLOTS.put(program_id, automation_manager.camera_resources.stream_slot_path(camera), image)
        VISION_FRAME_SLOTS.put(program_id, automation_manager.camera_resources.image_slot_path(camera), image)
        return {"success": True, "shape": list(image.shape)}
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/simulator/iot/{device_alias}/{point_alias}", summary="Set simulated IOT point")
def simulator_iot(program_id: str, device_alias: str, point_alias: str, request: SimPointRequest):
    try:
        program = automation_manager._active_program(repository.get(program_id))
        hit = automation_manager._declared_point(program, f"device.{device_alias}.{point_alias}")
        if hit is None: raise FileNotFoundError("Declared IOT point not found")
        device, point = hit
        if device.driver != "simulated": raise ValueError("Device driver must be simulated")
        io_controller.set_simulated_point(device, point, request.value)
        return {"success": True, "value": io_controller.read_declared_point(device, point)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/online", summary="Put all enabled Automation services online")
def program_online(program_id: str):
    try:
        repository.get(program_id)
        return {"success": True, "state": model_to_dict(automation_manager.online(program_id))}
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/offline", summary="Take whole Computer Vision program offline")
def program_offline(program_id: str):
    return {"success": True, "state": model_to_dict(automation_manager.offline(program_id))}


class AutomationValidateRequest(BaseModel):
    script: str = ""




class KeyboardStateRequest(BaseModel):
    key: str
    pressed: bool


@router.post("/programs/{program_id}/automation/keyboard", summary="Update application keyboard signal state")
def automation_keyboard(program_id: str, request: KeyboardStateRequest):
    try:
        repository.get(program_id)
        return {"success": True, "state": model_to_dict(automation_manager.set_keyboard_state(program_id, request.key, request.pressed))}
    except Exception as exc:
        raise _error(exc)

@router.post("/programs/{program_id}/automation/endpoints/preview", summary="Preview live typed endpoints from the unsaved editor program")
def automation_endpoints_preview(program_id: str, program: VisionProgramDefinition):
    try:
        if program.program_id != program_id:
            raise ValueError("program_id in payload does not match route")
        workspace = workspace_by_alias(program, program.active_workspace_id)
        preview_program = projected_program(program, workspace)
        return {
            "success": True,
            "endpoints": automation_manager.registry.as_dict(
                preview_program,
                automation_manager.snapshot(program_id),
                automation_manager.state(program_id),
            ),
        }
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/automation/endpoints", summary="List typed Automation IDE endpoints")
def automation_endpoints(program_id: str):
    try:
        repository.get(program_id)
        return {"success": True, "endpoints": automation_manager.catalog(program_id)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/automation/validate", summary="Validate safe Automation DSL without executing it")
def automation_validate(program_id: str, request: AutomationValidateRequest):
    try:
        repository.get(program_id)
        return {"success": True, "issues": [model_to_dict(item) for item in automation_manager.validate(request.script)]}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/automation/services/{service_id}/run", summary="Run or dry-run one Automation service")
def automation_run_service(program_id: str, service_id: str, dry_run: bool = False):
    try:
        result = automation_manager.run_service(program_id, service_id, dry_run=dry_run)
        return {"success": result.ok, "execution": model_to_dict(result), "state": model_to_dict(automation_manager.state(program_id))}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/automation/start", summary="Start Loop Automation scheduler")
def automation_start(program_id: str):
    try:
        repository.get(program_id)
        return {"success": True, "state": model_to_dict(automation_manager.start(program_id))}
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/automation/stop", summary="Stop Loop Automation scheduler")
def automation_stop(program_id: str):
    return {"success": True, "state": model_to_dict(automation_manager.shutdown_program(program_id))}


@router.get("/programs/{program_id}/automation/state", summary="Read Automation/System state")
def automation_state(program_id: str):
    try:
        repository.get(program_id)
        return {"success": True, "state": model_to_dict(automation_manager.state(program_id))}
    except FileNotFoundError as exc:
        raise _error(exc, 404)


@router.get("/programs/{program_id}/automation/trace", summary="Read Automation execution trace")
def automation_trace(program_id: str):
    try:
        repository.get(program_id)
        return {"success": True, "trace": [model_to_dict(item) for item in automation_manager.trace(program_id)]}
    except FileNotFoundError as exc:
        raise _error(exc, 404)


@router.delete("/programs/{program_id}/automation/trace", summary="Clear Automation execution trace")
def automation_clear_trace(program_id: str):
    automation_manager.clear_trace(program_id)
    return {"success": True}


@router.get("/programs/{program_id}/automation/latest-frame", summary="Read latest frame captured/used by Automation runtime")
def automation_latest_frame(program_id: str, workspace_id: str | None = None):
    try:
        repository.get(program_id)
        return Response(content=automation_manager.latest_frame_jpeg(program_id, workspace_alias=workspace_id), media_type="image/jpeg")
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/automation/latest-frame", summary="Upload current manual/test frame into Automation runtime")
async def automation_set_latest_frame(program_id: str, request: Request, workspace_id: str | None = None):
    try:
        repository.get(program_id)
        image = _decode(await request.body())
        automation_manager.set_latest_frame(program_id, image, workspace_alias=workspace_id, announce=False)
        return {"success": True, "shape": list(image.shape)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)

def _workspace_stream_resource(program, workspace_alias: str):
    workspace = workspace_by_alias(program, workspace_alias)
    camera = next((c for c in workspace.cameras.devices if c.enabled and c.declaration_id == workspace.camera_id), None)
    if camera is None:
        raise RuntimeError(f"Workspace {workspace.name} has no enabled assigned camera")
    return workspace, camera


@router.post("/programs/{program_id}/workspaces/{workspace_alias}/stream/start", summary="Start workspace backend camera stream")
def workspace_stream_start(program_id: str, workspace_alias: str):
    try:
        program = repository.get(program_id)
        workspace, camera = _workspace_stream_resource(program, workspace_alias)
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        return {"success": True, **automation_manager.streaming.ensure(program_id, alias, camera, f"browser:{alias}")}
    except Exception as exc:
        raise _error(exc)


@router.delete("/programs/{program_id}/workspaces/{workspace_alias}/stream/stop", summary="Release workspace browser stream consumer")
def workspace_stream_stop(program_id: str, workspace_alias: str):
    try:
        program = repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_alias)
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        return {"success": True, **automation_manager.streaming.release(program_id, alias, f"browser:{alias}")}
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/workspaces/{workspace_alias}/stream/status", summary="Read workspace stream/Soft Trigger status")
def workspace_stream_status(program_id: str, workspace_alias: str):
    try:
        program = repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_alias)
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        return {"success": True, **automation_manager.streaming.status(program_id, alias)}
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/workspaces/{workspace_alias}/stream/frame", summary="Lazy workspace stream JPEG")
def workspace_stream_frame(program_id: str, workspace_alias: str, after_sequence: int = 0, quality: int = 82):
    try:
        program = repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_alias)
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        status = automation_manager.streaming.status(program_id, alias)["stream"]
        sequence = int(status.get("sequence", 0))
        if sequence <= int(after_sequence):
            return Response(status_code=204, headers={"X-Frame-Sequence": str(sequence)})
        payload, sequence = automation_manager.streaming.jpeg(program_id, alias, quality)
        return Response(content=payload, media_type="image/jpeg", headers={"X-Frame-Sequence": str(sequence), "Cache-Control": "no-store"})
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/workspaces/{workspace_alias}/soft-trigger/analyze", summary="Analyze workspace Streaming_frame with draft Soft Trigger settings")
def workspace_soft_trigger_analyze(program_id: str, workspace_alias: str, config: SoftTriggerConfig):
    try:
        program = repository.get(program_id)
        workspace = workspace_by_alias(program, workspace_alias)
        alias = safe_alias(workspace.alias, workspace.workspace_id)
        image, _ = automation_manager.streaming.latest_frame(program_id, alias)
        return {"success": True, **automation_manager.streaming.analyze_frame(image, config)}
    except Exception as exc:
        raise _error(exc)
