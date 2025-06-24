from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["texture2ddecoder"])
def test_texture2ddecoder(selenium):
    import texture2ddecoder

    decoded_data = texture2ddecoder.decode_astc(
        b'\x00' * 4096,
        64, 64,
        4, 4
    )
    assert isinstance(decoded_data, bytes)

    # Expected output size for BGRA format: width * height * 4 bytes/pixel
    expected_output_size = 64 * 64 * 4
    assert len(decoded_data) == expected_output_size
