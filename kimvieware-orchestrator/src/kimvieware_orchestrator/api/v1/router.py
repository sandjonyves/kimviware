"""Agrégation API ``/api/v1``."""

from fastapi import APIRouter

from kimvieware_orchestrator.api.v1 import jobs, services, stats

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(jobs.router)
api_v1_router.include_router(services.router)
api_v1_router.include_router(stats.router)
