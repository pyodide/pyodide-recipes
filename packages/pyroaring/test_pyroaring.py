from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["pyroaring"])
def test_pyroaring(selenium):
    from pyroaring import BitMap

    bm1 = BitMap()
    bm1.add(3)
    bm1.add(18)
    assert 3 in bm1
    assert 4 not in bm1

    bm2 = BitMap([3, 27, 42])
    assert bm1 == BitMap([3, 18])
    assert bm2 == BitMap([3, 27, 42])
    assert bm1 & bm2 == BitMap([3])
    assert bm1 | bm2 == BitMap([3, 18, 27, 42])

