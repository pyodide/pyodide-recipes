from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["pycdfpp", "requests"])
def test_pycdfpp(selenium):
    import pycdfpp
    import requests
    cdf = pycdfpp.load(requests.get('https://cdaweb.gsfc.nasa.gov/pub/software/cdawlib/0MASTERS/a1_k0_mpa_00000000_v01.cdf').content)
    assert 'Epoch' in cdf
    assert cdf["unit_possyn_l"].shape == (1, 3, 11)
    