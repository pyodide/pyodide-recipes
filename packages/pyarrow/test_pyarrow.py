import pytest
from pytest_pyodide import run_in_pyodide


@pytest.mark.driver_timeout(120)
@run_in_pyodide(packages=["pyarrow", "numpy", "pandas"])
def test_read_write_parquet(selenium):
    import numpy as np
    import pandas as pd
    import pyarrow as pa

    df = pd.DataFrame(
        {
            "one": [-1, np.nan, 2.5],
            "two": ["foo", "bar", "baz"],
            "three": [True, False, True],
        },
        index=list("abc"),
    )
    table = pa.Table.from_pandas(df)
    import pyarrow.parquet as pq

    pq.write_table(table, "example.parquet")
    table2 = pq.read_table("example.parquet", columns=["one", "three"])
    assert table2["one"] == table["one"]
    assert table2["three"] == table["three"]


@pytest.mark.driver_timeout(120)
@run_in_pyodide(packages=["pyarrow"])
def test_timezone_data(selenium):
    from datetime import datetime

    import pyarrow as pa
    import pyarrow.compute as pc

    # needs the zone files from pyodide-unix-timezones
    arr = pa.array([datetime(2030, 1, 1, 12), datetime(2030, 7, 1, 12)])
    result = pc.assume_timezone(arr, "Europe/Brussels")
    assert pc.strftime(result, format="%z").to_pylist() == ["+0100", "+0200"]
