import pytest
from pytest_pyodide import run_in_pyodide

@run_in_pyodide(packages=[
  "pylimer-tools", "numpy", "micropip"
])
async def test_pylimer_tools_cpp(selenium):
    import numpy as np
    
    from pylimer_tools_cpp import Universe
    from pylimer_tools.calc.structure_analysis import compute_stoichiometric_imbalance


    # Basic test for the compiled part
    universe = Universe(10., 10., 10.)

    assert np.isclose(universe.get_volume(), 10.**3)

    # Basic test for the Python part
    r = compute_stoichiometric_imbalance(universe)

    assert np.isclose(r, 0., atol=1e-12)

