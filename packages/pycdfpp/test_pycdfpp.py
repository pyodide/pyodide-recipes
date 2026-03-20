import pytest
from pytest_pyodide import run_in_pyodide
from pytest_pyodide.decorator import copy_files_to_pyodide
import pathlib


_FILE_PATH = str(
    pathlib.Path(__file__).parent
    / "test_data"
    / "mms1_asp1_srvy_l1b_beam_00000000_v01.cdf"
)


@pytest.mark.xfail_browsers(node="FIXME")
@copy_files_to_pyodide(
    file_list=[(_FILE_PATH, "mms1_asp1_srvy_l1b_beam_00000000_v01.cdf")]
)
@run_in_pyodide(packages=["pycdfpp"])
def test_pycdfpp(selenium):
    import pycdfpp

    cdf = pycdfpp.load("mms1_asp1_srvy_l1b_beam_00000000_v01.cdf")
    assert "mms1_asp_epoch" in cdf
