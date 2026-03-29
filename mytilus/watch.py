from pathlib import Path
import sys

import mytilus.state as mytilus_state
import yaml

from .files import diagram_draw, file_diagram, source_diagram
from .interactive import (
    CTRL_C,
    CTRL_D,
    CTRL_J,
    CTRL_M,
    ShellConsole,
    apply_tty_input,
    default_shell_source_reader,
    emit_shell_source,
    read_shell_source,
)
from .state.shell import run_terminal_command, terminal_passthrough_command


SHELL_BANNER = "See [SKILL.md](mytilus/SKILL.md) for mytilus authoring and REPL usage."


def watch_log(message: str):
    """Write watcher status logs to stderr."""
    print(message, file=sys.stderr)


def has_interactive_terminal():
    """Return whether stdin, stdout, and stderr are all attached to a TTY."""
    return sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()


def execute_shell_diagram(diagram, stdin_text: str | None):
    # Terminal passthrough: check if this is a single command.
    if has_interactive_terminal() and stdin_text is None:
        command = terminal_passthrough_command(diagram)
        if command is not None:
            run_terminal_command(command)
            return None

    # Normal execution: captured output for tests or script usage.
    runner = mytilus_state.SHELL_INTERPRETER(diagram)
    # Call with 1-wire input to get 1-wire output (polymorphic runner).
    res = runner(stdin_text if stdin_text is not None else "")
    if isinstance(res, tuple) and len(res) == 2:
        # Stateful (P x io) -> just return io
        return res[1]
    return res


def emit_mytilus_result(run_res) -> int:
    """Emit one mytilus file or inline-command result, returning the last exit code."""
    # Ensure run_res is a list of results if it's a list.
    results = run_res if isinstance(run_res, list) else [run_res]
    exit_code = 0
    with open("mytilus.log", "a") as log:
        for res in results:
            for value in mytilus_state.runtime_values(res):
                if not isinstance(value, tuple) or len(value) != 3:
                    # Non-triple values (e.g. from pure Python boxes) emit as-is.
                    text = str(value)
                    sys.stdout.write(text)
                    log.write(text)
                    continue

                stdout, rc, stderr = value
                sys.stdout.write(stdout)
                log.write(stdout)
                if stderr:
                    sys.stderr.write(stderr)
                exit_code = rc
    sys.stdout.flush()
    return exit_code


def watch_main():
    """the process manager for the reader and """
    #  TODO watch this path to reload changed files,
    # returning an IO as always and maintaining the contract.
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class ShellHandler(FileSystemEventHandler):
        """Reload the shell on change."""

        def on_modified(self, event):
            if event.src_path.endswith(".yaml"):
                watch_log(f"reloading {event.src_path}")
                fd = file_diagram(str(event.src_path))
                diagram_draw(Path(event.src_path), fd)
                diagram_draw(Path(event.src_path + ".2"), fd)

    watch_log("watching for changes in current path")
    observer = Observer()
    shell_handler = ShellHandler()
    observer.schedule(shell_handler, ".", recursive=True)
    observer.start()
    return observer


class StoppedObserver:
    """Observer sentinel that makes stop() always safe."""

    def stop(self):
        return None


class ShellSession:
    """State holder for one interactive mytilus shell session."""

    def __init__(self, file_name, draw, watch, error_writer=None):
        self.file_name = file_name
        self.draw = draw
        self.watch = watch
        self.error_writer = sys.stderr.write if error_writer is None else error_writer
        self.observer = StoppedObserver()

    def read_source(self):
        self.stop_observer()
        if self.watch:
            self.observer = watch_main()
        return read_shell_source(self.file_name, default_shell_source_reader)

    def execute_source(self, source):
        try:
            emit_shell_source(source)
            try:
                run_shell_source(source, self.file_name, self.draw)
            except yaml.YAMLError as exc:
                self.error_writer(f"{exc.__class__.__name__}: {exc}\n")
        finally:
            self.stop_observer()

    def stop_observer(self):
        self.observer.stop()
        self.observer = StoppedObserver()


def run_shell_source(source, file_name, draw):
    """Execute one mytilus document inside the interactive shell."""
    source_d = source_diagram(source)
    path = Path(file_name)

    if draw:
        diagram_draw(path, source_d)
    res = execute_shell_diagram(source_d, None)
    emit_mytilus_result(res)
    # Status-triple error propagation: raise error for the interactive runner to capture.
    if isinstance(res, tuple) and len(res) == 3 and res[1] != 0:
        import subprocess
        raise subprocess.CalledProcessError(res[1], f"shell command failure: {source}")
    return res


def shell_main(file_name, draw, watch=False):
    session = ShellSession(file_name, draw, watch)

    def read_source(prompt):
        del prompt
        return session.read_source()

    console = ShellConsole(
        session.execute_source,
        read_source,
        lambda data: sys.stderr.write(data),
        file_name,
    )

    try:
        console.interact(banner=SHELL_BANNER, exitmsg="")
    finally:
        session.stop_observer()

    print("⌁")
    raise SystemExit(0)

def mytilus_main(file_name, draw):
    fd = file_diagram(file_name)
    path = Path(file_name)
    if draw:
        diagram_draw(path, fd)

    run_res = execute_shell_diagram(fd, None) if has_interactive_terminal() else execute_shell_diagram(fd, sys.stdin.read())
    return emit_mytilus_result(run_res)


def mytilus_source_main(source, draw):
    fd = source_diagram(source)
    path = Path("mytilus-command.yaml")
    if draw:
        diagram_draw(path, fd)

    run_res = execute_shell_diagram(fd, None) if has_interactive_terminal() else execute_shell_diagram(fd, sys.stdin.read())
    return emit_mytilus_result(run_res)
