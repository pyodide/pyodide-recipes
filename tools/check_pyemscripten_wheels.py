#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ruamel.yaml",
# ]
# ///
"""Check which source-built recipes already ship a PEP 783 ``pyemscripten`` wheel on PyPI.

This script does three things:

1. Scans every package recipe in the ``packages/`` directory and selects the ones
   that are *built from source* (i.e. ``source/url`` is an sdist/tarball, not a
   pre-built ``.whl``, and the recipe is a real Python ``package`` rather than a
   C ``static_library`` / ``shared_library`` / ``cpython_module``).

2. For each of those recipes it queries the PyPI Simple JSON API and checks
   whether the project publishes at least one wheel whose platform tag matches
   the PEP 783 ``pyemscripten`` series, i.e. the regular expression
   ``pyemscripten_[0-9]+_[0-9]+_wasm32`` (see https://peps.python.org/pep-0783/).

3. Optionally (``--update-issue``) it creates or updates a GitHub issue that
   tracks which packages now have an upstream ``pyemscripten`` wheel on PyPI, so
   that those recipes can eventually be removed from this repository.

Run it directly with ``uv`` (no manual dependency installation needed)::

    uv run tools/check_pyemscripten_wheels.py

Dependencies are declared in the PEP 723 inline-script metadata block above.
"""
import argparse
import concurrent.futures
import dataclasses
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

BASE_DIR = Path(__file__).resolve().parent.parent
RECIPE_DIR = BASE_DIR / "packages"

# PEP 783 platform tag series. Package indexes "SHOULD accept any wheel whose
# platform tag matches the regular expression pyemscripten_[0-9]+_[0-9]+_wasm32".
PEP783_PLATFORM_RE = re.compile(r"pyemscripten_[0-9]+_[0-9]+_wasm32")
# A wheel filename embeds platform tags in its last "-" separated component(s),
# e.g. ``numpy-2.4.3-cp314-cp314-pyemscripten_2026_0_wasm32.whl``.
PEP783_WHEEL_RE = re.compile(r"pyemscripten_[0-9]+_[0-9]+_wasm32(?=[.\-])")

PYPI_SIMPLE_URL = "https://pypi.org/simple/{name}/"
PYPI_SIMPLE_ACCEPT = "application/vnd.pypi.simple.v1+json"

GITHUB_API = "https://api.github.com"

DEFAULT_ISSUE_TITLE = "Tracking: packages with upstream pyemscripten wheels on PyPI"
DEFAULT_ISSUE_LABEL = "pyemscripten-wheel-tracker"
# Hidden marker so we can reliably find the issue we previously created.
ISSUE_MARKER = "<!-- pyemscripten-wheel-tracker:do-not-remove -->"

USER_AGENT = "pyodide-recipes-pyemscripten-checker/1.0"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = YAML(typ="safe").load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: meta.yaml did not parse to a mapping")
    return data


@dataclasses.dataclass
class Recipe:
    recipe_name: str
    package_name: str
    version: str
    source_url: str | None
    build_type: str

    @property
    def is_source_built(self) -> bool:
        """True if this recipe is built from source (not a pre-built wheel)."""
        if self.source_url is None:
            # No URL means an in-tree (source/path) recipe such as numpy-tests;
            # not something published on PyPI.
            return False
        if self.source_url.endswith(".whl"):
            return False
        # Only real Python packages live on PyPI as pyemscripten wheels.
        return self.build_type == "package"


def load_recipe(meta_path: Path) -> Recipe | None:
    """Load a single recipe; returns ``None`` if it cannot be parsed."""
    try:
        meta = _load_yaml(meta_path)
    except Exception as exc:  # noqa: BLE001 - we want to skip broken recipes
        print(f"WARNING: failed to parse {meta_path}: {exc}", file=sys.stderr)
        return None

    package = meta.get("package") or {}
    source = meta.get("source") or {}
    build = meta.get("build") or {}

    return Recipe(
        recipe_name=meta_path.parent.name,
        package_name=package.get("name") or meta_path.parent.name,
        version=str(package.get("version", "")),
        source_url=source.get("url"),
        build_type=str(build.get("type", "package")),
    )


