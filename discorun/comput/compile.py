"""Backward-compatible compiler facade for Run-language bubbles."""

from ..metaprog.compile import RunSpecializer


class Compile(RunSpecializer):
    """Preserve the historical compiler class API at the old import path."""
