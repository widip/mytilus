"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""

from ..comput.computer import Box, Computer, ComputableFunction, Diagram, Program, ProgramTy, Ty


class Metaprogram(Box):
    """
    a metaprogram, presented as a cartesian function G:I⊸P
    """

    def __init__(self, name, P: ProgramTy):
        Box.__init__(self, name, dom=Ty(), cod=P)


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


def __getattr__(name):
    if name == "SHELL_SPECIALIZER":
        from .widish import ShellSpecializer

        value = ShellSpecializer()
        globals()[name] = value
        return value
    if name == "SHELL_RUNNER":
        from .widish import ShellRunner

        value = ShellRunner()
        globals()[name] = value
        return value
    if name == "LOADER_TO_SHELL":
        from .loader import LoaderToShell

        value = LoaderToShell()
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
