from __future__ import annotations

import re
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.vision_labs.image.operators import load_builtin_operators
from app.services.vision_labs.image.pipeline import ImagePipelineDefinition, PipelineCompiler, model_to_dict
from app.services.vision_labs.image.types import BinaryMask, ColorSpace, ImageFrame
from app.services.vision_labs.sampling_geometry.operators import load_sampling_geometry_operators
from app.services.vision_labs.sampling_geometry.pipeline import SamplingPipelineCompiler, SamplingPipelineDefinition, model_to_dict as sampling_model_to_dict
from app.services.vision_labs.sampling_geometry.preview import SamplingPreviewEncoder
from app.services.vision_labs.contour_extractor.models import ContourExtractorDefinition
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
    workspace_type: str | None = None
    pipeline_snapshot: dict[str, Any]
    outputs: dict[str, DeployOutputRequest] = Field(default_factory=dict)
    description: str | None = None


def _http_error(exc: Exception, status_code: int = 400) -> HTTPException:
    if isinstance(exc, HTTPException): return exc
    if isinstance(exc, (FileNotFoundError, KeyError)): return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=status_code, detail=str(exc))


def _derive_contract(request: DeployLabServiceRequest):
    if request.lab_type == "image_processing":
        load_builtin_operators()
        pipeline = ImagePipelineDefinition(**request.pipeline_snapshot)
        compiled = PipelineCompiler().compile(pipeline)
        serializer = model_to_dict
    elif request.lab_type == "sampling_geometry":
        load_sampling_geometry_operators()
        pipeline = SamplingPipelineDefinition(**request.pipeline_snapshot)
        compiled = SamplingPipelineCompiler().compile(pipeline)
        serializer = sampling_model_to_dict
    elif request.lab_type == "contour_extractor":
        pipeline = ContourExtractorDefinition(**request.pipeline_snapshot)
        compiled = None
        serializer = lambda model: model.model_dump() if hasattr(model, "model_dump") else model.dict()
    else:
        raise ValueError(f"Unsupported Lab Service type: {request.lab_type}")

    inputs: dict[str, LabServicePort] = {}
    if request.lab_type == "contour_extractor":
        inputs["image"] = LabServicePort(type="image", required=True)
    elif request.lab_type == "sampling_geometry" and bool(getattr(pipeline, "source_board", {})):
        # A deployed Sampling/Geometry service reproduces the editor Source Board
        # internally. Its public contract therefore needs only the original raw
        # image; upstream image-processing pins remain implementation details.
        inputs["image"] = LabServicePort(type="image", required=True)
    else:
        for input_name, endpoint in pipeline.inputs.items():
            node = compiled.nodes.get(endpoint.node_id)
            if node is None: raise ValueError(f"Unknown input node: {endpoint.node_id}")
            port_spec = node.operator_class.INPUTS.get(endpoint.port)
            if port_spec is None: raise ValueError(f"Unknown input port: {endpoint.node_id}.{endpoint.port}")
            data_type = port_spec.data_type.value if hasattr(port_spec.data_type, "value") else str(port_spec.data_type)
            inputs[input_name] = LabServicePort(type=data_type, required=not bool(port_spec.optional))

    if not request.outputs: raise ValueError("Lab Service must expose at least one output")
    outputs: dict[str, LabServiceOutputBinding] = {}
    for output_name, binding in request.outputs.items():
        if not _OUTPUT_NAME.fullmatch(output_name):
            raise ValueError(f"Invalid service output name {output_name!r}; use letters, numbers and underscore")
        if request.lab_type == "contour_extractor":
            if binding.port != "contours":
                raise ValueError("Contour Extractor Service currently exposes only the final contours output")
            outputs[output_name] = LabServiceOutputBinding(type="contour_set", node_id="contour_runtime", port="contours", label=binding.label)
            continue
        node = compiled.nodes.get(binding.node_id)
        if node is None: raise ValueError(f"Unknown service output node: {binding.node_id}")
        port_spec = node.operator_class.OUTPUTS.get(binding.port)
        if port_spec is None: raise ValueError(f"Unknown service output port: {binding.node_id}.{binding.port}")
        data_type = port_spec.data_type.value if hasattr(port_spec.data_type, "value") else str(port_spec.data_type)
        outputs[output_name] = LabServiceOutputBinding(type=data_type, node_id=binding.node_id, port=binding.port, label=binding.label)

    workspace_type = request.workspace_type
    if request.lab_type == "sampling_geometry":
        workspace_type = workspace_type or pipeline.workspace
    return pipeline, inputs, outputs, workspace_type, serializer


