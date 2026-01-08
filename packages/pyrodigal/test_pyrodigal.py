from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["pyrodigal"])
def test_pyrodigal_unittests(selenium):
    import unittest

    prog = unittest.main("pyrodigal.tests", exit=False)
    assert prog.result.wasSuccessful
