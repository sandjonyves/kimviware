"""
Python Extractor — Vraie analyse symbolique par AST
=====================================================
Chaque trajectoire correspond à UN chemin réel dans le code :
  - branche True ou False d'un if/elif/else
  - corps d'une boucle for/while
  - bloc try ou except

Les contraintes contiennent les VRAIES conditions du code source
(ex: "a > b", "x > 0 and y < 10") pas des variables inventées.
"""
import ast
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any, Optional
import logging

from kimvieware_shared.models import Trajectory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Représentation interne d'un nœud de branche
# ---------------------------------------------------------------------------

class BranchNode:
    """Un point de branchement dans le code source."""
    _counter = 0

    def __init__(self, kind: str, condition: str, line: int,
                 true_block_id: int, false_block_id: Optional[int] = None):
        BranchNode._counter += 1
        self.id = BranchNode._counter
        self.kind = kind            # 'if', 'elif', 'for', 'while', 'try'
        self.condition = condition  # vraie condition extraite de l'AST
        self.line = line
        self.true_block_id = true_block_id
        self.false_block_id = false_block_id  # None si pas de else

    def __repr__(self):
        return f"Branch({self.kind}@{self.line}: {self.condition})"


# ---------------------------------------------------------------------------
# Extracteur de chemins par AST
# ---------------------------------------------------------------------------

class RealPathExtractor(ast.NodeVisitor):
    """
    Parcourt l'AST Python et construit tous les chemins d'exécution réels.

    Stratégie :
      Pour chaque nœud If/For/While/Try rencontré :
        - Chemin True  : condition satisfaite → corps du if / boucle
        - Chemin False : condition non satisfaite → bloc else ou suite

    On génère une trajectoire par combinaison de décisions de branches.
    """

    def __init__(self, source_file: Path, max_paths: int = 1000):
        self.source_file = source_file
        self.max_paths = max_paths
        self.branches: List[BranchNode] = []
        self._block_counter = 0
        self.trajectories: List[Trajectory] = []

    def _new_block(self) -> int:
        self._block_counter += 1
        return self._block_counter * 10  # adresses espacées pour lisibilité

    def extract(self) -> List[Trajectory]:
        """Point d'entrée principal."""
        try:
            source = self.source_file.read_text(encoding='utf-8', errors='replace')
            tree = ast.parse(source, filename=str(self.source_file))
        except SyntaxError as e:
            logger.warning(f"SyntaxError in {self.source_file}: {e}")
            return []

        # Collecter toutes les branches du fichier
        self._collect_branches(tree)

        if not self.branches:
            # Fichier sans branche — une seule trajectoire linéaire
            return [self._make_linear_trajectory(source)]

        # Générer les trajectoires par combinaisons de branches
        return self._generate_trajectories()

    # ------------------------------------------------------------------
    # Collecte des branches réelles
    # ------------------------------------------------------------------

    def _collect_branches(self, tree: ast.AST):
        """Parcourt l'AST et collecte toutes les branches réelles."""
        BranchNode._counter = 0
        self._visit_node(tree)

    def _visit_node(self, node: ast.AST):
        """Visite récursive de l'AST."""
        if isinstance(node, ast.If):
            self._handle_if(node)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            self._handle_for(node)
        elif isinstance(node, ast.While):
            self._handle_while(node)
        elif isinstance(node, ast.Try):
            self._handle_try(node)
        else:
            for child in ast.iter_child_nodes(node):
                self._visit_node(child)

    def _handle_if(self, node: ast.If):
        try:
            condition = ast.unparse(node.test)
        except Exception:
            condition = "unknown_condition"

        true_id = self._new_block()
        false_id = self._new_block() if node.orelse else None

        branch = BranchNode(
            kind='if',
            condition=condition,
            line=node.lineno,
            true_block_id=true_id,
            false_block_id=false_id
        )
        self.branches.append(branch)

        # Visiter les sous-blocs pour trouver les branches imbriquées
        for child in node.body:
            self._visit_node(child)
        for child in node.orelse:
            self._visit_node(child)

    def _handle_for(self, node: ast.For):
        try:
            target = ast.unparse(node.target)
            iter_ = ast.unparse(node.iter)
            condition = f"{target} in {iter_}"
        except Exception:
            condition = "for_loop"

        true_id = self._new_block()
        false_id = self._new_block()  # boucle non exécutée (itérable vide)

        branch = BranchNode(
            kind='for',
            condition=condition,
            line=node.lineno,
            true_block_id=true_id,
            false_block_id=false_id
        )
        self.branches.append(branch)

        for child in node.body:
            self._visit_node(child)

    def _handle_while(self, node: ast.While):
        try:
            condition = ast.unparse(node.test)
        except Exception:
            condition = "while_condition"

        true_id = self._new_block()
        false_id = self._new_block()

        branch = BranchNode(
            kind='while',
            condition=condition,
            line=node.lineno,
            true_block_id=true_id,
            false_block_id=false_id
        )
        self.branches.append(branch)

        for child in node.body:
            self._visit_node(child)

    def _handle_try(self, node: ast.Try):
        true_id = self._new_block()   # try réussi
        false_id = self._new_block()  # exception levée

        handlers = [h.type.id if h.type and isinstance(h.type, ast.Name) else 'Exception'
                    for h in node.handlers]
        condition = f"try (except {', '.join(handlers)})" if handlers else "try"

        branch = BranchNode(
            kind='try',
            condition=condition,
            line=node.lineno,
            true_block_id=true_id,
            false_block_id=false_id
        )
        self.branches.append(branch)

        for child in node.body:
            self._visit_node(child)
        for handler in node.handlers:
            for child in handler.body:
                self._visit_node(child)

    # ------------------------------------------------------------------
    # Génération des trajectoires
    # ------------------------------------------------------------------

    def _generate_trajectories(self) -> List[Trajectory]:
        """
        Génère une trajectoire par chemin possible.
        Chaque trajectoire représente une combinaison de décisions (True/False)
        pour chaque branche du code.
        """
        trajectories = []
        n = len(self.branches)

        # Cap : 2^n chemins max mais limité à max_paths
        max_combos = min(self.max_paths, 2 ** min(n, 12))

        for i in range(max_combos):
            # Décision binaire pour chaque branche (bit i = True/False)
            decisions = [(i >> j) & 1 for j in range(n)]

            constraints = []
            basic_blocks = []
            branches_covered: Set[Tuple[int, int]] = set()
            cost = 0.0

            prev_block = 0

            for j, branch in enumerate(self.branches):
                took_true = decisions[j] == 1

                if took_true:
                    constraints.append(branch.condition)
                    block_id = branch.true_block_id
                else:
                    # Négation de la condition
                    neg = self._negate(branch.condition)
                    constraints.append(neg)
                    block_id = branch.false_block_id if branch.false_block_id else branch.true_block_id + 1

                basic_blocks.append(block_id)
                branches_covered.add((prev_block, block_id))
                prev_block = block_id
                cost += 0.5 + (0.1 * branch.line)

            path_condition = " AND ".join(constraints) if constraints else "true"

            traj = Trajectory(
                path_id=f"py_path_{i:05d}",
                basic_blocks=basic_blocks,
                path_condition=path_condition,
                branches_covered=branches_covered,
                constraints=constraints,
                cost=round(cost, 3),
                is_feasible=True
            )
            trajectories.append(traj)

        return trajectories

    def _make_linear_trajectory(self, source: str) -> Trajectory:
        """Trajectoire unique pour un fichier sans branche."""
        lines = source.splitlines()
        return Trajectory(
            path_id="py_path_00000",
            basic_blocks=[10, 20],
            path_condition="true",
            branches_covered=set(),
            constraints=[],
            cost=float(len(lines)),
            is_feasible=True
        )

    @staticmethod
    def _negate(condition: str) -> str:
        """Négation simple d'une condition."""
        # Conditions simples à inverser directement
        negations = {
            '>': '<=', '>=': '<', '<': '>=', '<=': '>',
            '==': '!=', '!=': '=='
        }
        for op, neg_op in negations.items():
            if f' {op} ' in condition and '==' not in condition.replace(op, ''):
                return condition.replace(f' {op} ', f' {neg_op} ', 1)
        return f"not ({condition})"


