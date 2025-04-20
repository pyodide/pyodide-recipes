import sys
from pathlib import Path

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from parse_build_result import (
    format_time,
    generate_markdown_table,
    parse_build_results,
    parse_time,
    process_build_results,
)


def test_parse_time():
    """Test converting time strings to seconds."""
    assert parse_time("5s") == 5
    assert parse_time("1m 30s") == 90
    assert parse_time("2m") == 120
    assert parse_time("10m 0s") == 600


def test_format_time():
    """Test formatting seconds to human-readable time strings."""
    assert format_time(5) == "5s"
    assert format_time(90) == "1m 30s"
    assert format_time(120) == "2m"
    assert format_time(60) == "1m"
    assert format_time(600) == "10m"


def test_parse_build_results():
    """Test parsing build results from log content."""
    content = """
    [1/3] (thread 1) built numpy in 3m 45s
    [2/3] (thread 2) built pandas in 10m 10s
    [3/3] (thread 3) built matplotlib in 2m 20s
    Some other log line that should be ignored
    """

    results = parse_build_results(content)

    # Check if we have the right number of packages
    assert len(results) == 3

    # Check if the packages are parsed correctly
    package_names = [r[0] for r in results]
    assert "numpy" in package_names
    assert "pandas" in package_names
    assert "matplotlib" in package_names

    # Check if times are parsed correctly
    for package, seconds, time_str in results:
        if package == "numpy":
            assert seconds == 225  # 3m 45s = 225s
            assert time_str == "3m 45s"
        elif package == "pandas":
            assert seconds == 610  # 5m 10s = 310s
            assert time_str == "10m 10s"
        elif package == "matplotlib":
            assert seconds == 140  # 2m 20s = 140s
            assert time_str == "2m 20s"


def test_generate_markdown_table():
    """Test generating markdown table from build results."""
    results = [
        ("numpy", 225, "3m 45s"),
        ("pandas", 610, "10m 10s"),
        ("matplotlib", 140, "2m 20s"),
    ]

    # Test with default sorting (by time, descending)
    table = generate_markdown_table(results)
    table_lines = table.strip().split("\n")

    assert len(table_lines) == 5  # Header, separator, and 3 packages
    assert "| pandas | 10m 10s |" in table_lines  # Should be first by time
    assert "| numpy | 3m 45s |" in table_lines
    assert "| matplotlib | 2m 20s |" in table_lines  # Should be last by time

    # Test without sorting
    table_unsorted = generate_markdown_table(results, sort_by_time=False)
    table_unsorted_lines = table_unsorted.strip().split("\n")

    assert len(table_unsorted_lines) == 5
    assert table_unsorted_lines[2] == "| numpy | 3m 45s |"  # Original order
    assert table_unsorted_lines[3] == "| pandas | 10m 10s |"
    assert table_unsorted_lines[4] == "| matplotlib | 2m 20s |"


def test_process_build_results():
    """Test the entire processing pipeline."""
    content = """
    [1/3] (thread 1) built numpy in 3m 45s
    [2/3] (thread 2) built pandas in 10m 10s
    [3/3] (thread 3) built matplotlib in 2m 20s
    Building packages... ━━━━━━━━━━━━━━━━━━━━━━━━ 260/260 100% Time elapsed: 1:46:58
    """

    output = process_build_results(content)

    # Check if output contains expected elements
    assert "# Package Build Results" in output
    assert "Total packages built: 3" in output
    assert "Total build time: 1:46:58" in output  # 225 + 310 + 140 = 675s = 11m 15s
    assert "| Package | Build Time |" in output
    assert "| pandas | 10m 10s |" in output
    assert "Longest build: **pandas** (10m 10s)" in output
    assert "Packages built in more than 10 minutes: 1" in output  # Only pandas


def test_process_build_results_empty():
    """Test processing with empty content."""
    output = process_build_results("")

    assert "Total packages built: 0" in output
    assert "Total build time: Failed to parse total build time" in output
    assert "Longest build" not in output  # No statistics for empty results
