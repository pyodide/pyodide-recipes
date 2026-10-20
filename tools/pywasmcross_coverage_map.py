#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "coverage",
# ]
# ///
"""Map lines of pyodide-build's ``pywasmcross.py`` to the package builds that exercise them.

``pywasmcross.py`` is the compiler wrapper that pyodide-build symlinks as
``cc``/``c++``/``ar``/``cmake``/... during a package build. When the
``PYWASMCROSS_COVERAGE_DIR`` environment variable is set, every invocation of
the wrapper measures its own line coverage and appends one JSON record to
``$PYWASMCROSS_COVERAGE_DIR/<package>.jsonl``::

    {"cmd": "cc", "src": "<sha256 prefix>", "lines": [[start, end], ...]}

This script aggregates those files into a map ``line -> set of packages``.

Typical use::

    export PYWASMCROSS_COVERAGE_DIR=$PWD/pywasmcross-coverage
    pyodide build-recipes "*" --install
    python tools/pywasmcross_coverage_map.py pywasmcross-coverage \\
        --json pywasmcross-coverage.json \\
        --annotate pywasmcross-coverage.txt \\
        --coverage-data .coverage.pywasmcross

Outputs:

* ``--json``: machine-readable map (``lines`` -> packages, ``packages`` ->
  lines, unexercised lines, ...).
* ``--annotate``: the source of ``pywasmcross.py`` with the number of packages
  (and optionally their names) that exercised each line.
* ``--coverage-data``: a regular coverage data file with one *context* per
  package, so ``coverage html --show-contexts`` can be used for browsing.
* The summary (and the JSON) also includes a greedy approximation of the
  smallest set of packages that together exercise every line any package
  exercised. Useful for picking integration tests when changing
  ``pywasmcross.py``.

A caveat on what can be measured: coverage does not trace the frame in which
it was started, so module-level statements of ``pywasmcross.py`` (imports,
``def``/``class`` lines, decorators, the ``if IS_COMPILER_INVOCATION:``
preamble) are never recorded. They are reported separately as "module-level"
rather than as "never exercised".
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

try:
    from coverage import CoverageData
    from coverage.parser import PythonParser
except ImportError:
    raise SystemExit(
        "The 'coverage' package is required: pip install coverage"
    ) from None

# coverage's default `exclude_lines` pattern.
# Lines hit by this few packages or fewer are called out in the summary.
RARE_THRESHOLD = 3
NO_COVER_REGEX = r"#\s*(pragma|PRAGMA)[:\s]?\s*(no|NO)\s*(cover|COVER)"


@dataclass
class PackageRecords:
    """All wrapper invocations recorded for one package."""

    name: str
    invocations: int = 0
    commands: Counter[str] = field(default_factory=Counter)
    src_hashes: Counter[str] = field(default_factory=Counter)
    lines: set[int] = field(default_factory=set)


@dataclass
class SourceInfo:
    """Which lines of the source are statements, and which of those are module-level."""

    path: Path
    sha256_prefix: str
    text: str
    statements: set[int]
    module_level: set[int]

    @property
    def measurable(self) -> set[int]:
        return self.statements - self.module_level


def expand_ranges(ranges: list[list[int]]) -> set[int]:
    """Expand ``[[start, end], ...]`` (inclusive) into a set of line numbers."""
    return {n for start, end in ranges for n in range(start, end + 1)}


def load_records(coverage_dir: Path) -> dict[str, PackageRecords]:
    """Load every ``<package>.jsonl`` file under ``coverage_dir``."""
    packages: dict[str, PackageRecords] = {}
    for path in sorted(coverage_dir.glob("*.jsonl")):
        pkg = PackageRecords(name=path.stem)
        with path.open() as f:
            for lineno, raw in enumerate(f, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError:
                    print(
                        f"warning: skipping malformed record {path}:{lineno}",
                        file=sys.stderr,
                    )
                    continue
                pkg.invocations += 1
                pkg.commands[record.get("cmd", "?")] += 1
                pkg.src_hashes[record.get("src", "?")] += 1
                pkg.lines |= expand_ranges(record["lines"])
        packages[pkg.name] = pkg
    return packages


def default_source_path() -> Path:
    spec = importlib.util.find_spec("pyodide_build.pywasmcross")
    if spec is None or spec.origin is None:
        raise SystemExit(
            "Could not locate pyodide_build.pywasmcross; pass --source explicitly."
        )
    return Path(spec.origin)


def analyze_source(path: Path) -> SourceInfo:
    """
    Determine the statement lines of the source file (the lines coverage can
    report as executed) and which of those are module-level.

    Module-level means "executed when the file is imported/run, outside of any
    function body": the ``def`` line itself, decorators, class bodies, imports
    and the top-level ``if`` blocks. Lines inside a function body (including
    nested functions and classes defined inside functions) are measurable.
    """
    text = path.read_text()
    # Honor `# pragma: no cover` like coverage does. pywasmcross.py uses it
    # on its own instrumentation helpers, which necessarily run outside the
    # measured window.
    parser = PythonParser(text=text, filename=str(path), exclude=NO_COVER_REGEX)
    parser.parse_source()
    statements = set(parser.statements)

    tree = ast.parse(text, filename=str(path))
    function_body_lines: set[int] = set()

    def visit(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                for stmt in child.body:
                    assert stmt.end_lineno is not None
                    function_body_lines.update(range(stmt.lineno, stmt.end_lineno + 1))
                # Defaults/decorators of nested defs are evaluated in the
                # enclosing scope, which is already handled by the enclosing
                # function's body range. No need to recurse further: the whole
                # body is measurable.
            else:
                visit(child)

    visit(tree)
    module_level = statements - function_body_lines
    return SourceInfo(
        path=path,
        sha256_prefix=hashlib.sha256(text.encode()).hexdigest()[:16],
        text=text,
        statements=statements,
        module_level=module_level,
    )


def check_source_hashes(
    packages: dict[str, PackageRecords], source: SourceInfo
) -> None:
    """Warn if records were produced by a different version of the source file."""
    mismatched = sorted(
        pkg.name
        for pkg in packages.values()
        if set(pkg.src_hashes) - {source.sha256_prefix}
    )
    if mismatched:
        print(
            f"warning: {len(mismatched)} package(s) were built with a different "
            f"version of {source.path.name} than the one being annotated "
            f"(expected sha256 prefix {source.sha256_prefix}). Line numbers may "
            f"be off for: {', '.join(mismatched)}",
            file=sys.stderr,
        )


def build_line_map(packages: dict[str, PackageRecords]) -> dict[int, set[str]]:
    line_map: dict[int, set[str]] = defaultdict(set)
    for pkg in packages.values():
        for line in pkg.lines:
            line_map[line].add(pkg.name)
    return dict(line_map)


def greedy_cover(packages: dict[str, PackageRecords]) -> list[tuple[str, int]]:
    """
    Greedy set cover: repeatedly pick the package that adds the most not yet
    covered lines (ties: fewer wrapper invocations, then name). Returns
    ``[(package, newly_covered_lines), ...]``.
    """
    remaining = set().union(*(pkg.lines for pkg in packages.values()))
    chosen: list[tuple[str, int]] = []
    while remaining:
        best = min(
            packages.values(),
            key=lambda pkg: (-len(pkg.lines & remaining), pkg.invocations, pkg.name),
        )
        gained = len(best.lines & remaining)
        if gained == 0:
            break
        chosen.append((best.name, gained))
        remaining -= best.lines
    return chosen


def to_json(
    packages: dict[str, PackageRecords],
    source: SourceInfo,
    line_map: dict[int, set[str]],
) -> dict:
    measurable = source.measurable
    exercised = set(line_map)
    return {
        "source": str(source.path),
        "source_sha256_prefix": source.sha256_prefix,
        "n_packages": len(packages),
        "n_measurable_lines": len(measurable),
        "n_exercised_lines": len(exercised & measurable),
        "lines": {
            str(line): sorted(line_map.get(line, ())) for line in sorted(measurable)
        },
        "unexercised_lines": sorted(measurable - exercised),
        "module_level_lines": sorted(source.module_level),
        "packages": {
            name: {
                "invocations": pkg.invocations,
                "commands": dict(sorted(pkg.commands.items())),
                "lines": sorted(pkg.lines),
            }
            for name, pkg in sorted(packages.items())
        },
        "greedy_cover": [
            {"package": name, "new_lines": gained}
            for name, gained in greedy_cover(packages)
        ],
    }


def write_annotated(
    out: TextIO,
    source: SourceInfo,
    line_map: dict[int, set[str]],
    n_packages: int,
    show_packages: bool,
    max_names: int,
) -> None:
    """
    Write the source with a per-line prefix::

        <lineno> <n_packages> <marker> <source line>

    Markers: ``|`` measurable statement, ``!`` measurable but exercised by no
    package, ``-`` module-level statement (not measurable), `` `` not a statement.
    """
    out.write(
        f"# {source.path}\n"
        f"# {n_packages} package(s); column 2 is the number of packages that "
        "exercised the line.\n"
        "# markers: '|' measured, '!' never exercised, '-' module-level (not "
        "measurable), ' ' not a statement\n\n"
    )
    for lineno, text in enumerate(source.text.splitlines(), 1):
        pkgs = line_map.get(lineno, set())
        if lineno in source.module_level:
            count, marker = "-", "-"
        elif lineno in source.statements:
            count = str(len(pkgs))
            marker = "!" if not pkgs else "|"
        else:
            count, marker = "", " "
        suffix = ""
        if show_packages and pkgs and lineno in source.measurable:
            names = sorted(pkgs)
            shown = names[:max_names]
            if len(names) > max_names:
                shown.append(f"+{len(names) - max_names} more")
            suffix = f"  # {', '.join(shown)}"
        out.write(f"{lineno:5d} {count:>5} {marker} {text}{suffix}\n")


def write_coverage_data(
    out_path: Path, source: SourceInfo, packages: dict[str, PackageRecords]
) -> None:
    """
    Write a coverage data file with one measurement context per package, so
    the usual coverage tooling can be used, e.g.::

        coverage html --data-file=.coverage.pywasmcross --show-contexts
    """
    out_path.unlink(missing_ok=True)
    data = CoverageData(basename=str(out_path))
    for name, pkg in sorted(packages.items()):
        data.set_context(name)
        data.add_lines({str(source.path): sorted(pkg.lines)})
    data.write()


def print_summary(
    out: TextIO,
    packages: dict[str, PackageRecords],
    source: SourceInfo,
    line_map: dict[int, set[str]],
) -> None:
    measurable = source.measurable
    exercised = set(line_map) & measurable
    unexercised = sorted(measurable - exercised)
    source_lines = source.text.splitlines()
    out.write(
        f"{len(packages)} package(s), "
        f"{sum(p.invocations for p in packages.values())} wrapper invocation(s)\n"
        f"{len(exercised)}/{len(measurable)} measurable lines exercised "
        f"({len(source.module_level)} module-level lines not measurable)\n"
    )
    if unexercised:
        out.write("\nLines never exercised by any package:\n")
        for line in unexercised:
            out.write(f"  {line:5d}  {source_lines[line - 1].strip()}\n")

    rare = sorted(
        (line for line in exercised if len(line_map[line]) <= RARE_THRESHOLD),
        key=lambda line: (len(line_map[line]), line),
    )
    if rare and len(packages) > RARE_THRESHOLD:
        out.write(f"\nLines exercised by at most {RARE_THRESHOLD} packages:\n")
        for line in rare:
            names = ", ".join(sorted(line_map[line]))
            out.write(f"  {line:5d}  [{names}]  {source_lines[line - 1].strip()}\n")

    out.write("\nGreedy package set exercising every exercised line:\n")
    for name, gained in greedy_cover(packages):
        out.write(f"  {name} (+{gained})\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "coverage_dir",
        type=Path,
        help="Directory that PYWASMCROSS_COVERAGE_DIR pointed at during the builds",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Path to pywasmcross.py (default: the installed pyodide_build's copy)",
    )
    parser.add_argument("--json", type=Path, help="Write the JSON map here")
    parser.add_argument(
        "--annotate",
        type=Path,
        help="Write the annotated source here ('-' for stdout)",
    )
    parser.add_argument(
        "--show-packages",
        action="store_true",
        help="In the annotated source, list package names next to each line",
    )
    parser.add_argument(
        "--max-names",
        type=int,
        default=8,
        help="Maximum package names per line with --show-packages (default: 8)",
    )
    parser.add_argument(
        "--coverage-data",
        type=Path,
        help="Write a coverage data file with one context per package here",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Don't print the summary"
    )
    args = parser.parse_args(argv)

    if not args.coverage_dir.is_dir():
        parser.error(f"{args.coverage_dir} is not a directory")
    packages = load_records(args.coverage_dir)
    if not packages:
        parser.error(f"No *.jsonl coverage records found in {args.coverage_dir}")

    source = analyze_source(args.source or default_source_path())
    check_source_hashes(packages, source)
    line_map = build_line_map(packages)

    if args.json:
        args.json.write_text(json.dumps(to_json(packages, source, line_map), indent=1))
    if args.annotate:
        if str(args.annotate) == "-":
            write_annotated(
                sys.stdout,
                source,
                line_map,
                len(packages),
                args.show_packages,
                args.max_names,
            )
        else:
            with args.annotate.open("w") as f:
                write_annotated(
                    f,
                    source,
                    line_map,
                    len(packages),
                    args.show_packages,
                    args.max_names,
                )
    if args.coverage_data:
        write_coverage_data(args.coverage_data, source, packages)
    if not args.quiet:
        print_summary(sys.stdout, packages, source, line_map)
    return 0


if __name__ == "__main__":
    sys.exit(main())
