"""Generate a Markdown summary of failing tests from pytest JUnit XML artifacts.

Usage: python tools/parse_test_results.py <artifact-dir>

<artifact-dir> is expected to contain `test-results-<runtime>.zip` files, as
downloaded from the artifacts uploaded by the `test` job in
.github/workflows/build.yml. Prints nothing if there are no failing tests.

The artifacts come from pull request builds, so their contents are untrusted:
the zip files are read in memory and never extracted to disk, their size is
capped, and every value taken from them is rendered inside a code span so it
cannot inject Markdown, HTML, or @-mentions into the PR comment.
"""

import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

MAX_FAILURES = 50
MAX_TEXT_LENGTH = 200
MAX_XML_SIZE = 50 * 1024 * 1024
RUNTIME_PATTERN = re.compile(r"^test-results-([A-Za-z0-9._-]{1,50})$")


@dataclass
class RuntimeResult:
    runtime: str
    tests: int = 0
    failures: int = 0
    errors: int = 0
    skipped: int = 0
    failed: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return self.tests - self.failures - self.errors - self.skipped


def code_span(text: str) -> str:
    """Render untrusted text as a single-line inline code span."""
    text = " ".join(text.split())[:MAX_TEXT_LENGTH]
    text = text.replace("`", "'").replace("|", "\\|")
    return f"`{text}`" if text else ""


def _int_attr(element: ET.Element, name: str) -> int:
    try:
        return max(int(element.get(name, 0)), 0)
    except ValueError:
        return 0


def parse_junit_xml(content: bytes, runtime: str) -> RuntimeResult:
    root = ET.fromstring(content)
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))

    result = RuntimeResult(runtime)
    for suite in suites:
        result.tests += _int_attr(suite, "tests")
        result.failures += _int_attr(suite, "failures")
        result.errors += _int_attr(suite, "errors")
        result.skipped += _int_attr(suite, "skipped")

    for testcase in root.iter("testcase"):
        for child in testcase:
            if child.tag in ("failure", "error"):
                test_id = f"{testcase.get('classname', '')}::{testcase.get('name', '')}"
                lines = (child.get("message") or "").splitlines()
                message = lines[0] if lines else ""
                result.failed.append((child.tag, test_id.strip(":"), message))
                break

    return result


def read_artifact(zip_path: Path) -> RuntimeResult | None:
    """Parse the JUnit XML inside an artifact zip without extracting it."""
    match = RUNTIME_PATTERN.match(zip_path.stem)
    if not match:
        return None

    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.endswith(".xml"):
                continue
            if info.file_size > MAX_XML_SIZE:
                print(f"Skipping oversized {info.filename}", file=sys.stderr)
                continue
            # Read at most MAX_XML_SIZE bytes in case the header lies about the size
            with zf.open(info) as f:
                content = f.read(MAX_XML_SIZE + 1)
            if len(content) > MAX_XML_SIZE:
                print(f"Skipping oversized {info.filename}", file=sys.stderr)
                continue
            return parse_junit_xml(content, match.group(1))

    return None


def format_result(result: RuntimeResult) -> str:
    icon = "❌" if result.failed else "✅"
    lines = [
        f"## {icon} {result.runtime}",
        "",
        f"{result.tests} tests: {result.passed} passed, {result.failures} failed, "
        f"{result.errors} errors, {result.skipped} skipped",
    ]
    if result.failed:
        lines += ["", "| Result | Test | Message |", "| --- | --- | --- |"]
        for kind, test_id, message in result.failed[:MAX_FAILURES]:
            lines.append(f"| {kind} | {code_span(test_id)} | {code_span(message)} |")
        if len(result.failed) > MAX_FAILURES:
            lines.append(f"\n... and {len(result.failed) - MAX_FAILURES} more")
    return "\n".join(lines)


def generate_summary(artifact_dir: Path) -> str:
    results = []
    for zip_path in sorted(artifact_dir.glob("test-results-*.zip")):
        try:
            result = read_artifact(zip_path)
        except (zipfile.BadZipFile, ET.ParseError) as e:
            print(f"Skipping {zip_path.name}: {e}", file=sys.stderr)
            continue
        if result is not None:
            results.append(result)

    if not any(result.failed for result in results):
        return ""
    return "\n\n---\n\n".join(format_result(result) for result in results)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <artifact-dir>", file=sys.stderr)
        sys.exit(1)

    summary = generate_summary(Path(sys.argv[1]))
    if summary:
        print(summary)


if __name__ == "__main__":
    main()
