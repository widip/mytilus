import os
import subprocess
import sys


def run_mytilus(*args, env=None):
    run_env = os.environ.copy()
    if env is not None:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "mytilus", *args],
        text=True,
        capture_output=True,
        check=False,
        env=run_env,
    )


def test_exit_code_propagation():
    # Command that fails
    result = run_mytilus("-c", "sh: ['ls', 'non_existent_file_extremely_unlikely_to_exist']")
    assert result.returncode != 0
    assert "non_existent_file" in result.stderr


def test_command_tracing_x():
    # Command tracing with -x
    result = run_mytilus("-x", "-c", "sh: ['echo', 'trace-test']")
    assert result.returncode == 0
    assert "+ echo trace-test" in result.stderr
    assert "trace-test" in result.stdout


def test_stderr_propagation():
    # Explicit stderr output
    result = run_mytilus("-c", "sh: ['sh', '-c', 'echo error >&2']")
    assert "error" in result.stderr


def test_pipeline_exit_code():
    # Pipeline should return the exit code of the last command (standard behavior)
    # or the first failure if we implemented it that way.
    # In my implementation of SubstitutionPipeline:
    # if output.failed: break
    # So it returns the first failed command's result.
    result = run_mytilus("-c", "sh: [['ls', 'non_existent'], ['echo', 'should_not_run']]")
    assert result.returncode != 0
    assert "should_not_run" not in result.stdout
