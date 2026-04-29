"""
Java Extractor — Vraie analyse symbolique par javalang AST
===========================================================
Chaque trajectoire correspond à UN chemin réel :
  - Les contraintes contiennent les VRAIES conditions Java
    (ex: "x > 0", "obj != null", "i < list.size()")
  - path_condition est la conjonction logique des conditions du chemin.
"""
import javalang
from pathlib import Path
from typing import List, Set, Tuple, Optional
import logging
from dataclasses import dataclass, field

from kimvieware_shared.models import Trajectory

logger = logging.getLogger(__name__)


@dataclass
class CFGNode:
    """Nœud du Control Flow Graph Java."""
    node_id: int
    kind: str
    location: str
    condition: str = ""          # VRAIE condition extraite du code Java
    children: List[int] = field(default_factory=list)
    is_branch: bool = False


# ---------------------------------------------------------------------------
# Sérialisation des expressions javalang → string lisible
# ---------------------------------------------------------------------------

def serialize_expr(node) -> str:
    """
    Convertit un nœud d'expression javalang en string lisible.
    Couvre les cas courants : comparaisons, opérateurs logiques, appels, etc.
    """
    if node is None:
        return "null"

    t = type(node).__name__

    if t == 'BinaryOperation':
        left = serialize_expr(node.operandl)
        right = serialize_expr(node.operandr)
        return f"{left} {node.operator} {right}"

    elif t == 'MemberReference':
        qualifier = f"{node.qualifier}." if node.qualifier else ""
        return f"{qualifier}{node.member}"

    elif t == 'Literal':
        return str(node.value)

    elif t == 'MethodInvocation':
        qualifier = f"{node.qualifier}." if node.qualifier else ""
        args = ", ".join(serialize_expr(a) for a in (node.arguments or []))
        return f"{qualifier}{node.member}({args})"

    elif t == 'ClassCreator':
        args = ", ".join(serialize_expr(a) for a in (node.arguments or []))
        return f"new {node.type.name}({args})"

    elif t == 'ArrayAccess':
        return f"{serialize_expr(node.postfix_operators[0] if node.postfix_operators else node)}[{serialize_expr(node.index)}]"

    elif t == 'Cast':
        return f"({node.type.name}) {serialize_expr(node.expression)}"

    elif t == 'TernaryExpression':
        cond = serialize_expr(node.condition)
        if_true = serialize_expr(node.if_true)
        if_false = serialize_expr(node.if_false)
        return f"{cond} ? {if_true} : {if_false}"

    elif t == 'Assignment':
        return f"{serialize_expr(node.expressionl)} {node.type} {serialize_expr(node.value)}"

    elif hasattr(node, 'value'):
        return str(node.value)

    elif hasattr(node, 'name'):
        return str(node.name)

    return t  # fallback: nom du type de nœud


def serialize_condition(node) -> str:
    """Sérialise la condition d'un if/while/for."""
    if node is None:
        return "true"
    try:
        return serialize_expr(node)
    except Exception:
        return type(node).__name__


# ---------------------------------------------------------------------------
# Extracteur principal
# ---------------------------------------------------------------------------

