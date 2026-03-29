"""Chapter 2 bubble constructors for the Run language."""

from discopy import monoidal
from . import computer


class Partial(monoidal.Bubble):
    """
    Sec. 2.2.2. []:P×X⊸P as a partial-evaluation combinator.
    """

    def __init__(self, gamma, X: computer.Ty, A: computer.Ty, B: computer.Ty, P: computer.ProgramTy, name="partial"):
        self.gamma, self.X, self.A, self.B, self.P = gamma, X, A, B, P
        self.bubble_diagram = self.gamma @ self.X @ self.A >> computer.Computer(self.P, self.X @ self.A, self.B)
        monoidal.Bubble.__init__(self, self.bubble_diagram, dom=self.bubble_diagram.dom, cod=self.bubble_diagram.cod)
        self.name = name

    def specialize(self):
        """Fig. 2.5: compile partial-evaluator box as direct universal evaluation."""
        return self.bubble_diagram


class Sequential(monoidal.Bubble):
    """
    Sec. 2.2.3. (;)_ABC:P×P⊸P.
    """

    def __init__(self, F, G, A: computer.Ty, B: computer.Ty, C: computer.Ty, P: computer.ProgramTy):
        self.F, self.G = F, G
        self.A, self.B, self.C, self.P = A, B, C, P
        self.bubble_diagram = (
            G @ F @ A
            >> computer.Id(P) @ computer.Computer(P, A, B)
            >> computer.Computer(P, B, C)
        )
        monoidal.Bubble.__init__(self, self.bubble_diagram, dom=self.bubble_diagram.dom, cod=self.bubble_diagram.cod, draw_vertically=True)
        self.name = "(;)"

    def specialize(self):
        """Fig. 2.7: sequential composition of programs."""
        return self.bubble_diagram


class Parallel(monoidal.Bubble):
    """
    Sec. 2.2.3. (||)_AUBV:P×P⊸P.
    """

    def __init__(
        self,
        F,
        T,
        A: computer.Ty,
        U: computer.Ty,
        B: computer.Ty,
        V: computer.Ty,
        P: computer.ProgramTy,
    ):
        self.F, self.T = F, T
        self.A, self.U, self.B, self.V, self.P = A, U, B, V, P
        self.bubble_diagram = (
            F @ T @ A @ U
            >> computer.Id(P) @ computer.Swap(P, A) @ U
            >> computer.Computer(P, A, B) @ computer.Computer(P, U, V)
        )
        monoidal.Bubble.__init__(self, self.bubble_diagram, dom=self.bubble_diagram.dom, cod=self.bubble_diagram.cod, draw_vertically=True)
        self.name = "(||)"

    def specialize(self):
        """Fig. 2.7: parallel composition of programs."""
        return self.bubble_diagram


class Data(computer.Box):
    """
    Eq. 2.6. ⌜−⌝ : A⊸P.
    If value is provided, it acts as a closed literal I -> P.
    Historically called Quote in Chapter 2, but deduplicated to 'Data' here.
    """

    def __init__(self, P: computer.ProgramTy, A: computer.Ty = computer.Ty(), value=None, name=None):
        self.P, self.A, self.value = P, A, value
        computer.Box.__init__(self, name or "⌜data⌝", dom=A, cod=P)


class Idempotent(monoidal.Bubble):
    """
    Eq. 2.8: ρ_A = ⌜{ }_A⌝ : P -> P. 
    Filters programs by the type A via the retraction ρ_A = incl_A ○ retr^A.
    """

    def __init__(self, A, P: computer.ProgramTy):
        self.A = A if isinstance(A, computer.Ty) else computer.Ty(A)
        self.P = P
        self.bubble_diagram = computer.Computer(self.P, computer.Ty(), self.A) >> Data(self.P, self.A)
        monoidal.Bubble.__init__(self, self.bubble_diagram, dom=self.bubble_diagram.dom, cod=self.bubble_diagram.cod)
        self.name = f"ρ({self.A})"

    def specialize(self):
        """Eq. 2.8: compile the idempotent filter into its retraction components."""
        return self.bubble_diagram


class Quote(monoidal.Bubble):
    """
    Eq. 2.6. ⌜−⌝ : A⊸P and {}:P×I→A.
    The uncurried retraction Quote = id_A.
    """

    def __init__(self, A, P: computer.ProgramTy):
        self.A = A if isinstance(A, computer.Ty) else computer.Ty(A)
        self.P = P
        # Retraction property: eval ○ quote = id
        self.bubble_diagram = Data(self.P, self.A) >> computer.Computer(self.P, computer.Ty(), self.A)
        monoidal.Bubble.__init__(self, self.bubble_diagram, dom=self.bubble_diagram.dom, cod=self.bubble_diagram.cod)
        self.name = "quote"

    def specialize(self):
        """Eq. 2.6: uncurried retraction property."""
        return computer.Id(self.A)
