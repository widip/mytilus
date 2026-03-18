"""HIF-specific specializers and lowerings."""

from ..comput.computer import Ty
from ..state.hif import (
    document_root_node,
    mapping_entry_nodes,
    sequence_item_nodes,
    stream_document_nodes,
)
from ..wire.hif import HyperGraph, hif_node
from ..wire.loader import LoaderMapping, LoaderScalar, LoaderSequence, loader_id, pipeline


class HIFSpecializer:
    """Recursive structural lowering over YAML HIF nodes."""

    @staticmethod
    def metaprogram_dom():
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
                branches = tuple(pipeline((key, entry_value)) for key, entry_value in value)
                return LoaderMapping(branches, tag=tag)
            case _:
                raise ValueError(f"unsupported YAML node kind: {kind!r}")
