"""Services pipeline (versionné)."""

from fastapi import APIRouter

from kimvieware_orchestrator.services import pipeline_services

router = APIRouter(prefix="/services", tags=["pipeline-services"])


@router.get("/")
def list_services():
    return pipeline_services.refresh_services_from_rabbit()


@router.get("/{service_key}/health")
def health(service_key: str):
    return pipeline_services.service_health(service_key)


@router.get("/{service_key}/logs")
def logs(service_key: str):
    return pipeline_services.service_logs_text(service_key)


@router.post("/{service_key}/restart")
def restart(service_key: str):
    return pipeline_services.restart_service_simulated(service_key)
