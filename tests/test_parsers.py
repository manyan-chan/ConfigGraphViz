# tests/test_parsers.py
from pathlib import Path

import pytest

from configgraphviz import parse_config, parse_toml, parse_yaml

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# --- Test parse_config (main entry point) ---


def test_parse_config_ini():
    data = parse_config(FIXTURES_DIR / "example.ini")
    assert isinstance(data, dict)
    assert "bitbucket.org" in data
    assert "user" in data["bitbucket.org"]
    assert data["bitbucket.org"]["user"] == "hg"
    # Check type conversion
    assert data["database"]["port"] == 5432
    assert data["database"]["active"] is True
    assert data["database"]["threshold"] == 1.23
    # Check list parsing via json.loads
    assert isinstance(data["database"]["tables"], list)  # It *is* a list now
    assert data["database"]["tables"] == ["users", "products"]  # Expect a list


def test_parse_config_toml():
    if parse_toml is None:
        pytest.skip("TOML support not available.")
    data = parse_config(FIXTURES_DIR / "example.toml")
    assert isinstance(data, dict)
    assert "owner" in data
    assert data["owner"]["name"] == "Tom Preston-Werner"
    assert data["database"]["enabled"] is True
    assert data["servers"]["alpha"]["ip"] == "10.0.0.1"
    assert isinstance(data["database"]["ports"], list)
    assert data["database"]["ports"] == [8000, 8001, 8002]


def test_parse_config_yaml():
    if parse_yaml is None:
        pytest.skip("YAML support not available (PyYAML missing).")
    data = parse_config(FIXTURES_DIR / "example.yaml")
    assert isinstance(data, dict)
    assert "server" in data
    assert data["server"]["host"] == "192.168.1.100"
    assert data["server"]["enabled"] is True
    assert data["server"]["description"] is None
    assert isinstance(data["users"], list)
    assert len(data["users"]) == 2
    assert data["users"][0]["name"] == "alice"
    assert isinstance(data["users"][0]["tags"], list)


def test_parse_config_complex_yaml():
    if parse_yaml is None:
        pytest.skip("YAML support not available (PyYAML missing).")
    data = parse_config(FIXTURES_DIR / "complex.yaml")
    assert (
        data["application"]["settings"]["backend"]["endpoints"][0]["path"]
        == "/api/v1/users"
    )
    assert data["application"]["plugins"][1]["config"]["provider"] == "ldap"


def test_parse_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_config("non_existent_file.ini")


def test_parse_config_unsupported_format():
    # Create a dummy file
    dummy_file = Path("dummy.txt")
    dummy_file.touch()
    with pytest.raises(ValueError, match="Unsupported configuration file format: .txt"):
        parse_config(dummy_file)
    dummy_file.unlink()  # Clean up


def test_parse_config_invalid_content_ini():
    invalid_ini = "[section\nkey=value\nno_equals"
    with open("invalid.ini", "w") as f:
        f.write(invalid_ini)
    with pytest.raises(ValueError, match="Error processing file invalid.ini"):
        parse_config("invalid.ini")
    Path("invalid.ini").unlink()


# --- Add tests for individual parsers if needed, e.g. ---
# test_parse_ini_with_stream()
# test_parse_yaml_with_stream()
# test_parse_toml_with_stream()

if __name__ == "__main__":
    pytest.main()
