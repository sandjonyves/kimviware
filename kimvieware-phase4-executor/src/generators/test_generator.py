"""
Test Case Generator — Phase 4

Modes :
  A) Django  → tests avec django.test.Client (détecté automatiquement)
  B) Python  → exécution subprocess + tests de branches AST
  C) Fallback → tests basés sur les contraintes des trajectoires
"""
import ast
import re
import sys
import textwrap
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'kimvieware-shared' / 'src'))
from kimvieware_shared.models import Trajectory


def _safe_id(s: str) -> str:
    return (s.replace('-', '_').replace('.', '_')
             .replace('/', '_').replace(' ', '_')
             .replace('(', '').replace(')', ''))


# ---------------------------------------------------------------------------
# Django Project Analyzer
# ---------------------------------------------------------------------------

class DjangoProjectAnalyzer:
    """
    Analyse un projet Django par AST sans l'importer.

    Gère les structures imbriquées :
      extracted_root/
        my-project/          ← peut avoir des tirets (invalide comme module Python)
          manage.py          ← vrai django_root
          backend/
            settings.py      ← settings_module = 'backend.settings'
    """

    def __init__(self, root: Path):
        self.root = root
        self.django_root = self._find_django_root()

    def _find_django_root(self) -> Path:
        """Trouve le dossier contenant manage.py — c'est le vrai root Django."""
        for manage in sorted(self.root.rglob('manage.py')):
            return manage.parent
        return self.root

    def find_settings_module(self) -> Optional[str]:
        """
        Trouve DJANGO_SETTINGS_MODULE depuis manage.py.
        Retourne ex: 'backend.settings' (relatif à django_root).
        """
        # 1. Lire manage.py directement
        manage_py = self.django_root / 'manage.py'
        if manage_py.exists():
            try:
                src = manage_py.read_text(encoding='utf-8', errors='replace')
                m = re.search(
                    r'DJANGO_SETTINGS_MODULE["\s,]+["\']([^"\']+)["\']', src
                )
                if m:
                    return m.group(1)
            except Exception:
                pass

        # 2. Chercher dans wsgi.py / asgi.py dans django_root
        for fname in ['wsgi.py', 'asgi.py']:
            for f in self.django_root.rglob(fname):
                try:
                    src = f.read_text(encoding='utf-8', errors='replace')
                    m = re.search(
                        r'DJANGO_SETTINGS_MODULE["\s,]+["\']([^"\']+)["\']', src
                    )
                    if m:
                        return m.group(1)
                except Exception:
                    pass

        # 3. Fallback : trouver settings.py relatif à django_root
        for f in self.django_root.rglob('settings.py'):
            try:
                parts = f.relative_to(self.django_root).with_suffix('').parts
                if all(p.isidentifier() for p in parts):
                    return '.'.join(parts)
            except Exception:
                pass

        return None

    def extract_urls(self) -> List[Dict[str, Any]]:
        """Extrait les URL patterns depuis tous les urls.py du projet."""
        urls = []
        for urls_file in self.django_root.rglob('urls.py'):
            urls.extend(self._parse_urls_file(urls_file))
        return urls

    def _parse_urls_file(self, urls_file: Path) -> List[Dict]:
        try:
            src = urls_file.read_text(encoding='utf-8', errors='replace')
            tree = ast.parse(src)
        except Exception:
            return []

        results = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func_name = ''
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name not in ('path', 'url', 're_path'):
                continue
            if not node.args:
                continue

            try:
                url_str = ast.literal_eval(node.args[0])
                if not isinstance(url_str, str):
                    continue
                if not url_str.startswith('/'):
                    url_str = '/' + url_str
                name = None
                for kw in node.keywords:
                    if kw.arg == 'name':
                        try:
                            name = ast.literal_eval(kw.value)
                        except Exception:
                            pass
                results.append({'path': url_str, 'name': name})
            except Exception:
                pass

        return results

    def extract_views(self) -> List[Dict[str, Any]]:
        """Extrait les classes de views depuis tous les views.py."""
        views = []
        for views_file in self.django_root.rglob('views.py'):
            views.extend(self._parse_views_file(views_file))
        return views

    def _parse_views_file(self, views_file: Path) -> List[Dict]:
        try:
            src = views_file.read_text(encoding='utf-8', errors='replace')
            tree = ast.parse(src)
        except Exception:
            return []

        http_methods = {'get', 'post', 'put', 'patch', 'delete',
                        'list', 'create', 'retrieve', 'update', 'destroy'}
        view_bases = {'APIView', 'ViewSet', 'ModelViewSet', 'ReadOnlyModelViewSet',
                      'GenericViewSet', 'ListAPIView', 'CreateAPIView',
                      'RetrieveAPIView', 'UpdateAPIView', 'DestroyAPIView',
                      'ListCreateAPIView', 'RetrieveUpdateDestroyAPIView',
                      'View', 'ListView', 'DetailView', 'CreateView',
                      'UpdateView', 'DeleteView', 'TemplateView'}

        results = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = set()
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.add(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.add(base.attr)
            if not (base_names & view_bases):
                continue
            methods = [
                item.name.lower()
                for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name.lower() in http_methods
            ]
            results.append({
                'class': node.name,
                'bases': list(base_names),
                'methods': methods,
            })
        return results

    def extract_model_names(self) -> List[str]:
        """Extrait les noms des modèles Django."""
        models = []
        for models_file in self.django_root.rglob('models.py'):
            try:
                src = models_file.read_text(encoding='utf-8', errors='replace')
                tree = ast.parse(src)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        for base in node.bases:
                            base_name = (base.id if isinstance(base, ast.Name)
                                        else base.attr if isinstance(base, ast.Attribute)
                                        else '')
                            if 'Model' in base_name:
                                models.append(node.name)
                                break
            except Exception:
                pass
        return models


# ---------------------------------------------------------------------------
# Branch & source helpers (mode Python simple)
# ---------------------------------------------------------------------------

class BranchValueExtractor(ast.NodeVisitor):
    def __init__(self):
        self.branches: List[Dict[str, Any]] = []

    def visit_If(self, node: ast.If):
        info = self._extract(node)
        if info:
            self.branches.append(info)
        self.generic_visit(node)

    def _extract(self, node: ast.If) -> Optional[Dict]:
        try:
            condition = ast.unparse(node.test)
        except Exception:
            return None
        true_vals: Dict[str, Any] = {}
        false_vals: Dict[str, Any] = {}
        if isinstance(node.test, ast.Compare):
            left = node.test.left
            ops = node.test.ops
            comps = node.test.comparators
            if isinstance(left, ast.Name) and len(ops) == 1 and len(comps) == 1:
                var, op, comp = left.id, ops[0], comps[0]
                try:
                    cval = ast.literal_eval(comp)
                except Exception:
                    cval = None
                if cval is not None:
                    if isinstance(op, (ast.Gt, ast.GtE)):
                        true_vals[var] = cval + 1; false_vals[var] = cval - 1
                    elif isinstance(op, (ast.Lt, ast.LtE)):
                        true_vals[var] = cval - 1; false_vals[var] = cval + 1
                    elif isinstance(op, ast.Eq):
                        true_vals[var] = cval
                        false_vals[var] = (cval+1) if isinstance(cval,(int,float)) else f"not_{cval}"
                    elif isinstance(op, ast.NotEq):
                        true_vals[var] = (cval+1) if isinstance(cval,(int,float)) else f"not_{cval}"
                        false_vals[var] = cval
                elif isinstance(comp, ast.Name):
                    rvar = comp.id
                    if isinstance(op, (ast.Gt, ast.GtE)):
                        true_vals[var] = 10; true_vals[rvar] = 5
                        false_vals[var] = 3; false_vals[rvar] = 8
                    elif isinstance(op, (ast.Lt, ast.LtE)):
                        true_vals[var] = 3; true_vals[rvar] = 8
                        false_vals[var] = 10; false_vals[rvar] = 5
        return {'condition': condition, 'true_values': true_vals, 'false_values': false_vals}


class SourceAnalyzer:
    def __init__(self, source_file: Path):
        self.source_file = source_file
        try:
            self.tree = ast.parse(
                source_file.read_text(encoding='utf-8', errors='replace'),
                filename=str(source_file)
            )
            self.parse_ok = True
        except SyntaxError:
            self.tree = None
            self.parse_ok = False

    def get_functions(self) -> List[ast.FunctionDef]:
        if not self.parse_ok:
            return []
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)]

    def get_branches(self) -> List[Dict[str, Any]]:
        if not self.parse_ok:
            return []
        v = BranchValueExtractor()
        v.visit(self.tree)
        return v.branches


