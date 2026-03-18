"""Language-agnostic metaprogram abstractions and Futamura equations."""

from ..comput.computer import Box, Computer, ComputableFunction, Diagram, Functor, Program, ProgramTy, Ty


class Metaprogram(Box):
    """
    A metaprogram, presented as a cartesian function G:I⊸P.
    """

    def __init__(self, name, P: ProgramTy):
        Box.__init__(self, name, dom=Ty(), cod=P)


class SpecializerBox(Metaprogram):
    """Generic native specializer box: ``S : I -> P``."""

    def __init__(self, P: ProgramTy, name="S"):
        Metaprogram.__init__(self, name, P)


class InterpreterBox(Metaprogram):
    """Generic native interpreter box: ``H : I -> P``."""

    def __init__(self, P: ProgramTy, name="H"):
        Metaprogram.__init__(self, name, P)


class Specializer(Functor):
    """A functorial metaprogram with unit parameter type."""

    @staticmethod
    def metaprogram_dom():
        return Ty()

    def __init__(self, ob=None, ar=None, *, dom=None, cod=None):
        Functor.__init__(
            self,
            self.ob_map if ob is None else ob,
            self.ar_map if ar is None else ar,
            dom=Functor.dom if dom is None else dom,
            cod=Functor.cod if cod is None else cod,
        )

    @staticmethod
    def ob_map(ob):
        return ob

    @staticmethod
    def ar_map(ar):
        return ar

    def specialize(self, *args, **kwargs):
        return self(*args, **kwargs)


class Interpreter(Functor):
    """A functorial interpreter with unit metaprogram domain."""

    @staticmethod
    def metaprogram_dom():
        return Ty()

    def __init__(self, ob=None, ar=None, *, dom=None, cod=None):
        Functor.__init__(
            self,
            self.ob_map if ob is None else ob,
            self.ar_map if ar is None else ar,
            dom=Functor.dom if dom is None else dom,
            cod=Functor.cod if cod is None else cod,
        )

    @staticmethod
    def ob_map(ob):
        return ob

    @staticmethod
    def ar_map(ar):
        return ar

    def interpret(self, *args, **kwargs):
        return self(*args, **kwargs)


class ProgramComputation(Diagram):
    """
    Section 3.1: a function is computable when it is programmable.
    Fig 6.1: A computation f encoded such that f = {F}.
    """

    def __init__(self, name, P: ProgramTy, X: Ty, A: Ty, B: Ty):
        """
        Running a given program is a routine operation.
        Every function is computable, in the sense that there is a program for it.
        """
        self.universal_ev_diagram = ComputableFunction("{" + name + "}", X, A, B)
        diagram = (
            Program(name, P, X) @ A,
            Computer(P, A, B),
        )
        inside = sum(map(lambda d: d.inside, diagram), ())
        Diagram.__init__(self, inside, X @ A, B)

    def universal_ev(self):
        return self.universal_ev_diagram

    def specialize(self):
        """Pure wiring rewrite from a program layer to its encoded computation."""
        return self.universal_ev()


class MetaprogramComputation(Diagram):
    """
    Fig 6.1: A program F encoded such that F = {ℱ}.
    """

    def __init__(self, name, P: ProgramTy, PP: ProgramTy, X: Ty, A: Ty, B: Ty):
        self.universal_ev_diagram = ComputableFunction("{{" + name + "}}", X, A, B)
        self.partial_ev_diagram = (
            ProgramComputation("{" + name + "}", PP, Ty(), X, P) @ A
            >> Computer(P, A, B)
        )
        diagram = (
            Program(name, PP, Ty()) @ X @ A,
            Computer(PP, X, P) @ A,
            Computer(P, A, B),
        )
        inside = sum(map(lambda d: d.inside, diagram), ())
        Diagram.__init__(self, inside, X @ A, B)

    def universal_ev(self):
        return self.universal_ev_diagram

    def partial_ev(self):
        return self.partial_ev_diagram

    def specialize(self):
        """Pure wiring rewrite from a metaprogram layer to partial evaluation."""
        return self.partial_ev()


class ProgramFunctor:
    """
    Pure wiring transformation that strips one program-evaluation layer.
    """

    def __call__(self, other):
        if isinstance(other, ProgramComputation):
            return other.specialize()
        return other


class MetaprogramFunctor:
    """
    Pure wiring transformation that strips one metaprogram-evaluation layer.
    """

    def __call__(self, other):
        if isinstance(other, MetaprogramComputation):
            return other.specialize()
        return other


def sec_6_2_2_partial_application(
    program,
    static_input,
    *,
    specializer_box,
    evaluator_box,
    evaluator,
):
    """Sec. 6.2.2 as a diagram: ``pev(X, y)``."""
    return (
        (specializer_box @ program >> evaluator_box) @ static_input
        >> evaluator(static_input.cod, specializer_box.cod)
    )


def eq_2(
    program,
    static_input,
    *,
    specializer_box,
    evaluator_box,
    evaluator,
):
    """Eq. (2): ``pev X y = uev S (X, y)``."""
    return sec_6_2_2_partial_application(
        program,
        static_input,
        specializer_box=specializer_box,
        evaluator_box=evaluator_box,
        evaluator=evaluator,
    )


def eq_3(
    program,
    static_input,
    *,
    specializer_box,
    evaluator_box,
    evaluator,
):
    """Eq. (3): ``uev S (X, y) = uev (pev S X) y``."""
    return (
        ((specializer_box @ specializer_box >> evaluator_box) @ program >> evaluator_box)
        @ static_input
        >> evaluator(static_input.cod, specializer_box.cod)
    )


def first_futamura_projection(interpreter, *, specializer_box, evaluator_box):
    """`C1` as a diagram: partially evaluate the specializer on an interpreter."""
    return specializer_box @ interpreter >> evaluator_box


def eq_4(interpreter, *, specializer_box, evaluator_box):
    """Eq. (4): ``C2 = pev S H = uev S (S, H)``."""
    return (specializer_box @ specializer_box >> evaluator_box) @ interpreter >> evaluator_box


def compiler(interpreter, *, specializer_box, evaluator_box):
    """`C2`: second Futamura projection as a diagram."""
    return eq_4(interpreter, specializer_box=specializer_box, evaluator_box=evaluator_box)


def compiler_generator(*, specializer_box, evaluator_box):
    """`C3 = pev S S`: third Futamura projection as a diagram."""
    return specializer_box @ specializer_box >> evaluator_box


def eq_5(interpreter, *, specializer_box, evaluator_box):
    """Eq. (5): ``uev S (S, H) = uev (pev S S) H``."""
    return (
        compiler_generator(specializer_box=specializer_box, evaluator_box=evaluator_box)
        @ interpreter
        >> evaluator_box
    )
