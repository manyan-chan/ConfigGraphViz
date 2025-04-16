# configgraphviz/__init__.py
"""
ConfigGraphViz: Visualize your configuration files.

Parses common configuration formats (INI, YAML, TOML) and generates
Graphviz DOT language output to show the structure.
"""

from .graph_builder import build_dot_graph
from .parsers import ParsedConfig, parse_config, parse_ini, parse_toml, parse_yaml

__version__ = "0.1.0"

__all__ = [
    "parse_ini",
    "parse_toml",
    "parse_yaml",
    "parse_config",
    "build_dot_graph",
    "ParsedConfig",
    "__version__",
]
