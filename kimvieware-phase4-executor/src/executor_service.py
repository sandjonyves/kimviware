"""
Phase 4: Test Executor Service

Consumes : optimization.completed
Produces : execution.completed
"""
import sys
import ast as _ast
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'kimvieware-shared' / 'src'))

from kimvieware_shared import MicroserviceBase, JobStatus, Trajectory
from generators.test_generator import TestGenerator
from executors.test_executor import TestExecutor


def _parse_field(value):
    """
    Le MicroserviceBase transmet parfois les champs complexes comme des strings.
    Cette fonction les convertit en dict/list si nécessaire.
    """
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        # Essai JSON d'abord
        try:
            return json.loads(value)
        except Exception:
            pass
        # Fallback: ast.literal_eval (pour les repr Python style {'key': 'val'})
        try:
            return _ast.literal_eval(value)
        except Exception:
            pass
    return value


class ExecutorService(MicroserviceBase):
    """Phase 4: Test Execution with real pytest + branch coverage."""

    def __init__(self):
        super().__init__(
            service_name="Phase4_Executor",
            input_queue="optimization.completed",
            output_queue="execution.completed",
        )
        self.test_generator = TestGenerator()
        self.test_executor = TestExecutor()

    def process_message(self, message: dict) -> dict:
        job_id = message['job_id']

        if message.get('status') != 'optimized':
            self.logger.warning(f"[{job_id}] Skipping: status='{message.get('status')}'")
            return message

        # ── Parse les champs qui peuvent être des strings ─────────────────
        trajectories_data = _parse_field(message.get('trajectories', []))
        sut_info          = _parse_field(message.get('sut_info', {}))

        if not trajectories_data:
            return self._error(job_id, "No trajectories to execute")

        # ── Localiser le code source (extracted_path) ─────────────────────
        # La Phase 0 extrait le zip dans /tmp/kimvieware_validator/{job_id}/
        # Ce chemin n'est pas toujours propagé — on le reconstruit si absent.
        sut_source_path = self._resolve_source_path(message, sut_info, job_id)

        self.logger.info(
            f"[{job_id}] Phase 4: {len(trajectories_data)} trajectories | "
            f"source: {sut_source_path or 'not available'}"
        )

        trajectories = [Trajectory.from_dict(t) for t in trajectories_data]

        tmpdir_path = Path(f"/tmp/kimvi_{job_id}")
        tmpdir_path.mkdir(exist_ok=True)

        try:
            # Step 1 — Générer les tests
            test_file = self.test_generator.generate(
                trajectories=trajectories,
                output_dir=tmpdir_path,
                sut_source_path=sut_source_path,
            )

            # Step 2 — Exécuter avec pytest + coverage
            exec_stats = self.test_executor.execute(
                test_file=test_file,
                trajectories_data=trajectories_data,
                sut_source_path=sut_source_path,
            )

        except Exception as exc:
            self.logger.error(f"[{job_id}] Pipeline error: {exc}", exc_info=True)
            return self._error(job_id, str(exc))

        logical = exec_stats.get('logical_branch_coverage', {})
        self.logger.info(
            f"[{job_id}] ✅ "
            f"{exec_stats['passed']}/{exec_stats['total']} passed | "
            f"branch coverage — "
            f"minimal: {logical.get('minimal_coverage_pct', 'N/A')}% | "
            f"union: {logical.get('union_coverage_pct', 'N/A')}%"
        )

        return {
            'job_id': job_id,
            'status': JobStatus.COMPLETED.value,
            'sut_info': sut_info,
            'extracted_path': str(sut_source_path) if sut_source_path else None,
            'extraction_count': message.get('extraction_count'),
            'original_trajectories': message.get('original_trajectories'),
            'sgats_stats': message.get('sgats_stats'),
            'evopath_stats': message.get('evopath_stats'),
            'execution_stats': exec_stats,
            'trajectories_count': len(trajectories),
            'trajectories': [t.to_dict() for t in trajectories],
            'metadata': {
                'phase': 'execution',
                'test_count': len(trajectories),
                'sut_source': str(sut_source_path) if sut_source_path else None,
            },
        }

    # ------------------------------------------------------------------
    # Résolution du chemin source
    # ------------------------------------------------------------------

    def _resolve_source_path(self, message: dict, sut_info: dict, job_id: str) -> Path | None:
        """
        Cherche le code source extrait par la Phase 0.

        Stratégies (dans l'ordre) :
        1. extracted_path dans le message
        2. extracted_path dans sut_info
        3. Reconstruction : /tmp/kimvieware_validator/{job_id}
        4. Reconstruction : /tmp/kimvieware/{job_id}
        """
        candidates = []

        # 1. Champ direct dans le message
        raw = message.get('extracted_path') or message.get('sut_path')
        if raw:
            candidates.append(Path(raw))

        # 2. Dans sut_info
        raw2 = sut_info.get('extracted_path') or sut_info.get('source_path')
        if raw2:
            candidates.append(Path(raw2))

        # 3. Chemins reconstruits (Phase 0 utilise /tmp/kimvieware_validator/{job_id})
        candidates += [
            Path(f"/tmp/kimvieware_validator/{job_id}"),
            Path(f"/tmp/kimvieware/{job_id}"),
            Path(f"/tmp/kimvi_{job_id}"),
        ]

        for p in candidates:
            if p.exists() and p.is_dir():
                self.logger.info(f"[{job_id}] Source found: {p}")
                return p

        self.logger.warning(f"[{job_id}] Source not found. Tried: {[str(c) for c in candidates]}")
        return None

    def _error(self, job_id: str, msg: str) -> dict:
        return {
            'job_id': job_id,
            'status': JobStatus.FAILED.value,
            'error': msg,
            'phase': 'execution',
        }


if __name__ == "__main__":
    service = ExecutorService()
    service.start()