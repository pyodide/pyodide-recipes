import pytest
from pytest_pyodide import run_in_pyodide


@pytest.mark.driver_timeout(60)
@run_in_pyodide(packages=["fastcan"])
def test_fastcan(selenium):
    from fastcan import FastCan
    X = [[1, 0], [0, 1]]
    y = [1, 0]
    s = FastCan(verbose=0).fit(X, y).get_support()
    assert (s == [True, False]).all()
