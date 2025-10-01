import pytest
from pytest_pyodide import run_in_pyodide


@pytest.mark.driver_timeout(60)
@run_in_pyodide(packages=["plotly"])
def test_plotly_bar_chart(selenium):
    import plotly.express as px

    # Create a simple bar chart
    fig = px.bar(x=["a", "b", "c"], y=[1, 3, 2])

    # Check that the figure object has valid data and layout
    assert fig.data is not None
    assert len(fig.data) == 1
    assert fig.layout is not None

    # Verify that JSON conversion works (for browser rendering)
    js = fig.to_json()
    assert "data" in js
    assert "layout" in js
