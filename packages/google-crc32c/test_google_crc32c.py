import pytest
from pytest_pyodide import run_in_pyodide

EMPTY = b""
EMPTY_CRC = 0x00000000

# From: https://tools.ietf.org/html/rfc3720#appendix-B.4
#
#   32 bytes of zeroes:
#
#     Byte:        0  1  2  3
#
#        0:       00 00 00 00
#      ...
#       28:       00 00 00 00
#
#      CRC:       aa 36 91 8a

ALL_ZEROS = b"\x00" * 32
ALL_ZEROS_CRC = 0x8A9136AA

#   32 bytes of ones:
#
#     Byte:        0  1  2  3
#
#        0:       ff ff ff ff
#      ...
#       28:       ff ff ff ff
#
#      CRC:       43 ab a8 62

ALL_ONES = b"\xff" * 32
ALL_ONES_CRC = 0x62A8AB43

#
#   32 bytes of incrementing 00..1f:
#
#     Byte:        0  1  2  3
#
#        0:       00 01 02 03
#      ...
#       28:       1c 1d 1e 1f
#
#      CRC:       4e 79 dd 46

INCREMENTING = bytes(range(32))
INCREMENTING_CRC = 0x46DD794E

#
#   32 bytes of decrementing 1f..00:
#
#     Byte:        0  1  2  3
#
#        0:       1f 1e 1d 1c
#      ...
#       28:       03 02 01 00
#
#      CRC:       5c db 3f 11

DECREMENTING = bytes(reversed(range(32)))
DECREMENTING_CRC = 0x113FDB5C


_EXPECTED = [
    (EMPTY, EMPTY_CRC),
    (ALL_ZEROS, ALL_ZEROS_CRC),
    (ALL_ONES, ALL_ONES_CRC),
    (INCREMENTING, INCREMENTING_CRC),
    (DECREMENTING, DECREMENTING_CRC),
]


# adopted from https://github.com/googleapis/python-crc32c/blob/9652503fb296eef101d84b9b631f454cc7c1d538/tests/test___init__.py
@pytest.mark.parametrize("chunk, expected", _EXPECTED)
@run_in_pyodide(packages=["google-crc32c"])
def test_checksum_value(selenium, chunk, expected):
    import google_crc32c
    assert google_crc32c.value(bytes(chunk)) == expected
