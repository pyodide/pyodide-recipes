from gzip import decompress

import pytest
from pytest_pyodide import run_in_pyodide

data = decompress(b"\x1f\x8b\x08\x00\x17%Xh\x02\xff\x0b\xf2ts\xab`a`\x08w\x0csM\xcb-Q\x10````d`bpY\xc3\xc0 \xb0\x91\x89\x81\x85A\x80!%\xb1$\x11$^\x93\xfaI'e\x812\xfb\xa5cE\xa2\x7f\x04\x8f0x\xba\x18+\xc8\x02\xf5\x02i \xc9\xc0\xc0!\x1c\xe2\xe8\xe3\x04dp200\xfbV*8\xe6$\x95\xe62\x8c\x82Q0\nF.\xf0\xf1\x0c\x0e\x11\x03\xd2\x9e~n\xfe\x9e\x01A.\xc0\xc2\x81\x01Q8\x00\x00\x9c\x8f\x1e\xa2\x80\x04\x00\x00")
tags = {"ALBUM": ["My Album"]}

@pytest.mark.parametrize(
    "encoded_data,expected_tags", [[data, tags]]
)
@run_in_pyodide(packages=["pytaglib"])
def test_read(selenium, encoded_data, expected_tags):
    # pytaglib does not support BytesIO
    with open("/tmp/testfile.wav", "wb") as file:
        file.write(encoded_data)

    import taglib

    with taglib.File("/tmp/testfile.wav") as song:
        assert song.tags == expected_tags
