"""Chemins racine de l'orchestrateur (templates, static, uploads)."""

from pathlib import Path


def get_orchestrator_root() -> Path:
    """Répertoire racine du service (parent de ``src``)."""
    return Path(__file__).resolve().parents[2]
