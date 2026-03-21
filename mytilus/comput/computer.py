"""Monoidal-computer core layered over the Chapter 1 wire calculus."""

from discopy import cat, monoidal

from ..wire.functions import Box, Category, Functor
from ..wire.services import Copy, Delete, Swap
from ..wire.types import Diagram, Id, Ty


class ProgramOb(cat.Ob):
    """Distinguished atomic object for program wires."""


class ProgramTy(Ty):
    """Distinguished type constructor for program objects."""

    def __init__(self, name):
        Ty.__init__(self, ProgramOb(name))


class ComputableFunction(Box):
    """
    An X-parametrized computation XxA→B.
    X: state, A: input, B: output.
    Fig 6.1: program encoding.
    Figure 2: Computation as a conversation.
    """
    def __init__(self, name, X, A, B):
        Box.__init__(self, name, X @ A, B)


class Program(Box):
    """
    Eq. 2.2: an X-parametrized program, 
    presented as a cartesian function G:X⊸P 
    """
    def __init__(self, name, P: ProgramTy, X: Ty):
        Box.__init__(self, name, dom=X, cod=P)


class Computer(Box):
    """
    The program evaluators are computable functions, representing typed interpreters.
    2.2.1.1 Program evaluators are universal parametrized functions
    2.5.1 c) Program evaluator {}:P×A→B (default type P)
    """
    def __init__(self, P: ProgramTy, A: Ty, B: Ty):
        self.P, self.A, self.B = P, A, B
        Box.__init__(self, "{}", P @ A, B)


class Uncurry(monoidal.Bubble, Box):
    """
    Fig. 2.7 right-hand-side syntax: a composition-program box followed by eval.

    - `Uncurry((;), A, B, C)` stands for `((;) @ A) >> {}_{A,C}`
      with type `P×P×A⊸C`.
    - `Uncurry((||), A, U, B, V)` stands for `((||) @ A×U) >> {}_{A×U,B×V}`
      with type `P×P×A×U⊸B×V`.
    """
    def __init__(self, box, A, B):
        dom, cod = box.dom @ A, B
        # Keep uncurry as a typed layered diagram, analogous to closed.Curry.
        arg = box.bubble(dom=dom, cod=cod)
        monoidal.Bubble.__init__(self, arg, dom=dom, cod=cod, drawing_name="$\\Lambda^{-1}$")
        Box.__init__(self, f"uncurry({box.name})", dom, cod)
