"""Statistiques agrégées (versionné)."""

from fastapi import APIRouter

from kimvieware_orchestrator.services import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/")
def global_stats():
    return stats_service.compute_global_stats()
