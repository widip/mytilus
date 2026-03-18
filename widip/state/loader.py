"""Loader-specific stateful execution."""

from ..comput.loader import loader_program_ty
from ..wire.loader import loader_stream_ty
from .core import Execution


class LoaderExecution(Execution):
    """Stateful execution process for loader programs."""

    def __init__(self):
        Execution.__init__(
            self,
            "loader",
            loader_program_ty,
            loader_stream_ty,
            loader_stream_ty,
        )
