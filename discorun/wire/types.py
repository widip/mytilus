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
    
    @classmethod
    def bubble(cls, inner, **kwargs):
        """Categorical bubble factory that preserves the diagram class."""
        res = super().bubble(inner, **kwargs)
        return cls(res.inside, res.dom, res.cod)


def Id(x=Ty()):
    """Identity diagram over ``Ty`` (defaults to the monoidal unit)."""
    return Diagram.id(x)
