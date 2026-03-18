import os
import re
from pathlib import Path

import pytest
from nx_yaml import nx_compose_all

from widip.metaprog import LOADER_TO_SHELL, SHELL_TO_PYTHON, incidences_to_program
from widip.metaprog.widish import ShellSpecializer


FIXTURE_DIR = Path("tests/widish")

os.environ.setdefault("MPLCONFIGDIR", "/tmp/widip-mpl")


def case_paths():
    return tuple(sorted(path.with_suffix("") for path in FIXTURE_DIR.glob("*.yaml")))


def normalize_svg(svg_text: str) -> str:
    """Strip volatile Matplotlib metadata from golden SVGs."""
    svg_text = re.sub(r"<metadata>.*?</metadata>\s*", "", svg_text, flags=re.DOTALL)
    svg_text = re.sub(r'id="[^"]*[0-9a-f]{8,}[^"]*"', 'id="SVG_ID"', svg_text)
    svg_text = re.sub(r'url\(#([^)]*[0-9a-f]{8,}[^)]*)\)', 'url(#SVG_ID)', svg_text)
    svg_text = re.sub(r'xlink:href="#[^"]*[0-9a-f]{8,}[^"]*"', 'xlink:href="#SVG_ID"', svg_text)
    svg_text = re.sub(r"/tmp/widip-[^<\" ]+\.tmp", "/tmp/WIDIP_TMP", svg_text)
    marker_use_re = re.compile(r'^\s*<use xlink:href="#SVG_ID" x="[^"]+" y="[^"]+" style="stroke: #000000"/>\s*$', re.MULTILINE)
    marker_uses = iter(sorted(match.group(0).strip() for match in marker_use_re.finditer(svg_text)))
    svg_text = marker_use_re.sub(lambda _match: next(marker_uses), svg_text)
    return svg_text.strip()

@pytest.mark.parametrize("path", case_paths(), ids=lambda path: path.name)
def test_shell_runner_files(path, tmp_path):
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
    mprog = incidences_to_program(nx_compose_all(yaml_text))
    prog = ShellSpecializer()(LOADER_TO_SHELL(mprog))

    actual_mprog_svg_path = tmp_path / f"{path.name}.mprog.svg"
    actual_prog_svg_path = tmp_path / f"{path.name}.prog.svg"
    mprog.draw(path=str(actual_mprog_svg_path))
    prog.draw(path=str(actual_prog_svg_path))

    program = SHELL_TO_PYTHON(prog)

    assert program(stdin_path.read_text()) == stdout_path.read_text()
    assert normalize_svg(actual_prog_svg_path.read_text()) == normalize_svg(prog_svg_path.read_text())
    assert normalize_svg(actual_mprog_svg_path.read_text()) == normalize_svg(mprog_svg_path.read_text())
