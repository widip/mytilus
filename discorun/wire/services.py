"""Chapter 1 wire services: copying, deleting, swapping, and their functors."""

from .functions import Box, Functor
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


class DataServiceFunctor(Functor):
    """Functor interpreting copy, delete, and swap in a target category."""

    def __init__(self, *, dom=None, cod=None):
        Functor.__init__(
            self,
            self.object,
            self.ar_map,
            dom=Functor.dom if dom is None else dom,
            cod=Functor.cod if cod is None else cod,
        )

    def object(self, ob):
        del self
        return ob

    def copy_ar(self, dom, cod):
        raise TypeError(f"copy service is undefined for dom={dom!r}, cod={cod!r}")

    def delete_ar(self, dom, cod):
        raise TypeError(f"delete service is undefined for dom={dom!r}, cod={cod!r}")

    def swap_ar(self, left, right, dom, cod):
        raise TypeError(
            f"swap service is undefined for left={left!r}, right={right!r}, dom={dom!r}, cod={cod!r}"
        )

    def data_ar(self, box, dom, cod):
        raise TypeError(f"unsupported data-service box: {box!r}")

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)
        if isinstance(box, Copy):
            return self.copy_ar(dom, cod)
        if isinstance(box, Delete):
            return self.delete_ar(dom, cod)
        if isinstance(box, Swap):
            return self.swap_ar(self(box.left), self(box.right), dom, cod)
        return self.data_ar(box, dom, cod)
