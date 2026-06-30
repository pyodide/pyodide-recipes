"""
Functional tests for libblis.

We exercise one routine from each BLAS level, plus the complex Givens rotation
wrappers added in patch 0002.

The expected values can be computed with SciPy against a native BLAS. In order
to reproduce the reference numbers, run the snippet below:

```
import numpy as np
from scipy.linalg import blas

rng = np.random.RandomState(42)

# definitions
x = rng.uniform(-1, 1, 8)
y = rng.uniform(-1, 1, 8)
alpha = rng.uniform(-1, 1)
A = rng.uniform(-1, 1, (6, 5))
xv = rng.uniform(-1, 1, 5)
Am = rng.uniform(-1, 1, (4, 5))
Bm = rng.uniform(-1, 1, (5, 3))
za = complex(rng.uniform(-1, 1), rng.uniform(-1, 1))
zb = complex(rng.uniform(-1, 1), rng.uniform(-1, 1))
cx = (rng.uniform(-1, 1, 4) + 1j * rng.uniform(-1, 1, 4)).astype(np.complex64)
cy = (rng.uniform(-1, 1, 4) + 1j * rng.uniform(-1, 1, 4)).astype(np.complex64)
rc = rng.uniform(-1, 1)
rs = rng.uniform(-1, 1)

# tests
assert np.isclose(blas.ddot(x, y), x @ y)
assert np.isclose(blas.dnrm2(x), np.linalg.norm(x))
assert np.isclose(blas.dasum(x), np.abs(x).sum())
assert np.allclose(blas.daxpy(x, y.copy(), a=alpha), alpha * x + y)
assert np.allclose(blas.dgemv(1.0, A, xv), A @ xv)
assert np.allclose(blas.dgemm(1.0, Am, Bm), Am @ Bm)
# zrotg builds a rotation [[c, s], [-conj(s), c]] that sends [za, zb] to [r, 0].
c, s = blas.zrotg(za, zb)
c = c.real
assert np.isclose(c * c + abs(s) ** 2, 1.0)
assert np.isclose(-np.conj(s) * za + c * zb, 0.0, atol=1e-12)
# csrot applies a real rotation to a pair of complex vectors.
xr, yr = blas.csrot(cx, cy, rc, rs)
assert np.allclose(xr, rc * cx + rs * cy, atol=1e-6)
assert np.allclose(yr, rc * cy - rs * cx, atol=1e-6)
```

"""

