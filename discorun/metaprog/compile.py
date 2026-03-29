"""Principled diagram compilation of Run-language bubbles."""

from discopy import monoidal
from .core import Specializer, Interpreter, Diagram
from ..comput.boxes import Sequential, Parallel, Partial, Idempotent, Quote


class RunSpecializer(Specializer):
    """Metaprogram specializing standard Run-language bubbles (Sequential, Parallel, etc.)."""

    def __call__(self, other):
        # Dispatch to specialized bubble lowering.
        if isinstance(other, (Sequential, Parallel, Partial, Idempotent, Quote)):
            return self(other.specialize())
        if isinstance(other, monoidal.Bubble):
             # Recursively lower bubble contents.
             return self(other.arg)
        return super().__call__(other)


class RunInterpreter(Interpreter):
    """Interpreter supporting standard Run-language bubbles by first specializing them."""

    def __call__(self, other):
        if isinstance(other, (Sequential, Parallel, Partial, Idempotent, Quote)):
            return self(other.specialize())
        if isinstance(other, monoidal.Bubble):
             # Evaluate bubble inner contents.
             return self(other.arg)
        return super().__call__(other)


def compile_diagram(diagram):
    """Lower all Run-language bubbles in a diagram via the RunSpecializer."""
    return RunSpecializer()(diagram)
