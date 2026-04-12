"""État partagé léger (statut des services pipeline, connexion RabbitMQ publication)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from kimvieware_shared.storage.job_storage import JobStorage
from kimvieware_shared.utils.logging import setup_logger

services_status: Dict[str, Dict[str, str]] = {
    "validator": {"name": "Phase 0 - Validator", "status": "offline"},
    "extractor": {"name": "Phase 1 - Extractor", "status": "offline"},
    "sgats": {"name": "Phase 2 - SGATS", "status": "offline"},
    "evopath": {"name": "Phase 3 - EvoPath", "status": "offline"},
    "executor": {"name": "Phase 4 - Executor", "status": "offline"},
}

job_storage = JobStorage()
logger = setup_logger("Orchestrator")

rabbitmq_connection: Any = None
rabbitmq_channel: Any = None
