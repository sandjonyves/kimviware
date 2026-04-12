"""Logique métier des jobs (soumission, lecture)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, UploadFile

from kimvieware_shared.utils.rabbitmq import declare_queue, publish_message

from kimvieware_orchestrator import state


def make_job(job_id: str, filename: str, content_len: int) -> Dict[str, Any]:
    return {
        "job_id": job_id,
        "filename": filename,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "file_size": content_len,
        "status": "SUBMITTED",
        "phases": {
            "phase0": {"status": "pending", "progress": 0},
            "phase1": {"status": "pending", "progress": 0},
            "phase2": {"status": "pending", "progress": 0},
            "phase3": {"status": "pending", "progress": 0},
            "phase4": {"status": "pending", "progress": 0},
        },
        "error": None,
    }


def get_rabbitmq_channel():
    from kimvieware_shared.utils.rabbitmq import create_connection

    if state.rabbitmq_connection is None or state.rabbitmq_connection.is_closed:
        state.rabbitmq_connection = create_connection(logger=state.logger)
        state.rabbitmq_channel = state.rabbitmq_connection.channel()
        declare_queue(state.rabbitmq_channel, "submission.new")
    return state.rabbitmq_channel


async def submit_sut(file: UploadFile, base_dir: Path) -> Dict[str, str]:
    try:
        all_jobs = state.job_storage.get_all_jobs(limit=1000)
        job_id = f"job_{len(all_jobs) + 1:04d}"

        content = await file.read()

        upload_dir = base_dir / "uploads"
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{job_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)

        job = make_job(job_id, file.filename, len(content))
        state.job_storage.save_job(job)

        message = {
            "job_id": job_id,
            "sut_path": str(file_path),
            "filename": file.filename,
            "file_size": len(content),
            "submitted_at": job["uploaded_at"],
            "status": "submitted",
        }

        channel = get_rabbitmq_channel()
        publish_message(channel, "submission.new", message)
        state.logger.info("Published job %s to 'submission.new' queue", job_id)

        return {"job_id": job_id}

    except Exception as e:
        state.logger.error("Error submitting job: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}") from e


def list_jobs(limit: int = 50) -> Dict[str, Any]:
    try:
        all_jobs = state.job_storage.get_all_jobs(limit=limit)
        return {"total": len(all_jobs), "jobs": all_jobs}
    except Exception as e:
        state.logger.error("Error getting jobs: %s", e)
        return {"total": 0, "jobs": []}


def get_job(job_id: str) -> Dict[str, Any]:
    try:
        job = state.job_storage.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        state.logger.error("Error getting job %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}") from e
