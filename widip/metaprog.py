"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""
from .computer import *


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
        self.universal_ev_diagram = ComputableFunction("{"+name+"}", X, A, B)
        diagram = (
            Program(name, P, X) @ A,
            Computer(P, A, B))
        # TODO review .inside
        inside = sum(map(lambda d: d.inside, diagram), ())
        Diagram.__init__(self, inside, X @ A, B)

    def universal_ev(self):
        return self.universal_ev_diagram

class MetaprogramComputation(Diagram):
    """
    Fig 6.1: A program F encoded such that F = {ℱ}.
    """
    def __init__(self, name, P: ProgramTy, PP: ProgramTy, X: Ty, A: Ty, B: Ty):
        self.partial_ev_diagram = (
            ProgramComputation(name, PP, Ty(), X, P) @ A
            >> Computer(P, A, B)
        )
        diagram = (
            Program(name, PP, Ty()) @ X @ A,
            Computer(PP, X, P) @ A,
            Computer(P, A, B)
        )
        # TODO review .inside
        inside = sum(map(lambda d: d.inside, diagram), ())
        Diagram.__init__(self, inside, X @ A, B)

    def partial_ev(self):
        return self.partial_ev_diagram

class Interpreter(Program):
    """
    Sec 2.2: The program evaluators are computable functions representing typed interpreters. The type P is the set of program expressions.
    Ex 2.5.2: C_P's program evaluators correspond to P's interpreters.
    Sec 6.2.2: programs that implement universal evaluators are called interpreters.
    """


class Specializer(Metaprogram):
    """
    Ex 2.5.2: C_P's partial evaluators correspond to P's specializers.
    Sec 6.2.2: metaprograms that implement partial evaluators
    """
    def partial_ev(self, X):
        raise NotImplementedError()

class Compiler(Metaprogram):
    """Fig 6.4: partially evaluating a specializer on an interpreter gives a compiler."""
    def __init__(self, P: Specializer, X: Interpreter):
        """"""
    def partial_ev(self):
        """"""

class ProgramFunctor(Functor):
    """
    Evaluates programs.
    Preserves computer boxes and metaprograms.
    """
    def __call__(self, other):
        if isinstance(other, Program) and callable(getattr(other, "specialize", None)):
            other = other.specialize()
        return Functor.__call__(self, other)


class MetaprogramFunctor(Functor):
    """
    Evaluates metaprograms.
    Preserves computer boxes and programs.
    """
    def __call__(self, other):
        if isinstance(other, Metaprogram) and callable(getattr(other, "specialize", None)):
            return other.specialize()
        return Functor.__call__(self, other)