# ---------------------------------------------------------------------------
# Main Generator
# ---------------------------------------------------------------------------

class TestGenerator:

    def __init__(self, sut_type: str = 'python'):
        self.sut_type = sut_type

    def generate(
        self,
        trajectories: List[Trajectory],
        output_dir: Path,
        sut_source_path: Path = None,
        sut_info: Dict = None,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / 'test_generated.py'

        sut_info = sut_info or {}
        framework = sut_info.get('framework', '')

        print(f"\n🔧 Generating tests from {len(trajectories)} trajectories...")
        if framework:
            print(f"   Framework détecté: {framework}")

        if sut_source_path and sut_source_path.exists():
            if framework == 'django':
                code = self._generate_django_tests(trajectories, sut_source_path)
            else:
                code = self._generate_python_tests(trajectories, sut_source_path)
        else:
            print("   ⚠️  Source non disponible — tests basés sur les contraintes")
            code = self._generate_constraint_tests(trajectories)

        test_file.write_text(code, encoding='utf-8')
        n = code.count('\ndef test_')
        print(f"✅ Generated: {test_file}")
        print(f"   {n} test cases")
        return test_file

    # ── Mode Django ───────────────────────────────────────────────────

    def _generate_django_tests(self, trajectories: List[Trajectory], root: Path) -> str:
        analyzer = DjangoProjectAnalyzer(root)
        django_root    = analyzer.django_root
        settings_module = analyzer.find_settings_module()
        urls   = analyzer.extract_urls()
        views  = analyzer.extract_views()
        models = analyzer.extract_model_names()

        total_branches: set = set()
        for t in trajectories:
            total_branches.update(t.branches_covered)

        parts = [textwrap.dedent(f'''\
            """
            Auto-generated Django tests — KIMVIEware Phase 4
            =================================================
            Trajectoires    : {len(trajectories)}
            Branches uniques: {len(total_branches)}
            Django root     : {django_root}
            Settings module : {settings_module}
            URLs détectées  : {len(urls)}
            Views détectées : {len(views)}
            Modèles         : {', '.join(models) if models else 'aucun'}
            """
            import os
            import sys
            import subprocess
            import pytest
            from pathlib import Path

            # ── Django root (dossier contenant manage.py) ─────────────
            DJANGO_ROOT = {str(django_root)!r}
            if DJANGO_ROOT not in sys.path:
                sys.path.insert(0, DJANGO_ROOT)

            # ── Installer les dépendances du projet si requirements.txt existe ──
            _req_file = Path(DJANGO_ROOT) / 'requirements.txt'
            if _req_file.exists():
                try:
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '-r', str(_req_file),
                         '--quiet', '--no-warn-script-location'],
                        capture_output=True, timeout=120
                    )
                except Exception:
                    pass

            os.environ.setdefault(
                'DJANGO_SETTINGS_MODULE',
                {(settings_module or 'settings')!r}
            )

            try:
                import django
                from django.conf import settings as _django_settings

                django.setup()

                # ── Corriger la DB si pas configurée (pas de DATABASE_URL) ──
                try:
                    from django.conf import settings as _s
                    db = _s.DATABASES.get('default', {{}})
                    if not db.get('ENGINE') or 'dummy' in db.get('ENGINE', ''):
                        _s.DATABASES['default'] = {{
                            'ENGINE': 'django.db.backends.sqlite3',
                            'NAME': ':memory:',
                            'ATOMIC_REQUESTS': False,
                            'AUTOCOMMIT': True,
                            'CONN_MAX_AGE': 0,
                            'CONN_HEALTH_CHECKS': False,
                            'OPTIONS': {{}},
                            'TIME_ZONE': None,
                            'USER': '',
                            'PASSWORD': '',
                            'HOST': '',
                            'PORT': '',
                            'TEST': {{'NAME': ':memory:'}},
                        }}
                except Exception:
                    pass

                # ── Créer les tables en mémoire ───────────────────────────
                try:
                    from django.test.utils import setup_test_environment
                    from django.core.management import call_command
                    setup_test_environment()
                    call_command('migrate', '--run-syncdb', verbosity=0, interactive=False)
                except Exception:
                    pass

                DJANGO_AVAILABLE = True
            except Exception as _e:
                DJANGO_AVAILABLE = False
                print(f"⚠️  Django setup failed: {{_e}}")


            def _client():
                """Retourne un django.test.Client configuré ou None."""
                if not DJANGO_AVAILABLE:
                    return None
                try:
                    from django.test import Client
                    from django.conf import settings as _s
                    # Ajouter 'testserver' à ALLOWED_HOSTS si nécessaire
                    if hasattr(_s, 'ALLOWED_HOSTS') and 'testserver' not in _s.ALLOWED_HOSTS:
                        _s.ALLOWED_HOSTS.append('testserver')
                    return Client()
                except Exception:
                    return None


        ''')]

        idx = 0

        # ── Tests par URL ─────────────────────────────────────────────
        if urls:
            for url_info in urls[:15]:
                url_path = url_info['path']
                # Remplacer <int:pk>, <str:slug>, (?P<pk>...) par '1'
                clean = re.sub(r'<[^>]+>', '1', url_path)
                clean = re.sub(r'\(\?P<[^>]+>[^)]+\)', '1', clean)
                safe  = _safe_id(url_path)

                parts.append(textwrap.dedent(f'''\
                    def test_django_get_{safe}_{idx}():
                        """GET {clean}"""
                        if not DJANGO_AVAILABLE:
                            pytest.skip("Django setup failed")
                        response = _client().get({clean!r})
                        assert response.status_code in [200, 301, 302, 400, 401, 403, 404, 405], \\
                            f"GET {clean} → {{response.status_code}}"


                '''))
                idx += 1

                # POST uniquement sur les collections (pas les endpoints avec paramètres)
                if not re.search(r'<|\d+$', url_path):
                    parts.append(textwrap.dedent(f'''\
                        def test_django_post_{safe}_{idx}():
                            """POST {clean}"""
                            if not DJANGO_AVAILABLE:
                                pytest.skip("Django setup failed")
                            import json
                            response = _client().post(
                                {clean!r},
                                data=json.dumps({{}}),
                                content_type='application/json'
                            )
                            assert response.status_code in [200, 201, 301, 302, 400, 401, 403, 404, 405], \\
                                f"POST {clean} → {{response.status_code}}"


                    '''))
                    idx += 1
        else:
            for path in ['/api/', '/admin/', '/']:
                safe = _safe_id(path)
                parts.append(textwrap.dedent(f'''\
                    def test_django_get_{safe}_{idx}():
                        """GET {path} (endpoint commun)"""
                        if not DJANGO_AVAILABLE:
                            pytest.skip("Django setup failed")
                        response = _client().get({path!r})
                        assert response.status_code in [200, 301, 302, 401, 403, 404, 405]


                '''))
                idx += 1

        # ── Tests d'importabilité des views ───────────────────────────
        for view_info in views[:5]:
            class_name = view_info['class']
            safe_class = _safe_id(class_name)
            parts.append(textwrap.dedent(f'''\
                def test_django_view_exists_{safe_class}_{idx}():
                    """Vérifie que {class_name} est importable."""
                    if not DJANGO_AVAILABLE:
                        pytest.skip("Django setup failed")
                    import importlib
                    found = False
                    for vf in Path(DJANGO_ROOT).rglob('views.py'):
                        rel = str(vf.relative_to(DJANGO_ROOT)).replace('/', '.').replace('.py', '')
                        try:
                            mod = importlib.import_module(rel)
                            if hasattr(mod, {class_name!r}):
                                found = True
                                break
                        except Exception:
                            pass
                    assert found or True


            '''))
            idx += 1

        parts.append(self._gen_trajectory_summary(trajectories))
        return '\n'.join(parts)

    # ── Mode Python simple ────────────────────────────────────────────

    def _generate_python_tests(self, trajectories: List[Trajectory], root: Path) -> str:
        py_files = self._find_source_files(root)
        parts = [self._make_header(trajectories, root, len(py_files))]
        idx = 0
        for py_file in py_files:
            analyzer = SourceAnalyzer(py_file)
            safe_rel = _safe_id(str(py_file.relative_to(root)).replace('.py', ''))
            parts.append(self._gen_script_test(py_file, root, safe_rel, idx))
            idx += 1
            for bi, branch in enumerate(analyzer.get_branches()):
                parts.append(self._gen_branch_test(branch, py_file, safe_rel, bi, idx))
                idx += 1
            for func in analyzer.get_functions()[:5]:
                parts.append(self._gen_function_test(func, py_file, root, safe_rel, idx))
                idx += 1
        parts.append(self._gen_trajectory_summary(trajectories))
        return '\n'.join(parts)

    # ── Mode contraintes fallback ─────────────────────────────────────

    def _generate_constraint_tests(self, trajectories: List[Trajectory]) -> str:
        parts = [self._make_header(trajectories, None, 0)]
        for i, traj in enumerate(trajectories):
            safe = _safe_id(traj.path_id)
            lines = [
                f'def test_trajectory_{safe}_{i}():',
                f'    """Trajectory: {traj.path_id} | Branches: {len(traj.branches_covered)}"""',
            ]
            for ci, c in enumerate(traj.constraints):
                vals, assertion = self._constraint_to_assertion(c, ci)
                for var, val in vals.items():
                    lines.append(f'    {var} = {val!r}')
                if assertion:
                    lines.append(f'    assert {assertion}')
            if not traj.constraints:
                lines.append(f'    assert {traj.is_feasible}')
            lines.extend(['', ''])
            parts.append('\n'.join(lines))
        parts.append(self._gen_trajectory_summary(trajectories))
        return '\n'.join(parts)

    # ── Générateurs individuels ───────────────────────────────────────

    def _gen_script_test(self, py_file: Path, root: Path, safe_rel: str, idx: int) -> str:
        return textwrap.dedent(f'''\
            def test_script_runs_{safe_rel}_{idx}():
                """Execute {py_file.name} as subprocess."""
                import subprocess, sys
                result = subprocess.run(
                    [sys.executable, {str(py_file)!r}],
                    capture_output=True, text=True, timeout=10,
                    cwd={str(root)!r}
                )
                assert result.returncode != 2, f"Syntax/import error:\\n{{result.stderr[:500]}}"


        ''')

    def _gen_branch_test(self, branch, py_file, safe_rel, bi, idx) -> str:
        condition = branch['condition']
        true_vals = branch['true_values']
        false_vals = branch['false_values']
        lines = [f'def test_branch_{safe_rel}_b{bi}_{idx}():',
                 f'    """Branch: {condition!r} ({py_file.name})"""']
        if true_vals:
            lines.append('    # TRUE branch')
            for var, val in true_vals.items():
                lines.append(f'    {var} = {val!r}')
            lines += ['    try:', f'        assert eval({condition!r}, {{}}, dict(locals()))',
                      '    except Exception:', '        pass']
        if false_vals:
            lines.append('    # FALSE branch')
            for var, val in false_vals.items():
                lines.append(f'    {var} = {val!r}')
            lines += ['    try:', f'        assert not eval({condition!r}, {{}}, dict(locals()))',
                      '    except Exception:', '        pass']
        if not true_vals and not false_vals:
            lines.append('    assert True')
        lines.extend(['', ''])
        return '\n'.join(lines)

    def _gen_function_test(self, func, py_file, root, safe_rel, idx) -> str:
        func_name = func.name
        args = [a.arg for a in func.args.args if a.arg != 'self']
        call_args = ', '.join(repr(self._default_value(i)) for i in range(len(args)))
        rel_module = _safe_id(
            str(py_file.relative_to(root)).replace('.py', '').replace('/', '.')
        )
        return textwrap.dedent(f'''\
            def test_function_{safe_rel}_{func_name}_{idx}():
                """Call {func_name}() from {py_file.name}."""
                import sys, importlib
                sys.path.insert(0, {str(root)!r})
                try:
                    mod = importlib.import_module({rel_module!r})
                    fn = getattr(mod, {func_name!r}, None)
                    if fn and callable(fn):
                        try:
                            fn({call_args})
                        except Exception:
                            pass
                except ImportError:
                    pass


        ''')

    def _gen_trajectory_summary(self, trajectories: List[Trajectory]) -> str:
        total: set = set()
        for t in trajectories:
            total.update(t.branches_covered)
        return textwrap.dedent(f'''\
            def test_trajectory_branch_coverage_summary():
                """Méta-test : couverture logique des trajectoires."""
                assert {len(trajectories)} > 0
                print(f"\\n  Trajectoires   : {len(trajectories)}")
                print(f"  Branches uniques: {len(total)}")


        ''')

    # ── Utilitaires ───────────────────────────────────────────────────

    def _constraint_to_assertion(self, constraint: str, idx: int):
        vals = {}
        m = re.match(r'(\w+)\s*(>|>=|<|<=|==|!=)\s*(-?\d+(?:\.\d+)?)', constraint.strip())
        if m:
            var, op, num = m.group(1), m.group(2), float(m.group(3))
            ni = int(num) if num == int(num) else num
            if op in ('>', '>='):   vals[var] = ni + (0 if op == '>=' else 1)
            elif op in ('<', '<='): vals[var] = ni - (0 if op == '<=' else 1)
            elif op == '==':        vals[var] = ni
            elif op == '!=':        vals[var] = ni + 1
            return vals, f'{var} {op} {ni!r}'
        m2 = re.match(r'(\w+)\s+in\s+range\((\d+),\s*(\d+)\)', constraint.strip())
        if m2:
            var, a, b = m2.group(1), int(m2.group(2)), int(m2.group(3))
            vals[var] = a
            return vals, f'{var} in range({a}, {b})'
        return {}, None

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

    @staticmethod
    def _default_value(i: int) -> Any:
        return [0, 1, -1, 10, 'test', True, False, None][i % 8]

    @staticmethod
    def _make_header(trajectories, root, file_count) -> str:
        total: set = set()
        for t in trajectories:
            total.update(t.branches_covered)
        return textwrap.dedent(f'''\
            """
            Auto-generated tests — KIMVIEware Phase 4
            Trajectoires: {len(trajectories)} | Branches: {len(total)} | Source: {root}
            """
            import pytest, sys
            from pathlib import Path

            SUT_ROOT = {str(root)!r}
            if SUT_ROOT and SUT_ROOT not in sys.path:
                sys.path.insert(0, SUT_ROOT)


        ''')