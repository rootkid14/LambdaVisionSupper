from fastapi import APIRouter
from app.api.v1.endpoints import utils, graph_api, infra_api, db_api

api_router = APIRouter()

api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(graph_api.router, prefix="/nodes", tags=["Node-Based Logic"])
api_router.include_router(infra_api.router, prefix="/infra", tags=["InfraStructure API"])
api_router.include_router(db_api.router, prefix="/db", tags=["Database Traceability"])