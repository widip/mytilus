"""Generic Chapter 7 stateful process structure."""

from discopy import monoidal

from ..comput import computer
from ..metaprog import core as metaprog_core
from ..pcc.core import ProgramClosedCategory


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
        return fixed_state(self.output_diagram())

    def specialize(self):
        return self.universal_ev()


class ProcessRunner(monoidal.Functor):
    """Base interpreter of Eq. 7.1 process projections and wiring."""

    def __init__(self, cod):
        monoidal.Functor.__init__(
            self,
            ob=self.object,
            ar=self.ar_map,
            dom=computer.Category(),
            cod=cod,
        )

    def object(self, ob):
        del self
        return ob

    def process_ar_map(self, box, dom, cod):
        """Interpret the non-state-specific boxes of a process diagram."""
        raise TypeError(f"unsupported process box: {box!r}")

    def state_update_ar(self, dom, cod):
        """Interpret Eq. 7.1 ``sta`` arrows in the target category."""
        raise TypeError(f"state-update interpretation is undefined for dom={dom!r}, cod={cod!r}")

    def output_ar(self, dom, cod):
        """Interpret Eq. 7.1 ``out`` arrows in the target category."""
        raise TypeError(f"output interpretation is undefined for dom={dom!r}, cod={cod!r}")

    def map_projection(self, box, dom, cod):
        """Interpret the generic Eq. 7.1 state projections."""
        if isinstance(box, StateUpdateMap):
            return self.state_update_ar(dom, cod)
        if isinstance(box, InputOutputMap):
            return self.output_ar(dom, cod)
        return None

    def map_structural(self, box, dom, cod):
        """Interpret structural boxes in the target category."""
        del box, dom, cod
        return None

    def map_shared_ar(self, box, dom, cod):
        """Shared mapping for Eq. 7.1 projections and structural wiring."""
        projection = self.map_projection(box, dom, cod)
        if projection is not None:
            return projection
        return self.map_structural(box, dom, cod)

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)
        shared = self.map_shared_ar(box, dom, cod)
        if shared is not None:
            return shared
        return self.process_ar_map(box, dom, cod)


class ProcessSimulation(metaprog_core.Specializer):
    """Fig. 7.2 simulation as a state-aware diagrammatic transformation."""

    def __init__(self):
        metaprog_core.Specializer.__init__(
            self,
            dom=computer.Category(),
            cod=computer.Category(),
        )

    def simulation(self, item):
        """Simulation action on objects and non-projection arrows."""
        del self
        return item

    def sta(self, state_update: StateUpdateMap):
        """Eq. 7.1 state projection transport along a simulation."""
        return StateUpdateMap(
            state_update.process_name,
            self.simulation(state_update.X),
            self.simulation(state_update.A),
        )

    def out(self, output: InputOutputMap):
        """Eq. 7.1 output projection transport along a simulation."""
        return InputOutputMap(
            output.process_name,
            self.simulation(output.X),
            self.simulation(output.A),
            self.simulation(output.B),
        )

    def _identity_object(self, ob):
        return self.simulation(ob)

    def _identity_arrow(self, ar):
        if isinstance(ar, StateUpdateMap):
            return self.sta(ar)
        if isinstance(ar, InputOutputMap):
            return self.out(ar)
        return self.simulation(ar)


def simulate(q: computer.Diagram, s: computer.Diagram):
    """
    Fig. 7.2: a simulation along s is postcomposition with s x id_B.
    """
    if isinstance(q, Process):
        B = q.B
    else:
        if q.cod[:1] != s.dom:
            raise TypeError(f"simulation codomain mismatch: {q.cod!r} vs {s.dom!r}")
        B = q.cod[1:]
    if q.cod != s.dom @ B:
        raise TypeError(f"simulation codomain mismatch: {q.cod!r} vs {s.dom @ B!r}")
    return q >> s @ B


def execute(Q: computer.Diagram, A: computer.Ty, B: computer.Ty):
    """
    Sec. 7.3: execute an X-parameterized program as a stateful process.
    """
    stateful_evaluator = ProgramClosedCategory(Q.cod).execution(A, B).specialize()
    return Q @ A >> simulate(stateful_evaluator, computer.Id(Q.cod))


def fixed_state(g: computer.Diagram):
    """
    Sec. 7.4 proof b: lift g : X x A -> B to the fixed-state process X x A -> X x B.
    """
    X = g.dom[:1]
    A = g.dom[1:]
    return computer.Copy(X) @ A >> X @ g
