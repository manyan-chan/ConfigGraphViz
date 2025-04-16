# configgraphviz/parsers.py
import configparser
import json  # For handling simple value types consistently
from pathlib import Path
from typing import IO, Any, Dict, Union

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Use third-party tomli
    except ImportError:
        tomllib = None  # type: ignore # Mark as potentially unavailable

try:
    import yaml  # Use third-party PyYAML
except ImportError:
    yaml = None  # type: ignore # Mark as potentially unavailable


# Type alias for parsed config data
ParsedConfig = Dict[str, Any]


def _configparser_to_dict(cp: configparser.ConfigParser) -> ParsedConfig:
    """Converts a ConfigParser object to a nested dictionary."""
    data: ParsedConfig = {}
    # Add sections
    for section in cp.sections():
        data[section] = {}
        for key, value in cp.items(section):
            # Try to interpret simple types, otherwise keep as string
            try:
                # Use json.loads for basic type parsing (int, float, bool, null)
                data[section][key] = json.loads(value)
            except json.JSONDecodeError:
                # Keep as string if it's not simple JSON parseable
                data[section][key] = value
    # Handle DEFAULT section if it has unique keys
    if configparser.DEFAULTSECT in cp and cp.items(configparser.DEFAULTSECT):
        # Check if DEFAULT has items not present in other sections (less common use)
        # For simplicity, we can represent it as a top-level section.
        # Or decide to ignore it for graph clarity. Let's add it.
        if (
            configparser.DEFAULTSECT not in data
        ):  # Avoid overwriting if explicitly defined
            data[configparser.DEFAULTSECT] = {}
            for key, value in cp.items(configparser.DEFAULTSECT):
                try:
                    data[configparser.DEFAULTSECT][key] = json.loads(value)
                except json.JSONDecodeError:
                    data[configparser.DEFAULTSECT][key] = value

    return data


def parse_ini(stream: IO[str]) -> ParsedConfig:
    """Parses an INI file stream into a dictionary."""
    parser = configparser.ConfigParser(interpolation=None)  # Disable interpolation
    try:
        parser.read_file(stream)
        return _configparser_to_dict(parser)
    except configparser.Error as e:
        raise ValueError(f"Failed to parse INI file: {e}") from e


def parse_toml(stream: IO[bytes]) -> ParsedConfig:
    """Parses a TOML file stream (bytes) into a dictionary."""
    if tomllib is None:
        raise ImportError("TOML parsing requires Python 3.11+ or the 'tomli' package.")
    try:
        return tomllib.load(stream)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Failed to parse TOML file: {e}") from e


def parse_yaml(stream: IO[str]) -> ParsedConfig:
    """Parses a YAML file stream into a dictionary or list."""
    if yaml is None:
        raise ImportError("YAML parsing requires the 'PyYAML' package.")
    try:
        # safe_load typically returns dict or list
        data = yaml.safe_load(stream)
        if not isinstance(data, dict):
            # Wrap non-dict structures (like a list at the root) in a root dict
            # for consistent graph representation
            return {"root": data}
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML file: {e}") from e


def parse_config(file_path: Union[str, Path]) -> ParsedConfig:
    """
    Parses a configuration file based on its extension.

    Supports .ini, .toml, .yaml, .yml

    Args:
        file_path: Path to the configuration file.

    Returns:
        A dictionary representing the parsed configuration.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or parsing fails.
        ImportError: If required parsing libraries are not installed.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    suffix = path.suffix.lower()

    try:
        if suffix == ".ini":
            with path.open("r", encoding="utf-8") as f:
                return parse_ini(f)
        elif suffix == ".toml":
            if tomllib is None:
                raise ImportError("TOML support requires Python 3.11+ or 'tomli'.")
            with path.open("rb") as f:  # TOML parser expects bytes
                return parse_toml(f)
        elif suffix in (".yaml", ".yml"):
            if yaml is None:
                raise ImportError("YAML support requires 'PyYAML'.")
            with path.open("r", encoding="utf-8") as f:
                return parse_yaml(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {suffix}")
    except Exception as e:
        # Catch potential errors during file open or parsing
        raise ValueError(f"Error processing file {path}: {e}") from e
