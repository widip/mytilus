#!/bin/sh
# startup-check.sh: Runtime verification of the Mytilus environment

# This check uses `sh -c` to verify that the Mytilus shell is correctly configured.
# Mytilus recognizes the `!tag` syntax for command execution.

# Ensure /app/bin is in PATH for the check
export PATH="/app/bin:$PATH"

if sh -c "!echo Mytilus check passed" 2>/dev/null | grep -q "Mytilus check passed"; then
    echo "Check passed: Mytilus is correctly configured as the default shell."
    exit 0
else
    echo "Check failed: Mytilus environment is not properly active for the current shell."
    exit 1
fi
