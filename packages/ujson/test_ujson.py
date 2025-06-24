from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["ujson"])
def test_ujson(selenium):
    import ujson
    data = ujson.loads('{"a": 1, "b": {"c": 3}}')
    assert data["a"] == 1
    assert data["b"]["c"] == 3

    out = ujson.dumps(data)
    assert isinstance(out, str)
    assert '"c":3' in out
