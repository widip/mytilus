"""Shell-specific stateful execution."""

import subprocess
from collections.abc import Callable

from discopy import monoidal

from discorun.comput import computer
from discorun.metaprog import core as metaprog_core
from discorun.metaprog.compile import RunSpecializer, RunInterpreter
from discorun.state import core as state_core
from discorun.state.core import Execution, InputOutputMap, ProcessSimulation
from ..comput.python import PythonComputations
PYTHON_PCC = PythonComputations()

import mytilus.pcc as mytilus_pcc
import mytilus.metaprog as mytilus_metaprog
from ..comput import python as comput_python
from ..comput import shell as shell_lang
from ..metaprog import python as metaprog_python
from ..metaprog import shell as metaprog_shell
from ..wire import partial as partial_category
from ..wire import shell as shell_wire
from .python import ProcessRunner
from discorun.comput import boxes as discorun_comput_boxes
import os
import sys

# Public API alignment for tests/legacy code
Parallel = metaprog_shell.Parallel
Pipeline = metaprog_shell.Pipeline
parallel = metaprog_shell.parallel
pipeline = metaprog_shell.pipeline
ShellSpecializer = metaprog_shell.ShellSpecializer

# Stateful execution helpers.





def _run_hardened_paths(paths, stdin):
    """Execute all independent pipelines sequentially and concatenate outputs."""
    outputs = []
    # Every shell-related state is now a triple: (stdout, returncode, stderr).
    # If the input is a raw string (e.g. from initial stdin), wrap it.
    triple = (stdin, 0, "") if isinstance(stdin, str) else stdin

    for path in paths:
        for stage in path:
            triple = comput_python.run(stage, triple)
            if triple[1] != 0:
                break
        if triple[1] != 0:
            outputs.append(triple)
            break
        outputs.append(triple)

    if not outputs:
        return triple

    if len(outputs) == 1:
        return outputs[0]

    # Combine branch outputs using standard monoidal product rules for strings.
    # The last returncode is kept.
    return (
        "".join(o[0] for o in outputs),
        triple[1],
        "".join(o[2] for o in outputs),
    )


class ShellPythonDataServices(comput_python.PythonDataServices):
    """Python data services with shell-program object interpretation."""
    def object(self, ob):
        # Delegate to the base Python data services for stdout, rc, stderr, and Callables.
        return super().object(ob)

    def data_ar(self, box, dom, cod):
        from mytilus.wire.shell import Merge
        if isinstance(box, Merge):
             # Principled status-triple merging for parallel shell paths.
             def merge_triples(*args):
                 # Zip expects triples, but discopy flattening may have combined them.
                 triples = [args[i:i+3] for i in range(0, len(args), 3)]
                 stdouts, rcs, stderrs = zip(*triples)
                 return "".join(stdouts), max(rcs), "".join(stderrs)
             return partial_category.PartialArrow(merge_triples, dom, cod)
        return super().data_ar(box, dom, cod)


class SubstitutionPipeline:
    """Sequence of shell subprograms used inside command substitution."""

    def __init__(self, stages):
        self.stages = tuple(stages)


class SubstitutionParallel:
    """Parallel shell subprogram branches used inside command substitution."""

    def __init__(self, branches):
        self.branches = tuple(branches)


def _resolve_command_substitution(argument, stdin: str) -> str:
    """Evaluate one command-substitution argument."""
    if isinstance(argument, (shell_lang.Command, SubstitutionPipeline, SubstitutionParallel, metaprog_shell.Pipeline, metaprog_shell.Parallel)):
        # Shell command substitution strips trailing newlines.
        # Passing (stdin, 0, "") as 3 separate wires.
        result = _compile_shell_program(argument)(stdin, 0, "")
        return result[0].rstrip("\n")
    if hasattr(argument, "text"):
        return str(argument.text)
    if hasattr(argument, "value") and not isinstance(argument, str):
        return str(argument.value)
    if isinstance(argument, shell_lang.Empty) or (hasattr(argument, "name") and argument.name == "''"):
        return ""
    return str(argument)


def _resolve_command_argv(argv, stdin: str) -> tuple[str, ...]:
    """Resolve a shell command argv tuple to plain subprocess arguments."""
    return tuple(_resolve_command_substitution(argument, stdin) for argument in argv)


def _resolve_terminal_passthrough_argument(argument):
    """Resolve one passthrough-safe argv item without running nested subprograms."""
    if isinstance(argument, str):
        return argument
    if isinstance(argument, shell_lang.Literal):
        return argument.text
    if isinstance(argument, shell_lang.Empty):
        return ""
    return None


