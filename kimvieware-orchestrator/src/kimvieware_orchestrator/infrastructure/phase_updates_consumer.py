"""Consumer RabbitMQ ``phase.updates`` -> persistance MongoDB."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from kimvieware_shared.utils.rabbitmq import create_connection, declare_queue

from kimvieware_orchestrator import state


def run_phase_updates_consumer() -> None:
    """Bloquant : à lancer dans un thread dédié."""

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body.decode("utf-8"))
            job_id = message.get("job_id")
            status = message.get("status")

            if not job_id or not status:
                state.logger.warning(
                    "Received invalid phase update message without job_id/status"
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            state.logger.info("Phase update for job %s: %s", job_id, status)

            phase_from_status = {
                "validated": "phase0",
                "validation_failed": "phase0",
                "extracted": "phase1",
                "extraction_failed": "phase1",
                "reduced": "phase2",
                "reduction_failed": "phase2",
                "optimized": "phase3",
                "optimization_failed": "phase3",
                "completed": "phase4",
                "execution_failed": "phase4",
                "failed": "phase0",
            }
            phase_key = phase_from_status.get(status)
            if phase_key is None:
                state.logger.warning("Unknown status '%s' in phase update", status)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            phase_data: dict[str, Any] = {**message.get("metadata", {}), "status": status}

            if status in ["validated", "validation_failed"]:
                sut = message.get("sut_info") or {}
                phase_data.update(
                    {
                        "language": sut.get("language"),
                        "framework": sut.get("framework"),
                        "files_count": sut.get("files_count"),
                        "size_bytes": sut.get("size_bytes"),
                        "entry_point": sut.get("entry_point"),
                        "extracted_path": message.get("extracted_path"),
                    }
                )

            if status in ["extracted", "extraction_failed"]:
                phase_data.update(
                    {
                        "trajectories_count": message.get("trajectories_count"),
                        "trajectories": message.get("trajectories"),
                    }
                )

            if "sgats_stats" in message:
                phase_data["sgats_stats"] = message.get("sgats_stats")
            if "evopath_stats" in message:
                phase_data["evopath_stats"] = message.get("evopath_stats")
            if "execution_stats" in message:
                phase_data["execution_stats"] = message.get("execution_stats")
            if "mutation_stats" in message:
                phase_data["mutation_stats"] = message.get("mutation_stats")

            state.job_storage.update_phase(job_id, phase_key, phase_data)

            job_update: dict[str, Any] = {
                "job_id": job_id,
                "status": status,
                "error": message.get("error"),
                "phase": message.get("phase"),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }

            if "mutation_stats" in message:
                job_update["mutation_stats"] = message.get("mutation_stats")
            if "execution_stats" in message:
                job_update["execution_stats"] = message.get("execution_stats")
            if "sgats_stats" in message:
                job_update["sgats_stats"] = message.get("sgats_stats")
            if "evopath_stats" in message:
                job_update["evopath_stats"] = message.get("evopath_stats")

            state.job_storage.save_job(job_update)

            ch.basic_ack(delivery_tag=method.delivery_tag)
            state.logger.info("Updated MongoDB from phase.updates for job %s", job_id)

        except Exception as e:
            state.logger.error("Error processing phase update: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    try:
        connection = create_connection(logger=state.logger)
        channel = connection.channel()
        declare_queue(channel, "phase.updates")
        channel.basic_consume(queue="phase.updates", on_message_callback=callback)
        state.logger.info("Started consumer for phase.updates")
        channel.start_consuming()
    except Exception as e:
        state.logger.error("Failed to start consumer for phase.updates: %s", e)
