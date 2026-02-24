import pytest
from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["crcmod"])
def test_crc32(selenium):
    import pytest
    import crcmod.predefined

    crc32 = crcmod.predefined.Crc('crc-32')
    crc32.update(b'123456789')
    assert crc32.crcValue == 0xcbf43926
