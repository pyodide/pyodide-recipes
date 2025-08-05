from pytest_pyodide import run_in_pyodide
from pathlib import Path

def test_fastapi(selenium):

    @run_in_pyodide(packages=["fastapi", "pytest_asyncio"])
    def inner(selenium, file_contents):
        from pathlib import Path

        for key, value in file_contents:
            Path(key).write_text(value)
        import pytest
        assert pytest.main(["fastapi_test.py"]) == 0

    dir = Path(__file__).parent 
    file_contents = []
    for name in ["asgi", "fastapi_test", "fastapi_test_app"]:
        file = name + ".py"
        path = dir/file
        file_contents.append([file, path.read_text()])
    inner(selenium, file_contents)
