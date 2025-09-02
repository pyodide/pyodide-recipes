import pytest
from pytest_pyodide import run_in_pyodide

@run_in_pyodide(packages=[
  "pylimer-tools", "numpy", "micropip"
])
def test_pylimer_tools_cpp(selenium):
    import numpy as np
    
    from pylimer_tools_cpp import Universe
    from pylimer_tools.calc.miller_macosko_theory import predict_gelation_point

    import micropip
    await micropip.install("pint")

    # Basic test for the compiled part
    universe = Universe(10., 10., 10.)

    assert np.isclose(universe.get_volume(), 10.**3)

    # Basic test for the Python part
    p_gel = predict_gelation_point(r=1, f=4, b2=1)

    assert np.isclose(p_gel, 0.5773502691896257)

