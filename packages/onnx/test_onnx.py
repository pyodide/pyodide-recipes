from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["onnx"])
def test_onnx_create_check_and_serialize(selenium):
    import onnx
    from onnx import TensorProto, checker, helper

    node = helper.make_node("Relu", ["input"], ["output"])
    graph = helper.make_graph(
        [node],
        "browser_graph",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 2])],
        [helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 2])],
    )
    model = helper.make_model(
        graph,
        producer_name="pyodide-recipes",
        opset_imports=[helper.make_opsetid("", 18)],
    )

    checker.check_model(model)
    payload = model.SerializeToString()
    restored = onnx.load_model_from_string(payload)
    checker.check_model(restored)

    assert payload
    assert restored.graph.name == "browser_graph"
    assert restored.graph.node[0].op_type == "Relu"
