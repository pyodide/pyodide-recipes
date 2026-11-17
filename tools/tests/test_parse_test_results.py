import sys
from pathlib import Path

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from parse_test_results import generate_summary, parse_junit_xml

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


def write_artifact(artifact_dir: Path, runtime: str, content: str) -> Path:
    path = artifact_dir / f"test-results-{runtime}" / f"test-results-{runtime}.xml"
    path.parent.mkdir(parents=True)
    path.write_text(content)
    return path


def test_parse_junit_xml(tmp_path):
    path = write_artifact(tmp_path, "chrome", FAILING_XML)
    result = parse_junit_xml(path, "chrome")

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
    write_artifact(tmp_path, "chrome", FAILING_XML)
    write_artifact(tmp_path, "node", PASSING_XML)

    summary = generate_summary(tmp_path)

    assert "## ❌ chrome" in summary
    assert "4 tests: 1 passed, 1 failed, 1 errors, 1 skipped" in summary
    assert (
        "| failure | `packages.foo.test_foo::test_a[chrome]` | AssertionError: x \\| y |"
        in summary
    )
    assert "| error | `packages.foo.test_foo::test_b` | boom |" in summary
    assert "## ✅ node" in summary
    assert "2 tests: 1 passed, 0 failed, 0 errors, 1 skipped" in summary


def test_generate_summary_all_passing(tmp_path):
    write_artifact(tmp_path, "node", PASSING_XML)
    assert generate_summary(tmp_path) == ""


def test_generate_summary_no_artifacts(tmp_path):
    assert generate_summary(tmp_path) == ""
