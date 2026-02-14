import pytest
from pytest_pyodide import run_in_pyodide


@pytest.mark.driver_timeout(60)
@run_in_pyodide(packages=["scs", "numpy", "scipy"])
def test_scs_qp(selenium):
    import numpy as np
    import scipy
    import scs

    # Set up the problem data
    P = scipy.sparse.csc_matrix([[3.0, -1.0], [-1.0, 2.0]])
    A = scipy.sparse.csc_matrix([[-1.0, 1.0], [1.0, 0.0], [0.0, 1.0]])
    b = np.array([-1, 0.3, -0.5])
    c = np.array([-1.0, -1.0])

    # Populate dicts with data to pass into SCS
    data = dict(P=P, A=A, b=b, c=c)
    cone = dict(z=1, l=2)

    # Initialize solver
    solver = scs.SCS(data, cone, eps_abs=1e-9, eps_rel=1e-9)
    # Solve!
    sol = solver.solve()

    assert sol["info"]["status"] == "solved"
    assert sol["info"]["iter"] > 0
    assert len(sol["x"]) == 2
    assert len(sol["y"]) == 3
