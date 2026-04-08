import subprocess

import pytest
from nx_yaml import nx_compose_all

import mytilus.watch as watch
from mytilus.comput.shell import Command, io_ty
from mytilus.metaprog.hif import HIFToLoader
from mytilus.pcc import SHELL
from mytilus.state.loader import LoaderToShell
from mytilus.state.shell import terminal_passthrough_command
from mytilus.watch import CTRL_C, CTRL_D, CTRL_J, CTRL_M, apply_tty_input, emit_shell_source, read_shell_source, watch_log


def test_apply_tty_input_uses_ctrl_j_as_newline_and_ctrl_m_as_submit():
    buffer = []

    assert apply_tty_input(buffer, "!") == ("char", None)
    assert apply_tty_input(buffer, "e") == ("char", None)
    assert apply_tty_input(buffer, "c") == ("char", None)
    assert apply_tty_input(buffer, "h") == ("char", None)
    assert apply_tty_input(buffer, "o") == ("char", None)
    assert apply_tty_input(buffer, CTRL_J) == ("newline", None)
    assert apply_tty_input(buffer, "?") == ("char", None)
    assert apply_tty_input(buffer, CTRL_M) == ("submit", None)

    assert "".join(buffer) == "!echo\n?"


def test_apply_tty_input_ctrl_d_on_empty_buffer_is_eof():
    buffer = []
    assert apply_tty_input(buffer, CTRL_D) == ("eof", None)


def test_apply_tty_input_ctrl_d_on_non_empty_buffer_submits():
    buffer = ["a"]
    assert apply_tty_input(buffer, CTRL_D) == ("submit", None)


def test_apply_tty_input_ctrl_c_interrupts_without_mutating_buffer():
    buffer = ["a"]

    assert apply_tty_input(buffer, CTRL_C) == ("interrupt", None)
    assert buffer == ["a"]


def test_apply_tty_input_backspace_removes_last_character():
    buffer = ["a", "b"]
    action, removed = apply_tty_input(buffer, "\x7F")

    assert action == "backspace"
    assert removed == "b"
    assert buffer == ["a"]


def test_ctrl_j_multiline_document_compiles_as_expected():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    source = "!echo\n? foo\n? bar\n"
    diagram = LoaderToShell()(HIFToLoader()(nx_compose_all(source)))

    assert diagram == Command(["echo", "foo", "bar"]) @ io_ty >> execution


def test_read_shell_source_writes_prompt_to_stdout(capsys):
    source = read_shell_source("bin/yaml/shell.yaml", read_line=lambda: "scalar")
    captured = capsys.readouterr()

    assert source == "scalar"
    assert captured.out == "--- !bin/yaml/shell.yaml\n"
    assert captured.err == ""


def test_watch_log_writes_to_stderr(capsys):
    watch_log("watching for changes in current path")
    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == "watching for changes in current path\n"


def test_emit_shell_source_writes_a_trailing_newline(capsys):
    emit_shell_source("!echo ok")
    captured = capsys.readouterr()

    assert captured.out == "!echo ok\n"
    assert captured.err == ""


def test_terminal_passthrough_command_extracts_top_level_command():
    diagram = LoaderToShell()(HIFToLoader()(nx_compose_all("!echo ok\n")))
    command = terminal_passthrough_command(diagram)

    assert command == Command(["echo", "ok"])


def test_execute_shell_diagram_uses_terminal_passthrough_when_available(monkeypatch):
    diagram = LoaderToShell()(HIFToLoader()(nx_compose_all("!echo ok\n")))
    seen = {}

    monkeypatch.setattr(watch, "has_interactive_terminal", lambda: True)
    monkeypatch.setattr(watch, "run_terminal_command", lambda command, script_args: seen.setdefault("argv", command.argv))

    result = watch.execute_shell_diagram(diagram, None, script_args=())
    
    # Updated to expect status triple (stdout, rc, stderr) for passthrough commands.
    assert result == ("", ("echo", "ok"), "")
    assert seen["argv"] == ("echo", "ok")


def test_execute_shell_diagram_keeps_structured_programs_captured(monkeypatch):
    diagram = LoaderToShell()(HIFToLoader()(nx_compose_all("- !printf hi\n- !wc -c\n")))

    monkeypatch.setattr(watch, "has_interactive_terminal", lambda: True)

    assert watch.execute_shell_diagram(diagram, None, script_args=()) == ("2\n", 0, "")


def test_terminal_passthrough_command_rejects_nested_command_substitution():
    diagram = Command(["echo", Command(["printf", "ok"])]) @ io_ty >> SHELL.execution(io_ty, io_ty).output_diagram()

    assert terminal_passthrough_command(diagram) is None


def test_execute_shell_diagram_keeps_nested_command_substitution_captured(monkeypatch):
    diagram = Command(["echo", Command(["printf", "ok"])]) @ io_ty >> SHELL.execution(io_ty, io_ty).output_diagram()

    monkeypatch.setattr(watch, "has_interactive_terminal", lambda: True)
    monkeypatch.setattr(watch, "run_terminal_command", lambda command, script_args: pytest.fail(f"unexpected passthrough for {command.argv!r}"))

    assert watch.execute_shell_diagram(diagram, None, script_args=()) == ("ok\n", 0, "")


def test_shell_main_propagates_invalid_command_errors(monkeypatch, capsys):
    sources = iter(("!git status --short\n", "!echo ok\n"))

    def fake_read_line():
        try:
            return next(sources)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr(watch, "default_shell_source_reader", fake_read_line)

    with pytest.raises(subprocess.CalledProcessError):
        watch.shell_main("bin/yaml/shell.yaml", draw=False, watch=False, script_args=())

    captured = capsys.readouterr()

    assert watch.SHELL_BANNER in captured.err
    assert "!git status --short" in captured.out
    assert "!echo ok" not in captured.out


def test_shell_main_reports_yaml_reader_errors_and_continues(monkeypatch, capsys):
    sources = iter(("\x1b[200~!echo bad\n", "!echo ok\n"))

    def fake_read_line():
        try:
            return next(sources)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr(watch, "default_shell_source_reader", fake_read_line)

    with pytest.raises(SystemExit) as excinfo:
        watch.shell_main("bin/yaml/shell.yaml", draw=False, watch=False, script_args=())

    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    assert "ReaderError" in captured.err
    assert watch.SHELL_BANNER in captured.err
    assert "!echo ok" in captured.out
    assert "ok" in captured.out
