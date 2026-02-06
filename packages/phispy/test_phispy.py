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


@run_in_pyodide(packages=["phispy"])
def test_imports():
    """Test that all essential PhiSpy modules can be imported."""
    print("Testing PhiSpy imports...")
    
    # Test main module imports
    import PhiSpyModules
    print("✓ PhiSpyModules imported successfully")
    
    # Test C++ extension import
    import PhiSpyRepeatFinder
    print("✓ PhiSpyRepeatFinder (C++ extension) imported successfully")
    
    # Test submodules
    from PhiSpyModules import main
    print("✓ PhiSpyModules.main imported successfully")
    
    from PhiSpyModules import helper_functions
    print("✓ PhiSpyModules.helper_functions imported successfully")
    
    from PhiSpyModules import classification
    print("✓ PhiSpyModules.classification imported successfully")
    
    print("\nAll imports successful! PhiSpy is ready to use in Pyodide.")
    return True

if __name__ == "__main__":
    try:
        test_phispy_version()
        test_phispy_import()
        test_imports()
        print("\n" + "="*50)
        print("All tests passed! PhiSpy is working in Pyodide.")
        print("="*50)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise

