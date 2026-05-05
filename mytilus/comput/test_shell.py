import pytest
from mytilus.comput.shell import subprocess_run

def test_subprocess_run_success():
    # Simple echo
    result = subprocess_run(["echo", "-n", "hello"], "initial", 0, "", [])
    # Echo ignores stdin usually, but subprocess_run passes it.
    assert result[0] == "hello"
    assert result[1] == 0
    assert result[2] == ""

def test_subprocess_run_fails():
    # command that fails
    result = subprocess_run(["ls", "non_existent_file_12345"], "", 0, "", [])
    assert result[1] != 0
    assert "non_existent_file" in result[2]

def test_subprocess_run_fail_fast():
    # If the input rc already has an error, subprocess_run should skip.
    # It should return the input status exactly as it is.
    result = subprocess_run(["echo", "should_not_see_this"], "previous_output", 42, "previous_error", [])
    assert result == ("previous_output", 42, "previous_error")

def test_subprocess_run_with_stdin():
    # Test that stdin is correctly passed to the command.
    # 'cat' will repeat stdin to stdout.
    result = subprocess_run(["cat"], "hello world", 0, "", [])
    assert result[0] == "hello world"
    assert result[1] == 0

def test_subprocess_run_with_script_args():
    # Test (ARG n) resolution
    result = subprocess_run(["echo", "-n", "(ARG 0)"], "", 0, "", ["foo"])
    assert result[0] == "foo"
    assert result[1] == 0
