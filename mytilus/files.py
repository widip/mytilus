import io
import pathlib
import re

from nx_yaml import nx_compose_all

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


def source_diagram(source: str) -> Diagram:
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