class JavaExtractor:
    """
    Extrait les chemins d'exécution depuis du code Java avec javalang.

    Améliorations vs version précédente :
      - serialize_expr() convertit les nœuds javalang en conditions lisibles
      - path_condition = vraie formule logique du chemin
      - constraints = vraies conditions Java (pas juste "IfStatement@line")
    """

    BRANCH_TYPES = {
        'IfStatement', 'WhileStatement', 'ForStatement',
        'DoStatement', 'SwitchStatement', 'TryStatement',
        'EnhancedForStatement'
    }

    def __init__(self, max_paths: int = 100):
        self.max_paths = max_paths
        self.next_node_id = 0

    def extract_paths(self, source_dir: Path) -> List[Trajectory]:
        logger.info(f"🔍 Extracting Java paths from {source_dir}")

        java_files = list(source_dir.rglob("*.java"))
        if not java_files:
            logger.warning("No Java source files found")
            return []

        logger.info(f"Found {len(java_files)} .java files")
        all_trajectories = []

        for java_file in java_files:
            logger.info(f"Processing {java_file.name}...")
            try:
                trajs = self._extract_from_file(java_file)
                all_trajectories.extend(trajs)
                logger.info(f"  → {len(trajs)} paths extracted")
            except Exception as e:
                logger.error(f"Error processing {java_file}: {e}")

        logger.info(f"✅ Total paths extracted: {len(all_trajectories)}")

        if len(all_trajectories) > self.max_paths:
            all_trajectories = all_trajectories[:self.max_paths]

        return all_trajectories

    def _extract_from_file(self, file_path: Path) -> List[Trajectory]:
        try:
            code = file_path.read_text(encoding='utf-8', errors='replace')
            tree = javalang.parse.parse(code)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []

        trajectories = []
        methods = [node for _, node in tree.filter(javalang.tree.MethodDeclaration)]
        logger.info(f"  Found {len(methods)} methods")

        for method in methods:
            cfg = self._build_cfg(method)
            paths = self._generate_paths(cfg, method.name)
            for i, path in enumerate(paths):
                traj = self._path_to_trajectory(path, method.name, i)
                trajectories.append(traj)

        return trajectories

    # ------------------------------------------------------------------
    # Construction du CFG avec vraies conditions
    # ------------------------------------------------------------------

    def _build_cfg(self, method_node) -> List[CFGNode]:
        cfg: List[CFGNode] = []
        self.next_node_id = 0

        def create_node(node, is_branch=False, condition="") -> int:
            node_id = self.next_node_id
            self.next_node_id += 1
            kind = type(node).__name__
            loc = str(getattr(node, 'position', 'unknown'))
            cfg.append(CFGNode(
                node_id=node_id,
                kind=kind,
                location=loc,
                condition=condition,
                children=[],
                is_branch=is_branch
            ))
            return node_id

        def visit(node, parent_id=None) -> Optional[int]:
            if node is None:
                return None

            node_type = type(node).__name__
            is_branch = node_type in self.BRANCH_TYPES

            # Extraire la vraie condition
            condition = ""
            if node_type == 'IfStatement':
                condition = serialize_condition(getattr(node, 'condition', None))
            elif node_type == 'WhileStatement':
                condition = serialize_condition(getattr(node, 'condition', None))
            elif node_type == 'ForStatement':
                cond = getattr(node, 'condition', None)
                condition = serialize_condition(cond) if cond else "for_init"
            elif node_type == 'EnhancedForStatement':
                var = getattr(node, 'var', None)
                iter_ = getattr(node, 'iterable', None)
                var_name = getattr(var, 'name', 'var') if var else 'var'
                iter_str = serialize_condition(iter_)
                condition = f"{var_name} : {iter_str}"
            elif node_type == 'DoStatement':
                condition = serialize_condition(getattr(node, 'condition', None))
            elif node_type == 'TryStatement':
                catches = getattr(node, 'catches', []) or []
                exc_types = []
                for c in catches:
                    if hasattr(c, 'parameter') and hasattr(c.parameter, 'types'):
                        exc_types.extend(c.parameter.types)
                condition = f"try (catches: {', '.join(exc_types)})" if exc_types else "try"

            current_id = create_node(node, is_branch, condition)

            if parent_id is not None:
                cfg[parent_id].children.append(current_id)

            # Traversée structurée
            if node_type == 'IfStatement':
                then_stmt = getattr(node, 'then_statement', None)
                else_stmt = getattr(node, 'else_statement', None)
                if then_stmt:
                    visit(then_stmt, current_id)
                if else_stmt:
                    visit(else_stmt, current_id)

            elif node_type in ('WhileStatement', 'DoStatement'):
                body = getattr(node, 'body', None)
                if body:
                    visit(body, current_id)

            elif node_type in ('ForStatement', 'EnhancedForStatement'):
                body = getattr(node, 'body', None)
                if body:
                    visit(body, current_id)

            elif node_type == 'SwitchStatement':
                for case in (getattr(node, 'cases', []) or []):
                    visit(case, current_id)

            elif node_type == 'TryStatement':
                block = getattr(node, 'block', None)
                if block:
                    for stmt in (block if isinstance(block, list) else [block]):
                        visit(stmt, current_id)
                for catch in (getattr(node, 'catches', []) or []):
                    visit(catch, current_id)

            elif node_type == 'BlockStatement':
                for stmt in (getattr(node, 'statements', []) or []):
                    visit(stmt, current_id)

            else:
                # Traversée générique
                if hasattr(node, 'children'):
                    for child in node.children:
                        if child and isinstance(child, javalang.tree.Node):
                            visit(child, current_id)

            return current_id

        body = getattr(method_node, 'body', None)
        if body:
            for stmt in body:
                visit(stmt)

        return cfg

    # ------------------------------------------------------------------
    # DFS pour générer les chemins
    # ------------------------------------------------------------------

    def _generate_paths(self, cfg: List[CFGNode], method_name: str) -> List[List[CFGNode]]:
        if not cfg:
            return []

        paths: List[List[int]] = []
        max_depth = 50

        def dfs(node_id: int, current: List[int], visited: Set[int], depth: int):
            if depth > max_depth or len(paths) >= self.max_paths:
                return
            node = cfg[node_id]
            current.append(node_id)
            if not node.children:
                paths.append(current.copy())
            elif node.is_branch:
                for child_id in node.children:
                    if child_id not in visited:
                        dfs(child_id, current, visited | {child_id}, depth + 1)
            else:
                for child_id in node.children:
                    if child_id not in visited:
                        dfs(child_id, current, visited | {node_id}, depth + 1)
            current.pop()

        dfs(0, [], set(), 0)
        return [[cfg[nid] for nid in path] for path in paths]

    # ------------------------------------------------------------------
    # Conversion chemin → Trajectory
    # ------------------------------------------------------------------

    def _path_to_trajectory(self, path: List[CFGNode], method_name: str, idx: int) -> Trajectory:
        basic_blocks = [node.node_id for node in path]

        branches: Set[Tuple[int, int]] = set()
        for i in range(len(path) - 1):
            if path[i].is_branch:
                branches.add((path[i].node_id, path[i+1].node_id))

        constraints = [
            node.condition
            for node in path
            if node.is_branch and node.condition
        ]

        path_condition = " AND ".join(constraints) if constraints else f"{method_name}_path_{idx}"

        return Trajectory(
            path_id=f"java_{method_name}_path_{idx:03d}",
            basic_blocks=basic_blocks,
            path_condition=path_condition,
            branches_covered=branches,
            constraints=constraints,
            cost=float(len(path)),
            is_feasible=True
        )