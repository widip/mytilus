# Mytilus Environment Setup

To properly set up the Mytilus environment, run the following command from the repository root:

```bash
/app/bin/jules-setup.sh
```

This script will:
1. Create a Python virtual environment and install `mytilus` in editable mode.
2. Add `/app/bin/mytilus` to `/etc/shells` if not already present.
3. Change the login shell of the `jules` user to `/app/bin/mytilus`.

When `mytilus` is used as a login shell, it will automatically receive the `-l` or `--login` flag, which is supported and ignored for compatibility.

`mytilus` also ensures that the default shell source file `bin/yaml/shell.yaml` exists during startup.

## Runtime Verification

To verify that the Mytilus environment is correctly active as the default `sh` shell, run:

```bash
/app/startup-check.sh
```

This script uses `sh -c "!echo ..."` to confirm that the current shell process is Mytilus.

## Logging
Present the user with a history file of input activity, such as each command that is passed to the interactive shell and each `sh -c` invocation.
