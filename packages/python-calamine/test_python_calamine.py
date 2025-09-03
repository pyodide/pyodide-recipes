import pathlib
from datetime import date, datetime, time, timedelta

from pytest_pyodide import run_in_pyodide

@run_in_pyodide(
packages=["python-calamine"],
)

async def calamine_test_helper(selenium):
    from python_calamine import CalamineWorkbook
    from pathlib import Path
    from datetime import date, datetime, time, timedelta

    names = ["Sheet1", "Sheet2", "Sheet3", "Merged Cells"]
    data = [
        ["", "", "", "", "", "", "", "", "", ""],
        [
            "String",
            1,
            1.1,
            True,
            False,
            date(2010, 10, 10),
            datetime(2010, 10, 10, 10, 10, 10),
            time(10, 10, 10),
            timedelta(hours=10, minutes=10, seconds=10, microseconds=100000),
            timedelta(hours=255, minutes=10, seconds=10),
        ],
    ]

    reader = CalamineWorkbook.from_object(Path(__file__).parent / "test-data" / "base.xlsx")

    assert names == reader.sheet_names
    assert data == reader.get_sheet_by_index(0).to_python(skip_empty_area=False)


def test_python_calamine(selenium):
    calamine_test_helper(selenium)
