"""
Rétrocompatibilité : les imports ``from src.api.enhanced_gateway import app`` restent valides
si ``kimvieware-orchestrator/src`` est sur ``PYTHONPATH``.
"""

from kimvieware_orchestrator.main import app

__all__ = ["app"]
