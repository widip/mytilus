"""Chapter 8: Program-closed categories."""

from ..comput import computer


class MonoidalComputer(computer.Category):
    """
    The ambient computer category may contain more than one program language type.
    """


class ProgramClosedCategory(MonoidalComputer):
    """
    Sec. 8.3: a program-closed category chooses one distinguished program type.
    """

    def __init__(self, program_ty: computer.ProgramTy):
        self.program_ty = program_ty
        MonoidalComputer.__init__(self)

    def evaluator(self, A: computer.Ty, B: computer.Ty):
        # Eq. 7.3 / Eq. 8.1 interface: evaluator is the output projection of execution.
        return self.execution(A, B).output_diagram()

    def run(self, A: computer.Ty, B: computer.Ty):
        """Sec. 8.3 c'': program execution machine ``Run``."""
        from ..state.core import execute

        return execute(computer.Id(self.program_ty), A, B)

    def is_program(self, ob):
        """Check whether ``ob`` is this category's distinguished program type."""
        return ob == self.program_ty

    def is_evaluator(self, arrow):
        """Check whether ``arrow`` is this category's evaluator box."""
        if isinstance(arrow, computer.Computer) and self.is_program(arrow.P):
            return True
        return (
            getattr(arrow, "process_name", None) is not None
            and self.is_program(getattr(arrow, "X", None))
            and hasattr(arrow, "A")
            and hasattr(arrow, "B")
            and getattr(arrow, "dom", None) == arrow.X @ arrow.A
            and getattr(arrow, "cod", None) == arrow.B
        )

    def _simulate_type(self, ty, codomain: "ProgramClosedCategory"):
        """Transport program occurrences in a type along a language simulation."""
        if self.is_program(ty):
            return codomain.program_ty
        if not isinstance(ty, computer.Ty):
            return ty
        source_atom = self.program_ty.inside[0]
        target_program = codomain.program_ty
        mapped = computer.Ty()
        changed = False
        for atom in ty.inside:
            if atom == source_atom:
                mapped = mapped @ target_program
                changed = True
            else:
                mapped = mapped @ computer.Ty(atom)
        return mapped if changed else ty

    def simulate(self, item, codomain: "ProgramClosedCategory"):
        """
        Chapter 8: transport programs/evaluators to another program-closed category.
        """
        if self.is_evaluator(item):
            return codomain.evaluator(
                self._simulate_type(item.A, codomain),
                self._simulate_type(item.B, codomain),
            )
        return self._simulate_type(item, codomain)

    def execution(self, A: computer.Ty, B: computer.Ty):
        from ..state.core import Execution

        return Execution(
            "{}",
            self.program_ty,
            A,
            B,
        )
