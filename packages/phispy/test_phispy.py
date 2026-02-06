from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["phispy"])
def test_phispy_version(selenium):
    import PhiSpyModules
    
    version = PhiSpyModules.__version__
    assert version == "5.0.1"


@run_in_pyodide(packages=["phispy"])
def test_phispy_import(selenium):
    import PhiSpyModules
    
    # Test that basic module can be imported
    assert PhiSpyModules is not None
    assert hasattr(PhiSpyModules, "__version__")