def _resolve_terminal_passthrough_argv(argv):
    """Resolve argv when a top-level command can safely own the terminal."""
    resolved = tuple(_resolve_terminal_passthrough_argument(argument) for argument in argv)
    if any(argument is None for argument in resolved):
        return None
    return resolved


def parallel_io_diagram(branches):
    """Lower shell-IO branching to structural shell parallel composition."""
    branches = tuple(branches)
    if not branches:
        return shell_wire.shell_id()
    if len(branches) == 1:
        return branches[0]
    return Parallel(branches)




class ShellRuntime(metaprog_core.Interpreter):
    """Runtime functor lowering shell state diagrams through the Python runtime."""

    def __init__(self, python_runtime=None):
        if python_runtime is None:
            python_runtime = ShellPythonRuntime()
        self.python_runtime = python_runtime
        metaprog_core.Interpreter.__init__(
            self,
            dom=computer.Category(),
            cod=self.python_runtime.cod,
        )

    def _identity_object(self, ob):
        return self.python_runtime(self.program_functor(ob))

    def _identity_arrow(self, box):
        return self.python_runtime(self.program_functor(box))


class ShellToPythonProgram(state_core.ProcessSimulation):
    """Principled simulation from shell diagrams to Python programs."""

    def __init__(self):
        state_core.ProcessSimulation.__init__(
            self,
            source=mytilus_pcc.SHELL,
            target=PYTHON_PCC,
        )

    def __call__(self, other):
        # 1. Specialized diagram components (State projections, services)
        if isinstance(other, (state_core.StateUpdateMap, state_core.InputOutputMap)):
            return self._identity_arrow(other)
        from discorun.wire import services
        if isinstance(other, (services.Copy, services.Swap, services.Delete)):
             return self._identity_arrow(other)
        
        # 2. Lowering: generic bubbles should be un-bubbled (interrogated) here.
        if isinstance(other, monoidal.Bubble):
             return self(other.arg)

        # 3. Base class handles diagrams (layers) and atomic boxes.
        return super().__call__(other)

    def ar_map(self, box):
        """Pure atomic mapping: assume other cases (bubbles) were handled in __call__."""
        res = self._identity_arrow(box)
        if hasattr(res, "inside") and not isinstance(res, computer.Diagram):
             dom, cod = self(box.dom), self(box.cod)
             res = computer.Diagram(res.inside, dom, cod)
        return res

    def simulation(self, item):
        # 1. Base class handles types and structural services (Copy/Swap/Delete).
        mapped = super().simulation(item)
        if mapped is not item:
            return mapped

        # 2. Arrow mapping for specialized Shell boxes.
        if isinstance(item, (shell_lang.Literal, shell_lang.Empty, shell_lang.Command)):
            if isinstance(item, shell_lang.Command):
                argv = item.argv
                from ..comput.shell import subprocess_run

                def command_partial(stdout, v_rc=0, v_stderr="", **kwargs):
                    resolved_argv = _resolve_command_argv(argv, stdout)
                    try:
                        res = subprocess_run(resolved_argv, stdout, v_rc, v_stderr)
                        return res
                    except Exception as e:
                        return stdout, 1, str(e)

                return comput_python.runtime_value_box(
                    command_partial,
                    name=item.name,
                    cod=PYTHON_PCC.program_ty,
                )
            
            val = item.value if hasattr(item, "value") else ""
            def print_literal(stdout, v_rc=0, v_stderr="", **kwargs):
                return (val, v_rc, v_stderr)

            return comput_python.runtime_value_box(
                print_literal,
                name=f"⌜{val}⌝" if val else "Empty",
                cod=PYTHON_PCC.program_ty,
            )

        if isinstance(item, metaprog_shell.Parallel):
            n = len(item.branches)
            unit = self.simulation(item.branches[0].dom)
            copy = mytilus_wire.Copy(n, unit)
            branches = monoidal.Diagram.tensor(*(self(b) for b in item.branches))
            merge = mytilus_wire.Merge(n, self.simulation(item.branches[0].cod))
            return copy >> branches >> merge

        from ..wire.shell import Merge
        if isinstance(item, Merge):
            return item

        return item

def shell_program_runner(program):
    """Principled wrapper for running a shell program via the unified interpreter."""
    if isinstance(program, (shell_lang.Empty, shell_lang.Literal, shell_lang.Command)):
        mapped = ShellToPythonProgram()(program)
        return partial_category.PartialArrow(
            mapped.boxes[0].value,
            dom=(str, int, str),
            cod=(str, int, str),
        )
    from . import SHELL_INTERPRETER
    return SHELL_INTERPRETER(program)