def iter_recipes(packages_dir: Path) -> list[Recipe]:
    recipes: list[Recipe] = []
    for meta_path in sorted(packages_dir.glob("*/meta.yaml")):
        recipe = load_recipe(meta_path)
        if recipe is not None:
            recipes.append(recipe)
    return recipes


@dataclasses.dataclass
class PyPIResult:
    found: bool
    matching_wheels: list[str]
    platform_tags: list[str]
    wheel_versions: list[str]
    error: str | None = None


def _http_get_json(
    url: str, accept: str, timeout: float, retries: int = 3
) -> tuple[int, Any]:
    last_exc: Exception | None = None
    for _attempt in range(retries):
        request = urllib.request.Request(  # noqa: S310 - https URL, fixed scheme
            url, headers={"Accept": accept, "User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                payload = response.read().decode("utf-8")
            return response.status, json.loads(payload)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return 404, None
            last_exc = exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_exc = exc
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last_exc}")


def _version_from_wheel(filename: str) -> str:
    """Extract the version component from a wheel filename.

    Wheel filename: ``{name}-{version}(-{build})?-{python}-{abi}-{platform}.whl``.
    """
    parts = filename[: -len(".whl")].split("-")
    if len(parts) >= 2:
        return parts[1]
    return ""


def check_pypi_for_pyemscripten(name: str, timeout: float) -> PyPIResult:
    """Query the PyPI Simple JSON API for ``name`` and look for pyemscripten wheels."""
    url = PYPI_SIMPLE_URL.format(name=name)
    try:
        status, data = _http_get_json(url, PYPI_SIMPLE_ACCEPT, timeout)
    except RuntimeError as exc:
        return PyPIResult(False, [], [], [], error=str(exc))

    if status == 404 or data is None:
        return PyPIResult(False, [], [], [], error="not found on PyPI")

    matching_wheels: list[str] = []
    platform_tags: set[str] = set()
    wheel_versions: set[str] = set()

    for file_entry in data.get("files", []):
        filename = file_entry.get("filename", "")
        if not filename.endswith(".whl"):
            continue
        tag_match = PEP783_WHEEL_RE.search(filename)
        if tag_match:
            matching_wheels.append(filename)
            platform_tags.add(tag_match.group(0))
            wheel_versions.add(_version_from_wheel(filename))

    return PyPIResult(
        found=bool(matching_wheels),
        matching_wheels=sorted(matching_wheels),
        platform_tags=sorted(platform_tags),
        wheel_versions=sorted(wheel_versions),
    )


@dataclasses.dataclass
class PackageStatus:
    recipe: str
    pypi_name: str
    recipe_version: str
    has_pyemscripten_wheel: bool
    matching_wheels: list[str]
    platform_tags: list[str]
    wheel_versions: list[str]
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_report(
    recipes: list[Recipe], max_workers: int, timeout: float
) -> dict[str, Any]:
    source_recipes = [r for r in recipes if r.is_source_built]

    statuses: list[PackageStatus] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_recipe = {
            executor.submit(check_pypi_for_pyemscripten, r.package_name, timeout): r
            for r in source_recipes
        }
        for future in concurrent.futures.as_completed(future_to_recipe):
            recipe = future_to_recipe[future]
            result = future.result()
            statuses.append(
                PackageStatus(
                    recipe=recipe.recipe_name,
                    pypi_name=recipe.package_name,
                    recipe_version=recipe.version,
                    has_pyemscripten_wheel=result.found,
                    matching_wheels=result.matching_wheels,
                    platform_tags=result.platform_tags,
                    wheel_versions=result.wheel_versions,
                    error=result.error,
                )
            )

    statuses.sort(key=lambda s: s.recipe.lower())
    available = [s for s in statuses if s.has_pyemscripten_wheel]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "pep783_platform_regex": PEP783_PLATFORM_RE.pattern,
        "total_recipes": len(recipes),
        "total_source_recipes": len(source_recipes),
        "available_count": len(available),
        "packages": [s.to_dict() for s in statuses],
    }


