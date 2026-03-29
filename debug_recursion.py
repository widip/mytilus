from mytilus.comput.shell import Command, io_ty
from mytilus.state import SHELL_PROGRAM_TO_PYTHON

command = Command(["echo", "hello"])
print(f"Testing simulation of {command}")
try:
    lowered = SHELL_PROGRAM_TO_PYTHON(command)
    print(f"Lowered successful: {lowered}")
except Exception as e:
    print(f"Lowered failed: {e}")

# Try a pipeline
from mytilus.metaprog.shell import Pipeline
p = Pipeline((command,))
print(f"Testing simulation of {p}")
try:
    lowered_p = SHELL_PROGRAM_TO_PYTHON(p)
    print(f"Lowered P successful: {lowered_p}")
except Exception as e:
    print(f"Lowered P failed: {e}")
