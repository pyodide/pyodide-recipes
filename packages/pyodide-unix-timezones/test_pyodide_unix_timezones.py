from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["pyodide-unix-timezones"])
def test_unix_timezones(selenium):
    import struct
    from pathlib import Path

    import unix_timezones  # noqa: F401

    zoneinfo = Path("/usr/share/zoneinfo")
    assert (zoneinfo / "UTC").exists()
    assert (zoneinfo / "tzdata.zi").exists()

    # "Fat" TZif files list every transition in the version 1 data block,
    # and "slim" files leave it empty. See the tzfile(5) man page.
    data = (zoneinfo / "Europe/Brussels").read_bytes()
    assert data[:4] == b"TZif"
    (timecnt,) = struct.unpack(">l", data[32:36])
    assert timecnt > 0
