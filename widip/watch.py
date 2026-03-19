from pathlib import Path
import subprocess
import sys
import termios
import tty
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from yaml import YAMLError
from nx_yaml import nx_compose_all

from discopy.utils import tuplify, untuplify

from .files import diagram_draw, file_diagram
from .metaprog.hif import HIFToLoader
from .state.loader import LoaderToShell
from .state.python import SHELL_INTERPRETER


# TODO watch functor ??
CTRL_D = "\x04"
CTRL_J = "\x0A"
CTRL_M = "\x0D"
BACKSPACE = {"\x08", "\x7F"}


def apply_tty_input(buffer: list[str], char: str):
    """Update the pending YAML document buffer for one TTY character."""
    if char == CTRL_D:
        return ("eof" if not buffer else "submit", None)
    if char == CTRL_M:
        return ("submit", None)
    if char == CTRL_J:
        buffer.append("\n")
        return ("newline", None)
    if char in BACKSPACE:
        removed = buffer.pop() if buffer else None
        return ("backspace", removed)
    buffer.append(char)
    return ("char", None)


def read_tty_yaml_document():
    """Read one YAML document from TTY using Ctrl+J for LF and Ctrl+M to submit."""
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    buffer = []

    try:
        tty.setraw(fd)
        while True:
            raw = sys.stdin.buffer.read(1)
            if raw == b"":
                raise EOFError

            char = raw.decode("latin1")
            action, removed = apply_tty_input(buffer, char)

            if action == "eof":
                raise EOFError
            if action == "submit":
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buffer)
            if action == "newline":
                sys.stdout.write("\n")
                sys.stdout.flush()
                continue
            if action == "backspace":
                if removed and removed != "\n":
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue

            sys.stdout.write(char)
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)


def watch_log(message: str):
    """Write watcher status logs to stderr."""
    print(message, file=sys.stderr)


def read_shell_source(file_name: str, read_line=None):
    """Write command-document prompt to stdout and read one YAML document."""
    prompt = f"--- !{file_name}\n"
    sys.stdout.write(prompt)
    sys.stdout.flush()
    if read_line is not None:
        return read_line()
    if sys.stdin.isatty():
        return read_tty_yaml_document()
    source = sys.stdin.readline()
    if source == "":
        raise EOFError
    return source


def emit_shell_source(source: str):
    """Emit the executed YAML source document to stdout for transcript logging."""
    sys.stdout.write(source)
    if not source.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.flush()


class ShellHandler(FileSystemEventHandler):
    """Reload the shell on change."""
    def on_modified(self, event):
        if event.src_path.endswith(".yaml"):
            watch_log(f"reloading {event.src_path}")
            try:
                fd = file_diagram(str(event.src_path))
                diagram_draw(Path(event.src_path), fd)
                diagram_draw(Path(event.src_path+".2"), fd)
            except YAMLError as e:
                watch_log(str(e))

def watch_main():
    """the process manager for the reader and """
    #  TODO watch this path to reload changed files,
    # returning an IO as always and maintaining the contract.
    watch_log("watching for changes in current path")
    observer = Observer()
    shell_handler = ShellHandler()
    observer.schedule(shell_handler, ".", recursive=True)
    observer.start()
    return observer

def shell_main(file_name, draw=True):
    hif_to_loader = HIFToLoader()
    loader_to_shell = LoaderToShell()
    try:
        while True:
            observer = watch_main()
            try:
                source = read_shell_source(file_name)
                emit_shell_source(source)
                source_d = loader_to_shell(hif_to_loader(nx_compose_all(source)))
                # source_d.draw(
                #         textpad=(0.3, 0.1),
                #         fontsize=12,
                #         fontsize_types=8)
                path = Path(file_name)

                if draw:
                    diagram_draw(path, source_d)
                result_ev = SHELL_INTERPRETER(source_d)("")
                print(result_ev)
            except KeyboardInterrupt:
                print()
            except YAMLError as e:
                print(e)
            except subprocess.CalledProcessError as error:
                watch_log(str(error))
                stderr = (error.stderr or "").strip()
                if stderr:
                    watch_log(stderr)
            except FileNotFoundError as error:
                watch_log(str(error))
            finally:
                observer.stop()
    except EOFError:
        print("⌁")
        exit(0)

def widish_main(file_name, draw):
    fd = file_diagram(file_name)
    path = Path(file_name)
    if draw:
        diagram_draw(path, fd)
    runner = SHELL_INTERPRETER(fd)

    run_res = runner("") if sys.stdin.isatty() else runner(sys.stdin.read())

    print(*(tuple(x.rstrip() for x in tuplify(untuplify(run_res)) if x)), sep="\n")
