import signal
import sys
from discopy import python
from mytilus.comput.shell import Command, io_ty, Literal, Empty
import mytilus.state as mytilus_state
from mytilus.pcc import SHELL

def handler(signum, frame):
    raise TimeoutError("Execution timed out!")

signal.signal(signal.SIGALRM, handler)

print("--- Step 0: Object Mapping Debug ---")
runtime = mytilus_state.SHELL_PYTHON_RUNTIME
for ob in io_ty:
    mapped = runtime.ob_map(ob)
    print(f"Object '{ob.name}' maps to: {mapped} (Type: {type(mapped)})")

print("\n--- Step 1: Detailed Simple Command Trace ---")
program = Command(["echo", "hello"])
execution = SHELL.execution(io_ty, io_ty).output_diagram()
diagram = program @ io_ty >> execution

print("\n--- Simulation ---")
lowered = mytilus_state.SHELL_PROGRAM_TO_PYTHON(diagram)
print(f"Lowered Diagram: {lowered}")

print("\n--- Interpretation ---")
interp_fn = mytilus_state.SHELL_PYTHON_RUNTIME(lowered)
print(f"Interpreted function: {interp_fn}")
print(f"Interpreted Dom: {interp_fn.dom}")

print("\n--- Execution ---")
initial_triple = ("hello_input", 0, "")
try:
    signal.alarm(2)
    # 3-wire splat for initial triple
    result = interp_fn(*initial_triple)
    print(f"Final Raw Result: {result}")
    signal.alarm(0)
except Exception as e:
    print(f"Execution Failed: {e}")
    import traceback
    traceback.print_exc()
    signal.alarm(0)
