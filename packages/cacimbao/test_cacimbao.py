from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["cacimbao"])
def test_cacimbao(selenium):
    import cacimbao

    assert cacimbao.list_datasets()
