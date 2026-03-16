"""Loader-specific wire combinators and structural boxes."""

from discopy import monoidal

from .functions import Box
from .services import Copy as CopyService, Delete
from .types import Id, Ty


loader_stream_ty = Ty("yaml_stream")


class LoaderSequence(monoidal.Bubble, Box):
    """Bubble grouping loader stages in sequence."""

    def __init__(self, stages):
        self.stages = tuple(stages)
        monoidal.Bubble.__init__(
            self,
            pipeline(self.stages),
            dom=loader_stream_ty,
            cod=loader_stream_ty,
            draw_vertically=True,
            drawing_name="seq",
        )


class LoaderMapping(monoidal.Bubble, Box):
    """Bubble grouping loader branches in parallel."""

    def __init__(self, branches):
        self.branches = tuple(branches)
        arg = tensor_all(self.branches) if self.branches else loader_id()
        monoidal.Bubble.__init__(
            self,
            arg,
            dom=loader_stream_ty,
            cod=loader_stream_ty,
            drawing_name="map",
        )


def loader_id():
    """Identity diagram over the loader stream wire."""
    return Id(loader_stream_ty)


def pipeline(diagrams):
    """Compose loader stages from top to bottom, skipping identities."""
    result = loader_id()
    identity = loader_id()
    for diagram in diagrams:
        if diagram == identity:
            continue
        result = diagram if result == identity else result >> diagram
    return result


def tensor_all(diagrams):
    """Tensor loader stages left-to-right."""
    diagrams = tuple(diagrams)
    if not diagrams:
        return Id()
    result = diagrams[0]
    for diagram in diagrams[1:]:
        result = result @ diagram
    return result


def stream_wires(n: int):
    """Return the monoidal product of ``n`` loader stream wires."""
    wires = Ty()
    for _ in range(n):
        wires = wires @ loader_stream_ty
    return wires
