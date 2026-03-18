"""Ordered traversal over YAML documents encoded as HIF."""

from ..wire.hif import HyperGraph, hif_edge_incidences, hif_node_incidences


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
