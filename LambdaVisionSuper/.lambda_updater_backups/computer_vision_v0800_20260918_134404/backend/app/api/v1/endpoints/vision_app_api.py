from __future__ import annotations

import uuid
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.vision_app.io_runtime import ModbusIOController
from app.services.vision_app.models import VisionProgramDefinition, model_to_dict
from app.services.vision_app.repository import VisionProgramRepository
from app.services.vision_app.roi_search import locate_all
from app.services.vision_app.runtime import VisionProgramRuntime

router = APIRouter()
repository = VisionProgramRepository()
runtime = VisionProgramRuntime()
io_controller = ModbusIOController()


def _error(exc: Exception, status: int = 400) -> HTTPException:
    return HTTPException(status_code=status, detail=str(exc))


def _decode(raw: bytes) -> np.ndarray:
    if not raw:
        raise ValueError("Image body is empty")
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image body could not be decoded")
    return image


def _encode_jpeg(image: np.ndarray, quality: int = 92) -> bytes:
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("Image preview encoding failed")
    return encoded.tobytes()


class CreateProgramRequest(BaseModel):
    name: str = "Vision Program"


class PulseRequest(BaseModel):
    result: str
    seconds: float | None = None


@router.get("/programs", summary="List Computer Vision programs")
def list_programs():
    return {
        "success": True,
        "programs": [
            {**model_to_dict(program), "master_exists": repository.has_master(program.program_id)}
            for program in repository.list()
        ],
    }


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
        return {
            "success": True,
            "program": model_to_dict(program),
            "master_exists": repository.has_master(program_id),
        }
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
        image = repository.load_master(program_id)
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
        located = locate_all(program.master.rois, master, test)
        return {"success": True, "rois": [model_to_dict(item) for item in located]}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.post("/programs/{program_id}/test-run", summary="Locate stations and run configured Lab Services")
async def test_run(program_id: str, request: Request):
    try:
        program = repository.get(program_id)
        master = repository.load_master(program_id)
        test = _decode(await request.body())
        result = runtime.run_test(program, master, test)
        return {"success": True, "run": model_to_dict(result)}
    except FileNotFoundError as exc:
        raise _error(exc, 404)
    except Exception as exc:
        raise _error(exc)


@router.get("/programs/{program_id}/iot/trigger", summary="Read configured Modbus trigger input once")
def read_trigger(program_id: str):
    try:
        program = repository.get(program_id)
        value = io_controller.read_trigger(program.io)
        return {"success": True, "triggered": value}
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
