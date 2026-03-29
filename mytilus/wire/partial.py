"""Typed partial category for runtime interpretation without ``discopy.python``."""

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial

from discopy.cat import Composable
from discopy.utils import (
    Whiskerable,
    assert_iscomposable,
    assert_isinstance,
    classproperty,
    tuplify,
    untuplify,
)

Ty = tuple[type, ...]


def _identity(*xs):
    return untuplify(xs)


def _outputs(cod: Ty, result):
    if len(cod) != 1:
        return tuplify(result)
    if isinstance(result, tuple) and len(result) == 1:
        return result
    return (result,)


def _term(inside: Callable):
    return inside if isinstance(inside, partial) else partial(inside)


def _then_inside(left_term, left_cod: Ty, right_term, *args):
    return right_term(*_outputs(left_cod, left_term(*args)))


def _tensor_inside(left_term, split: int, left_cod: Ty, right_term, right_cod: Ty, *xs):
    left_xs, right_xs = xs[:split], xs[split:]
    return untuplify(
        _outputs(left_cod, left_term(*left_xs)) + _outputs(right_cod, right_term(*right_xs))
    )


def _swap_inside(left: Ty, *xs):
    pivot = len(left)
    return untuplify(tuplify(xs)[pivot:] + tuplify(xs)[:pivot])


def _copy_inside(n: int, *xs):
    return n * xs


@dataclass
class PartialArrow(Composable[type], Whiskerable):
    """Python partial term with typed sequential and monoidal composition."""

    inside: Callable
    dom: Ty
    cod: Ty

    type_checking = True

    def __init__(self, inside: Callable, dom: type, cod: type):
        self.inside = _term(inside)
        self.dom = tuplify(dom)
        self.cod = tuplify(cod)

    @classmethod
    def id(cls, dom: type) -> "PartialArrow":
        return cls(_identity, tuplify(dom), tuplify(dom))

    def __call__(self, *xs):
        if self.type_checking:
            if len(xs) != len(self.dom):
                raise ValueError((self.dom, xs))
            for x, t in zip(xs, self.dom):
                if not callable(x):
                    assert_isinstance(x, t)
        ys = self.inside(*xs)
        if self.type_checking:
            if len(self.cod) != 1 and (
                not isinstance(ys, tuple) or len(self.cod) != len(ys)
            ):
                raise RuntimeError((self.cod, ys))
            for y, t in zip(_outputs(self.cod, ys), self.cod):
                if not callable(y):
                    assert_isinstance(y, t)
        return ys

    def then(self, other: "PartialArrow") -> "PartialArrow":
        assert_isinstance(other, type(self))
        assert_iscomposable(self, other)
        return type(
            self
        )(partial(_then_inside, self.inside, self.cod, other.inside), self.dom, other.cod)

    def tensor(self, other: "PartialArrow") -> "PartialArrow":
        return type(self)(
            partial(
                _tensor_inside,
                self.inside,
                len(self.dom),
                self.cod,
                other.inside,
                other.cod,
            ),
            self.dom + other.dom,
            self.cod + other.cod,
        )

    @staticmethod
    def swap(left: Ty, right: Ty) -> "PartialArrow":
        return PartialArrow(
            partial(_swap_inside, left),
            dom=left + right,
            cod=right + left,
        )

    braid = swap

    @staticmethod
    def copy(dom: Ty, n=2) -> "PartialArrow":
        return PartialArrow(partial(_copy_inside, n), dom=dom, cod=n * dom)

    @staticmethod
    def discard(dom: Ty) -> "PartialArrow":
        return PartialArrow.copy(dom, 0)

    @classproperty
    @contextmanager
    def no_type_checking(cls):
        saved = cls.type_checking
        cls.type_checking = False
        try:
            yield
        finally:
            cls.type_checking = saved


def is_partial_arrow(value) -> bool:
    return isinstance(value, PartialArrow)


class Category:
    ob = Ty
    ar = PartialArrow