from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["libblis", "numpy"])
def test_blis_blas_levels(selenium):
    import ctypes
    from ctypes import POINTER, c_double, c_float, c_int
    from ctypes.util import find_library

    import numpy as np

    lib = ctypes.CDLL(find_library("blis") or "libblis.so")
    dp = POINTER(c_double)
    fp = POINTER(c_float)

    def f64(a):
        return np.ascontiguousarray(a, dtype=np.float64)

    def c64(a):
        return np.ascontiguousarray(a, dtype=np.complex64)

    def dptr(a):
        return a.ctypes.data_as(dp)

    def fptr(a):
        return a.ctypes.data_as(fp)

    # CBLAS enum values
    # For reference https://www.cs.ubc.ca/~mpf/bcls/cblas_8h.html
    ROW_MAJOR = 101
    NO_TRANS = 111

    rng = np.random.RandomState(42)
    x = f64(rng.uniform(-1, 1, 8))
    y = f64(rng.uniform(-1, 1, 8))
    alpha = float(rng.uniform(-1, 1))
    A = f64(rng.uniform(-1, 1, (6, 5)))
    xv = f64(rng.uniform(-1, 1, 5))
    Am = f64(rng.uniform(-1, 1, (4, 5)))
    Bm = f64(rng.uniform(-1, 1, (5, 3)))
    za_val = complex(rng.uniform(-1, 1), rng.uniform(-1, 1))
    zb_val = complex(rng.uniform(-1, 1), rng.uniform(-1, 1))
    cx = c64(rng.uniform(-1, 1, 4) + 1j * rng.uniform(-1, 1, 4))
    cy = c64(rng.uniform(-1, 1, 4) + 1j * rng.uniform(-1, 1, 4))
    rot_c = float(rng.uniform(-1, 1))
    rot_s = float(rng.uniform(-1, 1))

    # level 1
    lib.cblas_ddot.restype = c_double
    lib.cblas_ddot.argtypes = [c_int, dp, c_int, dp, c_int]
    assert np.isclose(lib.cblas_ddot(x.size, dptr(x), 1, dptr(y), 1), x @ y)

    lib.cblas_dnrm2.restype = c_double
    lib.cblas_dnrm2.argtypes = [c_int, dp, c_int]
    assert np.isclose(lib.cblas_dnrm2(x.size, dptr(x), 1), np.linalg.norm(x))

    lib.cblas_dasum.restype = c_double
    lib.cblas_dasum.argtypes = [c_int, dp, c_int]
    assert np.isclose(lib.cblas_dasum(x.size, dptr(x), 1), np.abs(x).sum())

    lib.cblas_daxpy.argtypes = [c_int, c_double, dp, c_int, dp, c_int]
    yb = y.copy()
    lib.cblas_daxpy(x.size, alpha, dptr(x), 1, dptr(yb), 1)
    assert np.allclose(yb, alpha * x + y)

    # level 2: y = A x
    lib.cblas_dgemv.argtypes = [
        c_int, c_int, c_int, c_int, c_double, dp, c_int, dp, c_int, c_double, dp, c_int
    ]
    m, n = A.shape
    yv = np.zeros(m, dtype=np.float64)
    lib.cblas_dgemv(ROW_MAJOR, NO_TRANS, m, n, 1.0, dptr(A), n, dptr(xv), 1, 0.0, dptr(yv), 1)
    assert np.allclose(yv, A @ xv)

    # level 3: C = A B
    lib.cblas_dgemm.argtypes = [
        c_int, c_int, c_int, c_int, c_int, c_int, c_double, dp, c_int, dp, c_int, c_double, dp, c_int
    ]
    mm, kk = Am.shape
    nn = Bm.shape[1]
    cm = np.zeros((mm, nn), dtype=np.float64)
    lib.cblas_dgemm(ROW_MAJOR, NO_TRANS, NO_TRANS, mm, nn, kk, 1.0,
                    dptr(Am), kk, dptr(Bm), nn, 0.0, dptr(cm), nn)
    assert np.allclose(cm, Am @ Bm)

    # zrotg. check that the rotation [[c, s], [-conj(s), c]] sends
    # [za, zb] to [r, 0], so the test is independent of the sign
    # convention for c and s.
    lib.cblas_zrotg.argtypes = [dp, dp, dp, dp]
    za = np.array([za_val], dtype=np.complex128)
    zb = np.array([zb_val], dtype=np.complex128)
    cc = c_double(0.0)
    ss = np.zeros(1, dtype=np.complex128)
    lib.cblas_zrotg(dptr(za), dptr(zb), ctypes.byref(cc), dptr(ss))
    c = cc.value
    s = ss[0]
    assert np.isclose(c * c + abs(s) ** 2, 1.0)
    assert np.isclose(-np.conj(s) * za_val + c * zb_val, 0.0, atol=1e-12)
    assert np.isclose(za[0], c * za_val + s * zb_val)

    # csrot sends (x, y) to (cx + sy, cy - sx)
    lib.cblas_csrot.argtypes = [c_int, fp, c_int, fp, c_int, c_float, c_float]
    cxb = cx.copy()
    cyb = cy.copy()
    lib.cblas_csrot(cx.size, fptr(cxb), 1, fptr(cyb), 1, rot_c, rot_s)
    assert np.allclose(cxb, rot_c * cx + rot_s * cy, atol=1e-6)
    assert np.allclose(cyb, rot_c * cy - rot_s * cx, atol=1e-6)
