"""Loader-specific wire combinators and structural boxes."""

from discopy import monoidal

from .functions import Box
from .types import Id, Ty


loader_stream_ty = Ty("yaml_stream")


class LoaderScalar(Box):
    """Atomic YAML scalar node in the loader language."""

    def __init__(self, value: str | tuple[str, ...], tag: str | None = None):
        self.value = value
        self.tag = tag
        if tag:
            name = f"!{tag}" if not value else f"!{tag} {value!r}"
        else:
            name = repr(value)
        Box.__init__(self, name, dom=loader_stream_ty, cod=loader_stream_ty)


class LoaderSequence(monoidal.Bubble, Box):
    """Bubble grouping loader stages in sequence."""

    def __init__(self, stages, tag: str | None = None):
        self.stages = tuple(stages)
        self.tag = tag
        name = "seq" if tag is None else f"!{tag} seq"
        monoidal.Bubble.__init__(
            self,
            pipeline(self.stages),
            dom=loader_stream_ty,
            cod=loader_stream_ty,
            name=name,
            draw_vertically=True,
            drawing_name="seq",
        )


class LoaderMapping(monoidal.Bubble, Box):
    """Bubble grouping loader branches in parallel."""

    def __init__(self, branches, tag: str | None = None):
        self.branches = tuple(branches)
        self.tag = tag
        arg = tensor_all(self.branches) if self.branches else loader_id()
        name = "map" if tag is None else f"!{tag} map"
        monoidal.Bubble.__init__(
            self,
            arg,
            dom=loader_stream_ty,
            cod=loader_stream_ty,
            name=name,
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
