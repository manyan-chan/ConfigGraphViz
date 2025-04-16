# tests/test_graph_builder.py
import re  # Import regex for better matching
from pathlib import Path

import pytest

from configgraphviz import build_dot_graph, parse_config

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# --- Helper Functions ---
def find_node_definition(dot_output: str, node_id: str) -> str:
    """Finds the full line defining a node, ignoring leading/trailing whitespace."""
    # Regex to find the node definition line, allowing for attributes
    # Matches "node_id" [ potentially complex attributes ];
    match = re.search(
        rf'^\s*"{re.escape(node_id)}"\s*\[.*\];\s*$', dot_output, re.MULTILINE
    )
    assert match, f"Node definition for ID '{node_id}' not found."
    return match.group(0)


def find_edge_definition(dot_output: str, from_id: str, to_id: str) -> str:
    """Finds the full line defining an edge, ignoring leading/trailing whitespace."""
    # Regex to find the edge definition line
    # Matches "from_id" -> "to_id" [ potentially complex attributes ];
    match = re.search(
        rf'^\s*"{re.escape(from_id)}"\s*->\s*"{re.escape(to_id)}"\s*\[.*\];\s*$',
        dot_output,
        re.MULTILINE,
    )
    assert match, f"Edge definition from '{from_id}' to '{to_id}' not found."
    return match.group(0)


def assert_label_in_definition(definition: str, expected_label: str):
    """Checks if the expected label attribute exists in the node/edge definition line."""
    # Simple check, assuming label="escaped_value" format
    assert f'label="{expected_label}"' in definition, (
        f"Expected label '{expected_label}' not found in definition: {definition}"
    )


# --- Test Cases ---


def test_build_dot_simple_dict():
    data = {"section_a": {"key1": "value1", "key2": 123}, "section_b": True}
    dot = build_dot_graph(data, "SimpleDict")
    print(dot)

    assert 'digraph "SimpleDict"' in dot
    assert "rankdir=LR" in dot

    # Check Nodes (existence and key attributes)
    node_root = find_node_definition(dot, "root")
    assert_label_in_definition(node_root, "(root)")
    assert "shape=box" in node_root
    assert "fillcolor=lightblue" in node_root

    node_sec_a = find_node_definition(dot, "root__section_a")
    assert_label_in_definition(node_sec_a, "section_a")
    assert "shape=box" in node_sec_a

    node_key1_val = find_node_definition(dot, "root__section_a__key1_value")
    assert_label_in_definition(node_key1_val, "value1")
    assert "shape=plaintext" in node_key1_val

    node_key2_val = find_node_definition(dot, "root__section_a__key2_value")
    assert_label_in_definition(node_key2_val, "123")
    assert "shape=plaintext" in node_key2_val

    node_sec_b_val = find_node_definition(dot, "root__section_b_value")
    assert_label_in_definition(node_sec_b_val, "True")
    assert "shape=plaintext" in node_sec_b_val

    # Check Edges (existence and labels)
    edge_root_a = find_edge_definition(dot, "root", "root__section_a")
    assert_label_in_definition(edge_root_a, "section_a")

    edge_root_b = find_edge_definition(dot, "root", "root__section_b_value")
    assert_label_in_definition(edge_root_b, "section_b")

    edge_a_k1 = find_edge_definition(
        dot, "root__section_a", "root__section_a__key1_value"
    )
    assert_label_in_definition(edge_a_k1, "key1")

    edge_a_k2 = find_edge_definition(
        dot, "root__section_a", "root__section_a__key2_value"
    )
    assert_label_in_definition(edge_a_k2, "key2")


