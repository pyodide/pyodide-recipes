from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["msgpack-white", "pytest"])
def test_msgpack_white(selenium):
    import msgpack_white
    import pytest

    w = msgpack_white.White()

    # msgpack.dumps({'x': 1}) ==> 81 A1 78 01
    # msgpack.dumps(True)     ==> C3
    assert w.feed(b"\x81\xA1") is None
    assert w.feed(b"\x78\x01\xC3") == 2
    with pytest.raises(ValueError, match="Invalid MessagePack message"):
        w.feed(b"\xC1")
