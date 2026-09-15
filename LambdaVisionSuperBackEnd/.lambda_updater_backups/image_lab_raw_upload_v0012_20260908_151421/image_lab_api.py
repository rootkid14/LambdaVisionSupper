from __future__ import annotations

import asyncio
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.vision_labs.core import ExecutionMode
from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.pipeline import (
    ImagePipelineDefinition,
    PipelineValidator,
    model_to_dict,
)
from app.services.vision_labs.image.registry import IMAGE_OPERATOR_REGISTRY
from app.services.vision_labs.image.repository import ImagePipelineRepository
from app.services.vision_labs.image.session import (
    ImageLabSessionManager,
    PreviewEncoder,
)
from app.services.vision_labs.image.types import ColorSpace, ImageFrame


load_builtin_operators()

router = APIRouter()
session_manager = ImageLabSessionManager()
pipeline_repository = ImagePipelineRepository()


class SavePipelineRequest(BaseModel):
    name: str
    pipeline: ImagePipelineDefinition


def _http_error(exc: Exception, status_code: int = 400) -> HTTPException:
    return HTTPException(status_code=status_code, detail=str(exc))


@router.get("/operators", summary="Image LAB operator catalog")
def get_operator_catalog():
    return {
        "success": True,
        "operators": IMAGE_OPERATOR_REGISTRY.manifests(),
    }


@router.post("/pipelines/validate", summary="Validate an Image LAB pipeline")
def validate_pipeline(pipeline: ImagePipelineDefinition):
    errors = PipelineValidator().validate(pipeline, raise_on_error=False)
    return {
        "success": not errors,
        "valid": not errors,
        "errors": errors,
    }


@router.get("/pipelines", summary="List saved Image LAB pipelines")
def list_pipelines():
    return {"success": True, "pipelines": pipeline_repository.list()}


@router.get("/pipelines/{name}", summary="Load a saved Image LAB pipeline")
def load_pipeline(name: str):
    try:
        pipeline = pipeline_repository.load(name)
        return {"success": True, "pipeline": model_to_dict(pipeline)}
    except FileNotFoundError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)


@router.post("/pipelines/save", summary="Save an Image LAB pipeline")
def save_pipeline(request: SavePipelineRequest):
    try:
        errors = PipelineValidator().validate(request.pipeline, raise_on_error=False)
        if errors:
            raise ValueError("Pipeline is invalid: " + "; ".join(errors))
        path = pipeline_repository.save(request.name, request.pipeline)
        return {"success": True, "name": request.name, "path": str(path)}
    except Exception as exc:
        raise _http_error(exc)


@router.post("/sessions", summary="Create an interactive Image LAB session")
def create_session():
    session = session_manager.create()
    return {
        "success": True,
        "session_id": session.session_id,
        "revision": session.revision,
    }


@router.delete("/sessions/{session_id}", summary="Close an Image LAB session")
def close_session(session_id: str):
    closed = session_manager.close(session_id)
    if not closed:
        raise HTTPException(status_code=404, detail=f"Unknown Image LAB session: {session_id}")
    return {"success": True}


@router.post("/sessions/{session_id}/input/{source_name}", summary="Upload an image into session RAM")
async def upload_input(
    session_id: str,
    source_name: str,
    file: UploadFile = File(...),
):
    try:
        session = session_manager.get(session_id)
        raw = await file.read()
        array = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError("Uploaded file could not be decoded as an image")
        if image.ndim == 2:
            color_space = ColorSpace.GRAY
        elif image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            color_space = ColorSpace.BGR
        else:
            color_space = ColorSpace.BGR
        frame = ImageFrame(data=image, color_space=color_space, source_id=source_name)
        session.set_source(source_name, frame)
        return {
            "success": True,
            "session_id": session_id,
            "source_name": source_name,
            "revision": session.revision,
            "shape": list(frame.shape),
            "color_space": frame.color_space.value,
        }
    except KeyError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)


