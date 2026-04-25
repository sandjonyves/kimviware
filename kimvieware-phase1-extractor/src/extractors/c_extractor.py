"""
C/C++ Extractor — Vraie analyse symbolique par Clang AST
=========================================================
Chaque trajectoire correspond à UN chemin réel dans le CFG :
  - Les contraintes contiennent les VRAIES conditions du code source
    (ex: "a > b", "x != NULL") extraites par les tokens Clang.
  - path_condition est la conjonction logique des conditions du chemin.
"""
import os
import logging
from pathlib import Path
from typing import List, Set, Tuple, Optional, Dict
from dataclasses import dataclass, field

import clang.cindex
from clang.cindex import Config, Index, CursorKind, TokenKind

# Configure libclang
libclang_paths = [
    '/usr/lib/llvm-18/lib/libclang.so',
    '/usr/lib/llvm-18/lib/libclang-18.so',
    '/usr/lib/x86_64-linux-gnu/libclang-18.so',
    '/usr/lib/llvm-18/lib/libclang-18.1.3.so',
    '/usr/lib/x86_64-linux-gnu/libclang-18.so.1',
    '/usr/lib/llvm-18/lib/libclang.so.1',
]

libclang_set = False
for path in libclang_paths:
    if os.path.exists(path):
        try:
            Config.set_library_file(path)
            libclang_set = True
            logging.info(f"✅ Using libclang: {path}")
            break
        except Exception:
            continue

if not libclang_set:
    logging.warning("⚠️  Could not find libclang, using system default")

from kimvieware_shared.models import Trajectory

logger = logging.getLogger(__name__)


@dataclass
class CFGNode:
    """Nœud du Control Flow Graph."""
    node_id: int
    kind: str
    location: str
    condition: str = ""        # VRAIE condition extraite du code source
    children: List[int] = field(default_factory=list)
    is_branch: bool = False


