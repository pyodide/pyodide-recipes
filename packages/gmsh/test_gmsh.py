from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["gmsh"])
def test_gmsh_initialize(selenium):
    import gmsh

    gmsh.initialize()
    assert gmsh.isInitialized() == 1
    gmsh.finalize()


@run_in_pyodide(packages=["gmsh"])
def test_gmsh_mesh_2d(selenium):
    import gmsh

    gmsh.initialize()
    gmsh.model.add("test")

    # Create a square using the built-in GEO kernel
    gmsh.model.geo.addPoint(0, 0, 0, 1.0, 1)
    gmsh.model.geo.addPoint(1, 0, 0, 1.0, 2)
    gmsh.model.geo.addPoint(1, 1, 0, 1.0, 3)
    gmsh.model.geo.addPoint(0, 1, 0, 1.0, 4)
    gmsh.model.geo.addLine(1, 2, 1)
    gmsh.model.geo.addLine(2, 3, 2)
    gmsh.model.geo.addLine(3, 4, 3)
    gmsh.model.geo.addLine(4, 1, 4)
    gmsh.model.geo.addCurveLoop([1, 2, 3, 4], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)
    gmsh.model.geo.synchronize()

    gmsh.model.mesh.generate(2)

    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    assert len(node_tags) > 4  # More than just corner nodes

    gmsh.finalize()
