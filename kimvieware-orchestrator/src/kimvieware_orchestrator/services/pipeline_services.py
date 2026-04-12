"""Statut / health / logs / restart des microservices pipeline (vue orchestrateur)."""

from __future__ import annotations

import socket
import threading
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException

from kimvieware_orchestrator import state

SERVICE_CHECKS = {
    "validator": {"port": 5672, "queue": "submission.new"},
    "extractor": {"port": 5672, "queue": "validation.completed"},
    "sgats": {"port": 5672, "queue": "extraction.completed"},
    "evopath": {"port": 5672, "queue": "reduction.completed"},
    "executor": {"port": 5672, "queue": "optimization.completed"},
}


def refresh_services_from_rabbit() -> Dict[str, Dict[str, str]]:
    for service_key, check in SERVICE_CHECKS.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", check["port"]))
            sock.close()

            if result == 0:
                state.services_status[service_key]["status"] = "online"
            else:
                state.services_status[service_key]["status"] = "offline"
        except OSError:
            state.services_status[service_key]["status"] = "unknown"
    return state.services_status


def service_health(service_key: str) -> Dict[str, Any]:
    if service_key not in state.services_status:
        raise HTTPException(status_code=404, detail=f"Service {service_key} not found")
    return {
        "service": service_key,
        "status": state.services_status[service_key]["status"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def service_logs_text(service_key: str) -> str:
    if service_key not in state.services_status:
        raise HTTPException(status_code=404, detail=f"Service {service_key} not found")
    st = state.services_status[service_key]["status"]
    return (
        f"Logs for service {service_key} - Status: {st}\n"
        f"[TIMESTAMP] Service started\n[TIMESTAMP] Processing jobs...\n"
    )


def restart_service_simulated(service_key: str) -> Dict[str, str]:
    if service_key not in state.services_status:
        raise HTTPException(status_code=404, detail=f"Service {service_key} not found")

    state.services_status[service_key]["status"] = "restarting"

    def simulate_restart():
        time.sleep(2)
        state.services_status[service_key]["status"] = "online"

    thread = threading.Thread(target=simulate_restart, daemon=True)
    thread.start()
    return {"message": f"Service {service_key} restart initiated"}