def render_markdown(report: dict[str, Any]) -> str:
    generated = report["generated_at"]
    total_source = report["total_source_recipes"]
    available = report["available_count"]
    packages: list[dict[str, Any]] = report["packages"]

    available_pkgs = [p for p in packages if p["has_pyemscripten_wheel"]]
    errored_pkgs = [
        p for p in packages if not p["has_pyemscripten_wheel"] and p["error"] and p["error"] != "not found on PyPI"
    ]

    lines: list[str] = []
    lines.append(ISSUE_MARKER)
    lines.append("")
    lines.append(
        "This issue is automatically maintained by "
        "[`tools/check_pyemscripten_wheels.py`](../blob/main/tools/check_pyemscripten_wheels.py)."
    )
    lines.append("")
    lines.append(
        "It tracks **source-built** recipes in this repository whose upstream "
        "project now publishes a [PEP 783](https://peps.python.org/pep-0783/) "
        "`pyemscripten` wheel on PyPI. Once a package ships such a wheel upstream, "
        "the recipe here can usually be removed."
    )
    lines.append("")
    lines.append(f"- **Last updated:** {generated}")
    lines.append(f"- **Source-built recipes scanned:** {total_source}")
    lines.append(f"- **Recipes with an upstream `pyemscripten` wheel:** {available}")
    lines.append(f"- **Platform tag pattern:** `{report['pep783_platform_regex']}`")
    lines.append("")

    lines.append("## Candidates for removal (pyemscripten wheel available on PyPI)")
    lines.append("")
    if available_pkgs:
        lines.append(
            "| Recipe | PyPI | Recipe version | Wheel version(s) | Platform tag(s) |"
        )
        lines.append("| --- | --- | --- | --- | --- |")
        for pkg in available_pkgs:
            pypi_link = f"[{pkg['pypi_name']}](https://pypi.org/project/{pkg['pypi_name']}/)"
            wheel_versions = ", ".join(pkg["wheel_versions"]) or "—"
            platform_tags = "<br>".join(f"`{t}`" for t in pkg["platform_tags"]) or "—"
            lines.append(
                f"| `{pkg['recipe']}` | {pypi_link} | {pkg['recipe_version']} "
                f"| {wheel_versions} | {platform_tags} |"
            )
    else:
        lines.append("_None yet._")
    lines.append("")

    lines.append(
        f"<details><summary>Recipes still without an upstream pyemscripten wheel "
        f"({total_source - available})</summary>"
    )
    lines.append("")
    not_available = [p for p in packages if not p["has_pyemscripten_wheel"]]
    if not_available:
        lines.append("| Recipe | PyPI | Recipe version | Note |")
        lines.append("| --- | --- | --- | --- |")
        for pkg in not_available:
            note = pkg["error"] or ""
            lines.append(
                f"| `{pkg['recipe']}` | `{pkg['pypi_name']}` "
                f"| {pkg['recipe_version']} | {note} |"
            )
    else:
        lines.append("_All scanned recipes have an upstream wheel._")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    if errored_pkgs:
        lines.append(
            f"> [!WARNING]\n> {len(errored_pkgs)} package(s) could not be checked due "
            "to PyPI errors; their status may be inaccurate this run."
        )
        lines.append("")

    return "\n".join(lines)


