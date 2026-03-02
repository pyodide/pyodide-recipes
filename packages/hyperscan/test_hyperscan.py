

@run_in_pyodide(packages=["hyperscan"])
def test_hyperscan(selenium_standalone):
    import hyperscan

    print(hyperscan.Database().info())  # just see if it raises an error
