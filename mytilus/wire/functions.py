"""Chapter 1 categorical structure for wire diagrams."""

from discopy import monoidal

from .types import Diagram, Ty


class Category(monoidal.Category):
    """Strict symmetric monoidal category of wire diagrams."""

    ob, ar = Ty, Diagram


class Functor(monoidal.Functor):
    """Functor between wire-diagram categories."""

    dom = Category()
    cod = Category()


class Box(monoidal.Box, Diagram):
    """Atomic box attached to input and output wires."""
