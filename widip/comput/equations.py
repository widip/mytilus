"""Chapter 2 helper equations for the Run language."""

from . import computer


def run(G: computer.Diagram, A: computer.Ty, B: computer.Ty):
    """Eq. 2.15: an X-natural family of surjections C(X × A, B) --→ C•(X,P)."""
    del G
    return computer.Eval(A, B)


def eval_f(G: computer.Diagram):
    """Eq. 2.15: evaluators as surjections from programs to computations."""
    return computer.Eval(G.dom, G.cod)


def parametrize(g: computer.Diagram):
    """
    Eq. 2.2: present an X-parametrized computation as a program G:X⊸P.
    """
    G = g.curry(left=False)
    A = g.dom[1:]
    return G >> computer.Eval(G.cod @ A >> g.cod)


def reparametrize(g: computer.Diagram, s: computer.Diagram):
    """
    Fig. 2.3: reparametrize x along s:Y⊸X to obtain a Y-indexed family.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> computer.Eval(Gs.cod @ A >> g.cod)


def substitute(g: computer.Diagram, s: computer.Diagram):
    """
    Fig. 2.3: substitute for a along t:C→A while keeping the same parameter space.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> computer.Eval(Gs.cod @ A >> g.cod)


def constant_a(f: computer.Diagram):
    """Sec. 2.2.1.3 a) f:I×A→B. f(a) = {Φ_a}()."""
    return f.curry(0, left=False)


def constant_b(f: computer.Diagram):
    """Sec. 2.2.1.3 b) f:A×I→B. f(a) = {F}(a)."""
    return f.curry(1, left=False)
