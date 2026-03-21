from __future__ import annotations

import ast
from pathlib import Path

from discorun.comput.computer import Box, Computer, ComputableFunction, Program


def iter_discorun_python_files() -> list[Path]:
    root = Path("discorun")
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def test_discorun_only_depends_on_discopy_or_itself():
    for path in iter_discorun_python_files():
        module = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                for name in node.names:
                    assert not name.name.startswith(
                        "mytilus"
                    ), f"{path} must not depend on mytilus ({name.name!r})"
                    assert name.name == "discopy", f"{path} imports external module {name.name!r}"
            if isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    continue
                assert not (node.module or "").startswith(
                    "mytilus"
                ), f"{path} must not depend on mytilus ({node.module!r})"
                assert node.module and node.module.startswith(
                    "discopy"
                ), f"{path} imports external module {node.module!r}"


def test_program_abstractions_are_diagrammatic_boxes():
    assert issubclass(Program, Box)
    assert issubclass(ComputableFunction, Box)
    assert issubclass(Computer, Box)
