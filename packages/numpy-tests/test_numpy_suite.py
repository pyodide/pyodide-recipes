import pytest
from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["numpy", "numpy-tests", "pytest", "micropip"])
async def test_numpy_test_suite(selenium):
    import micropip
    await micropip.install("hypothesis")

    import pytest

    pytest.main(["--pyargs", "numpy"])
