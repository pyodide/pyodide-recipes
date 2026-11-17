"""Generate a Markdown summary of failing tests from pytest JUnit XML files.

Usage: python tools/parse_test_results.py <artifact-dir>

<artifact-dir> is expected to contain `test-results-<runtime>/*.xml` files, as
uploaded by the `test` job in .github/workflows/build.yml. Prints nothing if
there are no failing tests.
"""

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

MAX_FAILURES = 50
MAX_MESSAGE_LENGTH = 200


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


def parse_junit_xml(path: Path, runtime: str) -> RuntimeResult:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))

    result = RuntimeResult(runtime)
    for suite in suites:
        result.tests += int(suite.get("tests", 0))
        result.failures += int(suite.get("failures", 0))
        result.errors += int(suite.get("errors", 0))
        result.skipped += int(suite.get("skipped", 0))

    for testcase in root.iter("testcase"):
        for child in testcase:
            if child.tag in ("failure", "error"):
                test_id = f"{testcase.get('classname', '')}::{testcase.get('name', '')}"
                lines = (child.get("message") or "").splitlines()
                message = lines[0][:MAX_MESSAGE_LENGTH] if lines else ""
                result.failed.append((child.tag, test_id.strip(":"), message))
                break

    return result


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
            message = message.replace("|", "\\|").replace("`", "'")
            lines.append(f"| {kind} | `{test_id}` | {message} |")
        if len(result.failed) > MAX_FAILURES:
            lines.append(f"\n... and {len(result.failed) - MAX_FAILURES} more")
    return "\n".join(lines)


def generate_summary(artifact_dir: Path) -> str:
    results = [
        parse_junit_xml(xml_file, xml_file.stem.removeprefix("test-results-"))
        for xml_file in sorted(artifact_dir.glob("test-results-*/*.xml"))
    ]
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
