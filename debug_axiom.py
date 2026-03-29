from discopy import python
from mytilus.comput.shell import Command, io_ty
from mytilus.state import SHELL_INTERPRETER, SHELL_PROGRAM_TO_PYTHON, SHELL_PYTHON_RUNTIME
from mytilus.pcc import SHELL
import discorun.state.core as state_core

print("--- Data Box Info ---")
program = Command(["echo", "hello"])
lowered_p = SHELL_PROGRAM_TO_PYTHON(program)
print(f"Data Box Cod: {lowered_p.cod}")

print("\n--- InputOutputMap Info ---")
execution = SHELL.execution(io_ty, io_ty).output_diagram()
for box in execution.boxes:
    if isinstance(box, state_core.InputOutputMap):
        print(f"Original Out Box Dom: {box.dom}")
        lowered_out = SHELL_PROGRAM_TO_PYTHON(box)
        print(f"Lowered Out Box Dom: {lowered_out.dom}")

print("\n--- Composition Test ---")
try:
    diag = lowered_p @ io_ty >> lowered_out
    print("Composition successful!")
except Exception as e:
    print(f"Composition failed: {e}")