def test_build_dot_with_list():
    data = {"items": ["a", 1, None, {"sub": "dict"}], "other": True}
    dot = build_dot_graph(data, "ListTest")
    print(dot)

    assert 'digraph "ListTest"' in dot
    list_node_id = "root__items_list"
    item0_val_id = f"{list_node_id}__item_0_value"
    item1_val_id = f"{list_node_id}__item_1_value"
    item2_val_id = f"{list_node_id}__item_2_value"
    item3_dict_id = f"{list_node_id}__item_3"
    item3_sub_val_id = f"{item3_dict_id}__sub_value"
    other_val_id = "root__other_value"

    # Check Nodes
    node_root = find_node_definition(dot, "root")
    assert_label_in_definition(node_root, "(root)")

    node_list = find_node_definition(dot, list_node_id)
    assert_label_in_definition(node_list, "items (list)")
    assert "shape=box3d" in node_list

    node_item0 = find_node_definition(dot, item0_val_id)
    assert_label_in_definition(node_item0, "a")

    node_item1 = find_node_definition(dot, item1_val_id)
    assert_label_in_definition(node_item1, "1")

    node_item2 = find_node_definition(dot, item2_val_id)
    assert_label_in_definition(node_item2, "None")

    node_item3_dict = find_node_definition(dot, item3_dict_id)
    assert_label_in_definition(
        node_item3_dict, "item_3"
    )  # Label is based on path prefix
    assert "shape=box" in node_item3_dict

    node_item3_sub_val = find_node_definition(dot, item3_sub_val_id)
    assert_label_in_definition(node_item3_sub_val, "dict")

    node_other_val = find_node_definition(dot, other_val_id)
    assert_label_in_definition(node_other_val, "True")

    # Check Edges
    edge_root_list = find_edge_definition(dot, "root", list_node_id)
    assert_label_in_definition(edge_root_list, "items")

    edge_root_other = find_edge_definition(dot, "root", other_val_id)
    assert_label_in_definition(edge_root_other, "other")

    edge_list_item0 = find_edge_definition(dot, list_node_id, item0_val_id)
    assert_label_in_definition(edge_list_item0, "0")

    edge_list_item1 = find_edge_definition(dot, list_node_id, item1_val_id)
    assert_label_in_definition(edge_list_item1, "1")

    edge_list_item2 = find_edge_definition(dot, list_node_id, item2_val_id)
    assert_label_in_definition(edge_list_item2, "2")

    edge_list_item3 = find_edge_definition(
        dot, list_node_id, item3_dict_id
    )  # Edge to the dict node
    assert_label_in_definition(edge_list_item3, "3")

    edge_item3_sub = find_edge_definition(dot, item3_dict_id, item3_sub_val_id)
    assert_label_in_definition(edge_item3_sub, "sub")


def test_build_dot_from_ini_file():
    data = parse_config(FIXTURES_DIR / "example.ini")
    dot = build_dot_graph(data, "INI_Graph")
    print(dot)

    assert 'digraph "INI_Graph"' in dot
    section_id = "root__bitbucket_org"
    value_id = f"{section_id}__user_value"

    node_sec = find_node_definition(dot, section_id)
    assert_label_in_definition(
        node_sec, "bitbucket_org"
    )  # Label is sanitized section name
    assert "shape=box" in node_sec

    node_val = find_node_definition(dot, value_id)
    assert_label_in_definition(node_val, "hg")
    assert "shape=plaintext" in node_val

    edge_root_sec = find_edge_definition(dot, "root", section_id)
    assert_label_in_definition(
        edge_root_sec, "bitbucket.org"
    )  # Edge label is original section name

    edge_sec_val = find_edge_definition(dot, section_id, value_id)
    assert_label_in_definition(edge_sec_val, "user")


def test_build_dot_escaping():
    data = {"key w/ space": {"sub<key>": "value\"'\n{}\\ T"}}
    dot = build_dot_graph(data, "Escape Test")
    print(dot)

    assert 'digraph "Escape Test"' in dot
    node1_id = "root__key_w_space"
    # The inner node ID prefix is based on the sanitized key 'sub_key'
    value_node_id = f"{node1_id}__sub_key_value"  # ID for the value node

    # Check node definitions
    node1 = find_node_definition(dot, node1_id)
    assert_label_in_definition(node1, "key_w_space")
    assert "shape=box" in node1

    # Check the value node definition and its complex label
    node_val = find_node_definition(dot, value_node_id)
    # Expected DOT label: value"'\n\{\}\\ T
    # Python string for expected label needs appropriate escaping:
    expected_value_label = "value\\\"'\\n\\{\\}\\\\ T"  # " ' \n { } \ T
    assert_label_in_definition(node_val, expected_value_label)
    assert "shape=plaintext" in node_val

    # Check edges
    edge1 = find_edge_definition(dot, "root", node1_id)
    assert_label_in_definition(edge1, "key w/ space")  # Edge label uses original key

    # Edge goes from dict node to value node, label is original key <sub<key>> escaped
    edge2 = find_edge_definition(dot, node1_id, value_node_id)
    expected_edge_label = "sub\\<key\\>"  # < and > escaped
    assert_label_in_definition(edge2, expected_edge_label)


def test_build_dot_truncation():
    long_value = "a" * 100
    data = {"long": long_value}
    dot = build_dot_graph(data, "Truncate")
    print(dot)

    # format_value_for_label uses str() now
    expected_label = "a" * 50 + "..."
    value_node_id = "root__long_value"

    node_val = find_node_definition(dot, value_node_id)
    assert_label_in_definition(node_val, expected_label)
    assert "shape=plaintext" in node_val

    edge_root_val = find_edge_definition(dot, "root", value_node_id)
    assert_label_in_definition(edge_root_val, "long")


if __name__ == "__main__":
    pytest.main()
