"""
Test Executor — Phase 4

Deux étapes séparées :
  1. pytest seul              → pass/fail counts fiables
  2. coverage run <script>    → branch coverage réelle sur le code source
                                (on trace les scripts directement, pas via pytest)
"""
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple


class TestExecutor:

    PYTEST_TIMEOUT = 120
    COV_TIMEOUT    = 30

    def execute(
        self,
        test_file: Path,
        trajectories_data: list = None,
        sut_source_path: Path = None,
    ) -> Dict[str, Any]:

        trajectories_data = trajectories_data or []

        print(f"\n🧪 Executing tests: {test_file.name}")

        # ── Étape 1 : pytest sans --cov ───────────────────────────────────
        pytest_cmd = [
            sys.executable, '-m', 'pytest',
            str(test_file),
            '-v', '--tb=short',
            '-p', 'no:cacheprovider',
        ]
        print(f"   Command: {' '.join(pytest_cmd)}\n")

        try:
            r = subprocess.run(
                pytest_cmd,
                capture_output=True, text=True,
                timeout=self.PYTEST_TIMEOUT,
                cwd=str(test_file.parent),
            )
            pytest_output = r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            pytest_output = "TIMEOUT"

        print("─── pytest output ───────────────────────────────────────")
        print(pytest_output[:3000])
        print("─────────────────────────────────────────────────────────")

        passed, failed, errors = self._parse_counts(pytest_output)
        total = passed + failed + errors

        # ── Étape 2 : coverage.py sur les scripts source ──────────────────
        line_cov, branch_cov_pct = None, None
        if sut_source_path and sut_source_path.exists():
            line_cov, branch_cov_pct = self._run_coverage(sut_source_path)

        # ── Couverture logique depuis les trajectoires ────────────────────
        logical = self._logical_branch_coverage(trajectories_data)

        self._print_summary(total, passed, failed, line_cov, branch_cov_pct, logical)

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': round((passed / total * 100) if total > 0 else 0.0, 1),
            'line_coverage_pct': line_cov,
            'branch_coverage_pct': branch_cov_pct,
            'logical_branch_coverage': logical,
            'simulated': False,
            'pytest_output': pytest_output[-3000:],
        }

    # ------------------------------------------------------------------
    # Coverage — exécution directe des scripts source
    # ------------------------------------------------------------------

    def _run_coverage(self, sut_source_path: Path) -> Tuple:
        """
        Mesure la couverture de branches en exécutant chaque fichier
        source Python directement sous coverage run.

        On n'utilise PAS pytest-cov pour éviter les conflits avec les
        dossiers nommés 'test' ou les conftest parasites.
        """
        py_files = self._find_source_files(sut_source_path)
        if not py_files:
            print("   ⚠️  Aucun fichier source Python trouvé")
            return None, None

        data_file = '/tmp/.kimvi_coverage'

        # Effacer les données précédentes
        subprocess.run(
            [sys.executable, '-m', 'coverage', 'erase', f'--data-file={data_file}'],
            capture_output=True,
        )

        # Tracer chaque fichier source en l'exécutant directement
        for py_file in py_files:
            cmd = [
                sys.executable, '-m', 'coverage', 'run',
                '--branch',
                f'--data-file={data_file}',
                '--append',
                str(py_file),
            ]
            try:
                subprocess.run(
                    cmd,
                    capture_output=True, text=True,
                    timeout=self.COV_TIMEOUT,
                    cwd=str(sut_source_path),
                )
            except Exception:
                pass  # un fichier peut planter, on continue

        # Générer le rapport
        include_list = ','.join(str(f) for f in py_files)
        report_cmd = [
            sys.executable, '-m', 'coverage', 'report',
            f'--data-file={data_file}',
            '--show-missing',
            f'--include={include_list}',
        ]

        try:
            r = subprocess.run(
                report_cmd,
                capture_output=True, text=True,
                timeout=30,
            )
            report = r.stdout + r.stderr
        except Exception as e:
            print(f"   ⚠️  coverage report failed: {e}")
            return None, None

        print("\n─── coverage report ─────────────────────────────────────")
        print(report[:2000])
        print("─────────────────────────────────────────────────────────")

        return self._parse_coverage(report)

    def _find_source_files(self, root: Path) -> List[Path]:
        """Trouve les fichiers Python source (hors tests et caches)."""
        ignore = {'__pycache__', 'venv', '.venv', 'env', '.git',
                  'node_modules', 'dist', 'build', '.pytest_cache'}
        files = []
        for f in sorted(root.rglob('*.py')):
            if any(p in ignore for p in f.parts):
                continue
            if f.name.startswith('test_') or f.name.endswith('_test.py'):
                continue
            files.append(f)
        return files

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    def _parse_counts(self, output: str) -> Tuple[int, int, int]:
        passed = failed = errors = 0
        for m in re.finditer(r'(\d+)\s+(passed|failed|error)', output):
            n, kind = int(m.group(1)), m.group(2)
            if kind == 'passed':   passed = n
            elif kind == 'failed': failed = n
            elif kind == 'error':  errors = n
        return passed, failed, errors

    def _parse_coverage(self, output: str) -> Tuple:
        """
        Parse la sortie de 'coverage report'.
        Avec --branch : TOTAL  Stmts  Miss  Branch  BrPart  Cover%
        Sans --branch : TOTAL  Stmts  Miss  Cover%
        """
        # Avec branches
        m = re.search(
            r'^TOTAL\s+\d+\s+\d+\s+(\d+)\s+\d+\s+(\d+)%',
            output, re.MULTILINE
        )
        if m:
            return int(m.group(2)), int(m.group(2))

        # Sans branches
        m = re.search(r'^TOTAL\s+\d+\s+\d+\s+(\d+)%', output, re.MULTILINE)
        if m:
            return int(m.group(1)), None

        return None, None

    # ------------------------------------------------------------------
    # Couverture logique (depuis les trajectoires)
    # ------------------------------------------------------------------

    def _logical_branch_coverage(self, trajectories_data: list) -> Dict[str, Any]:
        if not trajectories_data:
            return {
                'unique_branches': 0,
                'union_covered': 0,
                'minimal_covered': 0,
                'union_coverage_pct': 0.0,
                'minimal_coverage_pct': 0.0,
            }

        branch_sets: List[Set[Tuple[int, int]]] = []
        for t in trajectories_data:
            edges: Set[Tuple[int, int]] = set()
            for b in t.get('branches_covered', []):
                if isinstance(b, (list, tuple)) and len(b) == 2:
                    edges.add((int(b[0]), int(b[1])))
            branch_sets.append(edges)

        union: Set = set()
        for s in branch_sets:
            union |= s

        intersection: Set = branch_sets[0].copy() if branch_sets else set()
        for s in branch_sets[1:]:
            intersection &= s

        total = len(union)

        return {
            'unique_branches': total,
            'union_covered': len(union),
            'minimal_covered': len(intersection),
            'union_coverage_pct':     100.0 if total == 0 else round(len(union) / total * 100, 1),
            'minimal_coverage_pct':   100.0 if total == 0 else round(len(intersection) / total * 100, 1),
        }

    # ------------------------------------------------------------------
    # Résumé console
    # ------------------------------------------------------------------

    def _print_summary(self, total, passed, failed, line_cov, branch_cov, logical):
        rate = (passed / total * 100) if total > 0 else 0.0

        print(f"\n📊 Execution Results:")
        print(f"   Total  : {total}")
        print(f"   Passed : {passed}")
        print(f"   Failed : {failed}")
        print(f"   Rate   : {rate:.1f}%")

        print(f"\n📈 Branch Coverage:")
        if branch_cov is not None:
            print(f"   coverage.py (branches)   : {branch_cov}%")
        elif line_cov is not None:
            print(f"   coverage.py (lines)      : {line_cov}%")
        else:
            print(f"   coverage.py              : non disponible")

        print(f"   Logical (trajectoires):")
        print(f"      Branches uniques    : {logical['unique_branches']}")
        print(f"      Union  (≥1 traj.)   : {logical['union_covered']}  →  {logical['union_coverage_pct']}%")
        print(f"      Minimal (all traj.) : {logical['minimal_covered']}  →  {logical['minimal_coverage_pct']}%")