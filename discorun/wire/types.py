"""Chapter 1 wire types and diagrams."""

from discopy import monoidal
from discopy.utils import factory


@factory
class Ty(monoidal.Ty):
    """Wire types presented as strings in diagrams."""


@factory
class Diagram(monoidal.Diagram):
    """Typed wire diagrams."""

    ty_factory = Ty


def Id(x=Ty()):
    """Identity diagram over ``Ty`` (defaults to the monoidal unit)."""
    return Diagram.id(x)