def _decode_image(raw: bytes) -> ImageFrame:
    if not raw: raise ValueError("Lab Service input image body is empty")
    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_UNCHANGED)
    if image is None: raise ValueError("Lab Service input could not be decoded as an image")
    if image.ndim == 2: color_space = ColorSpace.GRAY
    elif image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR); color_space = ColorSpace.BGR
    else: color_space = ColorSpace.BGR
    return ImageFrame(data=image, color_space=color_space, source_id="lab_service_input")


def _decode_mask(raw: bytes) -> BinaryMask:
    if not raw: raise ValueError("Lab Service input mask body is empty")
    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_GRAYSCALE)
    if image is None: raise ValueError("Lab Service input could not be decoded as a binary mask")
    return BinaryMask(data=(image > 0).astype(np.uint8) * 255)

@router.get("")
def list_lab_services():
    return {"success": True, "services": [service_to_dict(s) for s in LAB_SERVICE_REPOSITORY.list_active()]}

@router.post("/deploy")
def deploy_lab_service(request: DeployLabServiceRequest):
    try:
        pipeline, inputs, outputs, workspace_type, serializer = _derive_contract(request)
        service = LAB_SERVICE_REPOSITORY.deploy(
            name=request.name,
            service_id=request.service_id,
            lab_type=request.lab_type,
            workspace_type=workspace_type,
            inputs=inputs,
            outputs=outputs,
            pipeline_snapshot=serializer(pipeline),
            description=request.description,
        )
        return {"success": True, "service": service_to_dict(service)}
    except Exception as exc: raise _http_error(exc)

@router.get("/runs/{run_id}/outputs/{output_name}")
def preview_run_output(run_id: str, output_name: str, max_width: int = Query(1200, ge=64, le=4096), quality: int = Query(88, ge=20, le=100)):
    try:
        run = LAB_SERVICE_RUN_STORE.get(run_id)
        if output_name not in run.outputs: raise KeyError(f"Unknown Lab Service output: {output_name}")
        payload, mime = SamplingPreviewEncoder.encode(run.outputs[output_name], max_width=max_width, quality=quality)
        return Response(content=payload, media_type=mime)
    except Exception as exc: raise _http_error(exc)

@router.delete("/{service_id}")
def delete_lab_service(service_id: str):
    try:
        deleted = LAB_SERVICE_REPOSITORY.delete(service_id)
        if not deleted:
            raise FileNotFoundError(f"Lab Service not found: {service_id}")
        return {"success": True, "service_id": service_id}
    except Exception as exc: raise _http_error(exc)

@router.get("/{service_id}/versions")
def list_lab_service_versions(service_id: str):
    try: return {"success": True, "versions": [service_to_dict(s) for s in LAB_SERVICE_REPOSITORY.list_versions(service_id)]}
    except Exception as exc: raise _http_error(exc)

@router.get("/{service_id}")
def get_lab_service(service_id: str, version: int | None = None):
    try: return {"success": True, "service": service_to_dict(LAB_SERVICE_REPOSITORY.get(service_id, version=version))}
    except Exception as exc: raise _http_error(exc)

@router.post("/{service_id}/run")
async def run_lab_service(service_id: str, request: Request, version: int | None = None):
    try:
        service = LAB_SERVICE_REPOSITORY.get(service_id, version=version)
        if len(service.inputs) != 1:
            raise NotImplementedError("Manual runner currently supports one raster input")
        input_name, port = next(iter(service.inputs.items()))
        raw = await request.body()
        if port.type == "image": value = _decode_image(raw)
        elif port.type == "binary_mask": value = _decode_mask(raw)
        else: raise NotImplementedError(f"Manual runner cannot decode input type {port.type!r} yet")
        run = LAB_SERVICE_RUNTIME.run(service, {input_name: value})
        LAB_SERVICE_RUN_STORE.put(run)
        return {"success": True, "run": service_to_dict(run.manifest)}
    except Exception as exc: raise _http_error(exc)
