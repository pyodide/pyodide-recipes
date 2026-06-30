"""
Functional tests for libblis.

We exercise one routine from each BLAS level, and plus the complex Givens
rotation wrappers added in patch 0002.

The expected values were computed with a native version of SciPy. In order
to reproduce the reference numbers, run the snippet below

```
import numpy as np
from scipy.linalg import blas

x = np.array([1., 2., 3., 4.])
y = np.array([5., 6., 7., 8.])
assert blas.ddot(x, y) == 70.0
assert blas.dnrm2(np.array([3., 4.])) == 5.0
assert blas.dasum(np.array([-1., 2., -3.])) == 6.0
assert list(
    blas.daxpy(np.array([1., 2., 3.]),
    np.array([4., 5., 6.]), a=2.0),
) == [6., 9., 12.]

A = np.arange(1, 10, dtype=float).reshape(3, 3)
assert list(A @ np.ones(3)) == [6., 15., 24.]

Am = np.array([[1., 2.], [3., 4.]])
Bm = np.array([[5., 6.], [7., 8.]])
assert list((Am @ Bm).ravel()) == [19., 22., 43., 50.]

c, s = blas.zrotg(complex(1, 1), complex(0, 0))
assert abs(c - 1) < 1e-12 and s == 0
xr, yr = blas.csrot(
    np.array([1 + 2j], np.complex64),
    np.array([3 + 4j], np.complex64),
    0.0,
    1.0,
)
assert xr[0] == 3 + 4j and yr[0] == -1 - 2j
```
"""

from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["libblis"])
def test_blis_blas_levels(selenium):
    import ctypes
    from ctypes import POINTER, c_double, c_float, c_int
    from ctypes.util import find_library

    lib = ctypes.CDLL(find_library("blis") or "libblis.so")
    dp = POINTER(c_double)
    fp = POINTER(c_float)

    def darr(values):
        return (c_double * len(values))(*values)

    def farr(values):
        return (c_float * len(values))(*values)

    def close(got, want, tol=1e-9):
        assert abs(got - want) <= tol, f"got {got!r} want {want!r}"

    # CBLAS enum values
    # For reference https://www.cs.ubc.ca/~mpf/bcls/cblas_8h.html
    ROW_MAJOR = 101
    NO_TRANS = 111

    # level 1
    lib.cblas_ddot.restype = c_double
    lib.cblas_ddot.argtypes = [c_int, dp, c_int, dp, c_int]
    close(lib.cblas_ddot(4, darr([1, 2, 3, 4]), 1, darr([5, 6, 7, 8]), 1), 70.0)

    lib.cblas_dnrm2.restype = c_double
    lib.cblas_dnrm2.argtypes = [c_int, dp, c_int]
    close(lib.cblas_dnrm2(2, darr([3, 4]), 1), 5.0)

    lib.cblas_dasum.restype = c_double
    lib.cblas_dasum.argtypes = [c_int, dp, c_int]
    close(lib.cblas_dasum(3, darr([-1, 2, -3]), 1), 6.0)

    lib.cblas_daxpy.argtypes = [c_int, c_double, dp, c_int, dp, c_int]
    ay = darr([4, 5, 6])
    lib.cblas_daxpy(3, 2.0, darr([1, 2, 3]), 1, ay, 1)
    assert [ay[i] for i in range(3)] == [6.0, 9.0, 12.0]

    # level 2: y = A x with A a row major 3 by 3 of 1..9 and x all ones
    lib.cblas_dgemv.argtypes = [
        c_int, c_int, c_int, c_int, c_double, dp, c_int, dp, c_int, c_double, dp, c_int
    ]
    yv = darr([0, 0, 0])
    lib.cblas_dgemv(
        ROW_MAJOR, NO_TRANS, 3, 3, 1.0, darr([1, 2, 3, 4, 5, 6, 7, 8, 9]), 3,
        darr([1, 1, 1]), 1, 0.0, yv, 1,
    )
    assert [yv[i] for i in range(3)] == [6.0, 15.0, 24.0]

    # level 3: C = A B with row major 2 by 2 inputs
    lib.cblas_dgemm.argtypes = [
        c_int, c_int, c_int, c_int, c_int, c_int, c_double, dp, c_int, dp, c_int, c_double, dp, c_int
    ]
    cm = darr([0, 0, 0, 0])
    lib.cblas_dgemm(
        ROW_MAJOR, NO_TRANS, NO_TRANS, 2, 2, 2, 1.0,
        darr([1, 2, 3, 4]), 2, darr([5, 6, 7, 8]), 2, 0.0, cm, 2,
    )
    assert [cm[i] for i in range(4)] == [19.0, 22.0, 43.0, 50.0]

    # zrotg with a = 1 + 1i and b = 0 should leave
    # r = a, cosine = 1, sine = 0
    lib.cblas_zrotg.argtypes = [dp, dp, dp, dp]
    za = darr([1, 1])
    cc = c_double(0)
    ss = darr([0, 0])
    lib.cblas_zrotg(za, darr([0, 0]), ctypes.byref(cc), ss)
    close(cc.value, 1.0)
    close(ss[0], 0.0)
    close(ss[1], 0.0)
    close(za[0], 1.0)
    close(za[1], 1.0)

    # csrot
    lib.cblas_csrot.argtypes = [c_int, fp, c_int, fp, c_int, c_float, c_float]
    cx = farr([1, 2])
    cy = farr([3, 4])
    lib.cblas_csrot(1, cx, 1, cy, 1, 0.0, 1.0)
    assert [cx[i] for i in range(2)] == [3.0, 4.0]
    assert [cy[i] for i in range(2)] == [-1.0, -2.0]
