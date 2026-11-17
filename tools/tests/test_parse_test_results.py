import sys
import zipfile
from pathlib import Path

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

import parse_test_results
from parse_test_results import code_span, generate_summary, parse_junit_xml

FAILING_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" errors="1" failures="1" skipped="1" tests="4">
    <testcase classname="packages.foo.test_foo" name="test_a[chrome]">
      <failure message="AssertionError: x | y&#10;second line">traceback</failure>
    </testcase>
    <testcase classname="packages.foo.test_foo" name="test_b">
      <error message="boom">traceback</error>
    </testcase>
    <testcase classname="packages.foo.test_foo" name="test_c">
      <skipped message="skip" />
    </testcase>
    <testcase classname="packages.foo.test_foo" name="test_d" />
  </testsuite>
</testsuites>
"""

PASSING_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" errors="0" failures="0" skipped="1" tests="2">
    <testcase classname="packages.bar.test_bar" name="test_ok" />
    <testcase classname="packages.bar.test_bar" name="test_skip">
      <skipped message="skip" />
    </testcase>
  </testsuite>
</testsuites>
"""

MALICIOUS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" errors="0" failures="1" skipped="0" tests="1">
    <testcase classname="x" name="t` @pyodide/maintainers [link](https://evil)">
      <failure message="` &lt;img src=x&gt; @someone">traceback</failure>
    </testcase>
  </testsuite>
</testsuites>
"""


def write_artifact(artifact_dir: Path, name: str, content: str) -> Path:
    path = artifact_dir / f"{name}.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(f"{name}.xml", content)
    return path


def test_parse_junit_xml():
    result = parse_junit_xml(FAILING_XML.encode(), "chrome")

    assert (result.tests, result.failures, result.errors, result.skipped) == (
        4,
        1,
        1,
        1,
    )
    assert result.passed == 1
    assert result.failed == [
        ("failure", "packages.foo.test_foo::test_a[chrome]", "AssertionError: x | y"),
        ("error", "packages.foo.test_foo::test_b", "boom"),
    ]


def test_generate_summary_with_failures(tmp_path):
    write_artifact(tmp_path, "test-results-chrome", FAILING_XML)
    write_artifact(tmp_path, "test-results-node", PASSING_XML)

    summary = generate_summary(tmp_path)

    assert "## ❌ chrome" in summary
    assert "4 tests: 1 passed, 1 failed, 1 errors, 1 skipped" in summary
    assert (
        "| failure | `packages.foo.test_foo::test_a[chrome]` | `AssertionError: x \\| y` |"
        in summary
    )
    assert "| error | `packages.foo.test_foo::test_b` | `boom` |" in summary
    assert "## ✅ node" in summary
    assert "2 tests: 1 passed, 0 failed, 0 errors, 1 skipped" in summary


def test_generate_summary_all_passing(tmp_path):
    write_artifact(tmp_path, "test-results-node", PASSING_XML)
    assert generate_summary(tmp_path) == ""


def test_generate_summary_no_artifacts(tmp_path):
    assert generate_summary(tmp_path) == ""


def test_code_span_cannot_be_escaped():
    assert code_span("a`b\nc|d") == "`a'b c\\|d`"
    assert code_span("") == ""
    assert len(code_span("x" * 1000)) == parse_test_results.MAX_TEXT_LENGTH + 2


def test_untrusted_text_is_kept_inside_code_spans(tmp_path):
    write_artifact(tmp_path, "test-results-chrome", MALICIOUS_XML)

    summary = generate_summary(tmp_path)
    row = next(line for line in summary.splitlines() if line.startswith("| failure"))

    # Every untrusted value is a single code span with no backticks inside
    assert row == (
        "| failure | `x::t' @pyodide/maintainers [link](https://evil)` "
        "| `' <img src=x> @someone` |"
    )


def test_invalid_artifact_names_are_ignored(tmp_path):
    write_artifact(tmp_path, "test-results-bad name", FAILING_XML)
    write_artifact(tmp_path, "test-results-" + "x" * 51, FAILING_XML)
    assert generate_summary(tmp_path) == ""


def test_invalid_zip_or_xml_is_skipped(tmp_path):
    (tmp_path / "test-results-broken.zip").write_bytes(b"not a zip")
    write_artifact(tmp_path, "test-results-badxml", "<testsuites>")
    write_artifact(tmp_path, "test-results-chrome", FAILING_XML)

    summary = generate_summary(tmp_path)
    assert "## ❌ chrome" in summary
    assert "broken" not in summary
    assert "badxml" not in summary


def test_oversized_xml_is_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(parse_test_results, "MAX_XML_SIZE", 100)
    write_artifact(tmp_path, "test-results-chrome", FAILING_XML)
    assert generate_summary(tmp_path) == ""


def test_zip_is_not_extracted(tmp_path):
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    with zipfile.ZipFile(artifact_dir / "test-results-chrome.zip", "w") as zf:
        zf.writestr("../escaped.txt", "pwned")
        zf.writestr("test-results-chrome.xml", FAILING_XML)

    generate_summary(artifact_dir)

    assert sorted(p.name for p in tmp_path.rglob("*")) == [
        "artifacts",
        "test-results-chrome.zip",
    ]
