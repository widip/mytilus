import pytest
from nx_yaml import nx_compose_all

import widip.watch as watch
from widip.comput.widish import Command, io_ty
from widip.metaprog.hif import HIFToLoader
from widip.pcc import SHELL
from widip.state.loader import LoaderToShell
from widip.watch import CTRL_D, CTRL_J, CTRL_M, apply_tty_input, emit_shell_source, read_shell_source, watch_log


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


def test_shell_main_continues_after_invalid_command(monkeypatch, capsys):
    class DummyObserver:
        def stop(self):
            return None

    sources = iter(("!git status --short\n", "!echo ok\n"))

    def fake_read_shell_source(_file_name):
        try:
            return next(sources)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr(watch, "watch_main", lambda: DummyObserver())
    monkeypatch.setattr(watch, "read_shell_source", fake_read_shell_source)

    with pytest.raises(SystemExit) as raised:
        watch.shell_main("bin/yaml/shell.yaml", draw=False)

    captured = capsys.readouterr()

    assert raised.value.code == 0
    assert "!git status --short" in captured.out
    assert "!echo ok" in captured.out
    assert "returned non-zero exit status" in captured.err
    assert "ok" in captured.out
