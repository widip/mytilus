import io
import pathlib
import re

from nx_yaml import nx_compose_all
import yaml

from discorun.comput.computer import Box, Diagram
from .metaprog.hif import HIFToLoader
from .state.loader import LoaderToShell


def normalize_svg(svg_text: str) -> str:
    """Strip volatile Matplotlib metadata from golden SVGs."""
    svg_text = re.sub(r"<metadata>.*?</metadata>\s*", "", svg_text, flags=re.DOTALL)
    svg_text = re.sub(r'id="[^"]*[0-9a-f]{8,}[^"]*"', 'id="SVG_ID"', svg_text)
    svg_text = re.sub(r'url\(#([^)]*[0-9a-f]{8,}[^)]*)\)', 'url(#SVG_ID)', svg_text)
    svg_text = re.sub(r'xlink:href="#[^"]*[0-9a-f]{8,}[^"]*"', 'xlink:href="#SVG_ID"', svg_text)
    svg_text = re.sub(r"/tmp/mytilus-[^<\" ]+\.tmp", "/tmp/MYTILUS_TMP", svg_text)
    marker_use_re = re.compile(r'^\s*<use xlink:href="#SVG_ID" x="[^"]+" y="[^"]+" style="stroke: #000000"/>\s*$', re.MULTILINE)
    marker_uses = iter(sorted(match.group(0).strip() for match in marker_use_re.finditer(svg_text)))
    svg_text = marker_use_re.sub(lambda _match: next(marker_uses), svg_text)
    return svg_text.strip()


def files_ar(ar: Box) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    if not ar.name.startswith("file://"):
        return ar

    try:
        return file_diagram(ar.name.lstrip("file://"))
    except IsADirectoryError:
        print("is a dir")
        return ar

def stream_diagram(stream) -> Diagram:
    return LoaderToShell()(HIFToLoader()(nx_compose_all(stream)))


def _inline_shell_diagram(source: str) -> Diagram | None:
    """Compile direct ``sh: [...]`` inline commands without routing through HIF."""
    try:
        parsed = yaml.safe_load(source)
    except yaml.YAMLError:
        return None

    if not isinstance(parsed, dict) or tuple(parsed.keys()) != ("sh",):
        return None

    spec = parsed["sh"]
    if not isinstance(spec, list) or not spec:
        return None

    def is_argv(argv):
        return isinstance(argv, list) and argv and all(isinstance(arg, str) for arg in argv)

    from .comput.shell import Command
    from .state.shell import Pipeline
    from .pcc import SHELL
    from .wire.shell import io_ty

    execution = SHELL.execution(io_ty, io_ty).output_diagram()

    if is_argv(spec):
        return Command(spec) @ io_ty >> execution
    if all(is_argv(stage) for stage in spec):
        return Pipeline(tuple(Command(stage) @ io_ty >> execution for stage in spec))
    return None


def source_diagram(source: str) -> Diagram:
    inline = _inline_shell_diagram(source)
    if inline is not None:
        return inline
    return stream_diagram(io.StringIO(source))


def file_diagram(file_name) -> Diagram:
    path = pathlib.Path(file_name)
    with path.open() as stream:
        fd = stream_diagram(stream)
    return fd

def diagram_draw(path, fd):
    svg_path = path.with_suffix(".svg")
    fd.draw(path=str(svg_path),
            textpad=(0.3, 0.1),
            fontsize=12,
            fontsize_types=8)
    svg_path.write_text(normalize_svg(svg_path.read_text()))
