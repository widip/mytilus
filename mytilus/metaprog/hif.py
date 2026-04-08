"""HIF-specific specializers and lowerings."""

from discorun.comput.computer import Ty
from ..wire.hif import HyperGraph, hif_edge_incidences, hif_node, hif_node_incidences
from ..wire.loader import LoaderMapping, LoaderScalar, LoaderSequence, loader_id, pipeline


def _is_command_substitution_program(node):
    """Return whether one loader node is a valid substitution subprogram."""
    if isinstance(node, LoaderScalar):
        return isinstance(node.value, str) and node.tag is not None
    if isinstance(node, LoaderSequence):
        return bool(node.stages) and all(_is_command_substitution_program(stage) for stage in node.stages)
    if isinstance(node, LoaderMapping):
        return bool(node.branches) and all(_is_command_substitution_program(branch) for branch in node.branches)
    return False


def _mapping_key_command_arg(key_node):
    """Compile one mapping key to an argv argument for tagged mappings."""
    if isinstance(key_node, (LoaderSequence, LoaderMapping)):
        if not _is_command_substitution_program(key_node):
            return None
        # Structured keys are command-substitution programs.
        return key_node
    if not isinstance(key_node, LoaderScalar):
        return None
    if key_node.tag is None:
        if not isinstance(key_node.value, str):
            return None
        return key_node.value
    # Tagged scalar keys (whether string or tuple argv) are command-substitution arguments.
    return LoaderScalar(key_node.value, key_node.tag)


def _mapping_command_args(entries):
    """Return argv pieces for tagged scalar mappings, else ``None``."""
    argv = []
    for key_node, value_node in entries:
        key_arg = _mapping_key_command_arg(key_node)
        if key_arg is None:
            return None

        # Value can be a plain scalar (argument) or an identity (empty argument).
        if value_node == loader_id():
            val = ""
        elif isinstance(value_node, LoaderScalar) and value_node.tag is None:
            if not isinstance(value_node.value, str):
                return None
            val = value_node.value
        else:
            return None

        if key_arg:
            argv.append(key_arg)
        if val:
            argv.append(val)
    return tuple(argv)


def _successor_nodes(graph: HyperGraph, node, *, edge_key="next", node_key="start"):
    """Yield successor nodes reached by one edge-node incidence pattern."""
    for edge, _, _, _ in hif_node_incidences(graph, node, key=edge_key, direction="head"):
        for _, target, _, _ in hif_edge_incidences(graph, edge, key=node_key, direction="head"):
            yield target


def _first_successor_node(graph: HyperGraph, node, *, edge_key="next", node_key="start"):
    """Return the first successor node for a given incidence pattern, if any."""
    return next(iter(_successor_nodes(graph, node, edge_key=edge_key, node_key=node_key)), None)


def stream_document_nodes(graph: HyperGraph, stream=0):
    """Yield stream documents in order by following next/forward links."""
    current = _first_successor_node(graph, stream, edge_key="next", node_key="start")
    while current is not None:
        yield current
        current = _first_successor_node(graph, current, edge_key="forward", node_key="start")


def document_root_node(graph: HyperGraph, document):
    """Return the root YAML node for a document node, if any."""
    return _first_successor_node(graph, document, edge_key="next", node_key="start")


def sequence_item_nodes(graph: HyperGraph, sequence):
    """Yield sequence items in order by following next/forward links."""
    current = _first_successor_node(graph, sequence, edge_key="next", node_key="start")
    while current is not None:
        yield current
        current = _first_successor_node(graph, current, edge_key="forward", node_key="start")


def mapping_entry_nodes(graph: HyperGraph, mapping):
    """Yield `(key_node, value_node)` pairs in order for a YAML mapping node."""
    key_node = _first_successor_node(graph, mapping, edge_key="next", node_key="start")
    while key_node is not None:
        value_node = _first_successor_node(graph, key_node, edge_key="forward", node_key="start")
        if value_node is None:
            break
        yield key_node, value_node
        key_node = _first_successor_node(graph, value_node, edge_key="forward", node_key="start")


class HIFSpecializer:
    """Recursive structural lowering over YAML HIF nodes."""

    def metaprogram_dom(self):
        del self
        return Ty()

    def specialize(self, graph: HyperGraph, node=0):
        node_data = hif_node(graph, node)
        kind = node_data["kind"]
        tag = (node_data.get("tag") or "")[1:] or None

        match kind:
            case "stream":
                value = tuple(self.specialize(graph, child) for child in stream_document_nodes(graph, node))
            case "document":
                root = document_root_node(graph, node)
                value = None if root is None else self.specialize(graph, root)
            case "scalar":
                value = node_data.get("value", "")
            case "sequence":
                value = tuple(self.specialize(graph, child) for child in sequence_item_nodes(graph, node))
            case "mapping":
                value = tuple(
                    (
                        self.specialize(graph, key_node),
                        self.specialize(graph, value_node),
                    )
                    for key_node, value_node in mapping_entry_nodes(graph, node)
                )
            case _:
                raise ValueError(f"unsupported YAML node kind: {kind!r}")
        return self.node_map(graph, node, kind, value, tag)

    def __call__(self, graph: HyperGraph, node=0):
        return self.specialize(graph, node)

    def node_map(self, graph: HyperGraph, node, kind: str, value, tag: str | None):
        raise NotImplementedError


class HIFToLoader(HIFSpecializer):
    """Specialize YAML HIF structure to loader-language diagrams."""

    def node_map(self, graph: HyperGraph, node, kind: str, value, tag: str | None):
        del graph, node
        match kind:
            case "stream":
                return pipeline(value)
            case "document":
                return loader_id() if value is None else value
            case "scalar":
                return LoaderScalar(value, tag)
            case "sequence":
                return LoaderSequence(value, tag=tag)
            case "mapping":
                if tag is not None:
                    command_args = _mapping_command_args(value)
                    if command_args is not None:
                        return LoaderScalar(command_args, tag)
                branches = tuple(LoaderSequence((key, entry_value)) for key, entry_value in value)
                return LoaderMapping(branches, tag=tag)
            case _:
                raise ValueError(f"unsupported YAML node kind: {kind!r}")
