"""Chapter 2 bubble constructors for the Run language."""

from discopy import monoidal

from . import computer


class Partial(monoidal.Bubble, computer.Box):
    """
    Sec. 2.2.2. []:P×A⊸P
    A partial evaluator is a (P×Y)-indexed program satisfying {[Γ]y}a = {Γ}(y,a).
    X=P×Y and g:P×Y×A→B
    """

    def __init__(self, gamma):
        self.gamma = gamma
        self.X, self.A = gamma.cod.exponent
        self.B = gamma.cod.base

        arg = (
            self.gamma @ self.X @ self.A
            >> computer.Box("[]", self.gamma.cod @ self.X, self.B << self.A) @ self.A
            >> computer.Eval(self.B << self.A)
        )

        monoidal.Bubble.__init__(self, arg, dom=arg.dom, cod=arg.cod)

    def specialize(self):
        """Fig. 2.5: compile partial-evaluator box as operator + eval."""
        return self.gamma @ self.X @ self.A >> computer.Eval(self.B << self.X @ self.A)


class Sequential(monoidal.Bubble, computer.Box):
    """
    Sec. 2.2.3. (;)_ABC:P×P⊸P
    A -{F;G}→ C = A -{F}→ B -{G}→ C
    """

    def __init__(self, F, G):
        self.F, self.G = F, G
        A = F.cod.exponent
        C = G.cod.base
        arg = (
            F @ G @ A
            >> computer.Box("(;)", F.cod @ G.cod, C << A) @ A
            >> computer.Eval(C << A)
        )

        monoidal.Bubble.__init__(self, arg, dom=arg.dom, draw_vertically=True)

    def specialize(self):
        F, G = self.F, self.G
        A = F.cod.exponent
        B = F.cod.base
        C = G.cod.base

        F_eval = computer.Eval(B << A)
        G_eval = computer.Eval(C << B)
        return G @ F @ A >> (C << B) @ F_eval >> G_eval


class Parallel(monoidal.Bubble, computer.Box):
    """
    Sec. 2.2.3. (||)_AUBV:P×P⊸P
    A×U -{F||H}→ B×V = A -{F}→ B × U-{T}→ V
    """

    def __init__(self, F, T):
        self.F, self.T = F, T
        A, B = F.cod.exponent, F.cod.base
        U, V = T.cod.exponent, T.cod.base
        arg = (
            F @ T @ A @ U
            >> computer.Box("(||)", F.cod @ T.cod, B @ V << A @ U) @ A @ U
            >> computer.Eval(B @ V << A @ U)
        )
        monoidal.Bubble.__init__(self, arg, dom=arg.dom, draw_vertically=True)

    def specialize(self):
        F, T = self.F, self.T
        A, B = F.cod.exponent, F.cod.base
        U, V = T.cod.exponent, T.cod.base

        first = computer.Eval(B << A)
        second = computer.Eval(V << U)
        swap = computer.Swap(V << U, A)
        return F @ T @ A @ U >> (B << A) @ swap @ U >> first @ second


class Data(monoidal.Bubble, computer.Box):
    """
    Eq. 2.6. ⌜−⌝ : A⊸P
    {}: P-→→A
    ⌜a⌝: P
    {⌜a⌝} = a
    """

    def __init__(self, A):
        self.A = A if isinstance(A, computer.Ty) else computer.Ty(A)
        arg = (
            computer.Box("⌜−⌝", self.A, self.A << computer.Ty())
            >> computer.Eval(self.A << computer.Ty())
        )
        monoidal.Bubble.__init__(self, arg, dom=self.A, cod=self.A)

    def specialize(self):
        """Eq. 2.8: compile quoted data using idempotent quote/eval structure."""
        return computer.Id(self.A)
