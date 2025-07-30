from pytest_pyodide import run_in_pyodide

@run_in_pyodide(packages=["bitstring"])
def test_bitstring(selenium):
    from bitstring import BitArray

    a = BitArray('0x3348')
    assert a.hex == '3348'
    assert a.bin == '0011001101001000'
    assert a.uint == 13128
    assert a.bytes == b'3H'
    assert a[10:3:-1].bin == '0101100'
    assert '0b100' + 3*a == BitArray('0x866906690669, 0b000')

    b = BitStream('0x160120f')
    assert b.read(12).hex == '160'
    b.pos = 0
    assert b.read('uint12') == 352

    c = BitArray('0b00010010010010001111')
    assert c.find('0x48') == (8,)
