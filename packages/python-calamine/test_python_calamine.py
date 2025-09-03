from pathlib import Path
from pytest_pyodide import run_in_pyodide

@run_in_pyodide(
    packages=["python-calamine"],
)
async def test_python_calamine(selenium):
    from python_calamine import CalamineWorkbook
    from datetime import date, datetime, time, timedelta
    import io

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

    # Load the Excel file from the bytes data passed to the function
    excel_data = selenium.pyodide.globals.get("excel_file_data")
    excel_file = io.BytesIO(excel_data)
    
    # Create the workbook reader
    reader = CalamineWorkbook.from_object(excel_file)

    # Test sheet names
    assert names == reader.sheet_names
    
    # Test sheet data
    actual_data = reader.get_sheet_by_index(0).to_python(skip_empty_area=False)
    assert expected_data == actual_data


def test_python_calamine_wrapper(selenium):
    """Wrapper test function that reads the Excel file and passes bytes to pyodide"""
    # Read the Excel file as bytes
    excel_file_path = Path(__file__).parent / "test-data" / "base.xlsx"
    with open(excel_file_path, "rb") as f:
        excel_file_data = f.read()
    
    # Set the data in pyodide globals so the inner test can access it
    selenium.pyodide.globals["excel_file_data"] = excel_file_data
    
    # Run the actual test
    test_python_calamine(selenium)