# ---------------------------------------------------------------------------
# Extracteur principal
# ---------------------------------------------------------------------------

class PythonExtractor:
    """
    Python symbolic execution extractor — vraie analyse AST.

    Chaque trajectoire représente un chemin réel avec les vraies conditions
    du code source comme contraintes.
    """

    def __init__(self, timeout: int = 120, max_paths: int = 1000):
        self.timeout = timeout
        self.max_paths = max_paths

    def extract_paths(self, service_path: Path) -> List[Trajectory]:
        """Extraire les chemins symboliques depuis un projet Python."""

        logger.info(f"\n{'='*60}")
        logger.info(f" Python Symbolic Execution — Vraie analyse AST")
        logger.info(f"{'='*60}")
        logger.info(f" Service: {service_path}")

        if not service_path.exists():
            logger.error(f"Path does not exist: {service_path}")
            return []

        py_files = self._find_python_files(service_path)
        logger.info(f"📊 Files: {len(py_files)}")

        all_trajectories = []
        file_path_budget = max(1, self.max_paths // max(1, len(py_files)))

        for py_file in py_files:
            logger.info(f"  Analyzing {py_file.name}...")
            extractor = RealPathExtractor(py_file, max_paths=file_path_budget)
            trajs = extractor.extract()

            # Préfixer les path_ids avec le nom du fichier
            stem = py_file.stem
            for j, t in enumerate(trajs):
                t.path_id = f"py_{stem}_{j:04d}"

            all_trajectories.extend(trajs)
            logger.info(f"    → {len(trajs)} trajectoires (branches: {len(extractor.branches)})")

        # Limiter au max global
        if len(all_trajectories) > self.max_paths:
            all_trajectories = all_trajectories[:self.max_paths]

        logger.info(f"\n✅ Total: {len(all_trajectories)} trajectoires extraites")
        logger.info(f"{'='*60}\n")

        return all_trajectories

    def _find_python_files(self, service_path: Path) -> List[Path]:
        """Trouver les fichiers Python source (hors venv, tests, cache)."""
        ignore_dirs = {
            'venv', '.venv', 'env', '.env', 'node_modules',
            '__pycache__', '.git', '.pytest_cache', '.idea', '.vscode',
            'site-packages', 'dist', 'build', 'migrations'
        }
        py_files = []
        for f in service_path.rglob('*.py'):
            if any(p in ignore_dirs for p in f.parts):
                continue
            if 'test_' in f.name or '_test' in f.name or f.name == '__init__.py':
                continue
            py_files.append(f)
        return sorted(py_files)

    # Conservé pour compatibilité avec ExtractorBase
    def find_entry_point(self, service_path: Path) -> Optional[Path]:
        candidates = ['main.py', 'app.py', '__main__.py', 'run.py', 'start.py']
        for name in candidates:
            p = service_path / name
            if p.exists():
                return p
        for f in service_path.rglob('*.py'):
            if '__pycache__' not in str(f):
                return f
        return None