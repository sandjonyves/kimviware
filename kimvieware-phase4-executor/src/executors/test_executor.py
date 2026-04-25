"""
Test Executor — Phase 4

Stratégie coverage :
  - Django  : coverage run -m pytest <test_file> avec conftest.py qui configure Django
              → trace views.py, serializers.py, permissions.py via appels HTTP réels
  - Python  : coverage run <script.py> directement pour chaque fichier source
"""
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple


class TestExecutor:

    PYTEST_TIMEOUT = 120
    COV_TIMEOUT    = 90

    def execute(
        self,
        test_file: Path,
        trajectories_data: list = None,
        sut_source_path: Path = None,
        sut_info: dict = None,
    ) -> Dict[str, Any]:

        trajectories_data = trajectories_data or []
        sut_info = sut_info or {}
        framework = sut_info.get('framework', '')

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

        # ── Étape 2 : coverage ────────────────────────────────────────────
        line_cov, branch_cov_pct = None, None
        if sut_source_path and sut_source_path.exists():
            if framework == 'django':
                line_cov, branch_cov_pct = self._run_coverage_django(
                    test_file, sut_source_path
                )
            else:
                line_cov, branch_cov_pct = self._run_coverage_scripts(sut_source_path)

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
    # Coverage Django — via pytest (trace les appels HTTP)
    # ------------------------------------------------------------------

    def _run_coverage_django(self, test_file: Path, sut_source_path: Path) -> Tuple:
        """
        Lance coverage run -m pytest sur le test_file Django.

        Pour éviter le conflit avec le dossier 'test/' dans le projet,
        on crée un conftest.py minimal dans le dossier tmp du test
        et on pointe --ignore vers le projet SUT.
        """
        data_file = '/tmp/.kimvi_coverage'

        # Effacer les données précédentes
        subprocess.run(
            [sys.executable, '-m', 'coverage', 'erase', f'--data-file={data_file}'],
            capture_output=True,
        )

        # Trouver le django_root (dossier avec manage.py)
        django_root = self._find_django_root(sut_source_path)
        cov_source = str(django_root) if django_root else str(sut_source_path)

        # Créer un conftest.py dans le dossier du test pour isoler pytest
        conftest = test_file.parent / 'conftest.py'
        conftest.write_text(
            '# conftest.py — généré par KIMVIEware Phase 4\n'
            'collect_ignore_glob = []\n',
            encoding='utf-8'
        )

        # Lancer coverage run -m pytest avec --source pointant vers le django_root
        cmd = [
            sys.executable, '-m', 'coverage', 'run',
            '--branch',
            f'--source={cov_source}',
            f'--data-file={data_file}',
            '-m', 'pytest',
            str(test_file),
            '-q', '--tb=no',
            '-p', 'no:cacheprovider',
            '--no-header',
            f'--rootdir={test_file.parent}',
            f'--ignore={cov_source}',   # évite que pytest collecte le projet SUT
        ]

        print(f"\n📐 Coverage Django: coverage run -m pytest ...")
        try:
            subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=self.COV_TIMEOUT,
                cwd=str(test_file.parent),
            )
        except Exception as e:
            print(f"   ⚠️  coverage run failed: {e}")
            return None, None

        return self._report_coverage(data_file, cov_source)

    def _find_django_root(self, root: Path) -> Path | None:
        """Trouve le dossier contenant manage.py."""
        for manage in sorted(root.rglob('manage.py')):
            return manage.parent
        return None

    # ------------------------------------------------------------------
    # Coverage Python simple — exécution directe des scripts
    # ------------------------------------------------------------------

    def _run_coverage_scripts(self, sut_source_path: Path) -> Tuple:
        """Trace chaque fichier Python source en l'exécutant directement."""
        py_files = self._find_source_files(sut_source_path)
        if not py_files:
            return None, None

        data_file = '/tmp/.kimvi_coverage'
        subprocess.run(
            [sys.executable, '-m', 'coverage', 'erase', f'--data-file={data_file}'],
            capture_output=True,
        )

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
                    cmd, capture_output=True, text=True,
                    timeout=self.COV_TIMEOUT,
                    cwd=str(sut_source_path),
                )
            except Exception:
                pass

        include_list = ','.join(str(f) for f in py_files)
        return self._report_coverage(data_file, None, include_list)

    # ------------------------------------------------------------------
    # Rapport coverage commun
    # ------------------------------------------------------------------

    def _report_coverage(
        self,
        data_file: str,
        source: str = None,
        include: str = None,
    ) -> Tuple:
        """Lance 'coverage report' et parse le résultat."""
        report_cmd = [
            sys.executable, '-m', 'coverage', 'report',
            f'--data-file={data_file}',
            '--show-missing',
        ]
        if source:
            report_cmd.append(f'--include={source}/*')
        if include:
            report_cmd.append(f'--include={include}')

        try:
            r = subprocess.run(
                report_cmd,
                capture_output=True, text=True, timeout=30,
            )
            report = r.stdout + r.stderr
        except Exception as e:
            print(f"   ⚠️  coverage report failed: {e}")
            return None, None

        print("\n─── coverage report ─────────────────────────────────────")
        print(report[:3000])
        print("─────────────────────────────────────────────────────────")

        return self._parse_coverage(report)

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
        # Avec branches : TOTAL  Stmts  Miss  Branch  BrPart  Cover%
        m = re.search(
            r'^TOTAL\s+\d+\s+\d+\s+(\d+)\s+\d+\s+(\d+)%',
            output, re.MULTILINE
        )
        if m:
            return int(m.group(2)), int(m.group(2))

        # Sans branches : TOTAL  Stmts  Miss  Cover%
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
            'union_coverage_pct':   100.0 if total == 0 else round(len(union) / total * 100, 1),
            'minimal_coverage_pct': 100.0 if total == 0 else round(len(intersection) / total * 100, 1),
        }

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _find_source_files(self, root: Path) -> List[Path]:
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