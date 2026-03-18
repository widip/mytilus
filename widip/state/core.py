"""Generic Chapter 7 stateful process structure."""

from discopy import monoidal, python

from ..comput import computer


class StateUpdateMap(computer.Box):
    """The Eq. 7.1 state-update projection sta(q) : X x A -> X."""

    def __init__(self, name: str, X: computer.Ty, A: computer.Ty):
        self.process_name, self.X, self.A = name, X, A
        computer.Box.__init__(self, f"sta({name})", X @ A, X)


class InputOutputMap(computer.Box):
    """The Eq. 7.1 output projection out(q) : X x A -> B."""

    def __init__(self, name: str, X: computer.Ty, A: computer.Ty, B: computer.Ty):
        self.process_name, self.X, self.A, self.B = name, X, A, B
        computer.Box.__init__(self, f"out({name})", X @ A, B)


class Process(computer.Diagram):
    """
    Eq. 7.1: a process q : X x A -> X x B is paired from state update and output.
    """

    def __init__(
        self,
        name,
        X: computer.Ty,
        A: computer.Ty,
        B: computer.Ty,
    ):
        self.name, self.X, self.A, self.B = name, X, A, B

        diagram = (
            computer.Copy(X @ A),
            self.state_update_diagram() @ self.output_diagram(),
        )
        inside = sum((d.inside for d in diagram), ())
        computer.Diagram.__init__(self, inside, X @ A, X @ B)

    def state_update_diagram(self):
        """Eq. 7.1 state-update component."""
        return StateUpdateMap(self.name, self.X, self.A)

    def output_diagram(self):
        """Eq. 7.1 output component."""
        return InputOutputMap(self.name, self.X, self.A, self.B)


class Execution(Process):
    """
    Sec. 7.3: program execution is a process P x A -> P x B.
    """

    def __init__(
        self,
        name: str,
        P: computer.ProgramTy,
        A: computer.Ty,
        B: computer.Ty,
    ):
        Process.__init__(
            self,
            name,
            P,
            A,
            B,
        )

    def universal_ev(self):
        """
        Eq. 7.3: program execution is the evaluator with output type P x B.
        """
        return computer.Computer(self.X, self.A, self.X @ self.B)

    def specialize(self):
        return self.universal_ev()


class ProcessRunner(monoidal.Functor):
    """Python interpretation of the generic Eq. 7.1 process projections."""

    def __init__(self, ob):
        monoidal.Functor.__init__(
            self,
            ob=ob,
            ar=self.ar_map,
            dom=computer.Category(),
            cod=python.Category(),
        )

    def process_ar_map(self, box, dom, cod):
        """Interpret the non-state-specific boxes of a process diagram."""
        raise TypeError(f"unsupported process box: {box!r}")

    @staticmethod
    def _state_update(state, _input):
        return state

    @staticmethod
    def _output(state, input_value):
        return state(input_value)

    def projection_ar_map(self, box, dom, cod):
        """Interpret the generic Eq. 7.1 state projections."""
        if isinstance(box, StateUpdateMap):
            return python.Function(self._state_update, dom, cod)
        if isinstance(box, InputOutputMap):
            return python.Function(self._output, dom, cod)
        return None

    def structural_ar_map(self, box, dom, cod):
        """Interpret the generic structural boxes of process diagrams."""
        del cod
        if isinstance(box, computer.Copy):
            return python.Function.copy(dom, n=2)
        if isinstance(box, computer.Delete):
            return python.Function.discard(dom)
        if isinstance(box, computer.Swap):
            return python.Function.swap(self(box.left), self(box.right))
        return None

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)
        projection = self.projection_ar_map(box, dom, cod)
        structural = self.structural_ar_map(box, dom, cod)

        if projection is not None:
            return projection
        if structural is not None:
            return structural
        return self.process_ar_map(box, dom, cod)


def map_process_box(box, ob):
    """Transport a process projection box along an object mapping."""
    if isinstance(box, StateUpdateMap):
        return StateUpdateMap(box.process_name, ob(box.X), ob(box.A))
    if isinstance(box, InputOutputMap):
        return InputOutputMap(box.process_name, ob(box.X), ob(box.A), ob(box.B))
    return box


def simulate(q: Process, s: computer.Diagram):
    """
    Fig. 7.2: a simulation along s is postcomposition with s x id_B.
    """
    return q >> s @ q.B


def execute(Q: computer.Diagram, A: computer.Ty, B: computer.Ty):
    """
    Sec. 7.3: execute an X-parameterized program as a stateful process.
    """
    return Q @ A >> Execution(
        "{}",
        Q.cod,
        A,
        B,
    )


def fixed_state(g: computer.Diagram):
    """
    Sec. 7.4 proof b: lift g : X x A -> B to the fixed-state process X x A -> X x B.
    """
    X = g.dom[:1]
    A = g.dom[1:]
    return computer.Copy(X) @ A >> X @ g
