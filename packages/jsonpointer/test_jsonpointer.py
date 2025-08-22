from pytest_pyodide import run_in_pyodide
from pathlib import Path



def test_jsonpointer(selenium):

    @run_in_pyodide(packages=["jsonpointer"])
    def inner(selenium, test_module):
        from pathlib import Path
        Path("test_jsonpointer.py").write_text(test_module)
        import unittest
        try:
            unittest.main(module="test_jsonpointer", verbosity=3)
        except SystemExit as e:
            assert e.code == 0
        else:
            assert False

    test_path = Path(__file__).parent / "jsonpointer_tests.py"
    test_module = test_path.read_text()
    inner(selenium, test_module)
