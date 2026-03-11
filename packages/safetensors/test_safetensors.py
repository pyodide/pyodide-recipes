from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["safetensors", "numpy"])
def test_safetensors(selenium):
    import numpy as np
    from safetensors.numpy import save, load

    tensors = {
        "weight": np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        "bias": np.array([0.1, 0.2], dtype=np.float32),
    }

    data = save(tensors)
    assert isinstance(data, bytes)

    loaded = load(data)
    assert set(loaded.keys()) == {"weight", "bias"}
    np.testing.assert_array_equal(loaded["weight"], tensors["weight"])
    np.testing.assert_array_equal(loaded["bias"], tensors["bias"])
