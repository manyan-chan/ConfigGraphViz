# configgraphviz/graph_builder.py

import re  # Import regex module
from typing import Any, Dict, List, Set, Tuple

# Type alias from parsers
ParsedConfig = Dict[str, Any]

# Node shape constants
SHAPE_SECTION = "box"  # For sections or dictionary keys
SHAPE_LIST = "box3d"  # For lists
SHAPE_SIMPLE_VALUE = "plaintext"  # For the actual value node

# Max length for value display
MAX_VALUE_LENGTH = 50
TRUNCATION_SUFFIX = "..."


def escape_dot_label(label: str) -> str:
    """Escapes characters special to DOT labels."""
    label = label.replace("\\", "\\\\")
    label = label.replace('"', '\\"')
    label = label.replace("{", "\\{")
    label = label.replace("}", "\\}")
    label = label.replace("<", "\\<")
    label = label.replace(">", "\\>")
    label = label.replace("|", "\\|")
    label = label.replace("\n", "\\n")
    label = label.replace("\r", "")
    return label


def format_value_for_label(value: Any) -> str:
    """Converts value to string suitable for DOT label, truncating if necessary."""
    # Use str() for a more direct representation in the label, not repr()
    s = str(value)
    if len(s) > MAX_VALUE_LENGTH:
        # Truncate the string representation
        return s[:MAX_VALUE_LENGTH] + TRUNCATION_SUFFIX
    # Return the original string representation if within limit
    return s


def _sanitize_for_id(text: str) -> str:
    """Replaces non-alphanumeric characters (excluding _) with underscores."""
    sanitized = re.sub(r"[^a-zA-Z0-9_]+", "_", text)
    sanitized = sanitized.strip("_")
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    if not sanitized:
        # Use hash for more deterministic fallback for empty/weird keys
        return f"empty_{hash(text) & 0xFFFFF}"
    return sanitized


def build_dot_graph(data: ParsedConfig, graph_name: str = "Config") -> str:
    """
    Builds a Graphviz DOT language string from a parsed config dictionary.

    Args:
        data: The dictionary representing the parsed configuration.
        graph_name: The name for the graph (defaults to "Config").

    Returns:
        A string containing the DOT language representation of the graph.
    """
    dot_lines: List[str] = []
    nodes: Set[str] = set()  # Keep track of defined nodes {node_id}
    edges: Set[Tuple[str, str]] = (
        set()
    )  # Keep track of defined edges {(from_id, to_id)}

    # Start DOT definition
    dot_lines.append(f'digraph "{escape_dot_label(graph_name)}" {{')
    dot_lines.append("  rankdir=LR; // Rank direction Left to Right")
    dot_lines.append(
        '  graph [fontsize=12, fontname="Arial", labeljust=l, ranksep=0.5, nodesep=0.4];'
    )
    dot_lines.append('  node [fontsize=10, fontname="Arial"];')  # Default node style
    dot_lines.append(
        '  edge [fontsize=9, fontname="Arial", arrowsize=0.6];'
    )  # Default edge style

    # Define base styles for different node types (applied later)
    # dot_lines.append(f'  node [shape={SHAPE_SECTION}, style=filled, fillcolor=lightblue]; // Section style')
    # dot_lines.append(f'  node [shape={SHAPE_LIST}, style=filled, fillcolor=lightgrey]; // List style')
    # dot_lines.append(f'  node [shape={SHAPE_SIMPLE_VALUE}, style="", fillcolor=""]; // Reset for value nodes')

    # Start the recursive process from the root dictionary, using a base "root" ID
    _add_node_recursive(data, "root", dot_lines, nodes, edges, 0)

    dot_lines.append("}")
    return "\n".join(dot_lines)


def _add_node_recursive(
    data: Any,
    node_id_prefix: str,  # Represents the path/context leading to this node
    dot_lines: List[str],
    nodes: Set[str],
    edges: Set[Tuple[str, str]],
    depth: int,
) -> str:
    """
    Recursively adds nodes and edges to the DOT representation.

    Returns the unique node ID created for the current data item.
    """
    current_node_id = node_id_prefix  # Base ID for this data item

    # --- Handle Dictionaries (Sections) ---
    if isinstance(data, dict):
        dict_node_id = current_node_id
        # Always define the node even if visited via another path (though less likely)
        if dict_node_id not in nodes:
            label = node_id_prefix.split("__")[-1]
            if node_id_prefix == "root":
                label = "(root)"
            dot_lines.append(
                f'  "{dict_node_id}" [label="{escape_dot_label(label)}", shape={SHAPE_SECTION}, style=filled, fillcolor=lightblue];'
            )
            nodes.add(dict_node_id)

        for key, value in data.items():
            sanitized_key = _sanitize_for_id(str(key))
            child_node_id_prefix = f"{dict_node_id}__{sanitized_key}"

            child_node_id = _add_node_recursive(
                value, child_node_id_prefix, dot_lines, nodes, edges, depth + 1
            )

            edge = (dict_node_id, child_node_id)
            if edge not in edges:
                dot_lines.append(
                    f'  "{dict_node_id}" -> "{child_node_id}" [label="{escape_dot_label(str(key))}"];'
                )
                edges.add(edge)
        return dict_node_id

    # --- Handle Lists ---
    elif isinstance(data, list):
        # Create a node for the list itself
        list_node_id = f"{current_node_id}_list"  # Append _list to distinguish from a dict with same key
        count = 0
        base_id = list_node_id
        while list_node_id in nodes:
            count += 1
            list_node_id = f"{base_id}_{count}"

        if list_node_id not in nodes:
            label_part = node_id_prefix.split("__")[-1]
            # Handle case where list might be root (wrapped in dict by parser)
            if label_part == "root":
                label = "(root list)"
            elif label_part.endswith("_list"):
                label_part = label_part[: -len("_list")]  # clean up if nested list
            label = f"{label_part} (list)"

            dot_lines.append(
                f'  "{list_node_id}" [label="{escape_dot_label(label)}", shape={SHAPE_LIST}, style=filled, fillcolor=lightgrey];'
            )
            nodes.add(list_node_id)

        for index, item in enumerate(data):
            # Generate item prefix based on list ID and index
            item_node_id_prefix = (
                f"{list_node_id}__item_{index}"  # Use __ like dict keys
            )

            item_node_id = _add_node_recursive(
                item, item_node_id_prefix, dot_lines, nodes, edges, depth + 1
            )

            edge = (list_node_id, item_node_id)
            if edge not in edges:
                dot_lines.append(
                    f'  "{list_node_id}" -> "{item_node_id}" [label="{index}"];'
                )
                edges.add(edge)
        return list_node_id

    # --- Handle Simple Values ---
    else:
        # Node ID needs to be unique for this specific value instance
        value_node_id = f"{current_node_id}_value"
        count = 0
        base_id = value_node_id
        while value_node_id in nodes:
            count += 1
            value_node_id = f"{base_id}_{count}"

        # Format value using str() and truncate for the label
        value_str_for_label = format_value_for_label(data)

        if value_node_id not in nodes:
            # Define the node with the formatted value as the label
            dot_lines.append(
                f'  "{value_node_id}" [label="{escape_dot_label(value_str_for_label)}", shape={SHAPE_SIMPLE_VALUE}];'
            )
            nodes.add(value_node_id)
        return value_node_id
