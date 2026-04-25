"""
JavaScript/TypeScript Extractor — Vraie analyse symbolique par Acorn AST
=========================================================================
Chaque trajectoire correspond à UN chemin réel :
  - Les contraintes contiennent les VRAIES conditions JS/TS
    (ex: "user === null", "password.length < 8", "i < arr.length")
  - path_condition est la conjonction logique des conditions du chemin.
"""
import json
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import List, Set, Tuple
import logging
from dataclasses import dataclass, field

from kimvieware_shared.models import Trajectory

logger = logging.getLogger(__name__)


@dataclass
class CFGNode:
    """Nœud du Control Flow Graph JavaScript."""
    node_id: int
    kind: str
    location: str
    condition: str = ""          # VRAIE condition extraite du code JS/TS
    children: List[int] = field(default_factory=list)
    is_branch: bool = False


# ---------------------------------------------------------------------------
# Script Node.js : parse avec Acorn ET sérialise les conditions
# ---------------------------------------------------------------------------

NODE_SCRIPT = textwrap.dedent("""
    const acorn = require('acorn');
    const fs = require('fs');

    const filePath = process.argv[2];
    const isTS = filePath.endsWith('.ts') || filePath.endsWith('.mts');

    let source;
    try {
        source = fs.readFileSync(filePath, 'utf8');
    } catch(e) {
        process.stderr.write('READ_ERROR: ' + e.message + '\\n');
        process.exit(1);
    }

    // Nettoyage minimal pour TypeScript
    if (isTS) {
        source = source
            .replace(/:\\s*[\\w<>\\[\\]|&,\\s]+(?=[,)=;{])/g, '')
            .replace(/<[^>]+>/g, '')
            .replace(/as\\s+\\w+/g, '')
            .replace(/:\\s*\\w+\\s*(?=\\{)/g, '');
    }

    const options = {
        ecmaVersion: 2022,
        sourceType: 'module',
        locations: true,
        allowHashBang: true,
        allowImportExportEverywhere: true,
    };

    let ast;
    try {
        ast = acorn.parse(source, options);
    } catch(e) {
        process.stderr.write('PARSE_ERROR: ' + e.message + '\\n');
        process.exit(1);
    }

    // ── Sérialisation des expressions en string lisible ──────────────────
    function serializeExpr(node) {
        if (!node) return 'null';
        switch(node.type) {
            case 'BinaryExpression':
            case 'LogicalExpression':
                return serializeExpr(node.left) + ' ' + node.operator + ' ' + serializeExpr(node.right);
            case 'UnaryExpression':
                return node.operator + serializeExpr(node.argument);
            case 'MemberExpression':
                return serializeExpr(node.object) + '.' + serializeExpr(node.property);
            case 'CallExpression':
                return serializeExpr(node.callee) + '(' +
                    (node.arguments || []).map(serializeExpr).join(', ') + ')';
            case 'Identifier':
                return node.name;
            case 'Literal':
                return JSON.stringify(node.value);
            case 'TemplateLiteral':
                return '`...`';
            case 'AssignmentExpression':
                return serializeExpr(node.left) + ' ' + node.operator + ' ' + serializeExpr(node.right);
            case 'ConditionalExpression':
                return serializeExpr(node.test) + ' ? ' + serializeExpr(node.consequent) + ' : ' + serializeExpr(node.alternate);
            case 'ArrayExpression':
                return '[' + (node.elements || []).map(serializeExpr).join(', ') + ']';
            case 'ObjectExpression':
                return '{...}';
            case 'NewExpression':
                return 'new ' + serializeExpr(node.callee) + '(...)';
            case 'UpdateExpression':
                return node.prefix ?
                    node.operator + serializeExpr(node.argument) :
                    serializeExpr(node.argument) + node.operator;
            case 'AwaitExpression':
                return 'await ' + serializeExpr(node.argument);
            default:
                return node.type;
        }
    }

    function getCondition(node) {
        switch(node.type) {
            case 'IfStatement':
                return serializeExpr(node.test);
            case 'WhileStatement':
            case 'DoWhileStatement':
                return serializeExpr(node.test);
            case 'ForStatement':
                return node.test ? serializeExpr(node.test) : 'for_init';
            case 'ForInStatement':
                return serializeExpr(node.left) + ' in ' + serializeExpr(node.right);
            case 'ForOfStatement':
                return serializeExpr(node.left) + ' of ' + serializeExpr(node.right);
            case 'SwitchStatement':
                return 'switch(' + serializeExpr(node.discriminant) + ')';
            case 'TryStatement':
                const handler = node.handler;
                const param = handler && handler.param ? serializeExpr(handler.param) : 'e';
                return 'try (catch ' + param + ')';
            case 'ConditionalExpression':
                return serializeExpr(node.test);
            default:
                return '';
        }
    }

    // ── Enrichissement de l'AST avec les conditions sérialisées ──────────
    const BRANCH_TYPES = new Set([
        'IfStatement', 'WhileStatement', 'DoWhileStatement',
        'ForStatement', 'ForInStatement', 'ForOfStatement',
        'SwitchStatement', 'TryStatement', 'ConditionalExpression'
    ]);

    function enrichAST(node) {
        if (!node || typeof node !== 'object') return;
        if (BRANCH_TYPES.has(node.type)) {
            node._condition = getCondition(node);
            node._is_branch = true;
        }
        for (const key of Object.keys(node)) {
            if (key.startsWith('_')) continue;
            const val = node[key];
            if (Array.isArray(val)) val.forEach(enrichAST);
            else if (val && typeof val === 'object' && val.type) enrichAST(val);
        }
    }

    enrichAST(ast);
    process.stdout.write(JSON.stringify(ast));
""")


