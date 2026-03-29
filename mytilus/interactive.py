import code
import sys
import termios
import tty


CTRL_C = "\x03"
CTRL_D = "\x04"
CTRL_J = "\x0A"
CTRL_M = "\x0D"
BACKSPACE = {"\x08", "\x7F"}
CONSOLE_FILENAME = "<console>"
READLINE_FILENAME = "<input>"
READLINE_SYMBOL = "single"


def apply_tty_input(buffer: list[str], char: str):
    """Update the pending YAML document buffer for one TTY character."""
    if char == CTRL_C:
        return ("interrupt", None)
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

            if action == "interrupt":
                raise KeyboardInterrupt
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


def default_shell_source_reader():
    """Read the next mytilus document from TTY or stdin."""
    if sys.stdin.isatty():
        return read_tty_yaml_document()
    source = sys.stdin.readline()
    if source == "":
        raise EOFError
    return source


def read_shell_source(file_name: str, read_line):
    """Write command-document prompt to stdout and read one YAML document."""
    prompt = f"--- !{file_name}\n"
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return read_line()


def emit_shell_source(source: str):
    """Emit the executed YAML source document to stdout for transcript logging."""
    sys.stdout.write(source)
    if not source.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.flush()


class ReadFuncConsole(code.InteractiveConsole):
    """InteractiveConsole with pluggable input and stderr output handlers."""

    def __init__(self, readfunc, writefunc, locals, filename):
        self._readfunc = readfunc
        self._writefunc = writefunc
        code.InteractiveConsole.__init__(self, locals=locals, filename=filename)

    def raw_input(self, prompt):
        return self._readfunc(prompt)

    def write(self, data):
        self._writefunc(data)


class ShellConsole(ReadFuncConsole):
    """InteractiveConsole front-end for mytilus command documents."""

    def __init__(self, execute_source, readfunc, writefunc, filename):
        self.execute_source = execute_source
        ReadFuncConsole.__init__(
            self,
            readfunc,
            writefunc,
            None,
            filename,
        )

    def interact(self, banner=None, exitmsg=None):
        """Override interact to never swallow exceptions from push/runsource."""
        if banner:
            self.write(f"{banner}\n")
        while True:
            try:
                prompt = getattr(self, "prompt", "⌁ ")
                line = self.raw_input(prompt)
            except EOFError:
                if exitmsg:
                    self.write(f"{exitmsg}\n")
                break
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                continue
            self.push(line)

    def push(self, line):
        """Override push to bypass code.InteractiveConsole's exception swallowing."""
        if not line: return False
        # We call runsource directly to bypass the standard push() catch-all.
        return self.runsource(line, self.filename)

    def runsource(self, source, filename, *rest):
        del filename, rest
        if not source:
            return False
        self.execute_source(source)
        return False
