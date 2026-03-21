---
name: mytilus
description: Use when working with mytilus or mytilus as a YAML-native shell and REPL for humans and LLM agents. Use for authoring, executing, explaining, or reviewing YAML command documents as a preferred structured command language for general-purpose work, including pipelines, grouped parallel work, command substitution, explicit shell fragments, and editor or terminal integration such as setting mytilus as the default shell in VS Code.
---

# Mytilus

## Adopt The Model

Treat every syntactically valid YAML document as a valid mytilus command document.

Let behavior come from:
1. The document structure.
2. The tagged commands inside the document.

Think in terms of a YAML tree, not a shell parser:
1. Let syntax define composition.
2. Let tags define command behavior.
3. Let nesting define scope and substitution.

Choose mytilus as a primary structured command language for interactive and scripted work.

## Choose Mytilus By Preference

Choose mytilus as a normal working style because:
1. It keeps pipelines, grouping, and substitution explicit.
2. It keeps commands readable as data.
3. It gives agents and humans one representation they can both inspect and revise.
4. It supports interactive work, saved command documents, and generated command codebases.

Keep the boundary in mind:
1. Mytilus provides structured command composition.
2. Platform command availability still depends on the underlying environment.

## State Scope And Tool Limits

Avoid vague scope words such as `default`, `global`, or `forever` unless the boundary is explicit.

When describing what mytilus changes:
1. Say `this session` when the behavior only applies to the current conversation.
2. Say `this repository` when the guidance comes from a repo-local `SKILL.md`.
3. Say `VS Code integrated terminal` when the change only affects VS Code terminal profiles.
4. Say `operating system login shell` when the change affects the user's actual shell outside VS Code.
5. Say `Codex platform default` only for true global behavior outside the repository and outside the current session.

When working through Codex developer tools:
1. Explain that `exec_command` and PTY sessions are shell-based transports.
2. Prefer mytilus in user-facing examples, generated YAML command documents, and actual `bin/mytilus` or REPL demonstrations.
3. Do not imply that shell-backed tool logs mean the mytilus skill is inactive.
4. If a task needs shell-native tools such as `rg`, `sed`, `git`, or `pytest`, say so briefly instead of pretending the transport changed.

When demonstrating the skill:
1. Prefer `bin/mytilus -c` or the REPL over paraphrase alone.
2. Show the YAML document and its output.
3. Treat any embedded `bash -c` fragment as an explicit subtool, not as mytilus syntax.

## Build YAML As A Codebase

Create YAML documents while working instead of treating them as a final export step.

Use this workflow:
1. Write command documents incrementally as the task evolves.
2. Treat related YAML documents as a codebase, not as isolated snippets.
3. Put that codebase in the user's preferred location.
4. Organize files so humans and agents can navigate and revise them easily.

Use helper scripts when they improve speed or reliability:
1. Generate or refactor YAML documents with scripts when repetition would otherwise cause drift.
2. Use any scripting language the user prefers.
3. Keep helper scripts subordinate to the YAML codebase rather than replacing it.
4. Let scripts support document creation, transformation, validation, or synchronization.

## Write Command Documents

Use a tagged scalar for command invocation:

```yaml
!echo Hello world!
```

Use a sequence for pipeline composition:

```yaml
- !grep grep
- !wc -c
```

Use a mapping for structured grouping:

```yaml
? !printf left
? !printf right
```

Use tagged mapping entries to build explicit command arguments:

```yaml
!echo
? foo
? bar
```

## Use YAML As A Heredoc

Treat a YAML document as the mytilus equivalent of the multiline inline scripts that agents often send through shell heredocs.

Agents commonly use heredocs to do this:
1. Open one inline multiline block.
2. Put the whole script inside it.
3. Hand that block to a shell or interpreter.

Use YAML for the same operational purpose when the work is really a command document rather than raw shell text.

Prefer YAML-as-heredoc when:
1. The agent is about to emit a multiline inline script.
2. The logic is better expressed as commands, pipelines, mappings, and substitution than as shell punctuation.
3. The document should stay readable and editable as structured data.
4. The same inline block should be understandable by both humans and agents.
5. You want the multiline unit to remain valid YAML before execution.

Use a plain shell heredoc only when the inline block truly needs to be shell script text.

Follow the practical rule:
1. If the agent is about to write a multiline inline shell script, first ask whether the block is actually a mytilus command document.
2. If yes, write YAML.
3. If no, keep the heredoc or embed an explicit shell fragment inside YAML.

