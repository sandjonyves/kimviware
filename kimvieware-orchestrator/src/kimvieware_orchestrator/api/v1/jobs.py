"""Ressource jobs (versionnée)."""

from fastapi import APIRouter, File, UploadFile

from kimvieware_orchestrator.api.deps import orchestrator_root
from kimvieware_orchestrator.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/")
async def create_job(file: UploadFile = File(...)):
    """Soumet un SUT (équivalent historique ``POST /api/submit``)."""
    return await job_service.submit_sut(file, orchestrator_root())


@router.get("/")
def list_jobs():
    return job_service.list_jobs(limit=50)


@router.get("/{job_id}")
def get_job(job_id: str):
    return job_service.get_job(job_id)
