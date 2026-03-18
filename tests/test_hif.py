from pathlib import Path

from nx_yaml import nx_compose_all

from widip.metaprog.hif import HIFSpecializer
from widip.state.hif import (
    document_root_node,
    mapping_entry_nodes,
    sequence_item_nodes,
    stream_document_nodes,
)
from widip.wire.hif import hif_node


class ShapeSpecializer(HIFSpecializer):
    def node_map(self, graph, node, kind, value, tag):
        del graph, node
        return (kind, tag, value)


def test_document_root_node_for_scalar_yaml():
    graph = nx_compose_all("a")

    documents = tuple(stream_document_nodes(graph))
    assert documents == (1,)

    root = document_root_node(graph, documents[0])
    assert hif_node(graph, root)["kind"] == "scalar"
    assert hif_node(graph, root).get("tag", "") == ""
    assert hif_node(graph, root).get("value", "") == "a"


def test_sequence_item_nodes_follow_next_and_forward_links():
    graph = nx_compose_all("- a\n- !echo b\n- c\n")
    document = tuple(stream_document_nodes(graph))[0]
    root = document_root_node(graph, document)

    items = tuple(sequence_item_nodes(graph, root))

    assert hif_node(graph, root)["kind"] == "sequence"
    assert [hif_node(graph, item).get("value", "") for item in items] == ["a", "b", "c"]
    assert [(hif_node(graph, item).get("tag") or "")[1:] for item in items] == ["", "echo", ""]


def test_mapping_entry_nodes_cover_the_shell_case_study():
    graph = nx_compose_all(Path("examples/shell.yaml").read_text())
    document = tuple(stream_document_nodes(graph))[0]
    outer_mapping = document_root_node(graph, document)

    outer_entries = tuple(mapping_entry_nodes(graph, outer_mapping))
    assert len(outer_entries) == 1

    outer_key, inner_mapping = outer_entries[0]
    assert (hif_node(graph, outer_key).get("tag") or "")[1:] == "cat"
    assert hif_node(graph, outer_key).get("value", "") == "examples/shell.yaml"
    assert hif_node(graph, inner_mapping)["kind"] == "mapping"

    inner_entries = tuple(mapping_entry_nodes(graph, inner_mapping))
    assert len(inner_entries) == 3

    first_key, first_value = inner_entries[0]
    assert ((hif_node(graph, first_key).get("tag") or "")[1:], hif_node(graph, first_key).get("value", "")) == (
        "wc",
        "-c",
    )
    assert hif_node(graph, first_value).get("value", "") == ""

    second_key, second_value = inner_entries[1]
    assert hif_node(graph, second_key)["kind"] == "mapping"
    assert hif_node(graph, second_value).get("value", "") == ""

    nested_entries = tuple(mapping_entry_nodes(graph, second_key))
    assert len(nested_entries) == 1
    nested_key, nested_value = nested_entries[0]
    assert ((hif_node(graph, nested_key).get("tag") or "")[1:], hif_node(graph, nested_key).get("value", "")) == (
        "grep",
        "grep",
    )
    assert (
        (hif_node(graph, nested_value).get("tag") or "")[1:],
        hif_node(graph, nested_value).get("value", ""),
    ) == ("wc", "-c")

    third_key, third_value = inner_entries[2]
    assert ((hif_node(graph, third_key).get("tag") or "")[1:], hif_node(graph, third_key).get("value", "")) == (
        "tail",
        "-2",
    )
    assert hif_node(graph, third_value).get("value", "") == ""


def test_fold_hif_uses_actual_yaml_node_kinds_for_scalar_documents():
    folded = ShapeSpecializer()(nx_compose_all("!echo a"))

    assert folded == ("stream", None, (("document", None, ("scalar", "echo", "a")),))


def test_fold_hif_preserves_tagged_mapping_structure():
    folded = ShapeSpecializer()(nx_compose_all("!echo\n? a\n"))

    assert folded[0] == "stream"
    assert len(folded[2]) == 1

    document = folded[2][0]
    assert document[0] == "document"

    mapping = document[2]
    assert mapping[0] == "mapping"
    assert mapping[1] == "echo"
    assert len(mapping[2]) == 1
    assert mapping[2][0][0] == ("scalar", None, "a")
    assert mapping[2][0][1] == ("scalar", None, "")


def test_fold_hif_exposes_multi_document_streams_directly():
    folded = ShapeSpecializer()(nx_compose_all("--- a\n--- b\n"))

    assert folded[0] == "stream"
    assert [document[2] for document in folded[2]] == [
        ("scalar", None, "a"),
        ("scalar", None, "b"),
    ]
