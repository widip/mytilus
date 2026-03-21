import io
import pathlib

from nx_yaml import nx_compose_all

from discorun.comput.computer import Box, Diagram
from .metaprog.hif import HIFToLoader
from .state.loader import LoaderToShell


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
    fd.draw(path=str(path.with_suffix(".jpg")),
            textpad=(0.3, 0.1),
            fontsize=12,
            fontsize_types=8)
