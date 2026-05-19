from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["segno"])
def test_segno_make_and_serialize(selenium_standalone):
    import io

    import segno

    qr = segno.make("https://pyodide.org", micro=False, error="m")
    assert qr.is_micro is False
    assert qr.error in {"M", "Q", "H"}

    svg = io.BytesIO()
    png = io.BytesIO()
    txt = io.StringIO()

    qr.save(svg, kind="svg")
    qr.save(png, kind="png", scale=2)
    qr.save(txt, kind="txt", border=1)

    assert b"<svg" in svg.getvalue()
    assert png.getvalue().startswith(b"\x89PNG\r\n\x1a\n")
    assert len(txt.getvalue().splitlines()) > 0


@run_in_pyodide(packages=["segno"])
def test_segno_sequence_and_micro(selenium_standalone):
    import segno

    micro = segno.make("RAIN")
    assert micro.is_micro is True
    assert micro.designator.startswith("M")

    sequence = segno.make_sequence("Day after day, alone on the hill", symbol_count=2)
    assert len(sequence) == 2
    assert all(item.is_micro is False for item in sequence)
