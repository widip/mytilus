import signal
from discopy import python
from mytilus.comput.shell import Command, io_ty
from mytilus.state import SHELL_INTERPRETER, SHELL_PROGRAM_TO_PYTHON, SHELL_PYTHON_RUNTIME
from mytilus.pcc import SHELL
from mytilus.metaprog.shell import Pipeline
import discorun.state.core as state_core

def handler(signum, frame):
    raise TimeoutError("Execution timed out!")

signal.signal(signal.SIGALRM, handler)

print("--- Step 1: Parallel/Pipeline Trace ---")
execution = SHELL.execution(io_ty, io_ty).output_diagram()
p1 = Command(["printf", "a"]) @ io_ty >> execution
p2 = Command(["printf", "b"]) @ io_ty >> execution
diagram = p1 >> p2
print(f"Diagram: {diagram}")

print("\n--- Step 2: Simulation ---")
try:
    signal.alarm(5)
    lowered = SHELL_PROGRAM_TO_PYTHON(diagram)
    print(f"Lowered successful: {lowered}")
    signal.alarm(0)
except Exception as e:
    print(f"Simulation failed: {e}")
    signal.alarm(0)

print("\n--- Step 3: Interpretation ---")
try:
    signal.alarm(5)
    interp_fn = SHELL_PYTHON_RUNTIME(lowered)
    print("Interpretation successful.")
    signal.alarm(0)
except Exception as e:
    print(f"Interpretation failed: {e}")
    signal.alarm(0)

print("\n--- Step 4: Execution ---")
initial_triple = ("", 0, "")
try:
    signal.alarm(5)
    result = interp_fn(initial_triple)
    print(f"Result: {result}")
    signal.alarm(0)
except Exception as e:
    print(f"Execution failed or timed out: {e}")
    signal.alarm(0)
