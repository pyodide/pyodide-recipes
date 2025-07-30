from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["cryptography"])
def test_cryptography(selenium):
    import certifi
    import os
    assert os.path.exists(certifi.where())
    certs = certifi.contents()
    assert certs
    assert isinstance(certs, str)
