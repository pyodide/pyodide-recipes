import pytest
from pytest_pyodide import run_in_pyodide


@pytest.mark.driver_timeout(60)
@run_in_pyodide(packages=["fastcan"])
def test_fastcan(selenium):
    from fastcan import FastCan
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LinearRegression
    n_samples = 200
    n_features = 20
    n_classes = 8
    n_informative = 5

    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=n_informative,
        n_redundant=0,
        n_repeated=0,
        n_classes=n_classes,
        n_clusters_per_class=1,
        flip_y=0.0,
        class_sep=10,
        shuffle=False,
        random_state=0,
    )

    reg = LinearRegression().fit(X[:, :n_informative], y)
    gtruth_ssc = reg.score(X[:, :n_informative], y)

    correlation_filter = FastCan(
        n_features_to_select=n_informative,
    )
    correlation_filter.fit(X, y)
    ssc = correlation_filter.scores_.sum()
    assert ssc == pytest.approx(gtruth_ssc)
