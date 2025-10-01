import pytest
from pytest_pyodide import run_in_pyodide


@pytest.mark.driver_timeout(30)
@run_in_pyodide(packages=["tenacity"])
def test_tenacity_import_and_retry(selenium):
    import tenacity

    # Basic import check
    assert hasattr(tenacity, "retry"), "tenacity.retry should exist"

    # A simple function that fails the first 2 times, then succeeds
    counter = {"n": 0}

    @tenacity.retry(stop=tenacity.stop_after_attempt(3))
    def sometimes_fails():
        counter["n"] += 1
        if counter["n"] < 3:
            raise ValueError("Fail until third attempt")
        return "success"

    result = sometimes_fails()
    assert result == "success"
    assert counter["n"] == 3