def _github_request(
    method: str,
    path: str,
    token: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> tuple[int, Any]:
    url = path if path.startswith("http") else f"{GITHUB_API}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)  # noqa: S310
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", USER_AGENT)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            body = response.read().decode("utf-8")
        return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed


def _ensure_label(repo: str, token: str, label: str) -> None:
    status, _ = _github_request(
        "POST",
        f"/repos/{repo}/labels",
        token,
        {
            "name": label,
            "color": "0e8a16",
            "description": "Recipes whose upstream now ships a PEP 783 pyemscripten wheel",
        },
    )
    # 201 = created, 422 = already exists. Anything else is surprising but non-fatal.
    if status not in (201, 422):
        print(f"WARNING: could not ensure label {label!r} (HTTP {status})", file=sys.stderr)


def _find_tracker_issue(repo: str, token: str, label: str) -> int | None:
    # Listing by our own label is immediate and reliable (no search index delay).
    status, issues = _github_request(
        "GET", f"/repos/{repo}/issues?state=all&labels={label}&per_page=100", token
    )
    if status != 200 or not isinstance(issues, list):
        return None
    for issue in issues:
        # Skip pull requests, which the issues endpoint also returns.
        if "pull_request" in issue:
            continue
        if ISSUE_MARKER in (issue.get("body") or ""):
            return int(issue["number"])
    # Fall back to the first non-PR issue carrying the label.
    for issue in issues:
        if "pull_request" not in issue:
            return int(issue["number"])
    return None


def update_github_issue(
    repo: str, token: str, title: str, label: str, body: str
) -> None:
    _ensure_label(repo, token, label)
    issue_number = _find_tracker_issue(repo, token, label)

    if issue_number is None:
        status, data = _github_request(
            "POST",
            f"/repos/{repo}/issues",
            token,
            {"title": title, "body": body, "labels": [label]},
        )
        if status == 201:
            print(f"Created tracker issue #{data['number']}: {data['html_url']}")
        else:
            raise RuntimeError(f"Failed to create issue (HTTP {status}): {data}")
    else:
        status, data = _github_request(
            "PATCH",
            f"/repos/{repo}/issues/{issue_number}",
            token,
            {"title": title, "body": body},
        )
        if status == 200:
            print(f"Updated tracker issue #{issue_number}: {data['html_url']}")
        else:
            raise RuntimeError(
                f"Failed to update issue #{issue_number} (HTTP {status}): {data}"
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-d",
        "--packages-dir",
        type=Path,
        default=RECIPE_DIR,
        help="Directory containing the package recipes (default: ./packages).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Write the full machine-readable status report to this JSON file.",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=None,
        help="Write the rendered Markdown report to this file.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=16,
        help="Number of concurrent PyPI requests (default: 16).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--update-issue",
        action="store_true",
        help="Create or update the GitHub tracker issue (needs GITHUB_TOKEN).",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="GitHub repository in 'owner/name' form (default: $GITHUB_REPOSITORY).",
    )
    parser.add_argument(
        "--issue-title",
        default=DEFAULT_ISSUE_TITLE,
        help="Title for the tracker issue.",
    )
    parser.add_argument(
        "--issue-label",
        default=DEFAULT_ISSUE_LABEL,
        help="Label used to find/create the tracker issue.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    packages_dir = args.packages_dir.resolve()
    if not packages_dir.is_dir():
        print(f"ERROR: packages directory not found: {packages_dir}", file=sys.stderr)
        return 1

    recipes = iter_recipes(packages_dir)
    source_count = sum(1 for r in recipes if r.is_source_built)
    print(
        f"Scanned {len(recipes)} recipes; {source_count} are built from source.",
        file=sys.stderr,
    )

    report = build_report(recipes, max_workers=args.max_workers, timeout=args.timeout)
    markdown = render_markdown(report)

    if args.output_json:
        args.output_json.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Wrote JSON report to {args.output_json}", file=sys.stderr)
    if args.output_markdown:
        args.output_markdown.write_text(markdown + "\n")
        print(f"Wrote Markdown report to {args.output_markdown}", file=sys.stderr)

    print(
        f"{report['available_count']} / {report['total_source_recipes']} "
        "source-built recipes now have an upstream pyemscripten wheel on PyPI.",
        file=sys.stderr,
    )

    if args.update_issue:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("ERROR: --update-issue requires GITHUB_TOKEN", file=sys.stderr)
            return 1
        if not args.repo:
            print(
                "ERROR: --update-issue requires --repo or $GITHUB_REPOSITORY",
                file=sys.stderr,
            )
            return 1
        update_github_issue(
            args.repo, token, args.issue_title, args.issue_label, markdown
        )
    else:
        # When not updating the issue, emit the Markdown to stdout so it can be
        # inspected or piped elsewhere.
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
