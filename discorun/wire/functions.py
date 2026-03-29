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

    def __call__(self, other):
        """Principled dispatch for specialized categorical objects and arrows."""
        # Note: Handled by modern discopy.monoidal.Functor: Ty, Ob, Layer, PRO, Dim, Bubble.
        
        # Handle closed-category objects: Over, Under, Exp.
        from discopy.closed import Over, Under, Exp, Curry, Eval
        for cls, attr in [(Over, "over"), (Under, "under"), (Exp, "exp")]:
            if isinstance(other, cls) and hasattr(self.cod.ar, attr):
                method = getattr(self.cod.ar, attr)
                return method(self(other.base), self(other.exponent))

        # Handle closed-category arrows: Curry, Eval.
        if isinstance(other, Curry) and hasattr(self.cod.ar, "curry"):
            return self.cod.ar.curry(
                self(other.arg), len(self(other.cod.exponent)), other.left)

        if isinstance(other, Eval) and hasattr(self.cod.ar, "ev"):
            return self.cod.ar.ev(
                self(other.base), self(other.exponent), other.left)

        # Let the base monoidal functor handle standard objects, arrows, and bubbles.
        return super().__call__(other)


class Box(monoidal.Box, Diagram):
    """Atomic box attached to input and output wires."""
