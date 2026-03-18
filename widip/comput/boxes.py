"""Chapter 2 bubble constructors for the Run language."""

from discopy import monoidal

from . import computer


class Partial(monoidal.Bubble, computer.Box):
    """
    Sec. 2.2.2. []:P×X⊸P as a partial-evaluation combinator.
    """

    def __init__(self, gamma, X: computer.Ty, A: computer.Ty, B: computer.Ty, P: computer.ProgramTy):
        self.gamma, self.X, self.A, self.B, self.P = gamma, X, A, B, P
        arg = self.gamma @ self.X @ self.A >> computer.Computer(self.P, self.X @ self.A, self.B)
        monoidal.Bubble.__init__(self, arg, dom=arg.dom, cod=arg.cod)

    def specialize(self):
        """Fig. 2.5: compile partial-evaluator box as direct universal evaluation."""
        return self.gamma @ self.X @ self.A >> computer.Computer(self.P, self.X @ self.A, self.B)


class Sequential(monoidal.Bubble, computer.Box):
    """
    Sec. 2.2.3. (;)_ABC:P×P⊸P.
    """

    def __init__(self, F, G, A: computer.Ty, B: computer.Ty, C: computer.Ty, P: computer.ProgramTy):
        self.F, self.G, self.A, self.B, self.C, self.P = F, G, A, B, C, P
        arg = (
            F @ G @ A
            >> computer.Id(P) @ computer.Computer(P, A, B)
            >> computer.Computer(P, B, C)
        )
        monoidal.Bubble.__init__(self, arg, dom=arg.dom, cod=arg.cod, draw_vertically=True)

    def specialize(self):
        return (
            self.G @ self.F @ self.A
            >> computer.Id(self.P) @ computer.Computer(self.P, self.A, self.B)
            >> computer.Computer(self.P, self.B, self.C)
        )


class Parallel(monoidal.Bubble, computer.Box):
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
        arg = (
            F @ T @ A @ U
            >> computer.Id(P) @ computer.Swap(P, A) @ U
            >> computer.Computer(P, A, B) @ computer.Computer(P, U, V)
        )
        monoidal.Bubble.__init__(self, arg, dom=arg.dom, cod=arg.cod, draw_vertically=True)

    def specialize(self):
        return (
            self.F @ self.T @ self.A @ self.U
            >> computer.Id(self.P) @ computer.Swap(self.P, self.A) @ self.U
            >> computer.Computer(self.P, self.A, self.B) @ computer.Computer(self.P, self.U, self.V)
        )


class Data(monoidal.Bubble, computer.Box):
    """
    Eq. 2.6. ⌜−⌝ : A⊸P and {}:P×I→A.
    """

    def __init__(self, A, P: computer.ProgramTy):
        self.A = A if isinstance(A, computer.Ty) else computer.Ty(A)
        self.P = P
        arg = computer.Box("⌜−⌝", self.A, self.P) >> computer.Computer(self.P, computer.Ty(), self.A)
        monoidal.Bubble.__init__(self, arg, dom=self.A, cod=self.A)

    def specialize(self):
        """Eq. 2.8: compile quoted data using idempotent quote/eval structure."""
        return computer.Id(self.A)
