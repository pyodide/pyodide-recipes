import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("coverage")
from coverage import CoverageData

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from pywasmcross_coverage_map import (
    analyze_source,
    build_line_map,
    expand_ranges,
    greedy_cover,
    load_records,
    main,
)

FAKE_SOURCE = '''\
"""docstring"""
import os

X = 1


def helper(a):  # line 7
    if a:
        return 1
    return 2


def skipped():  # pragma: no cover
    return 3


class C:
    y = 2

    def method(self):
        return helper(self.y)


if X:
    helper(0)
'''


def write_records(cov_dir: Path, name: str, records: list[dict]) -> None:
    with (cov_dir / f"{name}.jsonl").open("a") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def test_expand_ranges():
    assert expand_ranges([]) == set()
    assert expand_ranges([[1, 3], [5, 5], [9, 10]]) == {1, 2, 3, 5, 9, 10}


def test_analyze_source(tmp_path):
    src = tmp_path / "fake.py"
    src.write_text(FAKE_SOURCE)
    info = analyze_source(src)

    # Only function bodies are measurable. `def` lines, imports, class bodies
    # and the top-level `if` block are module-level. `skipped` is excluded.
    assert info.measurable == {8, 9, 10, 21}
    assert {2, 4, 7, 17, 18, 20, 24, 25} <= info.module_level
    # `# pragma: no cover` excludes the whole function, def line included.
    assert not {13, 14} & info.statements
    assert 1 not in info.statements  # docstring


def test_load_records_and_line_map(tmp_path):
    write_records(
        tmp_path,
        "alpha",
        [
            {"cmd": "cc", "src": "abc", "lines": [[8, 9]]},
            {"cmd": "cc", "src": "abc", "lines": [[8, 8], [10, 10]]},
        ],
    )
    write_records(tmp_path, "beta", [{"cmd": "ar", "src": "abc", "lines": [[8, 8]]}])
    (tmp_path / "gamma.jsonl").write_text("not json\n")

    packages = load_records(tmp_path)
    assert set(packages) == {"alpha", "beta", "gamma"}
    assert packages["alpha"].invocations == 2
    assert packages["alpha"].commands == {"cc": 2}
    assert packages["alpha"].lines == {8, 9, 10}
    assert packages["gamma"].invocations == 0

    assert build_line_map(packages) == {
        8: {"alpha", "beta"},
        9: {"alpha"},
        10: {"alpha"},
    }
    assert greedy_cover(packages) == [("alpha", 3)]


def test_main_outputs(tmp_path, capsys):
    src = tmp_path / "fake.py"
    src.write_text(FAKE_SOURCE)
    cov_dir = tmp_path / "cov"
    cov_dir.mkdir()
    write_records(cov_dir, "alpha", [{"cmd": "cc", "src": "stale", "lines": [[8, 9]]}])
    write_records(
        cov_dir, "beta", [{"cmd": "cc", "src": "stale", "lines": [[8, 8], [10, 10]]}]
    )

    json_out = tmp_path / "map.json"
    annotate_out = tmp_path / "map.txt"
    data_out = tmp_path / ".coverage.fake"
    assert (
        main(
            [
                str(cov_dir),
                "--source",
                str(src),
                "--json",
                str(json_out),
                "--annotate",
                str(annotate_out),
                "--show-packages",
                "--coverage-data",
                str(data_out),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "built with a different version" in captured.err
    assert "3/4 measurable lines exercised" in captured.out
    assert "21  return helper(self.y)" in captured.out

    result = json.loads(json_out.read_text())
    assert result["lines"] == {
        "8": ["alpha", "beta"],
        "9": ["alpha"],
        "10": ["beta"],
        "21": [],
    }
    assert result["unexercised_lines"] == [21]
    assert result["packages"]["beta"]["lines"] == [8, 10]
    assert [c["package"] for c in result["greedy_cover"]] == ["alpha", "beta"]

    annotated = annotate_out.read_text().splitlines()
    by_lineno = {
        int(line.split()[0]): line for line in annotated if line[:5].strip().isdigit()
    }
    assert by_lineno[8].endswith("# alpha, beta")
    assert "    7     - - def helper" in by_lineno[7]
    assert "   21     0 !" in by_lineno[21]

    data = CoverageData(basename=str(data_out))
    data.read()
    assert sorted(data.measured_contexts()) == ["alpha", "beta"]
    assert sorted(data.lines(str(src))) == [8, 9, 10]
