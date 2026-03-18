"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""
from nx_yaml import nx_compose_all

from ..comput.computer import Box, Computer, ComputableFunction, Diagram, Functor, Program, ProgramTy, Ty
from ..state.widish import ShellRunner
from ..wire.hif import HyperGraph


class Metaprogram(Box):
    """
    a metaprogram, presented as a cartesian function G:I⊸P
    """

    def __init__(self, name, P: ProgramTy):
        Box.__init__(self, name, dom=Ty(), cod=P)


class Specializer(Functor):
    """A functorial metaprogram with unit parameter type."""

    @staticmethod
    def metaprogram_dom():
        return Ty()

    def __init__(self, ob=None, ar=None, *, dom=None, cod=None):
        Functor.__init__(
            self,
            self.ob_map if ob is None else ob,
            self.ar_map if ar is None else ar,
            dom=Functor.dom if dom is None else dom,
            cod=Functor.cod if cod is None else cod,
        )

    @staticmethod
    def ob_map(ob):
        return ob

    @staticmethod
    def ar_map(ar):
        return ar

    def specialize(self, *args, **kwargs):
        return self(*args, **kwargs)


class ProgramComputation(Diagram):
    """
    Section 3.1: a function is computable when it is programmable.
    Fig 6.1: A computation f encoded such that f = {F}.
    """

    def __init__(self, name, P: ProgramTy, X: Ty, A: Ty, B: Ty):
        """
        Running a given program is a routine operation.
        Every function is computable, in the sense that there is a program for it.
        """
        self.universal_ev_diagram = ComputableFunction("{" + name + "}", X, A, B)
        diagram = (
            Program(name, P, X) @ A,
            Computer(P, A, B),
        )
        inside = sum(map(lambda d: d.inside, diagram), ())
        Diagram.__init__(self, inside, X @ A, B)

    def universal_ev(self):
        return self.universal_ev_diagram

    def specialize(self):
        """Pure wiring rewrite from a program layer to its encoded computation."""
        return self.universal_ev()


class MetaprogramComputation(Diagram):
    """
    Fig 6.1: A program F encoded such that F = {ℱ}.
    """

    def __init__(self, name, P: ProgramTy, PP: ProgramTy, X: Ty, A: Ty, B: Ty):
        self.universal_ev_diagram = ComputableFunction("{{" + name + "}}", X, A, B)
        self.partial_ev_diagram = (
            ProgramComputation("{" + name + "}", PP, Ty(), X, P) @ A
            >> Computer(P, A, B)
        )
        diagram = (
            Program(name, PP, Ty()) @ X @ A,
            Computer(PP, X, P) @ A,
            Computer(P, A, B),
        )
        inside = sum(map(lambda d: d.inside, diagram), ())
        Diagram.__init__(self, inside, X @ A, B)

    def universal_ev(self):
        return self.universal_ev_diagram

    def partial_ev(self):
        return self.partial_ev_diagram

    def specialize(self):
        """Pure wiring rewrite from a metaprogram layer to partial evaluation."""
        return self.partial_ev()


class ProgramFunctor:
    """
    Pure wiring transformation that strips one program-evaluation layer.
    """

    def __call__(self, other):
        if isinstance(other, ProgramComputation):
            return other.specialize()
        return other


class MetaprogramFunctor:
    """
    Pure wiring transformation that strips one metaprogram-evaluation layer.
    """

    def __call__(self, other):
        if isinstance(other, MetaprogramComputation):
            return other.specialize()
        return other


from .hif import HIFToLoader
from .loader import LoaderToShell
from .widish import ShellSpecializer


SHELL_SPECIALIZER = ShellSpecializer()
SHELL_TO_PYTHON = ShellRunner(SHELL_SPECIALIZER)
HIF_TO_LOADER = HIFToLoader()
LOADER_TO_SHELL = LoaderToShell()


def incidences_to_program(graph: HyperGraph):
    """Turn an ``nx_yaml`` hypergraph into a loader-language diagram."""
    return HIF_TO_LOADER(graph)


def repl_read(stream):
    """Parse a YAML stream and compile it to the shell backend."""
    return LOADER_TO_SHELL(incidences_to_program(nx_compose_all(stream)))
