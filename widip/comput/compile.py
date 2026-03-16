"""Chapter 2 compiler for custom Run-language bubbles."""

from discopy import closed, markov

from . import computer
from .boxes import Data, Parallel, Partial, Sequential


class Compile(closed.Functor, markov.Functor):
    """Pure diagram compilation of custom boxes into closed+markov structure."""

    dom = computer.Category()
    cod = computer.Category()

    def __init__(self):
        super().__init__(ob=lambda ob: ob, ar=self.ar_map)

    def __call__(self, box):
        if isinstance(box, (Sequential, Parallel, Partial, Data)):
            return box.specialize()
        return box

    def ar_map(self, box):
        assert not isinstance(box, computer.Box)
        return box
