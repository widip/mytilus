import os
import re
from pathlib import Path

import pytest
from nx_yaml import nx_compose_all

from mytilus.metaprog.hif import HIFToLoader
from mytilus.state import SHELL_INTERPRETER
from mytilus.state.loader import LoaderToShell
from mytilus.state.shell import ShellSpecializer


FIXTURE_DIR = Path("tests/mytilus")

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mytilus-mpl")


def case_paths():
    return tuple(sorted(path.with_suffix("") for path in FIXTURE_DIR.glob("*.yaml")))


from mytilus.files import normalize_svg

@pytest.mark.parametrize("path", case_paths(), ids=lambda path: path.name)
def test_shell_runner_files(path, tmp_path):
    hif_to_loader = HIFToLoader()
    loader_to_shell = LoaderToShell()
    yaml_path = path.with_suffix(".yaml")
    stdin_path = path.with_suffix(".in")
    stdout_path = path.with_suffix(".out")
    prog_svg_path = path.with_suffix(".prog.svg")
    mprog_svg_path = path.with_suffix(".mprog.svg")

    assert yaml_path.exists()
    assert stdin_path.exists()
    assert stdout_path.exists()
    assert prog_svg_path.exists()
    assert mprog_svg_path.exists()

    yaml_text = yaml_path.read_text()
    mprog = hif_to_loader(nx_compose_all(yaml_text))
    prog = ShellSpecializer()(loader_to_shell(mprog))

    actual_mprog_svg_path = tmp_path / f"{path.name}.mprog.svg"
    actual_prog_svg_path = tmp_path / f"{path.name}.prog.svg"
    
    from mytilus.files import diagram_draw
    diagram_draw(actual_mprog_svg_path, mprog)
    diagram_draw(actual_prog_svg_path, prog)

    program = SHELL_INTERPRETER(prog)

    assert program(stdin_path.read_text()) == stdout_path.read_text()
    assert normalize_svg(actual_prog_svg_path.read_text()) == normalize_svg(prog_svg_path.read_text())
    assert normalize_svg(actual_mprog_svg_path.read_text()) == normalize_svg(mprog_svg_path.read_text())
