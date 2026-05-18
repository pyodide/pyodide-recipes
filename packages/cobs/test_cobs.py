import pytest
from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["cobs"])
def test_cobs(selenium):
    import pytest
    from cobs import cobs

    assert cobs.encode(b"12345") == b"\x0612345"
    assert cobs.decode(b"\x01\x01\x01\x01") == b"\x00\x00\x00"


@run_in_pyodide(packages=["cobs"])
def test_cobsr(selenium):
    import pytest
    from cobs import cobsr

    assert cobsr.encode(b"\x01") == b"\x02\x01"
    assert cobsr.decode(b"\xFFa") == b"a\xFF"
