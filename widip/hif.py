"""Helpers for traversing YAML hypergraphs produced by nx_yaml."""

from nx_hif.hif import HyperGraph, hif_edge_incidences, hif_node, hif_node_incidences


def node_data(graph: HyperGraph, node):
    """Return the attribute dict of a hypergraph node."""
    return hif_node(graph, node)


def node_kind(graph: HyperGraph, node):
    """Return the YAML node kind for a hypergraph node."""
    return node_data(graph, node)["kind"]


def node_tag(graph: HyperGraph, node):
    """Return the YAML tag without the leading !, if present."""
    return (node_data(graph, node).get("tag") or "")[1:]


def node_value(graph: HyperGraph, node):
    """Return the scalar payload, defaulting to the empty string."""
    return node_data(graph, node).get("value", "")


def node_edges(graph: HyperGraph, node, *, key="next", direction="head"):
    """Return incidences leaving a node for the requested key/direction."""
    return tuple(hif_node_incidences(graph, node, key=key, direction=direction))


def edge_nodes(graph: HyperGraph, edge, *, key="start", direction="head"):
    """Return incidences from an edge to its incident nodes."""
    return tuple(hif_edge_incidences(graph, edge, key=key, direction=direction))


def successor_nodes(graph: HyperGraph, node, *, edge_key="next", node_key="start"):
    """
    Yield nodes reached by following incidences of type edge_key then node_key.
    """
    for edge, _, _, _ in node_edges(graph, node, key=edge_key):
        for _, target, _, _ in edge_nodes(graph, edge, key=node_key):
            yield target


def first_successor_node(graph: HyperGraph, node, *, edge_key="next", node_key="start"):
    """Return the first successor node for a given incidence pattern, if any."""
    return next(iter(successor_nodes(graph, node, edge_key=edge_key, node_key=node_key)), None)


def stream_document_nodes(graph: HyperGraph, stream=0):
    """Yield document nodes contained in a YAML stream node."""
    yield from successor_nodes(graph, stream, edge_key="next", node_key="start")


def document_root_node(graph: HyperGraph, document):
    """Return the root YAML node for a document node, if any."""
    return first_successor_node(graph, document, edge_key="next", node_key="start")


def sequence_item_nodes(graph: HyperGraph, sequence):
    """Yield sequence items in order by following next/forward links."""
    current = first_successor_node(graph, sequence, edge_key="next", node_key="start")
    while current is not None:
        yield current
        current = first_successor_node(graph, current, edge_key="forward", node_key="start")


def mapping_entry_nodes(graph: HyperGraph, mapping):
    """
    Yield `(key_node, value_node)` pairs in order for a YAML mapping node.
    """
    key_node = first_successor_node(graph, mapping, edge_key="next", node_key="start")
    while key_node is not None:
        value_node = first_successor_node(graph, key_node, edge_key="forward", node_key="start")
        if value_node is None:
            break
        yield key_node, value_node
        key_node = first_successor_node(graph, value_node, edge_key="forward", node_key="start")
