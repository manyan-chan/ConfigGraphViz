# example.py
"""
Example usage script for the configgraphviz library.

This script demonstrates how to:
1. Find existing sample configuration files (INI, YAML, TOML).
2. Include the project's pyproject.toml file as a TOML example.
3. Parse these files using configgraphviz.
4. Generate Graphviz DOT output.
5. Save the DOT output to files (e.g., example.yaml.dot).
6. Attempt to render the DOT files to PNG images (e.g., example.yaml.png).

Requires:
- configgraphviz installed (`pip install .`)
- PyYAML installed (`pip install pyyaml`)
- tomli installed if using Python < 3.11 (`pip install tomli`)
- Graphviz installed and the 'dot' command available in the system PATH
  (See: https://graphviz.org/download/)
"""

import shutil
import subprocess
import sys
from pathlib import Path

try:
    from configgraphviz import build_dot_graph, parse_config
except ImportError:
    print("Error: Cannot import configgraphviz.")
    print("Please install the package first, e.g., using 'pip install -e .'")
    sys.exit(1)

# --- Define Paths ---
# Assume this script is in the project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"  # Path to pyproject.toml
OUTPUT_DIR = PROJECT_ROOT / "output_examples"

# --- List of Configuration Files to Process ---
# Using actual files from the project structure
config_files_to_process = [
    FIXTURES_DIR / "example.ini",
    FIXTURES_DIR / "example.yaml",
    FIXTURES_DIR / "example.toml",
    FIXTURES_DIR / "complex.yaml",
    PYPROJECT_FILE,  # Add the pyproject.toml file to the list
]


# --- Main Script Logic ---
def main():
    """Parses specified config files, generates DOT, saves, and tries to render."""
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        print(f"Ensured output directory exists: {OUTPUT_DIR}")
    except OSError as e:
        print(f"Error creating output directory '{OUTPUT_DIR}': {e}")
        sys.exit(1)

    print("\n--- Processing Configuration Files ---")

    graphviz_found = shutil.which("dot") is not None
    if not graphviz_found:
        print("WARNING: Graphviz 'dot' command not found in PATH.")
        print(
            "         DOT files will be generated, but images cannot be rendered automatically."
        )
        print(
            "         Install Graphviz from https://graphviz.org/download/ to render images."
        )

    for config_file in config_files_to_process:
        # Check if the source file exists before processing
        if not config_file.is_file():
            print(f"\nSkipping: Source file not found - {config_file}")
            continue

        print(
            f"\nProcessing: {config_file.relative_to(PROJECT_ROOT)}"
        )  # Show relative path

        # --- Generate unique output filenames ---
        output_base_name = config_file.name  # e.g., "example.yaml", "pyproject.toml"
        dot_file = OUTPUT_DIR / f"{output_base_name}.dot"  # e.g., example.yaml.dot
        img_file = OUTPUT_DIR / f"{output_base_name}.png"  # e.g., example.yaml.png
        # Use the original filename as the graph title for clarity
        graph_name = output_base_name

        # 1. Parse
        try:
            parsed_data = parse_config(config_file)
            print("  Parsing: OK")
        except ImportError as e:
            print(f"  Parsing: FAILED - Missing dependency: {e}")
            print("         (Have you installed PyYAML and tomli?)")
            continue  # Skip to next file
        except (FileNotFoundError, ValueError) as e:
            print(f"  Parsing: FAILED - {e}")
            continue  # Skip to next file
        except Exception as e:  # Catch other potential errors
            print(f"  Parsing: FAILED - Unexpected error: {e}")
            continue

        # 2. Build DOT
        try:
            dot_string = build_dot_graph(parsed_data, graph_name=graph_name)
            print("  DOT Generation: OK")
        except Exception as e:  # Catch unexpected errors during graph build
            print(f"  DOT Generation: FAILED - Unexpected error: {e}")
            continue

        # 3. Save DOT file
        try:
            with dot_file.open("w", encoding="utf-8") as f:
                f.write(dot_string)
            print(f"  DOT Saved: {dot_file.relative_to(PROJECT_ROOT)}")
        except IOError as e:
            print(f"  DOT Save: FAILED - {e}")
            continue  # Cannot render if save failed

        # 4. Render PNG (if Graphviz 'dot' is available)
        if graphviz_found:
            try:
                cmd = ["dot", "-Tpng", str(dot_file), "-o", str(img_file)]
                print(f"  Rendering command: {' '.join(cmd)}")
                # Use timeout and capture output for better error reporting
                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=30,
                )
                if result.returncode == 0:
                    print(f"  Image Rendered: {img_file.relative_to(PROJECT_ROOT)}")
                else:
                    print(
                        f"  Rendering: FAILED - 'dot' command exited with code {result.returncode}"
                    )
                    if result.stderr:
                        print(f"  stderr:\n{result.stderr.strip()}")

            except FileNotFoundError:
                print("  Rendering: FAILED - 'dot' command not found during execution.")
            except subprocess.TimeoutExpired:
                print("  Rendering: FAILED - 'dot' command timed out.")
            except Exception as e:
                print(f"  Rendering: FAILED - Unexpected error during rendering: {e}")
        else:
            print("  Rendering: SKIPPED (Graphviz 'dot' not found)")

    print("\n--- Finished ---")
    print(f"Generated files are in the '{OUTPUT_DIR.name}/' directory.")
    if not graphviz_found:
        print(
            "Install Graphviz and run 'dot -Tpng <filename>.dot -o <filename>.png' to render images."
        )


if __name__ == "__main__":
    main()
