"""Chapter 1 wire services: copying, deleting, and swapping."""

from .functions import Box
from .types import Ty


class Copy(Box):
    """Copying data service: ``A -> A @ A``."""

    def __init__(self, A):
        Box.__init__(self, "∆", A, A @ A, draw_as_spider=True, drawing_name="")


class Delete(Box):
    """Deleting data service: ``A -> I``."""

    def __init__(self, A):
        Box.__init__(self, "⊸", A, Ty(), draw_as_spider=True, drawing_name="")


class Swap(Box):
    """Symmetry isomorphism swapping adjacent wires."""

    def __init__(self, left, right):
        self.left, self.right = left, right
        Box.__init__(
            self,
            "Swap",
            left @ right,
            right @ left,
            draw_as_wires=True,
            drawing_name="",
        )
