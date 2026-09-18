from fastapi import APIRouter
from app.api.v1.endpoints import utils, graph_api, infra_api, db_api
from app.api.v1.endpoints import lab_service_api
from app.api.v1.endpoints import sampling_geometry_api
from app.api.v1.endpoints import contour_extractor_api
from app.api.v1.endpoints import image_lab_api

api_router = APIRouter()

api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(graph_api.router, prefix="/nodes", tags=["Node-Based Logic"])
api_router.include_router(infra_api.router, prefix="/infra", tags=["InfraStructure API"])
api_router.include_router(db_api.router, prefix="/db", tags=["Database Traceability"])
api_router.include_router(image_lab_api.router, prefix="/image-lab", tags=["Image Processing LAB"])
api_router.include_router(lab_service_api.router, prefix="/lab-services", tags=["Lab Services"])
api_router.include_router(sampling_geometry_api.router, prefix="/sampling-geometry", tags=["Sampling / Geometry LAB"])
api_router.include_router(contour_extractor_api.router, prefix="/contour-extractor", tags=["Contour Extractor LAB"])