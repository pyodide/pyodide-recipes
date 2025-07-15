from pytest_pyodide import run_in_pyodide

@run_in_pyodide(packages=["audioop-lts"])
def test_read(selenium):
    import audioop

    assert audioop.add(b"1234", b"5678",2) == b"fhjl"
