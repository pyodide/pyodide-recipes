from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["narwhals"])
def test_narwhals_from_native(selenium):
    import narwhals as nw
    from narwhals.utils import Version

    class MyDictDataFrame:
        def __init__(self, data, version):
            self._data = data
            self._version = Version.MAIN

        def __narwhals_dataframe__(self):
            return self

        def _with_version(self, version):
            return self.__class__(self._data, version)

        @property
        def columns(self):
            return list(self._data)

    assert nw.from_native(
        MyDictDataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}, Version.MAIN)
    ).columns == ["a", "b"]
