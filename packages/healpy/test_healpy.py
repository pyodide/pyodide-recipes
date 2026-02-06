from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["healpy"])
def test_basic(selenium):
    import healpy
    assert healpy.nside2npix(32) == 12288
