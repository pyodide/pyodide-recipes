from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["argon2-cffi"])
def test_argon2(selenium):
    import argon2
    import pytest

    ph = argon2.PasswordHasher(parallelism=1)
    hash = ph.hash("test")

    assert ph.verify(hash, "test") is True

    with pytest.raises(argon2.exceptions.UnsupportedParametersError) as exinfo:
        argon2.PasswordHasher(parallelism=2).hash("test")

    assert str(exinfo.value) == "In WebAssembly environments `parallelism` must be 1."

    # test default params
    ph = argon2.PasswordHasher()
    hash = ph.hash("test")

    assert ph.verify(hash, "test") is True