# ---------------------------------------------------------------------------
# Extracteur principal
# ---------------------------------------------------------------------------

class JSExtractor:
    """
    Extrait les chemins d'exécution depuis du code JS/TS avec Acorn.

    Améliorations vs version précédente :
      - serializeExpr() dans le script Node.js convertit les AST nodes en strings
      - _condition contient la vraie condition du code source
      - path_condition = conjonction logique des conditions du chemin
    """

    BRANCH_TYPES = {
        'IfStatement', 'WhileStatement', 'DoWhileStatement',
        'ForStatement', 'ForInStatement', 'ForOfStatement',
        'SwitchStatement', 'TryStatement', 'ConditionalExpression'
    }

    def __init__(self, max_paths: int = 100):
        self.max_paths = max_paths
        self.next_node_id = 0
        self._check_node_and_acorn()

    def _check_node_and_acorn(self):
        try:
            subprocess.run(['node', '--version'], capture_output=True, timeout=5)
        except FileNotFoundError:
            raise RuntimeError("Node.js not found")
        try:
            r = subprocess.run(['node', '-e', 'require("acorn")'], capture_output=True, timeout=5)
            if r.returncode != 0:
                raise RuntimeError("acorn not found — run: npm install -g acorn")
        except FileNotFoundError:
            raise RuntimeError("Node.js not found")

    def extract_paths(self, source_dir: Path) -> List[Trajectory]:
        logger.info(f"🔍 Extracting JS/TS paths from {source_dir}")

        js_files  = list(source_dir.rglob("*.js"))
        mjs_files = list(source_dir.rglob("*.mjs"))
        ts_files  = list(source_dir.rglob("*.ts"))

        def _keep(f: Path) -> bool:
            bad = {'node_modules', 'dist', 'build', '.git', '__pycache__', '.venv', 'coverage'}
            return (not any(p in f.parts for p in bad)
                    and 'test' not in f.stem.lower()
                    and '.min.' not in f.name)

        all_files = [f for f in js_files + mjs_files + ts_files if _keep(f)]
        if not all_files:
            logger.warning("No JS/TS source files found")
            return []

        logger.info(f"Found {len(all_files)} files after filtering")
        all_trajectories = []

        for source_file in all_files:
            logger.info(f"Processing {source_file.name}...")
            try:
                trajs = self._extract_from_file(source_file)
                all_trajectories.extend(trajs)
                logger.info(f"  → {len(trajs)} paths extracted")
            except Exception as e:
                logger.error(f"Error processing {source_file}: {e}")

        logger.info(f"✅ Total JS/TS paths extracted: {len(all_trajectories)}")
        if len(all_trajectories) > self.max_paths:
            all_trajectories = all_trajectories[:self.max_paths]

        return all_trajectories

    # ------------------------------------------------------------------
    # Parse avec Acorn via subprocess
    # ------------------------------------------------------------------

    def _get_ast(self, file_path: Path) -> dict | None:
        with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False, encoding='utf-8') as tmp:
            tmp.write(NODE_SCRIPT)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ['node', tmp_path, str(file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                logger.warning(f"acorn error on {file_path.name}: {result.stderr.strip()[:200]}")
                return None
            return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.error(f"Error parsing {file_path.name}: {e}")
            return None
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _extract_from_file(self, file_path: Path) -> List[Trajectory]:
        ast = self._get_ast(file_path)
        if ast is None:
            return []

        trajectories = []
        functions = self._find_functions(ast)
        logger.info(f"  Found {len(functions)} functions")

        for func in functions:
            func_name = self._get_func_name(func)
            cfg = self._build_cfg(func)
            paths = self._generate_paths(cfg, func_name)
            for i, path in enumerate(paths):
                traj = self._path_to_trajectory(path, func_name, i)
                trajectories.append(traj)

        return trajectories

    # ------------------------------------------------------------------
    # Traversée AST
    # ------------------------------------------------------------------

    def _find_functions(self, node: dict) -> List[dict]:
        results = []
        func_types = {'FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'}
        def walk(n):
            if not isinstance(n, dict):
                return
            if n.get('type') in func_types:
                results.append(n)
            for v in n.values():
                if isinstance(v, dict):
                    walk(v)
                elif isinstance(v, list):
                    for item in v:
                        walk(item)
        walk(node)
        return results

    def _get_func_name(self, func_node: dict) -> str:
        id_node = func_node.get('id')
        if id_node:
            return id_node.get('name', 'anonymous')
        return 'anonymous'

    def _get_location(self, node: dict) -> str:
        loc = node.get('loc')
        if loc and 'start' in loc:
            return f"{loc['start']['line']}:{loc['start']['column']}"
        return 'unknown'

    # ------------------------------------------------------------------
    # Construction du CFG avec vraies conditions
    # ------------------------------------------------------------------

    def _build_cfg(self, func_node: dict) -> List[CFGNode]:
        cfg: List[CFGNode] = []
        self.next_node_id = 0

        def create_node(ast_node: dict, is_branch: bool = False, condition: str = "") -> int:
            node_id = self.next_node_id
            self.next_node_id += 1
            cfg.append(CFGNode(
                node_id=node_id,
                kind=ast_node.get('type', 'Unknown'),
                location=self._get_location(ast_node),
                condition=condition,
                children=[],
                is_branch=is_branch,
            ))
            return node_id

        def link(parent_id: int, child_id: int):
            cfg[parent_id].children.append(child_id)

        def visit(node, parent_id=None) -> int | None:
            if not isinstance(node, dict):
                return None

            node_type = node.get('type', '')
            is_branch = node_type in self.BRANCH_TYPES

            # Récupérer la condition sérialisée (ajoutée par le script Node.js)
            condition = node.get('_condition', '') if is_branch else ''

            current_id = create_node(node, is_branch, condition)
            if parent_id is not None:
                link(parent_id, current_id)

            # Traversée structurée
            if node_type == 'IfStatement':
                visit(node.get('test', {}), current_id)
                visit(node.get('consequent', {}), current_id)
                if node.get('alternate'):
                    visit(node['alternate'], current_id)

            elif node_type in ('WhileStatement', 'DoWhileStatement'):
                visit(node.get('test', {}), current_id)
                visit(node.get('body', {}), current_id)

            elif node_type == 'ForStatement':
                for key in ('init', 'test', 'update', 'body'):
                    if node.get(key):
                        visit(node[key], current_id)

            elif node_type in ('ForInStatement', 'ForOfStatement'):
                visit(node.get('left', {}), current_id)
                visit(node.get('right', {}), current_id)
                visit(node.get('body', {}), current_id)

            elif node_type == 'SwitchStatement':
                visit(node.get('discriminant', {}), current_id)
                for case in node.get('cases', []):
                    visit(case, current_id)

            elif node_type == 'TryStatement':
                visit(node.get('block', {}), current_id)
                if node.get('handler'):
                    visit(node['handler'], current_id)
                if node.get('finalizer'):
                    visit(node['finalizer'], current_id)

            elif node_type == 'BlockStatement':
                for stmt in node.get('body', []):
                    visit(stmt, current_id)

            elif node_type in ('FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'):
                body = node.get('body')
                if body:
                    visit(body, current_id)

            else:
                for v in node.values():
                    if isinstance(v, dict) and v.get('type'):
                        visit(v, current_id)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict) and item.get('type'):
                                visit(item, current_id)

            return current_id

        body = func_node.get('body')
        if body:
            visit(body)

        return cfg

    # ------------------------------------------------------------------
    # DFS pour générer les chemins
    # ------------------------------------------------------------------

    def _generate_paths(self, cfg: List[CFGNode], func_name: str) -> List[List[CFGNode]]:
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

    def _path_to_trajectory(self, path: List[CFGNode], func_name: str, idx: int) -> Trajectory:
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

        path_condition = " AND ".join(constraints) if constraints else f"{func_name}_path_{idx}"

        return Trajectory(
            path_id=f"js_{func_name}_path_{idx:03d}",
            basic_blocks=basic_blocks,
            path_condition=path_condition,
            branches_covered=branches,
            constraints=constraints,
            cost=float(len(path)),
            is_feasible=True
        )