"""Agrégation des statistiques dashboard."""

from __future__ import annotations

from typing import Any, Dict, Optional

from kimvieware_orchestrator import state


def compute_global_stats() -> Dict[str, Any]:
    try:
        all_jobs = state.job_storage.get_all_jobs(limit=1000)
        total = len(all_jobs)

        completed = sum(
            1
            for j in all_jobs
            if j.get("status")
            in [
                "completed",
                "validated",
                "extracted",
                "reduced",
                "optimized",
            ]
        )

        mutation_scores = []
        for job in all_jobs:
            if job.get("status") == "completed" and job.get("mutation_stats"):
                score = job["mutation_stats"].get("mutation_score")
                if score is not None:
                    mutation_scores.append(score)

        avg_mutation_score: Optional[float] = None
        if mutation_scores:
            avg_mutation_score = sum(mutation_scores) / len(mutation_scores)

        reductions = []
        for job in all_jobs:
            if job.get("status") == "completed":
                sgats_stats = job.get("sgats_stats")
                if sgats_stats and sgats_stats.get("reduction_rate") is not None:
                    reductions.append(sgats_stats["reduction_rate"] * 100)
                evopath_stats = job.get("evopath_stats")
                if evopath_stats and evopath_stats.get("size_reduction") is not None:
                    reductions.append(evopath_stats["size_reduction"] * 100)

        avg_reduction: Optional[float] = None
        if reductions:
            avg_reduction = sum(reductions) / len(reductions)

        return {
            "total_jobs": total,
            "completed": completed,
            "success_rate": 100.0 if total == 0 else (completed / total) * 100,
            "mutation_score": avg_mutation_score,
            "avg_reduction": avg_reduction,
        }
    except Exception as e:
        state.logger.error("Error getting stats: %s", e)
        return {
            "total_jobs": 0,
            "completed": 0,
            "success_rate": 0.0,
            "mutation_score": None,
            "avg_reduction": None,
        }
