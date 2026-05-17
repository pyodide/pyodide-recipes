from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["numpy", "zarr"])
def test_zarr_basic(selenium):
    import numpy as np
    import zarr

    z = zarr.zeros((1000, 1000), chunks=(100, 100), dtype="i4")
    assert z.shape == (1000, 1000)

    z[0, :] = np.arange(1000)
    assert z[0, 1] == 1


@run_in_pyodide(packages=["numpy", "zarr"])
def test_zarr_save_load(selenium):
    import numpy as np
    import zarr

    # test saving and loading
    a1 = np.arange(10)
    zarr.save("/tmp/example.zarr", a1)
    a2 = zarr.load("/tmp/example.zarr")
    np.testing.assert_equal(a1, a2)


@run_in_pyodide(packages=["numpy", "numcodecs", "zarr"])
def test_zarr_blosc_compressor(selenium):
    import numpy as np
    import zarr
    from numcodecs import Blosc

    # test compressor with zarr v2 format
    compressor = Blosc(cname="zstd", clevel=3, shuffle=Blosc.BITSHUFFLE)
    data = np.arange(10000, dtype="i4").reshape(100, 100)
    z = zarr.array(data, chunks=(10, 10), compressor=compressor, zarr_format=2)
    assert z.compressor == compressor


@run_in_pyodide(packages=["numpy", "numcodecs", "zarr"])
def test_zarr_numcodecs_v3(selenium):
    import numpy as np
    import zarr
    from numcodecs import GZip

    # test numcodecs codec as a zarr v3 bytes-to-bytes compressor
    data = np.arange(256, dtype="uint16").reshape(16, 16)
    z = zarr.array(data, chunks=(16, 16), compressors=[GZip(level=1)])
    np.testing.assert_array_equal(z[:], data)


@run_in_pyodide(packages=["numpy", "zarr"])
def test_zarr_sync_wasm(selenium):
    import numpy as np
    import zarr

    # If sync() is broken on WASM this will raise RuntimeError before any IO
    store = zarr.storage.MemoryStore()
    root = zarr.open_group(store=store, mode="w")
    arr = root.require_array("data", shape=(100,), chunks=(10,), dtype="f4")
    arr[:] = np.ones(100, dtype="f4")
    np.testing.assert_array_equal(arr[:], np.ones(100, dtype="f4"))


@run_in_pyodide(packages=["numpy", "zarr"])
def test_zarr_local_store_wasm(selenium):
    import numpy as np
    import zarr

    # exercises the exclusive-write path in LocalStore on Emscripten
    store = zarr.storage.LocalStore("/tmp/test_local.zarr")
    root = zarr.open_group(store=store, mode="w")
    arr = root.require_array("x", shape=(50,), chunks=(10,), dtype="i4")
    arr[:] = np.arange(50)
    np.testing.assert_array_equal(arr[:], np.arange(50))
