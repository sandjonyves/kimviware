"""Routes API historiques ``/api/*`` (compatibilité avec le dashboard existant)."""

from fastapi import APIRouter, File, UploadFile

from kimvieware_orchestrator.api.deps import orchestrator_root
from kimvieware_orchestrator.services import job_service, pipeline_services, stats_service

router = APIRouter(prefix="/api", tags=["api-legacy"])


@router.post("/submit")
async def submit_sut(file: UploadFile = File(...)):
    return await job_service.submit_sut(file, orchestrator_root())


@router.get("/jobs")
def list_jobs():
    return job_service.list_jobs(limit=50)


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    return job_service.get_job(job_id)


@router.get("/services")
def get_services():
    return pipeline_services.refresh_services_from_rabbit()


@router.get("/services/{service_key}/health")
def check_service_health(service_key: str):
    return pipeline_services.service_health(service_key)


@router.get("/services/{service_key}/logs")
def get_service_logs(service_key: str):
    return pipeline_services.service_logs_text(service_key)


@router.post("/services/{service_key}/restart")
def restart_service(service_key: str):
    return pipeline_services.restart_service_simulated(service_key)


@router.get("/stats")
def get_stats():
    return stats_service.compute_global_stats()
