from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["pyskein"])
def test_pyskein(selenium):
    from skein import skein256, skein512, skein1024
    h = skein512()
    h.update(b'Nobody inspects')
    h.update(b' the spammish repetition')
    assert h.digest() == b'\x1bN\x03+\xcb\x1d\xa4Rs\x01\x1c\xa9Ee\xef\x10|f+\x0b\xd3\r[5\xfbS5Ko\xced#\xa5\xeb\x10\xda\xe6\xf3v\xd6\xb2JNQ}\x85\xc7&\xfc\x01\xfb\x87J\x8f\xe2m\xe9Y\x1f\xa5\x9f\xa3\xc7\xd4'
    assert h.digest_size == 64
    assert h.digest_bits == 512
    assert h.block_size == 64
    assert h.block_bits == 512
    assert h.hashed_bits == 312
