"""Chapter 2 helper equations for evaluator-based program semantics."""

from . import computer


def run(program_ty: computer.ProgramTy, A: computer.Ty, B: computer.Ty):
    """Eq. 2.15 in evaluator form: an evaluator for language ``program_ty``."""
    return computer.Computer(program_ty, A, B)


def eval_f(program_ty: computer.ProgramTy, A: computer.Ty, B: computer.Ty):
    """Eq. 2.15: evaluator for computations on ``A -> B`` in language ``program_ty``."""
    return computer.Computer(program_ty, A, B)


def parametrize(g: computer.Diagram, program_ty: computer.ProgramTy):
    """
    Eq. 2.2 in evaluator form: turn a parametrized computation into program+eval.
    """
    G = g.curry(left=False)
    A = g.dom[1:]
    return G >> computer.Computer(program_ty, A, g.cod)


def reparametrize(g: computer.Diagram, s: computer.Diagram, program_ty: computer.ProgramTy):
    """
    Fig. 2.3 in evaluator form: reparametrize x along ``s:Y⊸X``.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> computer.Computer(program_ty, A, g.cod)


def substitute(g: computer.Diagram, s: computer.Diagram, program_ty: computer.ProgramTy):
    """
    Fig. 2.3 in evaluator form: substitute for ``a`` along ``s:C→A``.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> computer.Computer(program_ty, A, g.cod)


def constant_a(f: computer.Diagram):
    """Sec. 2.2.1.3 a) f:I×A→B."""
    return f.curry(0, left=False)


def constant_b(f: computer.Diagram):
    """Sec. 2.2.1.3 b) f:A×I→B."""
    return f.curry(1, left=False)