@router.put("/sessions/{session_id}/pipeline", summary="Set/compile session pipeline")
def set_session_pipeline(session_id: str, pipeline: ImagePipelineDefinition):
    try:
        session = session_manager.get(session_id)
        session.set_pipeline(pipeline)
        return {
            "success": True,
            "revision": session.revision,
            "pipeline": model_to_dict(pipeline),
        }
    except KeyError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)


@router.post("/sessions/{session_id}/run", summary="Run session pipeline")
def run_session(session_id: str):
    try:
        session = session_manager.get(session_id)
        result = session.run(mode=ExecutionMode.FINAL)
        return {
            "success": True,
            "revision": session.revision,
            "result": result.manifest(),
            "artifacts": session.runtime.artifacts.manifests() if session.runtime else [],
        }
    except KeyError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)


@router.get("/sessions/{session_id}/preview/source/{source_name}")
def preview_source(
    session_id: str,
    source_name: str,
    max_width: int = 1200,
    quality: int = 82,
):
    try:
        session = session_manager.get(session_id)
        value = session.get_source(source_name)
        payload, mime = PreviewEncoder.encode(value, max_width=max_width, quality=quality)
        return Response(content=payload, media_type=mime)
    except KeyError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)


@router.get("/sessions/{session_id}/preview/node/{node_id}/{port}")
def preview_node(
    session_id: str,
    node_id: str,
    port: str,
    max_width: int = 1200,
    quality: int = 82,
):
    try:
        session = session_manager.get(session_id)
        artifact = session.get_artifact(node_id, port)
        payload, mime = PreviewEncoder.encode(
            artifact.value,
            max_width=max_width,
            quality=quality,
        )
        return Response(content=payload, media_type=mime)
    except KeyError as exc:
        raise _http_error(exc, 404)
    except Exception as exc:
        raise _http_error(exc)


@router.websocket("/sessions/{session_id}/live")
async def image_lab_live(websocket: WebSocket, session_id: str):
    try:
        session = session_manager.get(session_id)
    except KeyError:
        await websocket.close(code=4404)
        return

    await websocket.accept()

    async def worker():
        while True:
            payload = await session.realtime.next()
            client_revision = int(payload.get("revision", 0))
            try:
                node_id = str(payload["node_id"])
                changes = dict(payload.get("changes", {}))
                mode = ExecutionMode(payload.get("mode", ExecutionMode.INTERACTIVE.value))

                result = await asyncio.to_thread(
                    session.update_parameters,
                    node_id,
                    changes,
                    mode=mode,
                )

                if session.realtime.is_stale(client_revision):
                    continue

                preview_node = payload.get("preview_node", node_id)
                preview_port = payload.get("preview_port")
                if preview_port is None:
                    op = session.runtime.compiled.nodes[preview_node]
                    preview_port = next(iter(op.operator_class.OUTPUTS))

                artifact = session.get_artifact(preview_node, preview_port)
                preview_bytes, mime = await asyncio.to_thread(
                    PreviewEncoder.encode,
                    artifact.value,
                    max_width=int(payload.get("max_width", 1200)),
                    quality=int(payload.get("quality", 82)),
                )

                await websocket.send_json(
                    {
                        "type": "preview",
                        "client_revision": client_revision,
                        "session_revision": session.revision,
                        "node_id": preview_node,
                        "port": preview_port,
                        "mime": mime,
                        "artifact": artifact.manifest(),
                        "timings_ms": result.timings_ms,
                        "executed_nodes": result.executed_nodes,
                        "cached_nodes": result.cached_nodes,
                        "binary_follows": True,
                    }
                )
                await websocket.send_bytes(preview_bytes)
            except Exception as exc:
                if not session.realtime.is_stale(client_revision):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "client_revision": client_revision,
                            "message": str(exc),
                        }
                    )
            finally:
                session.realtime.done()

    worker_task = asyncio.create_task(worker())
    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            if message_type == "parameter_update":
                session.realtime.submit(message)
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Unsupported live message type: {message_type}",
                    }
                )
    except WebSocketDisconnect:
        pass
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
