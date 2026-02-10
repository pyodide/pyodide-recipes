from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["ml-dtypes"])
def test_ml_dtypes(selenium):
    from ml_dtypes import bfloat16
    import numpy as np

    np.testing.assert_equal(np.zeros(4, dtype=bfloat16), np.array([0, 0, 0, 0], dtype=bfloat16))

    a = np.array([1.0, 2.0, 3.0], dtype=bfloat16)
    np.testing.assert_equal(a + 1, np.array([2.0, 3.0, 4.0], dtype=bfloat16))