def _to_diagram(program):
    """Recursively convert substitution objects to bubbles."""
    if isinstance(program, SubstitutionPipeline):
        return Pipeline(tuple(_to_diagram(s) for s in program.stages))
    if isinstance(program, SubstitutionParallel):
        return Parallel(tuple(_to_diagram(b) for b in program.branches))
    if isinstance(program, shell_lang.Command):
        # Wrap command into a standard io-to-io stage for subprogram pipelines.
        return program @ shell_lang.io_ty >> ShellExecution().output_diagram()
    return program


def _compile_shell_program(program):
    """Principled helper to wrap and run a shell program via the unified interpreter."""
    program = _to_diagram(program)

    import mytilus.state as mytilus_state
    if isinstance(program, computer.Diagram) and program.dom == shell_lang.io_ty and program.cod == shell_lang.io_ty:
        # Already a projected IO-to-IO diagram (e.g. from SubstitutionPipeline/Parallel).
        return mytilus_state.SHELL_INTERPRETER(program)

    # Ensure program is projected through the categorical shell execution model.
    # We use ShellExecution then project it to get the IO-to-IO map.
    exec_diag = ShellExecution()(program).output_diagram()
    # Apply the global interpreter to the projected diagram.
    res = mytilus_state.SHELL_INTERPRETER(exec_diag)
    def status_triple_to_stdout(stdin):
        out = res(stdin)
        return out[0] if isinstance(out, tuple) and len(out) == 3 else out
    return status_triple_to_stdout


class ShellInterpreter(ShellPythonDataServices, ProcessRunner, RunInterpreter):
    """Interpret shell diagrams as Python partial terms."""

    def __init__(self, program_functor, python_runtime):
        self.program_functor = program_functor
        self.python_runtime = python_runtime
        ShellPythonDataServices.__init__(self)
        ProcessRunner.__init__(self)

    def __call__(self, other):
        """Principled total lowering: simulate (lower) the diagram before interpretation."""
        if isinstance(other, metaprog_core.InterpreterBox):
             return self.interpret(other)
        if not isinstance(other, (computer.Diagram, monoidal.Diagram)):
            # Delegate to standard Functor dispatch for objects, types, and specialized atoms.
            return super().__call__(other)

        # Detect already-lowered diagrams to avoid infinite recursion during resolution.
        if (type(other) is monoidal.Diagram):
            return self.python_runtime(other)

        # Lowering: simulate then interpret.
        lowered = self.program_functor(other)
        if not isinstance(lowered, computer.Diagram):
            lowered = computer.Diagram(lowered.inside, lowered.dom, lowered.cod)
        
        result = self.python_runtime(lowered)
        if (partial_category.is_partial_arrow(result) and len(result.dom) >= 3
            and result.dom[-3] is str and result.dom[-2] is int and result.dom[-1] is str):
            # Polymorphic shell runner: handle stdin-only or full status triple for the IO part.
            def shell_run_polymorphic(*xs):
                # Ensure the input is treated as a status triple.
                if not xs:
                    tri = ("", 0, "")
                elif len(xs) == 1:
                    tri = (xs[0], 0, "")
                else:
                    tri = xs
                
                # result may expect shifted arguments if it's stateful (P x io).
                if len(result.dom) > 3 and len(tri) == 3:
                     # Stateful call with stdin only? (state, tri).
                     res = result("", *tri)
                     # Pack the status triple to return (state, (stdout, rc, stderr)).
                     # cod may be 4 (P x io) or 3 (io).
                     if len(result.cod) == 4:
                         return (res[0], (res[1], res[2], res[3]))
                     return res
                
                res = result(*tri)
                # If result is stateful and we passed full state, pack it similarly.
                if len(result.cod) == 4 and len(res) == 4:
                    return (res[0], (res[1], res[2], res[3]))
                return res
            res_fun = partial_category.PartialArrow(shell_run_polymorphic, result.dom, result.cod)
            res_fun.type_checking = False
            return res_fun
        return result

    def ar_map(self, box):
        # Delegate to __call__ to ensure total lowering or atomic interpretation.
        return self(box)

    def object(self, ob):
        # Override to ensure Shell-specific atom types.
        return ShellPythonDataServices.object(self, ob)

