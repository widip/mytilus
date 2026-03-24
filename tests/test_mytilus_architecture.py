from __future__ import annotations

import ast
from pathlib import Path


MYTILUS_ROOT = Path("mytilus")
LAYER_ORDER = ("state", "metaprog", "comput", "wire")
LAYER_INDEX = {name: index for index, name in enumerate(LAYER_ORDER)}
PACKAGE_SINGLETONS = {
    "LOADER",
    "SHELL",
    "SHELL_SPECIALIZER",
    "SHELL_RUNTIME",
    "SHELL_PROGRAM_TO_PYTHON",
    "SHELL_PYTHON_RUNTIME",
    "SHELL_INTERPRETER",
    "PYTHON_PROGRAMS",
    "PYTHON_SPECIALIZER_BOX",
    "PYTHON_INTERPRETER_BOX",
    "PYTHON_EVALUATOR_BOX",
    "PYTHON_RUNTIME",
    "PYTHON_COMPILER",
    "PYTHON_COMPILER_GENERATOR",
}


def iter_mytilus_python_files() -> list[Path]:
    return sorted(path for path in MYTILUS_ROOT.rglob("*.py") if "__pycache__" not in path.parts)


def module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def module_layer(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) < 2 or parts[0] != "mytilus":
        return None
    layer = parts[1]
    if layer in LAYER_INDEX:
        return layer
    return None


def resolve_imported_module(current_module: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    base = current_module.split(".")[:-node.level]
    if node.module:
        return ".".join(base + [node.module])
    return ".".join(base)


def top_level_assigned_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_mytilus_package_singletons_live_only_in_init_modules():
    for path in iter_mytilus_python_files():
        if path.name == "__init__.py":
            continue
        assigned = top_level_assigned_names(path)
        leaked = sorted(assigned & PACKAGE_SINGLETONS)
        assert not leaked, f"{path} defines package singleton globals: {leaked!r}"


def test_init_modules_do_not_backfill_submodule_attributes():
    init_paths = (
        Path("mytilus/pcc/__init__.py"),
        Path("mytilus/metaprog/__init__.py"),
        Path("mytilus/state/__init__.py"),
    )
    for path in init_paths:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            targets = ()
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
            if isinstance(node, ast.AnnAssign):
                targets = (node.target,)
            if isinstance(node, ast.AugAssign):
                targets = (node.target,)
            for target in targets:
                assert not isinstance(
                    target, ast.Attribute
                ), f"{path} backfills a submodule attribute via assignment"


def test_init_modules_use_absolute_imports_only():
    for path in iter_mytilus_python_files():
        if path.name != "__init__.py":
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.level == 0, f"{path} uses relative import"


def test_mytilus_layer_dependency_direction():
    for path in iter_mytilus_python_files():
        current_module = module_name(path)
        current_layer = module_layer(current_module)
        if current_layer is None:
            continue

        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            imported_modules: list[str] = []
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported_modules.append(resolve_imported_module(current_module, node))

            for imported_module in imported_modules:
                imported_layer = module_layer(imported_module)
                if imported_layer is None or imported_layer == current_layer:
                    continue
                assert LAYER_INDEX[current_layer] <= LAYER_INDEX[imported_layer], (
                    f"{path} violates layer order {LAYER_ORDER}: "
                    f"{current_module} imports {imported_module}"
                )


def test_python_named_modules_do_not_import_shell_named_modules():
    for path in iter_mytilus_python_files():
        if path.name != "python.py":
            continue

        current_module = module_name(path)
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            imported_modules: list[str] = []
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported_modules.append(resolve_imported_module(current_module, node))

            for imported_module in imported_modules:
                if imported_module.endswith(".shell"):
                    raise AssertionError(f"{path} imports shell module {imported_module}")


def _canonical_module(path: Path) -> str:
    parts = path.with_suffix("").parts
    if parts[-1] == "__init__":
        return ".".join(parts[:-1])
    return ".".join(parts)


def _module_import_graph() -> dict[str, set[str]]:
    module_paths = {_canonical_module(path): path for path in iter_mytilus_python_files()}

    def normalize(module: str) -> str:
        if module in module_paths:
            return module
        return f"{module}.__init__" if f"{module}.__init__" in module_paths else module

    graph = {module: set() for module in module_paths}
    for module, path in module_paths.items():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in tree.body:
            imported_modules: list[str] = []
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported_modules.append(resolve_imported_module(module, node))
            for imported_module in imported_modules:
                target = normalize(imported_module)
                if target in module_paths and target != module:
                    graph[module].add(target)
    return graph


def test_mytilus_top_level_imports_are_acyclic():
    graph = _module_import_graph()
    visited: set[str] = set()
    on_stack: set[str] = set()

    def visit(module: str):
        if module in on_stack:
            raise AssertionError(f"top-level import cycle contains {module}")
        if module in visited:
            return
        visited.add(module)
        on_stack.add(module)
        for dependency in graph[module]:
            visit(dependency)
        on_stack.remove(module)

    for module in sorted(graph):
        visit(module)
