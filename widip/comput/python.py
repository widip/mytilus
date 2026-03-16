from discopy import closed, markov, monoidal

from . import computer


class PythonComputationCategory(closed.Category, markov.Category):
    """"""


class PythonComputationFunctor(monoidal.Functor):
    """
    Transforms computer diagrams into lower-level runnable diagrams.
    Preserves computations including closed and markov boxes.
    """

    def __init__(self):
        monoidal.Functor.__init__(
            self,
            self.ob_map,
            self.ar_map,
            dom=computer.Category(),
            cod=PythonComputationCategory(),
        )

    def __call__(self, other):
        if hasattr(other, "partial_ev") and callable(other.partial_ev) and hasattr(other, "universal_ev") and callable(other.universal_ev):
            arg = other.universal_ev()
            return closed.Curry(arg, len(arg.dom))
        if hasattr(other, "universal_ev") and callable(other.universal_ev):
            return other.universal_ev()
        return other

    def ob_map(self, ob):
        return ob

    def ar_map(self, ar):
        return ar


to_py = PythonComputationFunctor()
