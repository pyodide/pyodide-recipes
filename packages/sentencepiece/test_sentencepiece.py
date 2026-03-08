from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["sentencepiece"])
def test_simple_sentencepiece(selenium):
    import sentencepiece

    processor = sentencepiece.SentencePieceProcessor(model_file='test/test_model.model')
    assert processor.encode('This is a test') == [284, 47, 11, 4, 15, 400]
