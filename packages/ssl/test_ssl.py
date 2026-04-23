from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["test", "ssl"], pytest_assert_rewrites=False)
def test_ssl(selenium):
    import platform
    import unittest
    import unittest.mock

    from test.libregrtest.main import main

    platform.platform(aliased=True)
    name = "test_ssl"
    ignore_tests = [
        "*test_context_custom_class*",
        "*ThreadedTests*",
        "*ocket*",
        "test_verify_flags",
        "test_subclass",
        "test_lib_reason",
        "test_unwrap",
        "test_bad_server_hostname",
        "test_cert_store_stats",
        "test_ciphers",
        "test_get_ca_certs",
        "test_get_ciphers",
        "test_load_cert_chain",
        "test_load_default_certs_env",
        "test_load_verify_cadata",
        "test_load_verify_locations",
        "test_min_max_version",
    ]
    match_tests = [[pat, False] for pat in ignore_tests]

    try:
        with unittest.mock.patch(
            "test.support.socket_helper.bind_port",
            side_effect=unittest.SkipTest("nope!"),
        ):
            main([name], match_tests=match_tests, verbose=True, verbose3=True)
    except SystemExit as e:
        if e.code != 0:
            raise RuntimeError(f"Failed with code: {e.code}") from None