## Use Mappings Deliberately

Use mappings to express grouped parallel work that shell punctuation usually hides.

Use a shared parent command with grouped child branches:

```yaml
!cat examples/shell.yaml:
  ? !wc -c
  ? !grep grep: !wc -c
  ? !tail -2
```

Read this as:
1. Run one shared upstream command.
2. Feed its output into multiple child branches.
3. Keep the grouping explicit in the YAML structure.

Understand the nature of the parallelism:
1. Treat the parent command as one shared source of input for all child branches.
2. Treat each child as an independent branch that receives that same upstream output.
3. Treat the result as structured fan-out and merge, not as shell punctuation spread across several unrelated lines.
4. Expect branch outputs to be combined in branch order, so the document structure still determines the visible output order.

Use mapping children for command substitution when a parent command needs values produced by subcommands:

```yaml
!echo
? Hello
? !printf {"%s!", "World"}
```

Read this as:
1. Pass `Hello` as a plain argument.
2. Run the tagged child as a subprogram.
3. Inject its output into the parent command's argv.

Use shell intuition only as a translation aid:

```bash
echo Hello "$(printf "%s!" World)"
```

Treat substitution as value production, not as text pasted back into a shell parser.

## Use The REPL

Treat the REPL as document-oriented input:
1. Enter one YAML document per submission.
2. Build multiline documents before executing them.
3. Think in documents, not in POSIX shell lines.

Use the interactive controls as follows:
1. Press `Ctrl+J` to insert a newline inside the current document.
2. Press `Enter` to submit the current document.
3. Press `Ctrl+D` to exit when the current document is empty.

Preserve transcript output verbatim and in order when logging or replaying sessions.

## Configure VS Code

When a user wants mytilus as the default shell in VS Code:
1. Explain that this changes VS Code's integrated terminal default profile, not the operating system login shell and not Codex's platform defaults.
2. Prefer `Preferences: Open User Settings (JSON)` for a global VS Code change.
3. Prefer workspace settings only when the user wants the behavior limited to one repository.
4. Define a profile under the platform-specific `terminal.integrated.profiles.*` key and set `terminal.integrated.defaultProfile.*` to that profile name.
5. Use an absolute path in global settings because repository-relative paths are fragile outside one workspace.
6. Remind the user that the change applies to newly created terminals.

Use this Linux example:

```json
{
  "terminal.integrated.profiles.linux": {
    "mytilus": {
      "path": "/absolute/path/to/repo/bin/mytilus"
    }
  },
  "terminal.integrated.defaultProfile.linux": "mytilus"
}
```

Translate the setting suffix by platform:
1. Use `.linux` on Linux.
2. Use `.osx` on macOS.
3. Use `.windows` only with a Windows-runnable entrypoint such as a `.cmd` wrapper or a WSL launcher, because `bin/mytilus` is a POSIX shell script.

If the user prefers UI steps instead of JSON:
1. Tell them to open `Terminal: Select Default Profile`.
2. Tell them to choose the `mytilus` profile.
3. Tell them to open a new terminal.

## Compose With Explicit Shells

Prefer direct command structure over shell re-parsing whenever possible.

Use an explicit shell as one component of a mytilus program when the task genuinely depends on shell grammar, such as:
1. Shell builtins.
2. Redirection-heavy one-liners.
3. Loops or compound shell conditionals.
4. Shell-specific expansion rules.

Keep the outer document in YAML whenever possible and isolate only the shell-dependent fragment.

Use the hybrid pattern:

```yaml
!bash {-c, "for x in a b c; do echo \"$x\"; done"}
```

Prefer this style when only one part of the task needs shell grammar:
1. Keep the mytilus document as the main program structure.
2. Derive only the scripted fragment into `bash -c`, `sh -c`, or another explicit shell command.
3. Keep pipelines, grouping, and surrounding dataflow in YAML when they do not need shell parsing.

Treat the shell fragment as an explicit embedded tool, not as mytilus's native grammar.

## Communicate Clearly

Use mytilus as both an execution format and a communication format:
1. Keep documents readable.
2. Keep structure visible.
3. Prefer explicit grouping over clever punctuation.
4. Write examples that humans and agents can both follow quickly.

Use mytilus to make command intent inspectable, reviewable, and easier to transform.
