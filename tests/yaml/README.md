# Process calling

Building a Mytilus codebase using YAML involves well-known Operating System integrations such as executable processes.

## run-hello -> hello

Consider hello.yaml and run-hello.yaml. We've set hello-bin.yaml file so that:
* it has a shebang pointing to mytilus binary
* it is executable with `chmod +x hello-bin.yaml`

The `!tests/yaml/hello-bin.yaml` tag and file configuration is a cohesive strategy that implements import-like behavior with no additional cost. The tradeoff of requiring explicit tracking of executable files is reinterpreted as a security policy in the context of an agentic shell.

Now `bin/mytilus tests/yaml/run-hello.yaml` uses a process call.
```yaml
? !tests/yaml/hello-bin.yaml
? " World!"
```

This is equivalent to the following Bash script.
```sh
tests/yaml/hello-bin.yaml
echo " World!"
```