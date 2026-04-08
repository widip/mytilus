Mytilus
-----

> _Types? Where we're going, we don't need types!_

Mytilus is an [interactive environment] for computing in modern systems. Many long-standing systems have thrived thanks to a uniform metaphor, which in our case is wiring diagrams.

System   |Metaphor
---------|--------------
Mytilus    |Wiring Diagram
UNIX     |File
Lisp     |List
Smalltalk|Object

![](examples/typical-vscode-setup.png)


# Installation

`mytilus` can be installed via [pip](https://pypi.org/project/mytilus/) and run from the command line. We recommend setting up a virtual environment such as with [`venv`](https://docs.python.org/3/library/venv.html):

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/mytilus
```

This will automatically install dependencies: [discopy](https://pypi.org/project/discopy/) (computing, drawing), [pyyaml](https://pypi.org/project/pyyaml/) (parser library), and [watchdog](https://pypi.org/project/watchdog/) (filesystem watcher).

## Local install

If you're working with a local copy of this repository, run `.venv/bin/pip install -e .`.

# Using `mytilus`

The `mytilus` program starts a [chatbot] or [command-line interface]. It integrates with the [filesystem] for rendering diagram files.

## Inline commands (`-c`)

Run a single YAML document from the command line:

```bash
.venv/bin/mytilus -c "!echo hello-from-mytilus"
# hello-from-mytilus
```

Python is treated as a first-class subprocess and inherits the terminal when run interactively:

```bash
.venv/bin/mytilus -c "!python3 -q"
# >>>
```

## Running YAML files

Pass a `.yaml` file as an argument to execute it as a program. Mytilus **renders an SVG diagram alongside the file by default**. Pass `--no-draw` to skip rendering:

```bash
# execute and render examples/pipeline/argv-example.svg
.venv/bin/mytilus examples/pipeline/argv-example.yaml Alpha Beta

# execute only, no SVG output
.venv/bin/mytilus --no-draw examples/pipeline/argv-example.yaml Alpha Beta
```

Mytilus automatically prepends the file's own directory to `PATH`, so sibling YAML binaries are resolvable by name — regardless of the working directory.

## Argument passing — `(ARG n)`

When a `.yaml` file is invoked, the command-line arguments are available inside it via the `(ARG n)` placeholder syntax, where `n` is **0-based**:

| Placeholder | Maps to |
|-------------|---------|
| `(ARG 0)` | First argument after the filename |
| `(ARG 1)` | Second argument |
| `(ARG n)` | *n*-th argument |

Missing arguments silently resolve to an **empty string `""`**, so scripts are safe to call with fewer arguments than expected.

### Example — `examples/pipeline/mybin.yaml`

```yaml
#!/usr/bin/env mytilus
!echo { (ARG 0), (ARG 1) }
```

```bash
.venv/bin/mytilus --no-draw examples/pipeline/mybin.yaml Hello World
# Hello World
```

### Forwarding arguments through a call chain

`(ARG n)` is resolved at each level independently from `sys.argv` of that process. This means intermediate scripts can reorder or filter arguments before forwarding.

`argv-example.yaml` forwards both args to `argv-bin.yaml` unchanged:

```yaml
#!/usr/bin/env mytilus
!argv-bin.yaml { (ARG 0), (ARG 1) }
```

`argv-bin.yaml` reverses them before calling `mybin.yaml`:

```yaml
#!/usr/bin/env mytilus
!mybin.yaml { (ARG 1), (ARG 0) }
```

So the full chain behaves as:

```bash
.venv/bin/mytilus --no-draw examples/pipeline/argv-example.yaml Alpha Beta
# Beta Alpha
```


## Interactive shell (`-i`)

Use `-i` to drop into the REPL after running a file or inline command:

```bash
.venv/bin/mytilus -i -c "!echo hello-from-interactive"
# hello-from-interactive
# --- !bin/yaml/shell.yaml
```

`Ctrl-C` interrupts the current document and returns to the prompt. `Ctrl-D` exits.

## Parallel pipelines

YAML sequences (`- item`) become pipelines; YAML mappings become parallel branches. The `examples/shell.yaml` demo fans out a file across several independent analyses:

```yaml
!cat examples/shell.yaml:
  ? !wc -c
  ? !grep grep: !wc -c
  ? !tail -2
```

## For documentation

Every time a `.yaml` file is loaded, Mytilus renders an SVG diagram next to it (e.g. `argv-example.svg`). Pass `--no-draw` to skip rendering. VS Code automatically reloads markdown previews when those images change, making widis great for git-based documentation.

## For graphical programming

Widis are also [graphical programming](https://graphicallinearalgebra.net/2015/04/26/adding-part-1-and-mr-fibonacci/) tools. Start with [examples/mascarpone](examples/mascarpone) then take a look at current work in a functional library at [src](src).


[UNIX shell]: https://en.wikipedia.org/wiki/Unix_shell
[chatbot]: https://en.wikipedia.org/wiki/chatbot
[command-line interface]: https://en.wikipedia.org/wiki/Command-line_interface
[filesystem]: https://en.wikipedia.org/wiki/File_manager
[interactive environment]: https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop
