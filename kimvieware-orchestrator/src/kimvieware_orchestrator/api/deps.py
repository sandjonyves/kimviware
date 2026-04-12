"""Dépendances FastAPI (chemins racine)."""

from functools import lru_cache

from kimvieware_orchestrator.paths import get_orchestrator_root


@lru_cache
def orchestrator_root():
    return get_orchestrator_root()