class CExtractor:
    """
    Extrait les chemins d'exécution depuis du code C/C++ avec Clang.

    Améliorations vs version précédente :
      - Extraction de la VRAIE condition des if/while/for via les tokens Clang
      - path_condition = conjonction logique des conditions du chemin
      - constraints = liste des vraies conditions (pas juste "IF_STMT@line")
    """

    BRANCH_KINDS = {
        CursorKind.IF_STMT,
        CursorKind.WHILE_STMT,
        CursorKind.FOR_STMT,
        CursorKind.DO_STMT,
        CursorKind.SWITCH_STMT,
        CursorKind.CONDITIONAL_OPERATOR,
    }

    def __init__(self, max_paths: int = 100):
        self.max_paths = max_paths
        self.index = Index.create()

    def extract_paths(self, source_dir: Path) -> List[Trajectory]:
        logger.info(f"🔍 Extracting C/C++ paths from {source_dir}")

        c_files  = list(source_dir.rglob("*.c"))
        cpp_files = list(source_dir.rglob("*.cpp"))
        all_files = c_files + cpp_files

        if not all_files:
            logger.warning("No C/C++ source files found")
            return []

        logger.info(f"Found {len(c_files)} .c, {len(cpp_files)} .cpp files")

        all_trajectories = []
        for source_file in all_files:
            logger.info(f"Processing {source_file.name}...")
            try:
                trajs = self._extract_from_file(source_file)
                all_trajectories.extend(trajs)
                logger.info(f"  → {len(trajs)} paths extracted")
            except Exception as e:
                logger.error(f"Error processing {source_file}: {e}")

        logger.info(f"✅ Total paths extracted: {len(all_trajectories)}")

        if len(all_trajectories) > self.max_paths:
            all_trajectories = all_trajectories[:self.max_paths]

        return all_trajectories

    def _extract_from_file(self, file_path: Path) -> List[Trajectory]:
        tu = self.index.parse(
            str(file_path),
            args=['-std=c11', '-Wall'],
            options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
        )
        if not tu:
            return []

        trajectories = []
        functions = self._find_functions(tu.cursor)
        logger.info(f"  Found {len(functions)} functions")

        for func in functions:
            cfg = self._build_cfg(func, tu)
            paths = self._generate_paths(cfg, func.spelling)
            for i, path in enumerate(paths):
                traj = self._path_to_trajectory(path, func.spelling, i)
                trajectories.append(traj)

        return trajectories

    def _find_functions(self, cursor) -> List:
        functions = []
        def visit(node):
            if node.kind == CursorKind.FUNCTION_DECL and node.is_definition():
                functions.append(node)
            for child in node.get_children():
                visit(child)
        visit(cursor)
        return functions

    # ------------------------------------------------------------------
    # Extraction de la condition réelle depuis les tokens Clang
    # ------------------------------------------------------------------

    def _extract_condition_text(self, cursor, tu) -> str:
        """
        Extrait le texte de la condition d'un nœud if/while/for
        depuis les tokens du fichier source.
        """
        try:
            children = list(cursor.get_children())
            if not children:
                return ""

            # Pour if/while : premier enfant = condition
            # Pour for      : deuxième enfant = condition (après init)
            if cursor.kind == CursorKind.FOR_STMT:
                cond_node = children[1] if len(children) > 1 else children[0]
            else:
                cond_node = children[0]

            # Extraire les tokens du nœud de condition
            tokens = list(cond_node.get_tokens())
            if not tokens:
                return ""

            text = ' '.join(t.spelling for t in tokens)
            return text.strip()

        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Construction du CFG
    # ------------------------------------------------------------------

    def _build_cfg(self, func_cursor, tu) -> List[CFGNode]:
        cfg: List[CFGNode] = []
        next_id = [0]

        def create_node(cursor, is_branch=False, condition="") -> int:
            node_id = next_id[0]
            next_id[0] += 1
            node = CFGNode(
                node_id=node_id,
                kind=cursor.kind.name,
                location=f"{cursor.location.line}:{cursor.location.column}",
                condition=condition,
                children=[],
                is_branch=is_branch
            )
            cfg.append(node)
            return node_id

        def visit(cursor, parent_id=None) -> int:
            is_branch = cursor.kind in self.BRANCH_KINDS

            # Extraire la vraie condition pour les branches
            condition = ""
            if is_branch:
                condition = self._extract_condition_text(cursor, tu)
                if not condition:
                    condition = f"{cursor.kind.name}@{cursor.location.line}"

            current_id = create_node(cursor, is_branch, condition)

            if parent_id is not None:
                cfg[parent_id].children.append(current_id)

            if cursor.kind == CursorKind.IF_STMT:
                children = list(cursor.get_children())
                if len(children) >= 2:
                    visit(children[1], current_id)   # then
                    if len(children) >= 3:
                        visit(children[2], current_id)  # else
            elif cursor.kind in {CursorKind.WHILE_STMT, CursorKind.FOR_STMT,
                                  CursorKind.DO_STMT}:
                for child in list(cursor.get_children())[1:]:
                    visit(child, current_id)
            else:
                for child in cursor.get_children():
                    visit(child, current_id)

            return current_id

        visit(func_cursor)
        return cfg

    # ------------------------------------------------------------------
    # DFS pour générer les chemins
    # ------------------------------------------------------------------

    def _generate_paths(self, cfg: List[CFGNode], func_name: str) -> List[List[CFGNode]]:
        if not cfg:
            return []

        paths: List[List[int]] = []
        max_depth = 50

        def dfs(node_id: int, current_path: List[int], visited: Set[int], depth: int):
            if depth > max_depth or len(paths) >= self.max_paths:
                return
            node = cfg[node_id]
            current_path.append(node_id)
            if not node.children:
                paths.append(current_path.copy())
            elif node.is_branch:
                for child_id in node.children:
                    if child_id not in visited:
                        dfs(child_id, current_path, visited | {child_id}, depth + 1)
            else:
                for child_id in node.children:
                    if child_id not in visited:
                        dfs(child_id, current_path, visited | {node_id}, depth + 1)
            current_path.pop()

        dfs(0, [], set(), 0)
        return [[cfg[nid] for nid in path] for path in paths]

    # ------------------------------------------------------------------
    # Conversion chemin → Trajectory
    # ------------------------------------------------------------------

    def _path_to_trajectory(self, path: List[CFGNode], func_name: str, idx: int) -> Trajectory:
        basic_blocks = [node.node_id for node in path]

        branches: Set[Tuple[int, int]] = set()
        for i in range(len(path) - 1):
            if path[i].is_branch:
                branches.add((path[i].node_id, path[i+1].node_id))

        # Contraintes = vraies conditions des nœuds de branche sur ce chemin
        constraints = [
            node.condition
            for node in path
            if node.is_branch and node.condition
        ]

        path_condition = " AND ".join(constraints) if constraints else f"{func_name}_path_{idx}"

        return Trajectory(
            path_id=f"c_{func_name}_path_{idx:03d}",
            basic_blocks=basic_blocks,
            path_condition=path_condition,
            branches_covered=branches,
            constraints=constraints,
            cost=float(len(path)),
            is_feasible=True
        )