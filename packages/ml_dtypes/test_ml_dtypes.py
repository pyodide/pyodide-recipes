from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["ml_dtypes"])
def test_ml_dtypes(selenium):
    from ml_dtypes import bfloat16
    import numpy as np

    np.testing.assert_equal(np.zeros(4, dtype=bfloat16), np.array([0, 0, 0, 0], dtype=bfloat16))
