"""Chapter 7: Stateful computing."""

from .core import (
    Execution,
    InputOutputMap,
    Process,
    ProcessRunner,
    StateUpdateMap,
    execute,
    fixed_state,
    simulate,
)
from .loader import LoaderExecution
from .widish import ShellExecution


def loader_state_update():
    """The loader execution state-update map sta(loader)."""
    return LoaderExecution().state_update_diagram()


def loader_output():
    """The loader execution output map out(loader)."""
    return LoaderExecution().output_diagram()


def shell_state_update():
    """The shell execution state-update map sta(shell)."""
    return ShellExecution().state_update_diagram()


def shell_output():
    """The shell execution output map out(shell)."""
    return ShellExecution().output_diagram()
