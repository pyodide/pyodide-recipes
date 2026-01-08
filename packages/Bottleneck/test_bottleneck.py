import pytest
from pytest_pyodide import run_in_pyodide

# adopted from https://github.com/pydata/bottleneck/tree/4dab1d5753168e9ff9c8104603aca6e66cdb88c9/bottleneck/tests

@run_in_pyodide(packages=["Bottleneck"])
def test_move_median_without_nans():
    import bottleneck as bn
    fmt = "\nfunc %s | window %d | min_count %s\n\nInput array:\n%s\n"
    aaae = assert_array_almost_equal
    min_count = 1
    size = 10
    func = bn.move_median
    func0 = bn.slow.move_median
    rs = np.random.RandomState([1, 2, 3])
    for i in range(100):
        a = np.arange(size, dtype=np.int64)
        rs.shuffle(a)
        for window in range(2, size + 1):
            actual = func(a, window=window, min_count=min_count)
            desired = func0(a, window=window, min_count=min_count)
            err_msg = fmt % (func.__name__, window, min_count, a)
            aaae(actual, desired, decimal=5, err_msg=err_msg)

@run_in_pyodide(packages=["Bottleneck"])
def test_move_std_sqrt():
    import bottleneck as bn
    a = [
        0.0011448196318903589,
        0.00028718669878572767,
        0.00028718669878572767,
        0.00028718669878572767,
        0.00028718669878572767,
    ]
    err_msg = "Square root of negative number. ndim = %d"
    b = bn.move_std(a, window=3)
    assert np.isfinite(b[2:]).all(), err_msg % 1

    a2 = np.array([a, a])
    b = bn.move_std(a2, window=3, axis=1)
    assert np.isfinite(b[:, 2:]).all(), err_msg % 2

    a3 = np.array([[a, a], [a, a]])
    b = bn.move_std(a3, window=3, axis=2)
    assert np.isfinite(b[:, :, 2:]).all(), err_msg % 3

@run_in_pyodide(packages=["Bottleneck"])
def test_transpose():
    import bottleneck as bn
    a = np.arange(12).reshape(4, 3)
    actual = bn.partition(a.T, 2, -1).T
    desired = bn.slow.partition(a.T, 2, -1).T
    assert_equal(actual, desired, "partition transpose test")

@run_in_pyodide(packages=["Bottleneck"])
def test_push():
    import bottleneck as bn
    ns = (0, 1, 2, 3, 4, 5, None)
    a = np.array([np.nan, 1, 2, np.nan, np.nan, np.nan, np.nan, 3, np.nan])
    for n in ns:
        actual = bn.push(a.copy(), n=n)
        desired = bn.slow.push(a.copy(), n=n)
        assert_array_equal(actual, desired, "failed on n=%s" % str(n))
