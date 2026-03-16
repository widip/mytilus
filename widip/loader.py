"""Load YAML hypergraphs into loader diagrams and compile them to shell."""

from nx_yaml import nx_compose_all

from .comput.loader import LoaderCommand, LoaderEmpty, LoaderLiteral
from .hif import (
    HyperGraph,
    document_root_node,
    mapping_entry_nodes,
    node_kind,
    node_tag,
    node_value,
    sequence_item_nodes,
    stream_document_nodes,
)
from .metaprog import LOADER_TO_SHELL
from .state.loader import run_loader_program
from .wire.loader import LoaderMapping, LoaderSequence, loader_id, pipeline


def repl_read(stream):
    """Parse a YAML stream and compile it to the shell backend."""
    incidences = nx_compose_all(stream)
    return LOADER_TO_SHELL(incidences_to_program(incidences))


def incidences_to_program(node: HyperGraph):
    """Turn an ``nx_yaml`` hypergraph into a loader-language diagram."""
    return _incidences_to_program(node, 0)


def _incidences_to_program(node: HyperGraph, index):
    kind = node_kind(node, index)
    tag = node_tag(node, index)

    match kind:
        case "stream":
            diagram = load_stream(node, index)
        case "document":
            diagram = load_document(node, index)
        case "scalar":
            return load_scalar(node, index, tag)
        case "sequence":
            if tag:
                return load_tagged_sequence(node, index, tag)
            diagram = load_sequence(node, index)
        case "mapping":
            if tag:
                return load_tagged_mapping(node, index, tag)
            diagram = load_mapping(node, index)
        case _:
            raise ValueError(f"unsupported YAML node kind: {kind!r}")

    if tag:
        diagram = diagram >> run_loader_program(LoaderCommand((tag,)))
    return diagram


def load_scalar(node, index, tag):
    """Scalars lower directly to runnable loader diagrams."""
    value = node_value(node, index)
    if not value and not tag:
        return loader_id()

    scalar = LoaderLiteral(value) if value else LoaderEmpty()
    if tag:
        scalar = scalar.partial_apply(LoaderCommand((tag,)))
    return run_loader_program(scalar)


def load_mapping(node, index):
    """Mappings denote parallel branches in the loader language."""
    branches = []
    for key_node, value_node in mapping_entry_nodes(node, index):
        key = _incidences_to_program(node, key_node)
        value = _incidences_to_program(node, value_node)
        branches.append(pipeline((key, value)))
    return LoaderMapping(branches)


def load_sequence(node, index):
    """Sequences denote shell-style pipelines in the loader language."""
    stages = tuple(_incidences_to_program(node, child) for child in sequence_item_nodes(node, index))
    return LoaderSequence(stages)


def argv_item(diagram):
    """Normalize one loader child diagram as one newline-delimited argv item."""
    return diagram >> run_loader_program(LoaderCommand(("xargs", "printf", "%s\n")))


def load_tagged_mapping(node, index, tag):
    """Tagged mappings treat each branch as an argv-supplying process."""
    branches = []
    for key_node, value_node in mapping_entry_nodes(node, index):
        key = _incidences_to_program(node, key_node)
        value = _incidences_to_program(node, value_node)
        branches.append(argv_item(pipeline((key, value))))
    return LoaderMapping(branches) >> run_loader_program(LoaderCommand(("xargs", tag)))


def load_tagged_sequence(node, index, tag):
    """Tagged sequences treat each item as an argv-supplying process."""
    branches = tuple(argv_item(_incidences_to_program(node, child)) for child in sequence_item_nodes(node, index))
    return LoaderMapping(branches) >> run_loader_program(LoaderCommand(("xargs", tag)))


def load_document(node, index):
    """A document is its root node, if present."""
    root = document_root_node(node, index)
    if root is None:
        return loader_id()
    return _incidences_to_program(node, root)


def load_stream(node, index):
    """A stream is the pipeline of its documents."""
    documents = tuple(_incidences_to_program(node, child) for child in stream_document_nodes(node, index))
    return pipeline(documents)
