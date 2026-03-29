from mytilus.comput.shell import Command, Empty, Literal, io_ty
from mytilus.state import SHELL_INTERPRETER, SHELL_PROGRAM_TO_PYTHON
from mytilus.metaprog.shell import Pipeline, Parallel
from mytilus.pcc import SHELL

def test_total_evaluation_simple_command():
    # echo "hello"
    program = Command(["echo", "hello"])
    # Total evaluation diagram: Command @ stdin >> Execution
    # Domain: io_ty, Codomain: io_ty
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    diagram = program @ io_ty >> execution
    
    # Run: Simulation -> Interpretation -> Execution
    # The input to the interpreted function is a (stdout, rc, stderr) triple.
    initial_triple = ("", 0, "")
    result_triple = SHELL_INTERPRETER(diagram)(*initial_triple)
    
    # Standard shell echo adds a newline
    assert result_triple[0] == "hello\n"
    assert result_triple[1] == 0
    assert result_triple[2] == ""

def test_total_evaluation_pipeline_halting():
    # false >> echo "should not run"
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    
    p1 = Command(["false"]) @ io_ty >> execution
    p2 = Command(["echo", "should_not_run"]) @ io_ty >> execution
    diagram = p1 >> p2
    
    # Run
    initial_triple = ("", 0, "")
    result_triple = SHELL_INTERPRETER(diagram)(*initial_triple)
    
    # result should have rc=1 (from false) and empty stdout (echo was skipped)
    assert result_triple[1] != 0
    assert "should_not_run" not in result_triple[0]

def test_total_evaluation_parallel_merging():
    # echo "a" || echo "b"
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    
    branch1 = Command(["printf", "a"]) @ io_ty >> execution
    branch2 = Command(["printf", "b"]) @ io_ty >> execution
    diagram = Parallel((branch1, branch2))
    
    # Run
    initial_triple = ("", 0, "")
    result_triple = SHELL_INTERPRETER(diagram)(*initial_triple)
    
    # Combined output: 'ab'
    assert result_triple[0] == "ab"

def test_total_evaluation_literal_resolution():
    # command with literal and empty
    # echo "foo" "" -> "foo \n"
    program = Command(["echo", Literal("foo"), Empty()])
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    diagram = program @ io_ty >> execution
    
    # Run
    initial_triple = ("", 0, "")
    result_triple = SHELL_INTERPRETER(diagram)(*initial_triple)
    
    # Literal 'foo' and Empty '' joined by space
    assert result_triple[0] == "foo \n"
