"""Chapter 7: Stateful computing."""

from . import computer


class Process(computer.Diagram):
    """
    Eq. 7.1: a process q : X x A -> X x B is paired from state update and output.
    """

    def __init__(self, name, X: computer.Ty, A: computer.Ty, B: computer.Ty):
        self.name, self.X, self.A, self.B = name, X, A, B
        self.state_update_diagram = computer.Box(f"sta({name})", X @ A, X)
        self.output_diagram = computer.Box(f"out({name})", X @ A, B)

        diagram = (
            computer.Copy(X @ A),
            self.state_update_diagram @ self.output_diagram,
        )
        inside = sum((d.inside for d in diagram), ())
        computer.Diagram.__init__(self, inside, X @ A, X @ B)

    def sta(self):
        return self.state_update_diagram

    def out(self):
        return self.output_diagram


class Execution(Process):
    """
    Sec. 7.3: program execution is a process P x A -> P x B.
    """

    def __init__(self, P: computer.ProgramTy, A: computer.Ty, B: computer.Ty):
        self.universal_ev_diagram = computer.Computer(P, A, P @ B)
        Process.__init__(self, "{}", P, A, B)

    def universal_ev(self):
        """
        Eq. 7.3: program execution is the evaluator with output type P x B.
        """
        return self.universal_ev_diagram

    def specialize(self):
        return self.universal_ev()


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
        return computer.Computer(self.program_ty, A, B)

    def execution(self, A: computer.Ty, B: computer.Ty):
        return Execution(self.program_ty, A, B)


def sta(q):
    """Projection to the state-update component of a process."""
    if hasattr(q, "sta") and callable(q.sta):
        return q.sta()
    raise TypeError("sta expects a state.Process")


def out(q):
    """Projection to the output component of a process."""
    if hasattr(q, "out") and callable(q.out):
        return q.out()
    raise TypeError("out expects a state.Process")


def simulate(q: Process, s: computer.Diagram):
    """
    Fig. 7.2: a simulation along s is postcomposition with s x id_B.
    """
    return q >> s @ q.B


def execute(Q: computer.Diagram, A: computer.Ty, B: computer.Ty):
    """
    Sec. 7.3: execute an X-parameterized program as a stateful process.
    """
    return Q @ A >> Execution(Q.cod, A, B)


def fixed_state(g: computer.Diagram):
    """
    Sec. 7.4 proof b: lift g : X x A -> B to the fixed-state process X x A -> X x B.
    """
    X = g.dom[:1]
    A = g.dom[1:]
    return computer.Copy(X) @ A >> X @ g
