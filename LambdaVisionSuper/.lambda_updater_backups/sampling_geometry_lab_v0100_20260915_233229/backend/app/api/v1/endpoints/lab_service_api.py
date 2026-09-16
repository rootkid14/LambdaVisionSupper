from __future__ import annotations

import re
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.pipeline import (
    ImagePipelineDefinition,
    PipelineCompiler,
    model_to_dict,
)
from app.services.vision_labs.image.session import PreviewEncoder
from app.services.vision_labs.image.types import ColorSpace, ImageFrame
from app.services.vision_labs.service import (
    LAB_SERVICE_REPOSITORY,
    LAB_SERVICE_RUNTIME,
    LAB_SERVICE_RUN_STORE,
    LabServiceOutputBinding,
    LabServicePort,
)
from app.services.vision_labs.service.repository import model_to_dict as service_to_dict


router = APIRouter()
_OUTPUT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class DeployOutputRequest(BaseModel):
    node_id: str
    port: str
    label: str | None = None


class DeployLabServiceRequest(BaseModel):
    name: str
    service_id: str | None = None
    lab_type: str = "image_processing"
    pipeline_snapshot: dict[str, Any]
    outputs: dict[str, DeployOutputRequest] = Field(default_factory=dict)
    description: str | None = None


def _http_error(exc: Exception, status_code: int = 400) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, FileNotFoundError) or isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=status_code, detail=str(exc))


def _derive_image_contract(request: DeployLabServiceRequest):
    if request.lab_type != "image_processing":
        raise ValueError(
            "Only image_processing Lab Services can be deployed in this version"
        )

    load_builtin_operators()
    pipeline = ImagePipelineDefinition(**request.pipeline_snapshot)
    compiled = PipelineCompiler().compile(pipeline)

    inputs: dict[str, LabServicePort] = {}
    for input_name, endpoint in pipeline.inputs.items():
        node = compiled.nodes.get(endpoint.node_id)
        if node is None:
            raise ValueError(f"Unknown input node: {endpoint.node_id}")
        port_spec = node.operator_class.INPUTS.get(endpoint.port)
        if port_spec is None:
            raise ValueError(
                f"Unknown input port: {endpoint.node_id}.{endpoint.port}"
            )
        inputs[input_name] = LabServicePort(
            type=port_spec.data_type.value,
            required=not bool(port_spec.optional),
        )

    if not request.outputs:
        raise ValueError("Lab Service must expose at least one output")

    outputs: dict[str, LabServiceOutputBinding] = {}
    for output_name, binding in request.outputs.items():
        if not _OUTPUT_NAME.fullmatch(output_name):
            raise ValueError(
                f"Invalid service output name {output_name!r}; use letters, numbers and underscore"
            )
        node = compiled.nodes.get(binding.node_id)
        if node is None:
            raise ValueError(f"Unknown service output node: {binding.node_id}")
        port_spec = node.operator_class.OUTPUTS.get(binding.port)
        if port_spec is None:
            raise ValueError(
                f"Unknown service output port: {binding.node_id}.{binding.port}"
            )
        outputs[output_name] = LabServiceOutputBinding(
            type=port_spec.data_type.value,
            node_id=binding.node_id,
            port=binding.port,
            label=binding.label,
        )

    return pipeline, inputs, outputs


def _decode_image(raw: bytes) -> ImageFrame:
    if not raw:
        raise ValueError("Lab Service input image body is empty")
    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Lab Service input could not be decoded as an image")
    if image.ndim == 2:
        color_space = ColorSpace.GRAY
    elif image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        color_space = ColorSpace.BGR
    else:
        color_space = ColorSpace.BGR
    return ImageFrame(data=image, color_space=color_space, source_id="lab_service_input")


@router.get("", summary="List deployed Lab Services")
def list_lab_services():
    return {
        "success": True,
        "services": [
            service_to_dict(service)
            for service in LAB_SERVICE_REPOSITORY.list_active()
        ],
    }


@router.post("/deploy", summary="Deploy a versioned Lab Service snapshot")
def deploy_lab_service(request: DeployLabServiceRequest):
    try:
        pipeline, inputs, outputs = _derive_image_contract(request)
        service = LAB_SERVICE_REPOSITORY.deploy(
            name=request.name,
            service_id=request.service_id,
            lab_type=request.lab_type,
            inputs=inputs,
            outputs=outputs,
            pipeline_snapshot=model_to_dict(pipeline),
            description=request.description,
        )
        return {"success": True, "service": service_to_dict(service)}
    except Exception as exc:
        raise _http_error(exc)


@router.get("/runs/{run_id}/outputs/{output_name}", summary="Preview a Lab Service run output")
def preview_run_output(
    run_id: str,
    output_name: str,
    max_width: int = Query(1200, ge=64, le=4096),
    quality: int = Query(88, ge=20, le=100),
):
    try:
        run = LAB_SERVICE_RUN_STORE.get(run_id)
        if output_name not in run.outputs:
            raise KeyError(f"Unknown Lab Service output: {output_name}")
        payload, mime = PreviewEncoder.encode(
            run.outputs[output_name],
            max_width=max_width,
            quality=quality,
        )
        return Response(content=payload, media_type=mime)
    except Exception as exc:
        raise _http_error(exc)


@router.get("/{service_id}/versions", summary="List Lab Service versions")
def list_lab_service_versions(service_id: str):
    try:
        return {
            "success": True,
            "versions": [
                service_to_dict(service)
                for service in LAB_SERVICE_REPOSITORY.list_versions(service_id)
            ],
        }
    except Exception as exc:
        raise _http_error(exc)


@router.get("/{service_id}", summary="Read the active Lab Service definition")
def get_lab_service(service_id: str, version: int | None = None):
    try:
        service = LAB_SERVICE_REPOSITORY.get(service_id, version=version)
        return {"success": True, "service": service_to_dict(service)}
    except Exception as exc:
        raise _http_error(exc)


@router.post("/{service_id}/run", summary="Manually execute a Lab Service")
async def run_lab_service(
    service_id: str,
    request: Request,
    version: int | None = None,
):
    try:
        service = LAB_SERVICE_REPOSITORY.get(service_id, version=version)
        if service.lab_type != "image_processing":
            raise NotImplementedError(
                f"Manual runner is not implemented for {service.lab_type!r}"
            )

        image_inputs = [
            name
            for name, port in service.inputs.items()
            if port.type == "image"
        ]
        if len(service.inputs) != 1 or len(image_inputs) != 1:
            raise NotImplementedError(
                "This manual runner currently supports one Image input"
            )

        raw = await request.body()
        frame = _decode_image(raw)
        run = LAB_SERVICE_RUNTIME.run(
            service,
            {image_inputs[0]: frame},
        )
        LAB_SERVICE_RUN_STORE.put(run)
        return {
            "success": True,
            "run": service_to_dict(run.manifest),
        }
    except Exception as exc:
        raise _http_error(exc)
