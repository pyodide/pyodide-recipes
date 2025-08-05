from pytest_pyodide import run_in_pyodide
from pathlib import Path



def test_jsonpatch(selenium):

    @run_in_pyodide(packages=["jsonpatch"])
    def inner(selenium, test_module, test_json):
        from pathlib import Path
        Path("test_jsonpatch.py").write_text(test_module)
        Path("tests.json").write_text(test_json)
        import unittest
        try:
            unittest.main(module="test_jsonpatch", verbosity=3)
        except SystemExit as e:
            assert e.code == 0
        else:
            assert False

    dir = Path(__file__).parent 
    test_path = dir / "jsonpatch_tests.py"
    test_module = test_path.read_text()
    test_json = (dir / "tests.json").read_text()
    inner(selenium, test_module, test_json)
