"""Mytilus-specific state package."""

import mytilus.state.shell as state_shell
import mytilus.state.python as state_python


SHELL_SPECIALIZER = state_shell.ShellSpecializer()
SHELL_RUNTIME = state_shell.ShellRuntime()
SHELL_PROGRAM_TO_PYTHON = state_shell.ShellToPythonProgram(script_args=[])
SHELL_PYTHON_RUNTIME = state_shell.ShellPythonRuntime()
SHELL_INTERPRETER = state_shell.ShellInterpreter(
    SHELL_PROGRAM_TO_PYTHON,
    SHELL_PYTHON_RUNTIME,
    script_args=[],
)
runtime_values = state_python.runtime_values
