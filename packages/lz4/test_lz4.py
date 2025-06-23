from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["lz4"])
def test_lz4(selenium):
    import os
    import lz4.frame
    input_data = 20 * 128 * os.urandom(1024)  # Read 20 * 128kb
    compressed = lz4.frame.compress(input_data)
    decompressed = lz4.frame.decompress(compressed)
    assert decompressed == input_data
