import os
import subprocess


def run_widish(*args, env=None):
    run_env = os.environ.copy()
    run_env.setdefault("MPLCONFIGDIR", "/tmp/widip-mpl")
    if env is not None:
        run_env.update(env)
    return subprocess.run(
        ["bin/widish", *args],
        text=True,
        capture_output=True,
        check=False,
        env=run_env,
    )


def test_bin_widish_c_executes_yaml_command():
    result = run_widish("-c", "!echo hello-from-widish")

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["hello-from-widish"]
    assert result.stderr == ""


def test_bin_widish_can_be_used_via_shell_env_var():
    env = os.environ.copy()
    env["SHELL"] = "bin/widish"
    result = run_widish("-c", "!echo hello-from-shell-env", env=env)

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["hello-from-shell-env"]


def test_bin_widish_c_requires_argument():
    result = run_widish("-c")

    assert result.returncode == 2
    assert "widish: missing argument for -c" in result.stderr
