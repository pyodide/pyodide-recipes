from pathlib import Path
from pytest_pyodide import run_in_pyodide, copy_files_to_pyodide


@copy_files_to_pyodide(
    [(Path(__file__).parent / "test-data" / "base.xlsx", "base.xlsx")]
)
@run_in_pyodide(
    packages=["python-calamine"]
)
def test_python_calamine(selenium):
    from python_calamine import CalamineWorkbook
    from datetime import date, datetime, time, timedelta

    # Test data to verify against
    names = ["Sheet1", "Sheet2", "Sheet3", "Merged Cells"]
    expected_data = [
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

    # Create the workbook reader
    reader = CalamineWorkbook.from_object("base.xlsx")

    # Test sheet names
    assert names == reader.sheet_names

    # Test sheet data
    actual_data = reader.get_sheet_by_index(0).to_python(skip_empty_area=False)
    assert expected_data == actual_data
