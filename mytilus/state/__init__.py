"""Mytilus-specific state package."""

import mytilus.state.mytilus as state_mytilus
import mytilus.state.python as state_python


SHELL_SPECIALIZER = state_mytilus.ShellSpecializer()
SHELL_PROGRAM_TO_PYTHON = state_python.ShellToPythonProgram()
SHELL_PYTHON_RUNTIME = state_python.ShellPythonRuntime()
SHELL_INTERPRETER = state_python.ShellInterpreter(
    SHELL_SPECIALIZER,
    SHELL_PROGRAM_TO_PYTHON,
    SHELL_PYTHON_RUNTIME,
)
runtime_values = state_python.runtime_values
