import os
import pty
import select
import subprocess
import sys
import time

PTY_TIMEOUT_SECONDS = 5.0


def run_mytilus(*args, env):
    run_env = os.environ.copy()
    run_env.pop("MYTILUS_TRACE", None)
    run_env.setdefault("MPLCONFIGDIR", "/tmp/mytilus-mpl")
    if env is not None:
        run_env.update(env)
    return subprocess.run(
        [".venv/bin/mytilus", *args],
        text=True,
        capture_output=True,
        check=False,
        env=run_env,
        stdin=subprocess.DEVNULL,
    )


def run_mytilus_pty(*args, env):
    run_env = os.environ.copy()
    run_env.pop("MYTILUS_TRACE", None)
    run_env.setdefault("MPLCONFIGDIR", "/tmp/mytilus-mpl")
    if env is not None:
        run_env.update(env)

    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(
        [".venv/bin/mytilus", *args],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=run_env,
        close_fds=True,
    )
    os.close(slave_fd)
    return process, master_fd


def read_pty_until(master_fd, needle, timeout):
    deadline = time.time() + timeout
    chunks = []
    data = b""

    while time.time() < deadline:
        ready, _, _ = select.select([master_fd], [], [], 0.1)
        if master_fd not in ready:
            continue
        try:
            chunk = os.read(master_fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        chunks.append(chunk)
        data = b"".join(chunks)
        if needle in data:
            return data

    raise AssertionError(f"Did not see {needle!r} in PTY output: {data!r}")


def test_bin_mytilus_c_executes_yaml_command():
    result = run_mytilus("-c", "!echo hello-from-mytilus", env=None)

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["hello-from-mytilus"]
    assert result.stderr == ""


def test_bin_mytilus_can_be_used_via_shell_env_var():
    env = os.environ.copy()
    env["SHELL"] = "bin/mytilus"
    result = run_mytilus("-c", "!echo hello-from-shell-env", env=env)

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["hello-from-shell-env"]


def test_bin_mytilus_c_requires_argument():
    result = run_mytilus("-c", env=None)

    assert result.returncode == 2
    assert "mytilus: error: argument -c/--command: expected one argument" in result.stderr


def test_bin_mytilus_c_runs_python_without_a_tty():
    result = run_mytilus("-c", f"!{sys.executable}", env=None)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_bin_mytilus_c_runs_python_batch_code():
    result = run_mytilus("-c", f'!{sys.executable} {{-c, "print(123)"}}', env=None)

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["123"]
    assert result.stderr == ""


def test_bin_mytilus_c_preserves_command_trailing_newline_behavior():
    no_newline = run_mytilus("-c", "!printf hello", env=None)
    with_newline = run_mytilus("-c", "!echo hello", env=None)

    assert no_newline.returncode == 0
    assert with_newline.returncode == 0
    assert no_newline.stdout == "hello"
    assert with_newline.stdout == "hello\n"


def test_bin_mytilus_c_preserves_tty_for_interactive_python():
    process, master_fd = run_mytilus_pty("-c", f"!{sys.executable} -q", env=None)

    try:
        assert b">>> " in read_pty_until(master_fd, b">>> ", PTY_TIMEOUT_SECONDS)

        os.write(master_fd, b"print(123)\n")
        interactive_output = read_pty_until(master_fd, b">>> ", PTY_TIMEOUT_SECONDS)

        assert b"123" in interactive_output

        os.write(master_fd, b"raise SystemExit\n")
        assert process.wait(timeout=5) == 0
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass
        if process.poll() is None:
            process.kill()
            process.wait()


def test_bin_mytilus_i_runs_command_then_starts_repl():
    process, master_fd = run_mytilus_pty("-i", "-c", "!echo hello-from-interactive", env=None)

    try:
        combined_output = read_pty_until(master_fd, b"--- !bin/yaml/shell.yaml", PTY_TIMEOUT_SECONDS)

        assert b"hello-from-interactive" in combined_output
        assert b"See [SKILL.md](mytilus/SKILL.md) for mytilus authoring and REPL usage." in combined_output
        assert b"watching for changes in current path" not in combined_output

        os.write(master_fd, b"\x04")
        try:
            exit_output = read_pty_until(master_fd, b"\xe2\x8c\x81", 1.0)
        except AssertionError:
            exit_output = b""
        if exit_output:
            assert b"\xe2\x8c\x81" in exit_output
        try:
            assert process.wait(timeout=5) == 0
        except subprocess.TimeoutExpired:
            os.write(master_fd, b"\x04")
            assert process.wait(timeout=5) == 0
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass
        if process.poll() is None:
            process.kill()
            process.wait()


def test_bin_mytilus_repl_ctrl_c_interrupts_current_document_and_recovers():
    process, master_fd = run_mytilus_pty(env=None)

    try:
        startup_output = read_pty_until(master_fd, b"--- !bin/yaml/shell.yaml", PTY_TIMEOUT_SECONDS)

        assert b"See [SKILL.md](mytilus/SKILL.md) for mytilus authoring and REPL usage." in startup_output

        os.write(master_fd, b"!echo partial")
        os.write(master_fd, b"\x03")
        interrupted_output = read_pty_until(master_fd, b"--- !bin/yaml/shell.yaml", PTY_TIMEOUT_SECONDS)

        assert b"KeyboardInterrupt" in interrupted_output

        os.write(master_fd, b"!echo recovered\r")
        recovered_output = read_pty_until(master_fd, b"recovered", PTY_TIMEOUT_SECONDS)

        assert b"recovered" in recovered_output

        os.write(master_fd, b"\x04")
        try:
            exit_output = read_pty_until(master_fd, b"\xe2\x8c\x81", 1.0)
        except AssertionError:
            exit_output = b""
        if exit_output:
            assert b"\xe2\x8c\x81" in exit_output
        try:
            assert process.wait(timeout=5) == 0
        except subprocess.TimeoutExpired:
            os.write(master_fd, b"\x04")
            assert process.wait(timeout=5) == 0
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass
        if process.poll() is None:
            process.kill()
            process.wait()


def test_example_pipeline_scoping_and_imports():
    """
    Test that Mytilus can resolve sibling YAML tools via the automated script-local PATH.
    The chain is: argv-example.yaml -> argv-bin.yaml -> mybin.yaml -> !echo.
    """
    # Run the top-level example from the repository root.
    # bin/mytilus adds bin/ to PATH.
    # examples/pipeline/argv-example.yaml adds examples/pipeline/ to PATH.
    result = run_mytilus("examples/pipeline/argv-example.yaml", "Alpha", "Beta", env=None)
    
    assert result.returncode == 0
    # mybin.yaml effectively ignores arguments and prints the constant "Hello World!"
    assert result.stdout.strip() == "Hello World!"


def test_example_pipeline_missing_args_resolved_to_empty_string():
    """
    Test that missing (ARG n) placeholders are handled gracefully (empty string) 
    instead of causing an IndexError.
    """
    # Providing no arguments to a script that expects ARG 0 and ARG 1
    result = run_mytilus("examples/pipeline/argv-example.yaml", env=None)
    
    assert result.returncode == 0
    assert result.stdout.strip() == "Hello World!"


def test_path_resolution_for_local_tools_in_subdirectories():
    """
    Test that running a script from a different directory (the root)
    successfully resolves its local sibling tools.
    """
    # Specifically call argv-bin.yaml directly from the root.
    # It should find its sibling mybin.yaml even though bin/ is the only relative directory in the wrapper's PATH.
    # The fix in mytilus_main() prepends the script's directory (examples/pipeline/) to the PATH.
    result = run_mytilus("examples/pipeline/argv-bin.yaml", "A", "B", env=None)
    
    assert result.returncode == 0
    assert result.stdout.strip() == "Hello World!"