class ShellPythonRuntime(ShellPythonDataServices, ProcessRunner):
    """Python runtime with shell-specific process evaluation."""

    def __init__(self):
        ShellPythonDataServices.__init__(self)
        ProcessRunner.__init__(self)
        # Use a lambda to ensure the (self, ob) convention matches the robust object().
        self.object_interpreter = lambda runtime, ob: self.object(ob)

    def state_update_ar(self, dom, cod):
        """Handle the identity program state update: P x A -> P."""
        return partial_category.PartialArrow(lambda p, *tri: (p,), dom, cod)

    def output_ar(self, dom, cod):
        """Handle the 3->3 shell closure application: P x A -> B."""
        def shell_uev(f, *tri):
            # tri may be length 1 if called with only stdin string from the REPL.
            v_stdin = tri[0]
            v_rc = tri[1] if len(tri) > 1 else 0
            v_stderr = tri[2] if len(tri) > 2 else ""

            if isinstance(f, tuple):
                from ..comput.shell import subprocess_run
                res = subprocess_run(f, v_stdin, v_rc, v_stderr)
                return res if isinstance(res, tuple) else (res, 0, "")

            # Otherwise f is my command_partial/print_literal, call it with triples.
            return f(v_stdin, v_rc=v_rc, v_stderr=v_stderr)
        return partial_category.PartialArrow(shell_uev, dom, cod)

    def process_ar_map(self, box, dom, cod):
        """Interpret specialized shell wires in the target category."""
        # Interpret structural fan-out, fan-in (Merge), and symmetry.
        from ..wire.shell import Merge
        if isinstance(box, Merge):
            def merge_run(*results):
                if not results: return ("", 0, "")
                # Specialized status-triple merge: concatenate stdout/stderr, take last rc.
                triples = [results[i:i+3] for i in range(0, len(results), 3)]
                last_rc = triples[-1][1]
                return ("".join(t[0] for t in triples), last_rc, "".join(t[2] for t in triples))
            return partial_category.PartialArrow(merge_run, dom, cod)
        from discorun.wire import services as wire_services
        if isinstance(box, wire_services.Copy) or (hasattr(box, "name") and box.name == "∆"):
            # ∆: copies the input wires.
            n = len(cod) // len(dom)
            return partial_category.PartialArrow(lambda *t: t * n, dom, cod)

        if isinstance(box, wire_services.Swap) or (hasattr(box, "name") and box.name == "Swap"):
            # Swap: (t1, t2) -> (t2, t1)
            return partial_category.PartialArrow(lambda *t: t[3:] + t[:3], dom, cod)

        # Let the base class handle standard Python runtime logic (Bubble, Function, etc.).
        return ProcessRunner.process_ar_map(self, box, dom, cod)


def terminal_passthrough_command(diagram):
    """Return the top-level command when one command can own the terminal."""
    if not hasattr(diagram, "inside"):
        return None

    # A simple terminal passthrough command usually looks like [Command, execution]
    inside = getattr(diagram, "inside", ())
    if len(inside) != 2:
        return None

    _, command_box, _ = inside[0]
    _, output_box, _ = inside[1]

    if not isinstance(command_box, shell_lang.Command):
        return None
    
    # We only passthrough simple commands with string arguments.
    for arg in command_box.argv:
        if not isinstance(arg, str):
            # Command substitution or other non-string arguments reject passthrough.
            return None

    # execution is always an InputOutputMap.
    if isinstance(output_box, InputOutputMap):
        return command_box
    
    return None


def run_terminal_command(program: shell_lang.Command):
    """Run one shell command attached directly to the current terminal."""
    argv = _resolve_terminal_passthrough_argv(program.argv)
    if argv is None:
        raise TypeError(f"terminal passthrough requires plain argv: {program.argv!r}")
    completed = subprocess.run(
        argv,
        check=True,
    )
    return completed.returncode


class Pipeline(metaprog_shell.Pipeline):
    """State-aware pipeline bubble."""

    def specialize(self):
        return metaprog_shell.Pipeline.specialize(self)


class Parallel(metaprog_shell.Parallel):
    """State-aware parallel bubble."""

    def specialize(self):
        return metaprog_shell.Parallel.specialize(self)


def pipeline(stages):
    """Build a state-aware shell pipeline bubble."""
    stages = tuple(stages)
    if not stages:
        return shell_wire.shell_id()
    return Pipeline(stages)


def parallel(branches):
    """Build a state-aware shell parallel bubble."""
    branches = tuple(branches)
    if not branches:
        return shell_wire.shell_id()
    return Parallel(branches)


class ShellSpecializer(metaprog_shell.ShellSpecializer):
    """State-aware shell bubble specializer."""

    def __init__(self):
        metaprog_shell.ShellSpecializer.__init__(self)


class ShellExecution(Execution):
    """Stateful shell evaluator P x io -> P x io."""

    def __init__(self):
        Execution.__init__(
            self,
            "{}",
            shell_lang.shell_program_ty,
            shell_lang.io_ty,
            shell_lang.io_ty,
        )
